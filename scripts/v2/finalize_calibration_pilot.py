"""Validate and regenerate generic pilot CSV/reports from append-only attempts."""

from __future__ import annotations

import json

from src.v2.pilot import prepare_pilot_root, verify_frozen_manifest, write_reports


if __name__ == "__main__":
    prepare_pilot_root()
    verify_frozen_manifest()
    print(json.dumps(write_reports(), indent=2, sort_keys=True))
