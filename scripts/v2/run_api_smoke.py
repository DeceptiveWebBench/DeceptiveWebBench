"""Explicitly authorized, non-formal entrypoint for the first Bedrock smoke."""

from __future__ import annotations

import argparse
import os

from scripts.v2.preflight_api_smoke import REQUIRED_CREDENTIAL_NAMES
from src.v2.matrix import load_schedule
from src.v2.runner import ProtocolV2Runner
from src.v2.smoke_executor import make_smoke_executor


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author-confirmed", action="store_true", required=True)
    parser.add_argument("--scheduled-run-id", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    if not args.author_confirmed:
        raise SystemExit("Explicit author confirmation is required")
    missing = [name for name in REQUIRED_CREDENTIAL_NAMES if not os.environ.get(name)]
    if missing:
        raise SystemExit("Missing credential variables: " + ", ".join(missing))
    cells = [cell for cell in load_schedule() if cell.scheduled_run_id == args.scheduled_run_id]
    if len(cells) != 1:
        raise SystemExit("--scheduled-run-id must identify exactly one canonical cell")
    runner = ProtocolV2Runner(
        executor=make_smoke_executor(base_url=args.base_url),
        smoke_api_run=True,
        explicit_smoke_authorization=True,
    )
    results = runner.run(cells)
    attempts = results[0].get("attempts") or []
    if not attempts or attempts[-1].get("run_validity") != "valid":
        validity = attempts[-1].get("run_validity") if attempts else "no_attempt_artifact"
        raise SystemExit(f"API-backed smoke did not produce a valid attempt: {validity}")
    print("One non-formal API-backed smoke cell completed; inspect logs/v2/smoke before proceeding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
