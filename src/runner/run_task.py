from __future__ import annotations

import asyncio
import sys

from scripts.smoke_browseruse.run import main


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
