"""Freeze one complete canonical second repeat before any Phase 4 API call."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from src.utils.io import write_json
from src.v2.pilot import (
    PILOT_ROOT,
    WORKING_BUDGET_USD,
    pilot_manifest,
    second_repeat_cells,
)


UNKNOWN_ATTEMPT_CONSERVATIVE_USD = 1.0


if __name__ == "__main__":
    manifest_path = PILOT_ROOT / "pilot_manifest.json"
    previous_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if previous_payload.get("phase_4_cells"):
        raise SystemExit("Complete second repeat was already frozen")
    previous = manifest_path.read_bytes()

    ledger_rows = [
        json.loads(line)
        for line in (PILOT_ROOT / "cost_ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    known_cost = sum(float(row.get("reconstructed_usd") or 0.0) for row in ledger_rows)
    unknown_attempts = sum(int(row.get("cost_unknown") or 0) for row in ledger_rows)
    projected_second_repeat = known_cost
    conservative_current = known_cost + unknown_attempts * UNKNOWN_ATTEMPT_CONSERVATIVE_USD
    projected_total = conservative_current + projected_second_repeat
    if projected_total >= WORKING_BUDGET_USD:
        raise SystemExit(
            f"Projected conservative exposure USD {projected_total:.6f} is not below working cap"
        )

    history = PILOT_ROOT / "manifest_history"
    history.mkdir(exist_ok=True)
    prior_path = history / "pilot_manifest_before_complete_second_repeat.json"
    if prior_path.exists():
        raise SystemExit("Complete second-repeat decision was already recorded")
    prior_path.write_bytes(previous)

    updated = pilot_manifest()
    updated["pre_api_technical_amendments"] = previous_payload.get(
        "pre_api_technical_amendments", []
    )
    updated["post_api_technical_amendments"] = previous_payload.get(
        "post_api_technical_amendments", []
    )
    updated["phase_4_cells"] = [
        {
            "pilot_order": index,
            "planned_order": cell.planned_order,
            "scheduled_run_id": cell.scheduled_run_id,
            "task_id": cell.task_id,
            "condition": cell.safeguard_condition,
            "repeat_id": cell.repeat_id,
            "calibration_repeat": 2,
        }
        for index, cell in enumerate(second_repeat_cells(), start=37)
    ]
    updated["second_repeat_decision"] = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "RUN_ONE_COMPLETE_SECOND_REPEAT",
        "previous_manifest_sha256": hashlib.sha256(previous).hexdigest(),
        "selection": "Second canonical appearance for every one of the 12x3 task-condition pairs",
        "selection_is_outcome_independent": True,
        "all_tasks_and_conditions_included": True,
        "known_cost_before_phase_4_usd": known_cost,
        "unknown_cost_attempts_before_phase_4": unknown_attempts,
        "unknown_attempt_conservative_usd": UNKNOWN_ATTEMPT_CONSERVATIVE_USD,
        "conservative_current_exposure_usd": conservative_current,
        "projected_second_repeat_cost_usd": projected_second_repeat,
        "projected_total_exposure_usd": projected_total,
        "working_budget_usd": WORKING_BUDGET_USD,
        "sampling_uncertainty_basis": (
            "The complete first repeat contains one observation per task-condition and zero "
            "unsafe-No-Warning to trustworthy-warning transitions. One complete, unchanged "
            "repeat can distinguish a persistent pattern from single-run variability and can "
            "therefore change the go/revise recommendation."
        ),
        "task_warning_model_scorer_and_runtime_unchanged": True,
        "third_repeat_permitted": False,
        "formal_collection_permitted": False,
    }
    write_json(manifest_path, updated)
    print(json.dumps(updated["second_repeat_decision"], indent=2, sort_keys=True))
