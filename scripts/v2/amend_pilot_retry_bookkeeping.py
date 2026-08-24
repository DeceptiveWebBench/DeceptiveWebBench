"""Record the technical retry-bookkeeping amendment before the allowed retry."""

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
        raise SystemExit("Retry bookkeeping must be frozen before the retry artifact exists")
    history = PILOT_ROOT / "manifest_history"
    history.mkdir(exist_ok=True)
    (history / "pilot_manifest_before_external_retry_bookkeeping.json").write_bytes(previous)
    updated = pilot_manifest()
    updated["pre_api_technical_amendments"] = previous_payload.get(
        "pre_api_technical_amendments", []
    )
    amendments = list(previous_payload.get("post_api_technical_amendments", []))
    amendments.append(
        {
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "previous_manifest_sha256": hashlib.sha256(previous).hexdigest(),
            "affected_scheduled_run_id": "v2__interface_location_access_003__no_warning__r2",
            "behavioral_result_admitted": False,
            "change": (
                "Count the preserved pre-artifact infrastructure failure as attempt 1, allow "
                "exactly one attempt-2 retry, label it infrastructure_retry, and include the "
                "unknown prior cost in the pre-call budget guard. No behavioral or semantic "
                "configuration changed."
            ),
        }
    )
    updated["post_api_technical_amendments"] = amendments
    write_json(manifest_path, updated)
    print(json.dumps(amendments[-1], indent=2))
