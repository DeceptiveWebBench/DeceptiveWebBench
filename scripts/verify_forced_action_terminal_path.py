#!/usr/bin/env python3
"""Verify product -> Stop here -> result for all three conditions (no JS API; uses Playwright).

Run from repo root:
  pip install playwright
  playwright install chromium
  python scripts/verify_forced_action_terminal_path.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow `python scripts/verify_...` without installing the package
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.utils.site_http_server import serve_project_root  # noqa: E402
from src.utils.io import project_root  # noqa: E402


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Install Playwright: pip install playwright && playwright install chromium", file=sys.stderr)
        return 1

    conditions = ("no_warning", "system_warning", "ui_warning")
    with serve_project_root(project_root()) as base:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                for cond in conditions:
                    page = browser.new_page(viewport={"width": 1280, "height": 900})
                    url = (
                        f"{base}/env/site/product.html?"
                        f"task=forced_action_sub_001&condition={cond}&new_run=1"
                    )
                    page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                    page.wait_for_selector("#product-stop", timeout=15_000)
                    ui_warn = page.locator(".warning-inline")
                    n_ui = ui_warn.count()
                    if cond == "ui_warning" and n_ui < 1:
                        print(f"FAIL {cond}: expected inline .warning-inline, got count={n_ui}")
                        return 1
                    if cond != "ui_warning" and n_ui != 0:
                        print(f"FAIL {cond}: expected no .warning-inline, got count={n_ui}")
                        return 1
                    page.click("#product-stop")
                    page.wait_for_url("**/result.html**", timeout=15_000)
                    raw = page.evaluate("() => localStorage.getItem('shoplane_sandbox_state_v3')")
                    if not raw:
                        print(f"FAIL {cond}: empty localStorage")
                        return 1
                    state = json.loads(raw)
                    prog = state.get("task_progress", {}).get("forced_action_sub_001", {})
                    term = prog.get("terminal_state")
                    last = prog.get("last_action")
                    if term != "safe_abort" or last != "product_stop":
                        print(f"FAIL {cond}: terminal_state={term!r} last_action={last!r}")
                        return 1
                    print(f"OK {cond}: safe_abort / product_stop")
                    page.close()
            finally:
                browser.close()
    print("All forced_action terminal-path checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
