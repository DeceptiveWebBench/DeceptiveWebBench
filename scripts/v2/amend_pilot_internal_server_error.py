"""Append the provider Internal Server Error classification amendment before its retry."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from src.utils.io import write_json
from src.v2.pilot import PILOT_ROOT, pilot_manifest


SCHEDULED_RUN_ID = "v2__interface_confirmshame_newsletter_002__ui_warning__r3"


if __name__ == "__main__":
    manifest_path = PILOT_ROOT / "pilot_manifest.json"
    previous_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    previous = manifest_path.read_bytes()
    attempt = PILOT_ROOT / "runs" / SCHEDULED_RUN_ID / "attempt_1"
    adjudication = json.loads((attempt / "technical_adjudication.json").read_text())
    if adjudication.get("adjudication_version") != (
        "protocol-v2-model-service-unavailable-adjudication-1.0"
    ):
        raise SystemExit("Missing validated provider-error adjudication")
    history = PILOT_ROOT / "manifest_history"
    history.mkdir(exist_ok=True)
    prior_path = history / "pilot_manifest_before_internal_server_error_retry.json"
    if prior_path.exists():
        raise SystemExit("Provider-error amendment already recorded")
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
            "original_attempt_preserved": True,
            "original_classification": "configuration_contract_failure",
            "adjudicated_classification": "model_service_unavailable",
            "machine_evidence": "exact structured error: Internal Server Error",
            "single_infrastructure_retry_permitted": True,
            "sdk_hidden_retry": False,
            "behavioral_result_admitted": False,
            "change": (
                "Map only an exact scaffold-recorded provider Internal Server Error to the "
                "already frozen retryable model_service_unavailable invalidity. Resume at "
                "attempt_2 once; no third attempt. No task, warning, model, runtime, scorer, "
                "boundary, selection, or behavior result changed."
            ),
        }
    )
    updated["post_api_technical_amendments"] = amendments
    updated["phase_4_cells"] = previous_payload["phase_4_cells"]
    updated["second_repeat_decision"] = previous_payload["second_repeat_decision"]
    write_json(manifest_path, updated)
    print(json.dumps(amendments[-1], indent=2, sort_keys=True))
