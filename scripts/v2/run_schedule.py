"""Protocol v2 schedule entrypoint.

The only built-in executor is deterministic and non-formal. A formal agent
adapter must be configured and author-approved before this CLI can write to the
formal directory.
"""

from __future__ import annotations

import argparse

from src.v2.matrix import load_schedule
from src.v2.runner import FormalRunGuardError, ProtocolV2Runner
from src.v2.state_machine import fixture_for


def deterministic_executor(cell, _attempt_id: int, _clean_context_id: str):
    raw = fixture_for(cell.task_id, 1, 1)
    raw["synthetic_fixture"] = True
    raw["agent_model_call"] = False
    raw["warning_delivery_status"] = (
        "not_applicable" if cell.safeguard_condition == "no_warning" else "verified"
    )
    return raw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Protocol v2 scheduled cells")
    parser.add_argument(
        "--smoke-cells",
        type=int,
        default=1,
        help="Number of deterministic non-formal cells to execute (default: 1)",
    )
    parser.add_argument(
        "--formal",
        action="store_true",
        help="Request formal output (will fail until manifest and authorization are complete)",
    )
    parser.add_argument(
        "--author-confirmed",
        action="store_true",
        help="Explicit author authorization; never inferred from other flags",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.smoke_cells < 1 or args.smoke_cells > 108:
        raise ValueError("--smoke-cells must be in 1..108")
    try:
        runner = ProtocolV2Runner(
            executor=deterministic_executor,
            formal_run=args.formal,
            explicit_author_confirmation=args.author_confirmed,
        )
        results = runner.run(load_schedule()[: args.smoke_cells])
    except FormalRunGuardError as exc:
        print(f"[FORMAL_RUN_BLOCKED] {exc}")
        return 2
    print(f"Executed {len(results)} deterministic cells; formal_run={args.formal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
