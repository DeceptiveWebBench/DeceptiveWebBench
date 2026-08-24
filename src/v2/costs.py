"""Provider-usage normalization, frozen-price reconstruction, and smoke budget guard."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

import yaml

from src.utils.io import project_root


COST_CALCULATION_VERSION = "protocol-v2-cost-calculator-1.0"
USAGE_COST_SCHEMA_VERSION = "protocol-v2-usage-cost-1.0"


class CostContractError(ValueError):
    """Raised when pricing, usage, or budget evidence is internally inconsistent."""


def pricing_config_path() -> Path:
    return project_root() / "configs/v2/pricing.yaml"


def load_pricing_config(path: Path | None = None) -> dict[str, Any]:
    selected = path or pricing_config_path()
    raw = yaml.safe_load(selected.read_text(encoding="utf-8")) or {}
    required = {
        "pricing_config_version",
        "pricing_date",
        "currency",
        "unit",
        "source",
        "model",
        "rates_per_1m_tokens",
    }
    missing = required - set(raw)
    if missing:
        raise CostContractError(f"Pricing config is missing fields: {sorted(missing)}")
    if raw["currency"] != "USD" or raw["unit"] != "per_1m_tokens":
        raise CostContractError("Protocol v2 pricing must use USD per 1M tokens")
    if raw["model"].get("documented_model_identifier") != "qwen.qwen3-vl-235b-a22b":
        raise CostContractError("Pricing model does not match the active Qwen3 VL candidate")
    if not str(raw["source"].get("url") or "").startswith("https://aws.amazon.com/"):
        raise CostContractError("Pricing source must be an official AWS URL")
    for field in ("input_tokens", "output_tokens"):
        value = raw["rates_per_1m_tokens"].get(field)
        if not isinstance(value, (int, float)) or value < 0:
            raise CostContractError(f"Invalid pricing rate: {field}")
    return raw


def _nullable_nonnegative_int(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CostContractError(f"{field} must be a non-negative integer or null")
    return value


def normalize_bedrock_usage(
    usage: dict[str, Any] | None,
    *,
    call_id: str,
    latency_seconds: float | None,
) -> dict[str, Any]:
    """Normalize only token fields actually exposed by a Bedrock response."""

    usage = dict(usage or {})
    cache_creation = usage.get("cache_creation") or {}
    if not isinstance(cache_creation, dict):
        raise CostContractError("cache_creation usage must be an object when present")
    record = {
        "call_id": call_id,
        "input_tokens": _nullable_nonnegative_int(
            usage.get("input_tokens", usage.get("inputTokens")), "input_tokens"
        ),
        "output_tokens": _nullable_nonnegative_int(
            usage.get("output_tokens", usage.get("outputTokens")), "output_tokens"
        ),
        "reasoning_tokens": None,
        "reasoning_tokens_availability": "not_exposed_separately_by_selected_endpoint",
        "cached_input_tokens": _nullable_nonnegative_int(
            usage.get("cache_read_input_tokens"), "cache_read_input_tokens"
        ),
        "cache_creation_input_tokens": _nullable_nonnegative_int(
            usage.get("cache_creation_input_tokens"), "cache_creation_input_tokens"
        ),
        "cache_creation_5m_input_tokens": _nullable_nonnegative_int(
            cache_creation.get("ephemeral_5m_input_tokens"),
            "cache_creation.ephemeral_5m_input_tokens",
        ),
        "cache_creation_1h_input_tokens": _nullable_nonnegative_int(
            cache_creation.get("ephemeral_1h_input_tokens"),
            "cache_creation.ephemeral_1h_input_tokens",
        ),
        "latency_seconds": None if latency_seconds is None else float(latency_seconds),
    }
    primary = (record["input_tokens"], record["output_tokens"])
    record["usage_availability"] = "complete" if all(v is not None for v in primary) else (
        "unavailable" if all(v is None for v in primary) else "partial"
    )
    known_tokens = [
        record[key]
        for key in (
            "input_tokens",
            "output_tokens",
            "cached_input_tokens",
            "cache_creation_input_tokens",
        )
        if record[key] is not None
    ]
    record["total_tokens"] = sum(known_tokens) if known_tokens else None
    return record


# Backward-compatible name for historical fixtures and archived reports.
normalize_anthropic_usage = normalize_bedrock_usage


def _component_cost(tokens: int | None, rate: float | int | None) -> float | None:
    if tokens is None or rate is None:
        return None
    return tokens * float(rate) / 1_000_000


def calculate_usage_cost(
    calls: list[dict[str, Any]],
    *,
    provider_reported_cost: float | None = None,
    pricing: dict[str, Any] | None = None,
    synthetic_no_model_call: bool = False,
) -> dict[str, Any]:
    pricing = pricing or load_pricing_config()
    rates = pricing["rates_per_1m_tokens"]
    if provider_reported_cost is not None:
        provider_reported_cost = float(provider_reported_cost)
        if not math.isfinite(provider_reported_cost) or provider_reported_cost < 0:
            raise CostContractError("provider_reported_cost must be finite and non-negative")

    if not calls:
        reconstructed = 0.0 if synthetic_no_model_call else None
        status = "synthetic_no_model_call" if synthetic_no_model_call else (
            "authoritative" if provider_reported_cost is not None else "unavailable"
        )
        totals = {
            "input_tokens": None,
            "output_tokens": None,
            "reasoning_tokens": None,
            "cached_input_tokens": None,
            "cache_creation_input_tokens": None,
            "total_tokens": None,
            "model_calls": 0,
            "cumulative_model_latency_seconds": 0.0,
        }
    else:
        totals: dict[str, Any] = {"model_calls": len(calls)}
        for field in (
            "input_tokens",
            "output_tokens",
            "reasoning_tokens",
            "cached_input_tokens",
            "cache_creation_input_tokens",
            "total_tokens",
        ):
            values = [call.get(field) for call in calls]
            totals[field] = sum(values) if all(value is not None for value in values) else None
        latencies = [call.get("latency_seconds") for call in calls]
        totals["cumulative_model_latency_seconds"] = (
            sum(float(value) for value in latencies)
            if all(value is not None for value in latencies)
            else None
        )

        component_costs: list[float] = []
        complete = True
        for call in calls:
            for token_field, rate_field in (
                ("input_tokens", "input_tokens"),
                ("output_tokens", "output_tokens"),
                ("cached_input_tokens", "cache_read_input_tokens"),
                ("cache_creation_5m_input_tokens", "cache_creation_input_tokens_5m"),
                ("cache_creation_1h_input_tokens", "cache_creation_input_tokens_1h"),
            ):
                tokens = call.get(token_field)
                if tokens is None:
                    if token_field in {"input_tokens", "output_tokens"}:
                        complete = False
                    continue
                cost = _component_cost(tokens, rates.get(rate_field))
                if cost is None:
                    complete = False
                else:
                    component_costs.append(cost)
            generic_creation = call.get("cache_creation_input_tokens")
            split_creation = (
                call.get("cache_creation_5m_input_tokens"),
                call.get("cache_creation_1h_input_tokens"),
            )
            if generic_creation not in (None, 0) and all(value is None for value in split_creation):
                complete = False
        reconstructed = sum(component_costs) if component_costs and complete else None
        if provider_reported_cost is not None:
            status = "authoritative" if complete else "authoritative_reconstruction_partial"
        elif complete and reconstructed is not None:
            status = "reconstructed"
        elif component_costs:
            status = "partial"
        else:
            status = "unavailable"

    return {
        "usage_cost_schema_version": USAGE_COST_SCHEMA_VERSION,
        "model_calls_usage": calls,
        "trajectory_totals": totals,
        "provider_reported_cost": provider_reported_cost,
        "reconstructed_cost": reconstructed,
        "cost_currency": pricing["currency"],
        "pricing_date": str(pricing["pricing_date"]),
        "pricing_source_url": pricing["source"]["url"],
        "pricing_unit": pricing["unit"],
        "rates_per_1m_tokens": dict(rates),
        "cost_calculation_version": COST_CALCULATION_VERSION,
        "cost_status": status,
    }


def reconstructed_or_authoritative_cost(record: dict[str, Any]) -> float | None:
    authoritative = record.get("provider_reported_cost")
    if authoritative is not None:
        return float(authoritative)
    reconstructed = record.get("reconstructed_cost")
    return None if reconstructed is None else float(reconstructed)


@dataclass(frozen=True)
class BudgetDecision:
    allowed: bool
    event: str | None
    cumulative_cost_usd: float
    conservative_next_attempt_cost_usd: float
    projected_cost_usd: float
    budget_usd: float
    cost_basis: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "event": self.event,
            "cumulative_cost_usd": self.cumulative_cost_usd,
            "conservative_next_attempt_cost_usd": self.conservative_next_attempt_cost_usd,
            "projected_cost_usd": self.projected_cost_usd,
            "budget_usd": self.budget_usd,
            "cost_basis": self.cost_basis,
        }


def assess_smoke_budget(
    prior_attempt_records: list[dict[str, Any]],
    *,
    budget_usd: float = 10.0,
    conservative_next_attempt_cost_usd: float = 1.0,
) -> BudgetDecision:
    known: list[float] = []
    unknown = 0
    for record in prior_attempt_records:
        value = reconstructed_or_authoritative_cost(record)
        if value is None:
            unknown += 1
        else:
            known.append(value)
    fallback = max([conservative_next_attempt_cost_usd, *known], default=conservative_next_attempt_cost_usd)
    cumulative = sum(known) + unknown * fallback
    projected = cumulative + fallback
    allowed = cumulative < budget_usd and projected < budget_usd
    return BudgetDecision(
        allowed=allowed,
        event=None if allowed else "budget_guard_stop",
        cumulative_cost_usd=cumulative,
        conservative_next_attempt_cost_usd=fallback,
        projected_cost_usd=projected,
        budget_usd=budget_usd,
        cost_basis="authoritative_or_reconstructed_else_conservative_max_observed",
    )


def quartiles(values: list[float]) -> tuple[float, float, float]:
    """Return deterministic Tukey-style Q1/median/Q3 for reporting."""

    if not values:
        raise CostContractError("Cannot calculate quartiles for an empty sequence")
    ordered = sorted(values)
    mid = len(ordered) // 2
    lower = ordered[:mid] or ordered
    upper = ordered[mid + (len(ordered) % 2) :] or ordered
    return median(lower), median(ordered), median(upper)
