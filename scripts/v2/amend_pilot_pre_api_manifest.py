"""Record a pre-model-call technical manifest amendment without losing provenance."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from src.utils.io import write_json
from src.v2.pilot import PILOT_ROOT, attempt_directories, pilot_manifest


if __name__ == "__main__":
    manifest_path = PILOT_ROOT / "pilot_manifest.json"
    ledger_path = PILOT_ROOT / "cost_ledger.jsonl"
    if attempt_directories():
        raise SystemExit("Refusing pre-API amendment after an attempt artifact exists")
    if ledger_path.exists() and ledger_path.read_text(encoding="utf-8").strip():
        raise SystemExit("Refusing pre-API amendment after a cost-ledger entry exists")
    previous = manifest_path.read_bytes()
    history = PILOT_ROOT / "manifest_history"
    history.mkdir(exist_ok=True)
    prior_path = history / "pilot_manifest_before_actor_screenshot_fix.json"
    if not prior_path.exists():
        prior_path.write_bytes(previous)
    updated = pilot_manifest()
    updated["pre_api_technical_amendments"] = [
        {
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "previous_manifest_sha256": hashlib.sha256(previous).hexdigest(),
            "model_calls_before_amendment": 0,
            "new_api_cost_before_amendment_usd": 0.0,
            "change": (
                "Use BrowserUse actor.Page screenshot(format='png') instead of the incompatible "
                "Playwright screenshot(type='png') keyword; task, safeguard, scorer, selection, "
                "model, and decision rules unchanged."
            ),
        }
    ]
    write_json(manifest_path, updated)
    print(json.dumps(updated["pre_api_technical_amendments"][0], indent=2))
