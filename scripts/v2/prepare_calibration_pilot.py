"""Create the immutable generic-pilot protocol and manifest before paid calls."""

from __future__ import annotations

from src.v2.pilot import PILOT_ROOT, prepare_pilot_root


if __name__ == "__main__":
    prepare_pilot_root()
    print(f"Prepared {PILOT_ROOT}")

