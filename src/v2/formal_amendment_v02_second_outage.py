"""Second append-only endpoint-outage amendment in formal v0.2 Repeat 1."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.utils.io import write_json
from src.v2.formal_repeat1_v02 import FORMAL_ROOT, FormalV02Runner, repeat1_cells
from src.v2.runner import ProtocolV2Runner


AMENDMENT_ID = "formal-v02-repeat1-bedrock-endpoint-outage-2-20260822"
TARGET_RUN_ID = "v2__interface_confirmshame_newsletter_002__system_warning__r1"
TARGET_ATTEMPT = FORMAL_ROOT / "runs" / TARGET_RUN_ID / "attempt_1"
EXPECTED_ERROR = 'Could not connect to the endpoint URL: "https://bedrock-runtime.us-east-1.amazonaws.com/model/qwen.qwen3-vl-235b-a22b/converse"'


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_adjudication():
    scored = json.loads((TARGET_ATTEMPT / "scored_outcome.json").read_text())
    raw = json.loads((TARGET_ATTEMPT / "raw_state.json").read_text())
    usage = json.loads((TARGET_ATTEMPT / "usage_cost.json").read_text())
    errors = [str(r.get("error") or "") for a in raw.get("actions") or [] for r in a.get("result") or [] if r.get("error")]
    if scored.get("run_validity") != "configuration_contract_failure" or errors != [EXPECTED_ERROR]:
        raise RuntimeError("Second outage evidence does not match the exact structured contract")
    if usage.get("trajectory_totals", {}).get("model_calls") != 0 or raw.get("agent_model_call"):
        raise RuntimeError("Second outage must precede every completed model call")
    record = {
        "amendment_id": AMENDMENT_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scheduled_run_id": TARGET_RUN_ID,
        "attempt_id": 1,
        "original_artifacts_unchanged": True,
        "original_hashes": {n:_sha256(TARGET_ATTEMPT/n) for n in ("run_metadata.json","raw_state.json","scored_outcome.json","usage_cost.json")},
        "structured_error": EXPECTED_ERROR,
        "adjudicated_infrastructure_class": "model_service_unavailable",
        "retry_eligible_under_frozen_allowlist": True,
        "maximum_additional_attempts": 1,
        "behavioral_evidence_available": False,
        "semantic_or_scorer_change": False,
    }
    out = FORMAL_ROOT / "amendments" / f"{AMENDMENT_ID}.json"; out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        old=json.loads(out.read_text())
        if old.get("original_hashes") != record["original_hashes"]: raise RuntimeError("Existing amendment mismatch")
        return old
    write_json(out, record); return record


class SecondEndpointRetryRunner(FormalV02Runner):
    def _run_cell(self, cell):
        if cell.scheduled_run_id != TARGET_RUN_ID or cell.repeat_id != 1: raise RuntimeError("Wrong amendment cell")
        create_adjudication(); self.formal_run=False
        try: return ProtocolV2Runner._run_cell(self, cell)
        finally: self.formal_run=True

    def _write_attempt(self, cell, attempt_id, raw, scored, usage_cost, screenshot_payloads):
        if attempt_id != 2: raise RuntimeError("Only attempt 2 is authorized")
        raw["formal_run"]=True; old=self.formal_run; self.formal_run=True
        try: return FormalV02Runner._write_attempt(self,cell,attempt_id,raw,scored,usage_cost,screenshot_payloads)
        finally: self.formal_run=old


def target_cell(): return next(c for c in repeat1_cells() if c.scheduled_run_id==TARGET_RUN_ID)
