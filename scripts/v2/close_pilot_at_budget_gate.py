"""Close the optional second repeat after the immutable working-budget guard stop."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone

from src.utils.io import write_json
from src.v2.pilot import PILOT_ROOT, pilot_manifest


if __name__ == "__main__":
    manifest_path = PILOT_ROOT / "pilot_manifest.json"
    previous_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    previous = manifest_path.read_bytes()
    budget_path = PILOT_ROOT / "runs/budget_guard_stop.json"
    budget = json.loads(budget_path.read_text(encoding="utf-8"))
    if budget.get("allowed") is not False or budget.get("event") != "budget_guard_stop":
        raise SystemExit("Missing a machine-recorded budget guard stop")
    validation = json.loads((PILOT_ROOT / "artifact_validation_report.json").read_text())
    ledger = [
        json.loads(line)
        for line in (PILOT_ROOT / "cost_ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    known = sum(float(row.get("reconstructed_usd") or 0.0) for row in ledger)
    unknown = sum(int(row.get("cost_unknown") or 0) for row in ledger)

    history = PILOT_ROOT / "manifest_history"
    history.mkdir(exist_ok=True)
    prior_path = history / "pilot_manifest_before_budget_gate_closure.json"
    if prior_path.exists():
        raise SystemExit("Budget-gate closure was already recorded")
    prior_path.write_bytes(previous)

    updated = pilot_manifest()
    updated["status"] = "closed_at_working_budget_gate"
    updated["pre_api_technical_amendments"] = previous_payload.get(
        "pre_api_technical_amendments", []
    )
    updated["post_api_technical_amendments"] = previous_payload.get(
        "post_api_technical_amendments", []
    )
    updated["phase_4_cells"] = previous_payload["phase_4_cells"]
    updated["second_repeat_decision"] = previous_payload["second_repeat_decision"]
    updated["pilot_closure"] = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "previous_manifest_sha256": hashlib.sha256(previous).hexdigest(),
        "reason": "working_budget_guard",
        "budget_guard": budget,
        "valid_cells": validation["valid_selected_cells"],
        "expected_cells": validation["expected_cells"],
        "attempts_checked": validation["attempts_checked"],
        "known_cost_usd": known,
        "unknown_cost_attempts": unknown,
        "conservative_exposure_usd": known + unknown * 1.0,
        "third_repeat_permitted": False,
        "additional_phase_4_calls_permitted": False,
        "formal_collection_permitted": False,
        "formal_authorization": False,
    }
    write_json(manifest_path, updated)
    print(json.dumps(updated["pilot_closure"], indent=2, sort_keys=True))
