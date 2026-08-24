"""Record the author's request to complete four missing calibration cells."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone

from src.utils.io import write_json
from src.v2.pilot import HARD_BUDGET_USD, PILOT_ROOT, verify_frozen_manifest


TARGETS = (
    "v2__forced_contact_share_003__ui_warning__r1",
    "v2__interface_perm_001__ui_warning__r1",
    "v2__sneaking_travel_bundle_004__no_warning__r2",
    "v2__forced_identity_upload_004__system_warning__r3",
)


if __name__ == "__main__":
    verify_frozen_manifest()
    manifest_path = PILOT_ROOT / "pilot_manifest.json"
    previous = manifest_path.read_bytes()
    payload = json.loads(previous)
    if payload.get("status") != "closed_at_working_budget_gate":
        raise SystemExit("Expected the working-budget-closed pilot")
    if "post_closure_completion_authorization" in payload:
        raise SystemExit("Post-closure completion was already authorized")

    baseline = PILOT_ROOT / "post_closure_baseline"
    baseline.mkdir(exist_ok=False)
    for name in (
        "calibration_report.md",
        "decision_memo.md",
        "cell_results.csv",
        "artifact_validation_report.json",
        "excluded_or_invalid_attempts.json",
    ):
        shutil.copy2(PILOT_ROOT / name, baseline / name)
    (baseline / "pilot_manifest.json").write_bytes(previous)

    history = PILOT_ROOT / "manifest_history"
    history.mkdir(exist_ok=True)
    history_path = history / "pilot_manifest_before_author_directed_completion.json"
    if history_path.exists():
        raise SystemExit("Author-directed completion was already recorded")
    history_path.write_bytes(previous)

    payload["status"] = "author_directed_post_closure_completion"
    payload["post_closure_completion_authorization"] = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "previous_manifest_sha256": hashlib.sha256(previous).hexdigest(),
        "source": "explicit_author_instruction_in_active_codex_thread",
        "targets": list(TARGETS),
        "budget_limit_usd": HARD_BUDGET_USD,
        "working_budget_override_authorized": True,
        "absolute_hard_limit_unchanged": True,
        "formal_run": False,
        "formal_authorization": False,
        "third_repeat": False,
        "original_attempts_and_reports_preserved": True,
        "nonretryable_invalid_replacement_policy": (
            "Run one append-only supplemental attempt for forced_identity_upload_004 System. "
            "It is a post-closure protocol deviation and must be analyzed both included and "
            "excluded; it does not retroactively change the original retry rule."
        ),
    }
    write_json(manifest_path, payload)
    print(json.dumps(payload["post_closure_completion_authorization"], indent=2))
