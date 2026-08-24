"""Create and verify the append-only formal malformed-action adjudication."""

from __future__ import annotations

import json

from src.v2.formal_action_schema_adjudication import create_adjudication, verify_adjudication


def main() -> int:
    create_adjudication()
    record = verify_adjudication()
    print(json.dumps({"status": "PASS", **record}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

