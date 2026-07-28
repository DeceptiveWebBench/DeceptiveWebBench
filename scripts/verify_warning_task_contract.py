#!/usr/bin/env python3
"""Verify warning/task source-of-truth contract consistency."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.config_contract import collect_contract_issues  # noqa: E402


def main() -> int:
    issues = collect_contract_issues()
    if not issues:
        print("OK warning/task contract checks passed.")
        return 0
    print("FAIL warning/task contract checks:")
    for issue in issues:
        print(f"- [{issue.task_id}] {issue.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

