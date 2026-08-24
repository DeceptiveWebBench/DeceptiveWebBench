"""Serial, budget-guarded runner for the preregistered generic calibration phases."""

from __future__ import annotations

import argparse
import os

from src.utils.site_http_server import serve_project_root
from src.v2.pilot import (
    PILOT_ID,
    PILOT_ROOT,
    WORKING_BUDGET_USD,
    cell_requires_execution,
    external_retry_reason_for_cell,
    phase_cells,
    phase_is_valid,
    prepare_pilot_root,
    pre_artifact_budget_records,
    selected_attempt,
    sync_cost_ledger,
    verify_frozen_manifest,
    write_reports,
)
from src.v2.runner import ProtocolV2Runner
from src.v2.smoke_executor import make_smoke_executor


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, choices=(1, 2, 3, 4), required=True)
    parser.add_argument("--author-confirmed", action="store_true", required=True)
    args = parser.parse_args()
    if not args.author_confirmed:
        raise SystemExit("Explicit author confirmation is required")
    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        raise SystemExit("Missing credential variable AWS_BEARER_TOKEN_BEDROCK")
    prepare_pilot_root()
    verify_frozen_manifest()
    if args.phase >= 2 and not phase_is_valid(1):
        raise SystemExit("Phase 1 technical gate has not passed")
    if args.phase >= 3 and not phase_is_valid(2):
        raise SystemExit("Phase 2 technical gate has not passed")
    if args.phase >= 4 and not phase_is_valid(3):
        raise SystemExit("Phase 3 technical gate has not passed")
    targets = [cell for cell in phase_cells(args.phase) if cell_requires_execution(cell)]
    with serve_project_root() as base_url:
        for index, cell in enumerate(targets, start=1):
            print(
                f"[{index}/{len(targets)}] {cell.scheduled_run_id} "
                f"({cell.safeguard_condition})"
            )
            runner = ProtocolV2Runner(
                executor=make_smoke_executor(base_url=base_url),
                output_root=PILOT_ROOT / "runs",
                smoke_api_run=True,
                explicit_smoke_authorization=True,
                collection_scope="calibration_pilot",
                collection_id=PILOT_ID,
                budget_limit_usd=WORKING_BUDGET_USD,
                budget_prior_records=pre_artifact_budget_records(),
                external_retry_reason=external_retry_reason_for_cell(cell),
            )
            result = runner.run([cell])[0]
            sync_cost_ledger()
            attempts = result.get("attempts") or []
            if result.get("operational_stop"):
                write_reports()
                raise SystemExit("Pilot stopped by working-budget guard")
            if not attempts or attempts[-1].get("run_validity") != "valid":
                write_reports()
                raise SystemExit(
                    f"Technical gate failed for {cell.scheduled_run_id}; preserve artifacts and diagnose"
                )
    outcome = write_reports()
    print(outcome)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
