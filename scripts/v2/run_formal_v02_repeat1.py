"""Run only the author-authorized v0.2 formal Repeat 1 tranche."""

from __future__ import annotations

import argparse
import os

import yaml

from src.utils.site_http_server import serve_project_root
from src.v2.formal_executor_v02 import make_formal_executor
from src.v2.formal_repeat1_v02 import (
    AUTHORIZATION_PATH,
    FORMAL_ROOT,
    FormalV02Runner,
    cell_needs_execution,
    load_authorization,
    prepare_formal_root,
    repeat1_cells,
    sync_ledger,
    validate_requested_tranche,
    write_reports,
)


def _set_status(status: str) -> None:
    raw = yaml.safe_load(AUTHORIZATION_PATH.read_text(encoding="utf-8")) or {}
    raw["status"] = status
    AUTHORIZATION_PATH.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author-confirmed", action="store_true", required=True)
    args = parser.parse_args()
    if not args.author_confirmed:
        raise SystemExit("Explicit author confirmation is required")
    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        raise SystemExit("Missing scoped Bedrock credential")
    load_authorization()
    existing = {cell.scheduled_run_id for cell in repeat1_cells() if not cell_needs_execution(cell)}
    if not existing:
        validate_requested_tranche(
            repeat1_cells(),
            safeguard_version="protocol-v2-generic-safeguard-v0.2",
            collection_id="protocol-v2-generic-safeguard-v0.2-repeat-1",
            budget_usd=8.0,
        )
    prepare_formal_root()
    _set_status("in_progress")
    targets = [cell for cell in repeat1_cells() if cell_needs_execution(cell)]
    try:
        with serve_project_root() as base_url:
            for index, cell in enumerate(targets, start=1):
                print(f"[{index}/{len(targets)}] {cell.scheduled_run_id} ({cell.safeguard_condition})", flush=True)
                runner = FormalV02Runner(
                    executor=make_formal_executor(base_url=base_url),
                    output_root=FORMAL_ROOT / "runs",
                )
                result = runner.run([cell])[0]
                sync_ledger(); write_reports()
                if result.get("operational_stop"):
                    _set_status("stopped_by_budget_guard")
                    raise SystemExit("Repeat 1 stopped before a call by the USD 8 budget guard")
                attempts = result.get("attempts") or []
                if not attempts or attempts[-1].get("run_validity") != "valid":
                    _set_status("technical_review_required")
                    raise SystemExit(f"Technical gate failed for {cell.scheduled_run_id}")
        summary = write_reports()
        _set_status("consumed")
        print(summary)
        return 0
    except BaseException:
        write_reports()
        raise


if __name__ == "__main__":
    raise SystemExit(main())
