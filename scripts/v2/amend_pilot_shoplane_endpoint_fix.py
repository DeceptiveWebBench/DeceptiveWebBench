"""Append the ShopLane terminal-state adapter amendment before Phase 3."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from src.utils.io import write_json
from src.v2.pilot import PILOT_ROOT, pilot_manifest


SCHEDULED_RUN_IDS = (
    "v2__sneaking_pay_001__no_warning__r1",
    "v2__sneaking_pay_001__system_warning__r2",
    "v2__sneaking_pay_001__ui_warning__r3",
)


if __name__ == "__main__":
    manifest_path = PILOT_ROOT / "pilot_manifest.json"
    previous_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    previous = manifest_path.read_bytes()
    for scheduled_run_id in SCHEDULED_RUN_IDS:
        path = PILOT_ROOT / "runs" / scheduled_run_id / "attempt_1/technical_adjudication.json"
        if not path.exists():
            raise SystemExit(f"Missing validated adjudication: {scheduled_run_id}")
    history = PILOT_ROOT / "manifest_history"
    history.mkdir(exist_ok=True)
    prior_path = history / "pilot_manifest_before_shoplane_endpoint_fix.json"
    if prior_path.exists():
        raise SystemExit("ShopLane endpoint amendment was already recorded")
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
            "affected_scheduled_run_ids": list(SCHEDULED_RUN_IDS),
            "behavioral_rerun_permitted": False,
            "original_attempts_preserved": True,
            "change": (
                "Prevent BrowserUse done from overwriting a machine-verified benchmark terminal "
                "event on visual sites that omit the optional route field. Three ShopLane "
                "attempts are corrected only from their task-specific endpoint=true field and "
                "frozen endpoint event; model prose is excluded. No task, generic safeguard, "
                "model, sampling, scorer, cell selection, boundary, or decision rule changed."
            ),
        }
    )
    updated["post_api_technical_amendments"] = amendments
    write_json(manifest_path, updated)
    print(json.dumps(amendments[-1], indent=2, sort_keys=True))
