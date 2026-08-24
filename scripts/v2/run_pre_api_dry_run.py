"""Run the complete model-free Protocol v2 pipeline validation."""

from __future__ import annotations

import json

from src.v2.pre_api_dry_run import run_pre_api_dry_run


if __name__ == "__main__":
    print(json.dumps(run_pre_api_dry_run(), indent=2, sort_keys=True))
