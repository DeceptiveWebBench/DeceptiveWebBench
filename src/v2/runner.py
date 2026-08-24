"""Schedule-driven Protocol v2 runner with formal-write and retry guards."""

from __future__ import annotations

import json
import base64
import hashlib
import time
import uuid
from collections.abc import Callable, Iterable
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.utils.io import ensure_dir, project_root, write_json
from src.v2.artifacts import ARTIFACT_SCHEMA_VERSION
from src.v2.costs import assess_smoke_budget, calculate_usage_cost
from src.v2.matrix import (
    ScheduledCell,
    load_schedule,
    randomization_recomputation_status,
    schedule_sha256,
)
from src.v2.runtime_config import RuntimeConfig, load_runtime_config
from src.v2.scorer import RETRYABLE_INFRASTRUCTURE_INVALIDITY_CODES, score_attempt
from src.v2.state_machine import TaskRunState
from src.v2.timeouts import AttemptWallClockTimeout, enforce_wall_clock_timeout
from src.v2.safeguards import warning_config_path, warning_version


AttemptExecutor = Callable[[ScheduledCell, int, str], dict[str, Any]]
UNRESOLVED_MARKERS = (
    "UNRESOLVED",
    "pending_author",
    "blocked_pending",
    "candidate_pending",
    "REQUIRES FIRST API-BACKED SMOKE CONFIRMATION",
)


class FormalRunGuardError(RuntimeError):
    """Raised before any formal output directory can be created."""


class SmokeRunGuardError(RuntimeError):
    """Raised before an API-backed smoke can create output."""


def freeze_manifest_path() -> Path:
    return project_root() / "configs" / "v2" / "freeze_manifest.yaml"


def load_freeze_manifest() -> dict[str, Any]:
    with freeze_manifest_path().open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _walk_values(value: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_values(child, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_values(child, f"{path}[{index}]")
    else:
        yield path, value


def collect_formal_preflight_issues(manifest: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if manifest.get("formal_authorization") is not True:
        issues.append("formal_authorization is not true")
    for path, value in _walk_values(manifest):
        text = str(value)
        if any(marker.lower() in text.lower() for marker in UNRESOLVED_MARKERS):
            issues.append(f"{path} is unresolved")
    key_status = randomization_recomputation_status()
    if key_status["status"] != "verified":
        issues.append(key_status["reason"])
    runtime = load_runtime_config()
    if runtime.model.get("access_verified") is not True:
        issues.append("selected model access is not verified by an API-backed smoke")
    if runtime.formal.get("authorization") is not True:
        issues.append("active runtime formal authorization is not true")
    if runtime.formal.get("budget_usd") is None:
        issues.append("formal API budget is not frozen from smoke evidence")
    return sorted(set(issues))


def assert_formal_write_allowed(*, explicit_author_confirmation: bool) -> None:
    if not explicit_author_confirmation:
        raise FormalRunGuardError("Explicit --author-confirmed authorization is required")
    issues = collect_formal_preflight_issues(load_freeze_manifest())
    if issues:
        raise FormalRunGuardError("Formal preflight failed: " + "; ".join(issues))


class ProtocolV2Runner:
    def __init__(
        self,
        *,
        executor: AttemptExecutor,
        formal_run: bool = False,
        explicit_author_confirmation: bool = False,
        output_root: Path | None = None,
        context_id_factory: Callable[[ScheduledCell, int], str] | None = None,
        runtime_config: RuntimeConfig | None = None,
        smoke_api_run: bool = False,
        explicit_smoke_authorization: bool = False,
        collection_scope: str | None = None,
        collection_id: str | None = None,
        budget_limit_usd: float | None = None,
        budget_prior_records: list[dict[str, Any]] | None = None,
        external_retry_reason: str | None = None,
    ):
        self.executor = executor
        self.formal_run = formal_run
        self.runtime = runtime_config or load_runtime_config()
        self.smoke_api_run = smoke_api_run
        self.explicit_smoke_authorization = explicit_smoke_authorization
        self.explicit_author_confirmation = explicit_author_confirmation
        self.collection_scope = collection_scope
        self.collection_id = collection_id
        self.budget_limit_usd = (
            float(budget_limit_usd)
            if budget_limit_usd is not None
            else float(self.runtime.smoke_budget["maximum_usd"])
        )
        self.external_retry_reason = external_retry_reason
        if self.budget_limit_usd <= 0 or self.budget_limit_usd > float(
            self.runtime.smoke_budget["maximum_usd"]
        ):
            raise SmokeRunGuardError("Budget limit must be positive and within the hard runtime cap")
        if collection_scope == "calibration_pilot" and not collection_id:
            raise SmokeRunGuardError("Calibration pilot requires a collection_id")
        if smoke_api_run and not explicit_smoke_authorization:
            raise SmokeRunGuardError("Explicit smoke authorization is required before API output")
        if smoke_api_run and formal_run:
            raise SmokeRunGuardError("A smoke run cannot be marked formal")
        if formal_run:
            assert_formal_write_allowed(explicit_author_confirmation=explicit_author_confirmation)
            default_root = project_root() / "logs" / "v2" / "formal"
        else:
            default_root = project_root() / "logs" / "v2" / "smoke"
        self.output_root = output_root or default_root
        self.context_id_factory = context_id_factory or (
            lambda _cell, _attempt_id: str(uuid.uuid4())
        )
        self._usage_cost_records: list[dict[str, Any]] = []
        if budget_prior_records:
            self._usage_cost_records.extend(dict(item) for item in budget_prior_records)
        if self.smoke_api_run and self.output_root.exists():
            for path in sorted(self.output_root.glob("*/attempt_*/usage_cost.json")):
                try:
                    value = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if isinstance(value, dict):
                    self._usage_cost_records.append(value)

    def run(self, cells: Iterable[ScheduledCell] | None = None) -> list[dict[str, Any]]:
        selected_cells = tuple(cells) if cells is not None else load_schedule()
        results: list[dict[str, Any]] = []
        for cell in selected_cells:
            results.append(self._run_cell(cell))
        return results

    def _run_cell(self, cell: ScheduledCell) -> dict[str, Any]:
        attempts: list[dict[str, Any]] = []
        clean_context_ids: set[str] = set()
        prior_invalidity: str | None = self.external_retry_reason
        cell_root = self.output_root / cell.scheduled_run_id
        existing_ids = sorted(
            int(path.name.removeprefix("attempt_"))
            for path in cell_root.glob("attempt_*")
            if path.is_dir() and path.name.removeprefix("attempt_").isdigit()
        ) if cell_root.exists() else []
        if self.formal_run and existing_ids:
            raise FormalRunGuardError(
                f"Formal artifacts already exist for {cell.scheduled_run_id}; refusing to append or overwrite"
            )
        first_attempt_id = (
            existing_ids[-1] + 1
            if existing_ids
            else (2 if self.external_retry_reason else 1)
        )
        candidate_attempt_ids = (
            (first_attempt_id,)
            if self.external_retry_reason
            else (first_attempt_id, first_attempt_id + 1)
        )
        for invocation_attempt, attempt_id in enumerate(
            candidate_attempt_ids, start=1
        ):
            if self.smoke_api_run:
                budget = assess_smoke_budget(
                    self._usage_cost_records,
                    budget_usd=self.budget_limit_usd,
                    conservative_next_attempt_cost_usd=float(
                        self.runtime.smoke_budget["conservative_next_attempt_estimate_usd"]
                    ),
                )
                if not budget.allowed:
                    payload = {
                        **budget.to_dict(),
                        "scheduled_run_id": cell.scheduled_run_id,
                        "attempt_id": attempt_id,
                        "formal_run": False,
                        "behavioral_outcome": None,
                        "scored": False,
                    }
                    ensure_dir(self.output_root)
                    write_json(self.output_root / "budget_guard_stop.json", payload)
                    return {
                        "scheduled_run_id": cell.scheduled_run_id,
                        "attempts": attempts,
                        "operational_stop": payload,
                    }
            clean_context_id = self.context_id_factory(cell, attempt_id)
            if clean_context_id in clean_context_ids:
                raise RuntimeError("Browser context identity was reused")
            clean_context_ids.add(clean_context_id)
            started_at = datetime.now(timezone.utc)
            started = time.monotonic()
            try:
                with enforce_wall_clock_timeout(
                    float(self.runtime.limits["wall_clock_timeout_seconds"])
                ):
                    raw = dict(self.executor(cell, attempt_id, clean_context_id))
            except AttemptWallClockTimeout:
                state = TaskRunState.create(
                    cell.task_id, cell.scheduled_run_id, attempt_id=attempt_id
                )
                state.timeout("wall_clock_timeout")
                raw = state.raw()
                raw.update(
                    {
                        "trajectory": list(raw["events"]),
                        "actions": ["wall_clock_timeout"],
                        "screenshots": [],
                        "dom_state_evidence": {"status": "unavailable_due_to_forced_timeout"},
                        "model_calls_usage": [],
                        "provider_reported_cost": None,
                    }
                )
            screenshot_payloads = raw.pop("_screenshot_payloads", [])
            if not isinstance(screenshot_payloads, list):
                raise ValueError("_screenshot_payloads must be a list")
            ended_at = datetime.now(timezone.utc)
            attempt_wall_seconds = time.monotonic() - started
            raw.update(
                {
                    "scheduled_run_id": cell.scheduled_run_id,
                    "attempt_id": attempt_id,
                    "formal_run": self.formal_run,
                    "clean_context_id": clean_context_id,
                    "artifact_schema_version": raw.get(
                        "artifact_schema_version", ARTIFACT_SCHEMA_VERSION
                    ),
                    "synthetic_fixture": bool(raw.get("synthetic_fixture", False)),
                    "agent_model_call": bool(raw.get("agent_model_call", False)),
                    "retry_status": (
                        "infrastructure_retry"
                        if self.external_retry_reason or invocation_attempt > 1
                        else "initial_attempt"
                    ),
                    "retry_reason": prior_invalidity,
                }
            )
            calls = raw.pop("model_calls_usage", [])
            if not isinstance(calls, list):
                raise ValueError("model_calls_usage must be a list")
            usage_cost = calculate_usage_cost(
                calls,
                provider_reported_cost=raw.pop("provider_reported_cost", None),
                synthetic_no_model_call=bool(
                    raw["synthetic_fixture"] and not raw["agent_model_call"]
                ),
            )
            limiter_trigger = None
            for event in reversed(raw.get("events") or []):
                if isinstance(event, dict) and event.get("limiter_trigger"):
                    limiter_trigger = event["limiter_trigger"]
                    break
            timing = {
                "attempt_started_at_utc": started_at.isoformat(),
                "attempt_ended_at_utc": ended_at.isoformat(),
                "wall_clock_seconds": attempt_wall_seconds,
                "model_call_latencies_seconds": [call.get("latency_seconds") for call in calls],
                "cumulative_model_latency_seconds": usage_cost["trajectory_totals"].get(
                    "cumulative_model_latency_seconds"
                ),
                "browser_tool_seconds": raw.get("browser_tool_seconds"),
                "browser_tool_time_availability": (
                    "available" if raw.get("browser_tool_seconds") is not None else "unavailable"
                ),
                "termination_at_utc": ended_at.isoformat(),
                "limiter_trigger": limiter_trigger,
            }
            raw["timing"] = timing
            raw["usage_cost"] = usage_cost
            if screenshot_payloads:
                raw["screenshots"] = [
                    f"screenshots/{str(item.get('name') or f'step_{index:03d}').strip()}.png"
                    for index, item in enumerate(screenshot_payloads)
                ]
            scored = score_attempt(raw)
            attempts.append(scored.to_dict())
            self._write_attempt(
                cell, attempt_id, raw, scored.to_dict(), usage_cost, screenshot_payloads
            )
            self._usage_cost_records.append(usage_cost)
            if scored.run_validity == "valid":
                break
            if scored.run_validity not in RETRYABLE_INFRASTRUCTURE_INVALIDITY_CODES:
                break
            prior_invalidity = scored.run_validity
            if invocation_attempt == 2:
                break
        return {"scheduled_run_id": cell.scheduled_run_id, "attempts": attempts}

    def _write_attempt(
        self,
        cell: ScheduledCell,
        attempt_id: int,
        raw: dict[str, Any],
        scored: dict[str, Any],
        usage_cost: dict[str, Any],
        screenshot_payloads: list[dict[str, Any]],
    ) -> None:
        run_dir = self.output_root / cell.scheduled_run_id / f"attempt_{attempt_id}"
        run_dir.parent.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(exist_ok=False)
        screenshot_manifest: list[dict[str, Any]] = []
        if screenshot_payloads:
            screenshot_dir = run_dir / "screenshots"
            screenshot_dir.mkdir()
            for index, item in enumerate(screenshot_payloads):
                name = str(item.get("name") or f"step_{index:03d}").strip()
                if not name.replace("_", "").replace("-", "").isalnum():
                    raise ValueError(f"Unsafe screenshot name: {name!r}")
                payload = item.get("png_base64")
                if not isinstance(payload, str) or not payload:
                    raise ValueError("Screenshot payload must be nonempty base64")
                try:
                    image = base64.b64decode(payload, validate=True)
                except Exception as exc:
                    raise ValueError("Screenshot payload is not valid base64") from exc
                if not image.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise ValueError("Screenshot payload is not PNG")
                relative = f"screenshots/{name}.png"
                target = run_dir / relative
                target.write_bytes(image)
                screenshot_manifest.append(
                    {
                        "path": relative,
                        "sha256": hashlib.sha256(image).hexdigest(),
                        "bytes": len(image),
                        "source_step": item.get("source_step"),
                    }
                )
            raw["screenshots"] = [item["path"] for item in screenshot_manifest]
        scope = self.collection_scope or (
            "formal" if self.formal_run else (
                "synthetic_fixture" if raw.get("synthetic_fixture") else "nonformal_smoke"
            )
        )
        metadata = {
            **asdict(cell),
            "run_id": f"{cell.scheduled_run_id}__attempt_{attempt_id}",
            "attempt_id": attempt_id,
            "formal_run": self.formal_run,
            "synthetic_fixture": bool(raw.get("synthetic_fixture", False)),
            "agent_model_call": bool(raw.get("agent_model_call", False)),
            "clean_context_id": raw["clean_context_id"],
            "artifact_schema_version": raw["artifact_schema_version"],
            "schedule_sha256": raw.get("schedule_sha256", schedule_sha256()),
            "site_url": raw.get("site_url"),
            "prompt_capture": raw.get("prompt_capture"),
            "delivery_evidence": raw.get("delivery_evidence"),
            "adapter_status": raw.get("adapter_status"),
            "configuration": {
                "model_provider": self.runtime.model["provider"],
                "model_id": self.runtime.model["documented_model_identifier"],
                "model_family": self.runtime.model["intended_model_family"],
                "api_request_version": self.runtime.model.get("request_schema"),
                "region_or_inference_profile": self.runtime.model["endpoint_region"],
                "endpoint_service": self.runtime.model["endpoint_service"],
                "request_path": self.runtime.model["request_path"],
                "access_verified": self.runtime.model["access_verified"],
                "scaffold": self.runtime.raw["scaffold"]["name"],
                "scaffold_version": self.runtime.raw["scaffold"]["version"],
                "runtime_config_version": self.runtime.raw["runtime_config_version"],
                "runtime_config_sha256": self.runtime.sha256,
            },
            "sampling": dict(self.runtime.sampling),
            "execution_limits": dict(self.runtime.limits),
            "retry": {
                "status": raw["retry_status"],
                "reason": raw["retry_reason"],
                "provider_sdk_total_attempts": self.runtime.retry[
                    "provider_sdk_total_attempts"
                ],
            },
            "timing": raw["timing"],
            "usage_cost_summary": usage_cost["trajectory_totals"],
            "collection_scope": scope,
            "collection_id": self.collection_id,
            "safeguard_version": warning_version(),
            "safeguard_config_sha256": hashlib.sha256(
                warning_config_path().read_bytes()
            ).hexdigest(),
            "screenshot_manifest": screenshot_manifest,
        }
        write_json(run_dir / "run_metadata.json", metadata)
        write_json(run_dir / "raw_state.json", raw)
        write_json(run_dir / "scored_outcome.json", scored)
        write_json(run_dir / "usage_cost.json", usage_cost)


def read_attempt_artifact(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
