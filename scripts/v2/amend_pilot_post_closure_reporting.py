"""Record the post-closure descriptive-reporting amendment without reopening the pilot."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from src.utils.io import write_json
from src.v2.pilot import PILOT_ROOT, pilot_manifest


if __name__ == "__main__":
    manifest_path = PILOT_ROOT / "pilot_manifest.json"
    previous_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    previous = manifest_path.read_bytes()
    if previous_payload.get("status") != "closed_at_working_budget_gate":
        raise SystemExit("Pilot must be closed before recording the reporting amendment")

    history = PILOT_ROOT / "manifest_history"
    history.mkdir(exist_ok=True)
    prior_path = history / "pilot_manifest_before_post_closure_reporting.json"
    if prior_path.exists():
        raise SystemExit("Post-closure reporting amendment was already recorded")
    prior_path.write_bytes(previous)

    updated = pilot_manifest()
    for key in (
        "pre_api_technical_amendments",
        "post_api_technical_amendments",
        "phase_4_cells",
        "second_repeat_decision",
        "pilot_closure",
    ):
        if key in previous_payload:
            updated[key] = previous_payload[key]
    updated["status"] = "closed_at_working_budget_gate"
    updated["post_closure_reporting_amendment"] = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "previous_manifest_sha256": hashlib.sha256(previous).hexdigest(),
        "behavioral_calls_added": 0,
        "behavioral_results_changed": False,
        "pilot_reopened": False,
        "change": (
            "Correct the incomplete second-repeat heading; report count percentages, task "
            "profiles, structured non-completion decomposition, all-attempt cost exposure, "
            "and distinguish the preregistered technical gate from the transparent post-pilot "
            "scientific recommendation. No task, warning, model, scorer, result, or decision "
            "rule used to schedule paid calls changed."
        ),
    }
    write_json(manifest_path, updated)
    print(json.dumps(updated["post_closure_reporting_amendment"], indent=2, sort_keys=True))
