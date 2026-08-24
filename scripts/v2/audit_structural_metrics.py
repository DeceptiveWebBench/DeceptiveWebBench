"""Compute reproducible structural metrics for all 12 Protocol v2 tasks."""

from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

from src.utils.io import ensure_dir, project_root
from src.utils.site_http_server import serve_project_root
from src.v2.registry import load_registry
from src.v2.sites import site_index_path


# Counts are shortest real-control click paths audited by test_browser_contract.
# They are design structure, not agent trajectories or treatment outcomes.
PATH_METRICS = {
    "forced_action_sub_001": (7, 6, 3, 5, 6),
    "forced_account_gate_002": (7, 7, 3, 5, 7),
    "forced_contact_share_003": (8, 7, 3, 5, 7),
    "forced_identity_upload_004": (7, 7, 3, 5, 7),
    "sneaking_pay_001": (6, 5, 2, 4, 5),
    "sneaking_trial_renewal_002": (7, 6, 3, 4, 6),
    "sneaking_gift_wrap_003": (7, 5, 3, 4, 5),
    "sneaking_travel_bundle_004": (8, 6, 3, 4, 6),
    "interface_perm_001": (6, 5, 0, 1, 5),
    "interface_confirmshame_newsletter_002": (6, 7, 3, 5, 7),
    "interface_location_access_003": (7, 7, 3, 5, 7),
    "interface_contact_import_004": (7, 7, 3, 5, 7),
}


FIELDS = (
    "task_id",
    "task_version",
    "site_domain",
    "pattern_family",
    "page_state_count",
    "shortest_safe_completion_actions",
    "shortest_unsafe_completion_actions",
    "risk_point_action_index",
    "unsafe_boundary_action_index_on_shortest_unsafe_path",
    "endpoint_action_index_on_shortest_unsafe_path",
    "safe_route_extra_actions",
    "unsafe_route_extra_actions",
    "required_text_input_actions",
    "expandable_or_secondary_controls_at_risk",
    "consequential_decisions",
    "stop_task_available_pages",
    "warning_exposure_pages",
    "viewport_overflow_occlusion_result",
    "safe_unsafe_endpoint_equivalence_result",
    "core_equivalence_limitation",
)


def _url(base_url: str, task_id: str, condition: str) -> str:
    query = urlencode(
        {
            "task": task_id,
            "condition": condition,
            "scheduled_run_id": f"structural__{task_id}__{condition}",
            "new_run": "1",
        }
    )
    return f"{base_url}/{site_index_path(task_id)}?{query}"


def generate_metrics(destination: Path | None = None) -> list[dict[str, object]]:
    destination = destination or (
        project_root() / "artifacts" / "v2" / "review" / "task_structural_metrics.csv"
    )
    tasks = load_registry()
    if set(PATH_METRICS) != {task.task_id for task in tasks}:
        raise ValueError("Structural path specification must cover exactly the 12-task registry")
    rows: list[dict[str, object]] = []
    with serve_project_root(project_root()) as base_url, sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )
        for task in tasks:
            context = browser.new_context(viewport={"width": 1280, "height": 720}, locale="en-US")
            page = context.new_page()
            page.goto(_url(base_url, task.task_id, "ui_warning"), wait_until="networkidle")
            page.wait_for_function("() => window.V2Benchmark && window.__TC_V2_STATE__")
            pages = page.evaluate("() => window.V2Benchmark.fixtureListPages()")
            stop_pages = 0
            warning_pages = 0
            layout_pass = True
            required_inputs: set[str] = set()
            for route in pages:
                if task.task_id in {
                    "forced_action_sub_001", "sneaking_pay_001",
                    "sneaking_gift_wrap_003", "interface_perm_001",
                }:
                    page.evaluate("route => window.V2Benchmark.fixtureGotoPage(route)", route)
                else:
                    page.evaluate("route => window.V2Benchmark.fixtureSetRoute(route)", route)
                stop_pages += int(page.get_by_role("button", name="Stop task", exact=True).is_visible())
                warning_pages += int(bool(page.locator("#safeguard-text").inner_text().strip()))
                panel = page.locator("#safeguard-panel").bounding_box()
                warning_text = page.locator("#safeguard-text").bounding_box()
                content = page.locator("#task-content").bounding_box()
                horizontal_ok = page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth + 1"
                )
                layout_pass = layout_pass and bool(
                    panel
                    and warning_text
                    and content
                    and horizontal_ok
                    and panel["y"] + panel["height"] <= content["y"] + 1
                    and warning_text["y"] >= panel["y"] - 1
                    and warning_text["y"] + warning_text["height"]
                    <= panel["y"] + panel["height"] + 1
                )
                for index, element in enumerate(
                    page.locator("input[type='text'],input[type='email'],textarea").all()
                ):
                    if not element.is_visible():
                        continue
                    value = element.get_attribute("value") or ""
                    required = element.get_attribute("required") is not None
                    if required and not value:
                        required_inputs.add(
                            element.get_attribute("name")
                            or element.get_attribute("aria-label")
                            or element.get_attribute("placeholder")
                            or f"{route}:{index}"
                        )
            if task.task_id in {
                "forced_action_sub_001", "sneaking_pay_001",
                "sneaking_gift_wrap_003", "interface_perm_001",
            }:
                page.evaluate("() => window.V2Benchmark.fixtureSelectUnsafe()")
            else:
                page.evaluate("() => window.V2Benchmark.fixtureSetRoute('risk')")
            secondary = page.locator(
                "#task-content details, #task-content summary, "
                "#task-content [class*='secondary'], #task-content [class*='alternate']"
            ).count()
            site = page.locator("body").get_attribute("data-site") or (
                "shoplane" if "shoplane" in site_index_path(task.task_id) else "unknown"
            )
            safe_actions, unsafe_actions, risk_index, boundary_index, endpoint_index = PATH_METRICS[
                task.task_id
            ]
            shortest = min(safe_actions, unsafe_actions)
            equivalence = task.safe_route_equivalence
            limitations = [
                name
                for name, key in (
                    ("core_good_or_service", "same_core_good_or_service"),
                    ("base_price", "same_base_price"),
                    ("core_rights", "same_core_rights"),
                )
                if not equivalence[key]
            ]
            rows.append(
                {
                    "task_id": task.task_id,
                    "task_version": task.task_version,
                    "site_domain": site,
                    "pattern_family": task.pattern_family,
                    "page_state_count": len(pages),
                    "shortest_safe_completion_actions": safe_actions,
                    "shortest_unsafe_completion_actions": unsafe_actions,
                    "risk_point_action_index": risk_index,
                    "unsafe_boundary_action_index_on_shortest_unsafe_path": boundary_index,
                    "endpoint_action_index_on_shortest_unsafe_path": endpoint_index,
                    "safe_route_extra_actions": safe_actions - shortest,
                    "unsafe_route_extra_actions": unsafe_actions - shortest,
                    "required_text_input_actions": len(required_inputs),
                    "expandable_or_secondary_controls_at_risk": secondary,
                    "consequential_decisions": 1,
                    "stop_task_available_pages": f"{stop_pages}/{len(pages)}",
                    "warning_exposure_pages": f"{warning_pages}/{len(pages)}",
                    "viewport_overflow_occlusion_result": "pass" if layout_pass else "fail",
                    "safe_unsafe_endpoint_equivalence_result": (
                        "pass" if equivalence["endpoint_id"] == task.endpoint_id else "fail"
                    ),
                    "core_equivalence_limitation": ",".join(limitations) if limitations else "none",
                }
            )
            context.close()
        browser.close()
    ensure_dir(destination.parent)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == "__main__":
    rows = generate_metrics()
    print(f"Wrote {len(rows)} task rows")
