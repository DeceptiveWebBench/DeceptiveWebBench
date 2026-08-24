"""Amend freeze hashes after a documented paid technical-invalid attempt."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from src.utils.io import write_json
from src.v2.pilot import PILOT_ROOT, attempt_directories, pilot_manifest


if __name__ == "__main__":
    manifest_path = PILOT_ROOT / "pilot_manifest.json"
    previous_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    previous = manifest_path.read_bytes()
    if attempt_directories():
        raise SystemExit("This amendment is only for the pre-artifact technical failure")
    failures = PILOT_ROOT / "pre_artifact_failures.jsonl"
    if not failures.exists() or not failures.read_text(encoding="utf-8").strip():
        raise SystemExit("Missing preserved pre-artifact failure evidence")
    history = PILOT_ROOT / "manifest_history"
    history.mkdir(exist_ok=True)
    prior_path = history / "pilot_manifest_before_post_done_state_fix.json"
    if not prior_path.exists():
        prior_path.write_bytes(previous)
    updated = pilot_manifest()
    if previous_payload.get("pre_api_technical_amendments"):
        updated["pre_api_technical_amendments"] = previous_payload["pre_api_technical_amendments"]
    updated["post_api_technical_amendments"] = [
        {
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "previous_manifest_sha256": hashlib.sha256(previous).hexdigest(),
            "affected_scheduled_run_id": "v2__interface_location_access_003__no_warning__r2",
            "failed_attempt_id": "preartifact-location-no-warning-20260818-001",
            "model_call_occurred": True,
            "behavioral_result_admitted": False,
            "cost_status": "unknown_conservatively_budgeted_as_usd_1",
            "retry_allowed_basis": "artifact_write_failure_after_agent_done",
            "change": (
                "Capture benchmark state on every BrowserUse step and use the last structured "
                "terminal observation if actor.Page detaches after done; include pre-artifact "
                "unknown cost in every later budget check. Tasks, generic safeguard, model, "
                "scorer, cell selection, and decision rules unchanged."
            ),
        }
    ]
    write_json(manifest_path, updated)
    print(json.dumps(updated["post_api_technical_amendments"][0], indent=2))
