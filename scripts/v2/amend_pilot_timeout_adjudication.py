"""Append the structured-timeout adapter amendment before further paid calls."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from src.utils.io import write_json
from src.v2.pilot import PILOT_ROOT, pilot_manifest


SCHEDULED_RUN_ID = "v2__interface_location_access_003__system_warning__r3"


if __name__ == "__main__":
    manifest_path = PILOT_ROOT / "pilot_manifest.json"
    previous_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    previous = manifest_path.read_bytes()
    attempt = PILOT_ROOT / "runs" / SCHEDULED_RUN_ID / "attempt_1"
    if not (attempt / "technical_adjudication.json").exists():
        raise SystemExit("Apply and validate the documented adjudication first")
    history = PILOT_ROOT / "manifest_history"
    history.mkdir(exist_ok=True)
    prior_path = history / "pilot_manifest_before_structured_timeout_adjudication.json"
    if prior_path.exists():
        raise SystemExit("Structured-timeout amendment was already recorded")
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
            "behavioral_rerun_permitted": False,
            "original_attempt_preserved": True,
            "change": (
                "Map the exact structured BrowserUse error 'LLM call timed out after 120 "
                "seconds' to the already frozen timeout_or_step_limit class. Preserve the "
                "original raw and scored artifacts and add hash-linked adjudicated artifacts. "
                "Also repair and test the existing runner wall-clock fallback. No task, generic "
                "safeguard, model, sampling, scorer, cell selection, outcome boundary, or decision "
                "rule changed."
            ),
        }
    )
    updated["post_api_technical_amendments"] = amendments
    write_json(manifest_path, updated)
    print(json.dumps(amendments[-1], indent=2, sort_keys=True))
