"""Supplement-oriented Protocol v2 cost summaries; never affects C/S analysis."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from analysis.v2_pipeline import assert_formal_analysis_eligible, load_formal_attempts
from src.v2.artifacts import read_json, validate_attempt_directory
from src.v2.costs import quartiles, reconstructed_or_authoritative_cost
from src.v2.matrix import load_schedule


def load_all_formal_cost_attempts(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for cell in load_schedule():
        run_dir = root / cell.scheduled_run_id
        for attempt_dir in sorted(run_dir.glob("attempt_*")):
            metadata = read_json(attempt_dir / "run_metadata.json")
            assert_formal_analysis_eligible(metadata)
            validate_attempt_directory(attempt_dir, cell=cell)
            records.append(
                {
                    "cell": cell,
                    "metadata": metadata,
                    "scored": read_json(attempt_dir / "scored_outcome.json"),
                    "usage_cost": read_json(attempt_dir / "usage_cost.json"),
                    "attempt_dir": attempt_dir,
                }
            )
    return records


def _number_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "mean": None, "median": None, "q1": None, "q3": None, "iqr": None, "min": None, "max": None}
    q1, med, q3 = quartiles(values)
    return {
        "n": len(values),
        "mean": mean(values),
        "median": med,
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "min": min(values),
        "max": max(values),
    }


def summarize_formal_costs(root: Path) -> dict[str, Any]:
    selected = load_formal_attempts(root)
    attempts = load_all_formal_cost_attempts(root)
    selected_valid = [item for item in selected if item["scored"] is not None]
    selected_records = []
    for item in selected_valid:
        usage = read_json(item["attempt_dir"] / "usage_cost.json")
        selected_records.append({**item, "usage_cost": usage})

    all_costs = [reconstructed_or_authoritative_cost(item["usage_cost"]) for item in attempts]
    known_all_costs = [value for value in all_costs if value is not None]
    valid_costs = [
        reconstructed_or_authoritative_cost(item["usage_cost"]) for item in selected_records
    ]
    known_valid_costs = [value for value in valid_costs if value is not None]
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in selected_records:
        by_condition[item["cell"].safeguard_condition].append(item)

    condition_rows: dict[str, Any] = {}
    for condition in ("no_warning", "system_warning", "ui_warning"):
        items = by_condition[condition]
        costs = [reconstructed_or_authoritative_cost(item["usage_cost"]) for item in items]
        costs = [value for value in costs if value is not None]
        totals = [item["usage_cost"]["trajectory_totals"] for item in items]
        condition_rows[condition] = {
            "cost": _number_summary(costs),
            "median_total_tokens": median(
                [row["total_tokens"] for row in totals if row.get("total_tokens") is not None]
            ) if any(row.get("total_tokens") is not None for row in totals) else None,
            "median_model_calls": median([row["model_calls"] for row in totals]) if totals else None,
            "median_model_latency_seconds": median(
                [row["cumulative_model_latency_seconds"] for row in totals if row.get("cumulative_model_latency_seconds") is not None]
            ) if any(row.get("cumulative_model_latency_seconds") is not None for row in totals) else None,
        }

    no_median = condition_rows["no_warning"]["cost"]["median"]
    def _difference(condition: str) -> float | None:
        value = condition_rows[condition]["cost"]["median"]
        return None if value is None or no_median is None else value - no_median

    retry_attempts = [item for item in attempts if item["metadata"]["attempt_id"] == 2]
    invalid_attempts = [item for item in attempts if item["scored"]["run_validity"] != "valid"]
    overhead_records = {str(item["attempt_dir"]): item for item in [*retry_attempts, *invalid_attempts]}
    overhead_costs = [
        reconstructed_or_authoritative_cost(item["usage_cost"])
        for item in overhead_records.values()
    ]
    overhead_known = [value for value in overhead_costs if value is not None]
    trustworthy = [
        item for item in selected_records if item["scored"]["outcome_label"] == "trustworthy_completion"
    ]
    return {
        "reporting_scope": "supplement_or_artifact_only",
        "cost_does_not_affect_cs_or_validity": True,
        "total_experiment_api_cost": sum(known_all_costs) if len(known_all_costs) == len(all_costs) else None,
        "total_cost_status": "complete" if len(known_all_costs) == len(all_costs) else "partial_or_unavailable",
        "per_valid_run_cost": _number_summary(known_valid_costs),
        "by_condition": condition_rows,
        "descriptive_median_cost_difference": {
            "system_warning_minus_no_warning": _difference("system_warning"),
            "ui_warning_minus_no_warning": _difference("ui_warning"),
        },
        "infrastructure_invalid_and_retry_overhead": {
            "attempts": len(overhead_records),
            "known_cost_usd": sum(overhead_known) if len(overhead_known) == len(overhead_records) else None,
            "status": "complete" if len(overhead_known) == len(overhead_records) else "partial_or_unavailable",
        },
        "cost_per_trustworthy_completion": (
            None if not trustworthy or len(known_valid_costs) != len(valid_costs)
            else sum(known_valid_costs) / len(trustworthy)
        ),
        "cost_per_trustworthy_completion_status": "NA_zero_denominator" if not trustworthy else (
            "available" if len(known_valid_costs) == len(valid_costs) else "unavailable_cost"
        ),
    }

