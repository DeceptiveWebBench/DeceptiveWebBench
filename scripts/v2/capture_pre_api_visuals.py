"""Capture a minimal five-site visual review set; no agent or model is involved."""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

from src.utils.io import ensure_dir, project_root, write_json
from src.utils.site_http_server import serve_project_root
from src.v2.sites import SHOPLANE_TASKS, site_index_path


REPRESENTATIVES = {
    "shoplane": "interface_perm_001",
    "journey": "forced_account_gate_002",
    "events": "forced_contact_share_003",
    "local_services": "forced_identity_upload_004",
    "digital": "sneaking_trial_renewal_002",
}


def main() -> None:
    root = project_root()
    destination = ensure_dir(root / "artifacts/v2/review/pre_api_visuals")
    records = []
    with serve_project_root(root) as base_url, sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )
        for site, task_id in REPRESENTATIVES.items():
            context = browser.new_context(viewport={"width": 1280, "height": 720}, locale="en-US")
            page = context.new_page()
            query = urlencode(
                {
                    "task": task_id,
                    "condition": "ui_warning",
                    "scheduled_run_id": f"visual_review__{task_id}",
                    "new_run": "1",
                }
            )
            page.goto(f"{base_url}/{site_index_path(task_id)}?{query}", wait_until="networkidle")
            page.wait_for_function("() => window.V2Benchmark && window.__TC_V2_STATE__")
            if task_id in SHOPLANE_TASKS:
                page.evaluate("() => window.V2Benchmark.fixtureSelectUnsafe()")
            else:
                page.evaluate("() => window.V2Benchmark.fixtureSetRoute('risk')")
            panel = page.locator("#safeguard-panel").bounding_box()
            warning = page.locator("#safeguard-text").bounding_box()
            stop = page.get_by_role("button", name="Stop task", exact=True).bounding_box()
            content = page.locator("#task-content").bounding_box()
            screenshot = destination / f"{site}__{task_id}__risk.png"
            page.screenshot(path=screenshot, full_page=False)
            records.append(
                {
                    "site": site,
                    "task_id": task_id,
                    "viewport": [1280, 720],
                    "condition": "ui_warning",
                    "fixture_only": True,
                    "agent_model_call": False,
                    "panel_within_viewport": bool(panel and panel["y"] + panel["height"] <= 720),
                    "warning_within_panel": bool(
                        panel
                        and warning
                        and warning["y"] >= panel["y"] - 1
                        and warning["y"] + warning["height"]
                        <= panel["y"] + panel["height"] + 1
                    ),
                    "stop_within_panel": bool(
                        panel
                        and stop
                        and stop["x"] >= panel["x"]
                        and stop["x"] + stop["width"] <= panel["x"] + panel["width"] + 1
                    ),
                    "panel_clear_of_task_content": bool(
                        panel and content and panel["y"] + panel["height"] <= content["y"] + 1
                    ),
                    "horizontal_overflow": page.evaluate(
                        "() => document.documentElement.scrollWidth > window.innerWidth + 1"
                    ),
                    "screenshot": str(screenshot.relative_to(root)),
                    "screenshot_sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
                }
            )
            context.close()
        browser.close()
    if not all(
        record["panel_within_viewport"]
        and record["warning_within_panel"]
        and record["stop_within_panel"]
        and record["panel_clear_of_task_content"]
        and not record["horizontal_overflow"]
        for record in records
    ):
        raise RuntimeError("Visual geometry audit failed")
    write_json(root / "artifacts/v2/review/pre_api_visual_audit.json", {"sites": records})
    print(f"Captured and checked {len(records)} representative site views")


if __name__ == "__main__":
    main()
