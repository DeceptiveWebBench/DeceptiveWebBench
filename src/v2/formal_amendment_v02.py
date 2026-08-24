"""Append-only technical amendment for a pre-model Bedrock endpoint outage."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.utils.io import write_json
from src.v2.formal_repeat1_v02 import FORMAL_ROOT, FormalV02Runner, repeat1_cells
from src.v2.runner import ProtocolV2Runner


AMENDMENT_ID = "formal-v02-repeat1-bedrock-endpoint-outage-20260822"
TARGET_RUN_ID = "v2__sneaking_pay_001__system_warning__r1"
TARGET_ATTEMPT = FORMAL_ROOT / "runs" / TARGET_RUN_ID / "attempt_1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_endpoint_outage_adjudication() -> dict[str, Any]:
    scored = json.loads((TARGET_ATTEMPT / "scored_outcome.json").read_text(encoding="utf-8"))
    raw = json.loads((TARGET_ATTEMPT / "raw_state.json").read_text(encoding="utf-8"))
    usage = json.loads((TARGET_ATTEMPT / "usage_cost.json").read_text(encoding="utf-8"))
    errors = [
        str(result.get("error") or "")
        for action in raw.get("actions") or []
        for result in action.get("result") or []
        if result.get("error")
    ]
    expected = 'Could not connect to the endpoint URL: "https://bedrock-runtime.us-east-1.amazonaws.com/model/qwen.qwen3-vl-235b-a22b/converse"'
    if scored.get("run_validity") != "configuration_contract_failure":
        raise RuntimeError("Original scorer classification is not the documented adapter fallback")
    if usage.get("trajectory_totals", {}).get("model_calls") != 0 or raw.get("agent_model_call"):
        raise RuntimeError("Endpoint-outage adjudication requires zero completed provider calls")
    if errors != [expected]:
        raise RuntimeError("Structured provider endpoint error does not match the amendment contract")
    record = {
        "amendment_id": AMENDMENT_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scheduled_run_id": TARGET_RUN_ID,
        "attempt_id": 1,
        "original_artifacts_unchanged": True,
        "original_hashes": {name: _sha256(TARGET_ATTEMPT / name) for name in (
            "run_metadata.json", "raw_state.json", "scored_outcome.json", "usage_cost.json"
        )},
        "structured_error": expected,
        "adjudicated_infrastructure_class": "model_service_unavailable",
        "retry_eligible_under_frozen_allowlist": True,
        "maximum_additional_attempts": 1,
        "behavioral_evidence_available": False,
        "semantic_or_scorer_change": False,
    }
    amendment_dir = FORMAL_ROOT / "amendments"
    amendment_dir.mkdir(parents=True, exist_ok=True)
    target = amendment_dir / f"{AMENDMENT_ID}.json"
    if target.exists():
        old = json.loads(target.read_text(encoding="utf-8"))
        for key in ("scheduled_run_id", "attempt_id", "original_hashes", "structured_error", "adjudicated_infrastructure_class"):
            if old.get(key) != record[key]:
                raise RuntimeError("Existing amendment record mismatch")
        return old
    write_json(target, record)
    return record


class AppendOnlyEndpointRetryRunner(FormalV02Runner):
    """Allow only attempt 2 while persisting it as a formal v0.2 artifact."""

    def _run_cell(self, cell):
        if cell.scheduled_run_id != TARGET_RUN_ID or cell.repeat_id != 1:
            raise RuntimeError("Amendment runner is scoped to one frozen cell")
        create_endpoint_outage_adjudication()
        self.formal_run = False
        try:
            return ProtocolV2Runner._run_cell(self, cell)
        finally:
            self.formal_run = True

    def _write_attempt(self, cell, attempt_id, raw, scored, usage_cost, screenshot_payloads):
        if attempt_id != 2:
            raise RuntimeError("Amendment permits only attempt 2")
        raw["formal_run"] = True
        old = self.formal_run
        self.formal_run = True
        try:
            return FormalV02Runner._write_attempt(
                self, cell, attempt_id, raw, scored, usage_cost, screenshot_payloads
            )
        finally:
            self.formal_run = old


def target_cell():
    return next(cell for cell in repeat1_cells() if cell.scheduled_run_id == TARGET_RUN_ID)
