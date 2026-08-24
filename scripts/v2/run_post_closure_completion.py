"""Run only the four author-authorized post-closure calibration cells."""

from __future__ import annotations

import json
import os

from src.utils.io import write_json
from src.utils.site_http_server import serve_project_root
from src.v2.pilot import (
    HARD_BUDGET_USD,
    PILOT_ID,
    PILOT_ROOT,
    phase_cells,
    pre_artifact_budget_records,
    sync_cost_ledger,
    verify_frozen_manifest,
)
from src.v2.runner import ProtocolV2Runner
from src.v2.smoke_executor import make_smoke_executor

from scripts.v2.authorize_post_closure_completion import TARGETS


DEVIATION_TARGET = "v2__forced_identity_upload_004__system_warning__r3"


def main() -> int:
    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        raise SystemExit("Missing credential variable AWS_BEARER_TOKEN_BEDROCK")
    verify_frozen_manifest()
    manifest = json.loads((PILOT_ROOT / "pilot_manifest.json").read_text())
    authorization = manifest.get("post_closure_completion_authorization") or {}
    if tuple(authorization.get("targets") or ()) != TARGETS:
        raise SystemExit("Missing exact author-directed target authorization")
    if authorization.get("budget_limit_usd") != HARD_BUDGET_USD:
        raise SystemExit("Hard-budget authorization mismatch")

    cells = {cell.scheduled_run_id: cell for cell in phase_cells(4)}
    progress_path = PILOT_ROOT / "post_closure_completion_progress.json"
    completed: list[dict[str, object]] = []
    with serve_project_root() as base_url:
        for scheduled_run_id in TARGETS:
            cell = cells[scheduled_run_id]
            existing_valid = any(
                (path / "scored_outcome.json").exists()
                and json.loads((path / "scored_outcome.json").read_text()).get("run_validity")
                == "valid"
                for path in (PILOT_ROOT / "runs" / scheduled_run_id).glob("attempt_*")
            )
            if existing_valid:
                completed.append({"scheduled_run_id": scheduled_run_id, "status": "already_valid"})
                continue
            deviation = scheduled_run_id == DEVIATION_TARGET
            runner = ProtocolV2Runner(
                executor=make_smoke_executor(base_url=base_url),
                output_root=PILOT_ROOT / "runs",
                smoke_api_run=True,
                explicit_smoke_authorization=True,
                collection_scope="calibration_pilot",
                collection_id=PILOT_ID,
                budget_limit_usd=HARD_BUDGET_USD,
                budget_prior_records=pre_artifact_budget_records(),
                external_retry_reason=(
                    "author_authorized_post_closure_protocol_deviation" if deviation else None
                ),
            )
            result = runner.run([cell])[0]
            sync_cost_ledger()
            attempts = result.get("attempts") or []
            entry: dict[str, object] = {
                "scheduled_run_id": scheduled_run_id,
                "protocol_deviation": deviation,
                "attempts": attempts,
            }
            if result.get("operational_stop"):
                entry["status"] = "budget_guard_stop"
                completed.append(entry)
                write_json(progress_path, {"targets": list(TARGETS), "completed": completed})
                raise SystemExit("Stopped before the next API call by the absolute budget guard")
            entry["status"] = (
                "valid" if attempts and attempts[-1].get("run_validity") == "valid" else "invalid"
            )
            completed.append(entry)
            write_json(progress_path, {"targets": list(TARGETS), "completed": completed})
            if entry["status"] != "valid":
                raise SystemExit(f"Technical invalidity in {scheduled_run_id}; preserved and stopped")
    print(json.dumps({"completed": completed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
