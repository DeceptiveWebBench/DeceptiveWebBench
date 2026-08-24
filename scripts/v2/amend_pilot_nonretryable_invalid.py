"""Record the first Phase 4 non-retryable invalid before continuing untouched cells."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from src.utils.io import write_json
from src.v2.pilot import PILOT_ROOT, WORKING_BUDGET_USD, pilot_manifest, second_repeat_cells


SCHEDULED_RUN_ID = "v2__forced_identity_upload_004__system_warning__r3"
UNKNOWN_ATTEMPT_CONSERVATIVE_USD = 1.0


if __name__ == "__main__":
    manifest_path = PILOT_ROOT / "pilot_manifest.json"
    previous_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    previous = manifest_path.read_bytes()
    attempt = PILOT_ROOT / "runs" / SCHEDULED_RUN_ID / "attempt_1"
    scored = json.loads((attempt / "scored_outcome.json").read_text(encoding="utf-8"))
    raw = json.loads((attempt / "raw_state.json").read_text(encoding="utf-8"))
    if scored.get("run_validity") != "configuration_contract_failure":
        raise SystemExit("Expected the preserved non-retryable configuration contract failure")
    errors = [
        str(result.get("error") or "")
        for action in raw.get("actions") or []
        for result in action.get("result") or []
        if isinstance(result, dict)
    ]
    if not any("Failed to validate structured output" in error for error in errors):
        raise SystemExit("Missing machine-recorded structured-output validation evidence")

    ledger = [
        json.loads(line)
        for line in (PILOT_ROOT / "cost_ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    known = sum(float(row.get("reconstructed_usd") or 0.0) for row in ledger)
    unknown = sum(int(row.get("cost_unknown") or 0) for row in ledger)
    phase4_ids = {cell.scheduled_run_id for cell in second_repeat_cells()}
    phase4_costs = [
        float(row["reconstructed_usd"])
        for row in ledger
        if row.get("scheduled_run_id") in phase4_ids
        and row.get("reconstructed_usd") is not None
    ]
    remaining = 36 - len({
        row.get("scheduled_run_id") for row in ledger if row.get("scheduled_run_id") in phase4_ids
    })
    projected_remaining = (sum(phase4_costs) / len(phase4_costs)) * remaining
    projected_total = known + unknown * UNKNOWN_ATTEMPT_CONSERVATIVE_USD + projected_remaining
    if projected_total >= WORKING_BUDGET_USD:
        raise SystemExit(f"Updated Phase 4 projection USD {projected_total:.6f} reaches working cap")

    history = PILOT_ROOT / "manifest_history"
    history.mkdir(exist_ok=True)
    prior_path = history / "pilot_manifest_before_nonretryable_structured_output_invalid.json"
    if prior_path.exists():
        raise SystemExit("Non-retryable invalid amendment was already recorded")
    prior_path.write_bytes(previous)

    updated = pilot_manifest()
    updated["pre_api_technical_amendments"] = previous_payload.get(
        "pre_api_technical_amendments", []
    )
    amendments = list(previous_payload.get("post_api_technical_amendments", []))
    amendments.append(
        {
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "previous_manifest_sha256": hashlib.sha256(previous).hexdigest(),
            "affected_scheduled_run_id": SCHEDULED_RUN_ID,
            "invalidity": "configuration_contract_failure",
            "evidence": "machine-recorded Failed to validate structured output error after prior valid actions",
            "infrastructure_retry_evidence_present": False,
            "behavioral_rerun_permitted": False,
            "original_attempt_preserved": True,
            "operational_change": (
                "A resumed pilot skips any preserved non-retryable invalid cell instead of "
                "silently issuing a prohibited behavioral rerun. It continues only untouched "
                "cells in the already frozen complete second-repeat schedule. Every newly "
                "encountered invalid still stops the serial runner for review."
            ),
            "remaining_cells": remaining,
            "known_cost_usd": known,
            "unknown_cost_attempts": unknown,
            "phase4_mean_cost_usd": sum(phase4_costs) / len(phase4_costs),
            "projected_remaining_cost_usd": projected_remaining,
            "projected_total_exposure_usd": projected_total,
            "working_budget_usd": WORKING_BUDGET_USD,
            "task_warning_model_scorer_and_runtime_unchanged": True,
        }
    )
    updated["post_api_technical_amendments"] = amendments
    updated["phase_4_cells"] = previous_payload["phase_4_cells"]
    updated["second_repeat_decision"] = previous_payload["second_repeat_decision"]
    write_json(manifest_path, updated)
    print(json.dumps(amendments[-1], indent=2, sort_keys=True))
