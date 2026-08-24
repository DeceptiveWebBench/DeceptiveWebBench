"""Legacy bulk author-review generator retained for provenance only.

The pre-API workflow intentionally does not call this module: it creates the
superseded 184-image review set and legacy audit formats. Use the focused
``audit_*``, ``capture_pre_api_visuals.py``, and verification scripts instead.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import yaml
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from src.utils.io import ensure_dir, project_root, write_json, write_text
from src.utils.site_http_server import serve_project_root
from src.v2.matrix import (
    randomization_recomputation_status,
    schedule_sha256,
)
from src.v2.registry import load_registry
from src.v2.safeguards import build_prompt_bundle, payload_sha256, render_warning
from src.v2.sites import SHOPLANE_INDEX, is_shoplane_task, site_index_path


REVIEW_ROOT = project_root() / "artifacts" / "v2" / "review"
SCREENSHOT_ROOT = REVIEW_ROOT / "screenshots"
CONDITIONS = ("no_warning", "system_warning", "ui_warning")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(root: Path, pattern: str = "*") -> str:
    digest = hashlib.sha256()
    for path in sorted(candidate for candidate in root.rglob(pattern) if candidate.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def write_registry_tables() -> None:
    table_path = REVIEW_ROOT / "rendered_risk_actions.csv"
    with table_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "task_id",
                "task_version",
                "pattern_family",
                "risk_action",
                "rendered_payload",
                "payload_sha256",
            ],
        )
        writer.writeheader()
        for task in load_registry():
            payload = render_warning(task)
            writer.writerow(
                {
                    "task_id": task.task_id,
                    "task_version": task.task_version,
                    "pattern_family": task.pattern_family,
                    "risk_action": task.risk_action,
                    "rendered_payload": payload,
                    "payload_sha256": payload_sha256(payload),
                }
            )


def _dom_entry(task, condition: str, label: str, page) -> dict[str, object]:
    body_text = page.locator("body").inner_text()
    panel_text = page.locator("#safeguard-text").text_content() or ""
    panel_status = page.locator("#benchmark-status").text_content() or ""
    panel_box = page.locator("#safeguard-panel").bounding_box()
    stop_control = page.get_by_role("button", name="Stop task", exact=True)
    browser_state = page.evaluate("() => window.V2Benchmark.getState()")
    return {
        "task_id": task.task_id,
        "task_version": task.task_version,
        "site": browser_state.get("site", "generic"),
        "formal_run": False,
        "paid_api_calls": 0,
        "condition": condition,
        "route": label,
        "shell": task.shell,
        "mechanism": task.mechanism,
        "boundary_stage": task.boundary_stage,
        "body_text_sha256": hashlib.sha256(body_text.encode("utf-8")).hexdigest(),
        "panel_text": panel_text,
        "panel_status": panel_status,
        "panel_text_sha256": hashlib.sha256(panel_text.encode("utf-8")).hexdigest(),
        "panel_bounding_box": panel_box,
        "panel_count": page.locator("#safeguard-panel").count(),
        "panel_visible": page.locator("#safeguard-panel").is_visible(),
        "stop_control_count": stop_control.count(),
        "stop_control_visible": stop_control.is_visible(),
        "stop_control_bounding_box": stop_control.bounding_box(),
        "task_content_sha256": hashlib.sha256(
            page.locator("#task-content").inner_html().encode("utf-8")
        ).hexdigest(),
        "viewport": {"width": 1280, "height": 720},
        "warning_delivery_status": browser_state["warning_delivery_status"],
        "warning_delivery_channel": browser_state["warning_delivery_channel"],
        "warning_first_delivery_step": browser_state["warning_first_delivery_step"],
        "warning_first_delivery_time": browser_state["warning_first_delivery_time"],
        "risk_point_id": browser_state["risk_point_id"],
        "unsafe_boundary_first_step": browser_state["unsafe_boundary_first_step"],
        "protocol_deviation_codes": browser_state["protocol_deviation_codes"],
    }


def _url_for(base_url: str, index: str, task_id: str, condition: str) -> str:
    query = urlencode(
        {
            "task": task_id,
            "condition": condition,
            "scheduled_run_id": f"review__{task_id}__{condition}",
            "new_run": "1",
        }
    )
    return f"{base_url}/{index}?{query}"


def _capture_scenario_task(browser, base_url, task, prompt_audit, dom_audit) -> None:
    source_images: list[tuple[str, str, Path]] = []
    columns: list[str] = []
    for condition in CONDITIONS:
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        url = _url_for(base_url, site_index_path(task.task_id), task.task_id, condition)
        page.goto(url, wait_until="networkidle")
        page.wait_for_function("() => window.V2Benchmark && window.__TC_V2_STATE__")
        bundle = build_prompt_bundle(
            task_id=task.task_id,
            condition=condition,
            page_url=url,
            scheduled_run_id=f"review__{task.task_id}__{condition}",
        )
        prompt_audit.append({**bundle.capture, "formal_run": False, "paid_api_calls": 0})
        routes = page.evaluate("() => window.V2Benchmark.fixtureListPages()")
        columns = list(routes)
        for route in routes:
            page.evaluate("(value) => window.V2Benchmark.fixtureSetRoute(value)", route)
            screenshot_dir = ensure_dir(SCREENSHOT_ROOT / task.task_id / condition)
            screenshot_path = screenshot_dir / f"{route}.png"
            page.screenshot(path=str(screenshot_path), full_page=False)
            source_images.append((condition, route, screenshot_path))
            dom_audit.append(_dom_entry(task, condition, route, page))
        context.close()
    make_contact_sheet(task.task_id, source_images, columns)


def _capture_shoplane_task(browser, base_url, task, prompt_audit, dom_audit) -> list[str]:
    source_images: list[tuple[str, str, Path]] = []
    columns: list[str] = []
    for condition in CONDITIONS:
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        url = _url_for(base_url, SHOPLANE_INDEX, task.task_id, condition)
        page.goto(url, wait_until="networkidle")
        page.wait_for_function("() => window.V2Benchmark && window.__TC_V2_STATE__")
        bundle = build_prompt_bundle(
            task_id=task.task_id,
            condition=condition,
            page_url=url,
            scheduled_run_id=f"review__{task.task_id}__{condition}",
        )
        prompt_audit.append({**bundle.capture, "formal_run": False, "paid_api_calls": 0})
        pages = page.evaluate("() => window.V2Benchmark.fixtureListPages()")
        columns = [*pages, "confirmation"]
        screenshot_dir = ensure_dir(SCREENSHOT_ROOT / task.task_id / condition)
        for name in pages:
            page.evaluate("(name) => window.V2Benchmark.fixtureGotoPage(name)", name)
            screenshot_path = screenshot_dir / f"{name}.png"
            page.screenshot(path=str(screenshot_path), full_page=False)
            source_images.append((condition, name, screenshot_path))
            dom_audit.append(_dom_entry(task, condition, name, page))
        # Complete the safe path once to capture the shared terminal confirmation page.
        page.evaluate("() => window.V2Benchmark.fixtureSelectSafe()")
        page.evaluate("() => window.V2Benchmark.fixtureCommit()")
        page.evaluate("() => window.V2Benchmark.fixtureCompleteEndpoint()")
        confirm_path = screenshot_dir / "confirmation.png"
        page.screenshot(path=str(confirm_path), full_page=False)
        source_images.append((condition, "confirmation", confirm_path))
        dom_audit.append(_dom_entry(task, condition, "confirmation", page))
        context.close()
    make_contact_sheet(task.task_id, source_images, columns)
    return columns


def _capture_old_vs_new_shoplane(browser, base_url) -> None:
    """Side-by-side of the legacy ShopLane product page and the new storefront product page."""
    shots: dict[str, Path] = {}
    old_context = browser.new_context(viewport={"width": 1280, "height": 720})
    old_page = old_context.new_page()
    old_query = urlencode({"task": "forced_action_sub_001", "condition": "no_warning", "new_run": "1"})
    old_page.goto(f"{base_url}/env/site/product.html?{old_query}", wait_until="networkidle")
    old_page.wait_for_timeout(700)
    shots["old"] = SCREENSHOT_ROOT / "_shoplane_old_product.png"
    old_page.screenshot(path=str(shots["old"]), full_page=False)
    old_context.close()

    new_context = browser.new_context(viewport={"width": 1280, "height": 720})
    new_page = new_context.new_page()
    new_page.goto(
        _url_for(base_url, SHOPLANE_INDEX, "forced_action_sub_001", "no_warning"),
        wait_until="networkidle",
    )
    new_page.wait_for_function("() => window.V2Benchmark && window.__TC_V2_STATE__")
    new_page.evaluate("() => window.V2Benchmark.fixtureGotoPage('product')")
    shots["new"] = SCREENSHOT_ROOT / "_shoplane_new_product.png"
    new_page.screenshot(path=str(shots["new"]), full_page=False)
    new_context.close()

    tile_w, tile_h, label_h = 620, 349, 28
    sheet = Image.new("RGB", (tile_w * 2, tile_h + label_h), "white")
    draw = ImageDraw.Draw(sheet)
    for column, (key, caption) in enumerate((("old", "Legacy ShopLane (v1)"), ("new", "ShopLane v2 storefront"))):
        image = Image.open(shots[key]).convert("RGB")
        image.thumbnail((tile_w, tile_h))
        x = column * tile_w
        draw.rectangle((x, 0, x + tile_w, label_h), fill="#17233f")
        draw.text((x + 8, 8), caption, fill="white")
        sheet.paste(image, (x, label_h))
    sheet.save(SCREENSHOT_ROOT / "shoplane_old_vs_new.png")
    for path in shots.values():
        path.unlink(missing_ok=True)


def capture_visuals_and_prompts() -> None:
    if SCREENSHOT_ROOT.exists():
        shutil.rmtree(SCREENSHOT_ROOT)
    ensure_dir(SCREENSHOT_ROOT)
    prompt_audit: list[dict[str, object]] = []
    dom_audit: list[dict[str, object]] = []
    with serve_project_root(project_root()) as base_url, sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )
        for task in load_registry():
            if is_shoplane_task(task.task_id):
                _capture_shoplane_task(browser, base_url, task, prompt_audit, dom_audit)
            else:
                _capture_scenario_task(browser, base_url, task, prompt_audit, dom_audit)
        _capture_old_vs_new_shoplane(browser, base_url)
        browser.close()
    write_json(REVIEW_ROOT / "prompt_capture_audit.json", prompt_audit)
    write_json(REVIEW_ROOT / "dom_geometry_audit.json", dom_audit)


def make_contact_sheet(task_id: str, source_images: list[tuple[str, str, Path]], columns) -> None:
    columns = list(columns)
    tile_width, tile_height, label_height = 300, 169, 24
    sheet = Image.new(
        "RGB",
        (tile_width * len(columns), (tile_height + label_height) * len(CONDITIONS)),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    lookup = {(condition, label): path for condition, label, path in source_images}
    for row, condition in enumerate(CONDITIONS):
        for column, label in enumerate(columns):
            path = lookup.get((condition, label))
            x = column * tile_width
            y = row * (tile_height + label_height)
            draw.rectangle((x, y, x + tile_width, y + label_height), fill="#17233f")
            draw.text((x + 7, y + 6), f"{condition} · {label}", fill="white")
            if path is None:
                continue
            image = Image.open(path).convert("RGB")
            image.thumbnail((tile_width, tile_height))
            sheet.paste(image, (x, y + label_height))
    sheet.save(SCREENSHOT_ROOT / f"{task_id}__contact_sheet.png")


def protected_hash_report() -> None:
    protected_roots = [
        project_root() / "paper" / "neurips_2026.tex",
        project_root() / "logs" / "experiment_runs",
        project_root() / "env" / "tasks",
        project_root() / "analysis" / "outputs",
        project_root() / "docs" / "archive" / "v1",
        project_root() / "configs" / "manifests" / "archive",
    ]
    files: list[Path] = []
    for root in protected_roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(path for path in root.rglob("*") if path.is_file())

    entries = []
    for path in sorted(set(files)):
        relative = path.relative_to(project_root()).as_posix()
        head_hash = None
        head_status = "not_tracked_at_head"
        result = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=project_root(),
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            head_hash = hashlib.sha256(result.stdout).hexdigest()
            head_status = "matches_head" if head_hash == sha256_file(path) else "pre_existing_worktree_difference"
        entries.append(
            {
                "path": relative,
                "working_tree_sha256": sha256_file(path),
                "head_sha256": head_hash,
                "head_comparison": head_status,
            }
        )
    write_json(
        REVIEW_ROOT / "protected_file_hashes.json",
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope_note": (
                "Current working-tree hashes and HEAD comparisons. Differences already present "
                "before Goal 2B are labeled; Goal 2B writes only v2 namespaces."
            ),
            "files": entries,
        },
    )


def test_report() -> int:
    command = [
        str(project_root() / ".venv" / "bin" / "python"),
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests/v2",
        "-v",
    ]
    result = subprocess.run(command, cwd=project_root(), capture_output=True, text=True, check=False)
    combined = result.stdout + result.stderr
    ran_match = re.search(r"Ran (\d+) tests?", combined)
    skipped_match = re.search(r"skipped=(\d+)", combined)
    failures_match = re.search(r"failures=(\d+)", combined)
    errors_match = re.search(r"errors=(\d+)", combined)
    write_json(
        REVIEW_ROOT / "test_report.json",
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "command": " ".join(command),
            "exit_code": result.returncode,
            "acceptance_status": "pass" if result.returncode == 0 else "fail",
            "counts": {
                "tests_run": int(ran_match.group(1)) if ran_match else None,
                "failures": int(failures_match.group(1)) if failures_match else 0,
                "errors": int(errors_match.group(1)) if errors_match else 0,
                "skipped_blocked": int(skipped_match.group(1)) if skipped_match else 0,
            },
            "known_blocked_assertions": [],
            "randomization_key_recomputation": randomization_recomputation_status(),
            "formal_runs_executed": 0,
            "paid_api_calls": 0,
            "output": combined,
        },
    )
    return result.returncode


def completion_memo() -> None:
    task_lines = "\n".join(
        (
            f"- `{task.task_id}` ({task.shell}): {task.mechanism}. "
            f"Boundary: `{task.unsafe_event_id}` at `{task.boundary_stage}`. "
            f"Floor/ceiling review: {task.floor_ceiling_risk}"
        )
        for task in load_registry()
    )
    memo = f"""# Protocol v2 Goal 2B.1 implementation completion memo

Status: redesigned task interfaces and review materials generated; formal collection remains blocked.

Reused architecture and components:

- The Goal 2B runner, independent C/S scorer, safeguard adapters, formal-write guard, fixture
  contract, and audit schema are retained.
- ShopLane-inspired catalog, product, cart, expandable price detail, checkout/review, and order
  summary components are adapted for v2 without its condition labels, hidden aborts, or outcome
  annotations.
- WorkHub-inspired stepper, disclosure, modal, permission-confirmation, summary, and multi-step
  state-recording patterns are adapted into four consumer shells: commerce, booking, permission,
  and digital service.

Task mechanisms and consequence boundaries:

{task_lines}

Review findings:

- Automated DOM checks found no task-content occurrences of condition labels, gold labels, debug
  fields, event IDs, risk-point IDs, “safe route,” “unsafe,” “unnecessary,” or “the user did not
  request.” The canonical UI-warning payload is intentionally present only inside the safeguard
  panel.
- Initial preselection and opening a permission/upload/form panel do not cross a boundary.
  Deterministic and browser fixtures verify reversal before consequence, task-specific crossing,
  and monotonic `S_r=0` after crossing.
- Floor/ceiling risks remain task-dependent as listed above. These are review risks, not tuned-away
  results, because no agent has been run.
- The 108-cell schedule now recomputes from the author-supplied UTF-8 pipe-delimited SHA-256
  contract and remains separate from execution authorization.

Execution accounting:

- Formal model runs: **0**
- Paid API or model calls: **0**
- Screenshot/test artifacts: local Playwright and deterministic fixtures only, all
  `formal_run=false`

Pending author decisions:

- Approve or revise exact visual hierarchy and merchant copy after reviewing the 12 contact sheets.
- Freeze the unresolved model/scaffold, browser, and run-limit fields already listed in
  `configs/v2/freeze_manifest.yaml`.
- Formal collection remains prohibited until explicit authorization; the guard was not changed.
"""
    write_text(REVIEW_ROOT / "implementation_completion_memo.md", memo)


def update_freeze_manifest() -> None:
    path = project_root() / "configs" / "v2" / "freeze_manifest.yaml"
    with path.open("r", encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle) or {}
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["schedule"]["sha256"] = schedule_sha256()
    manifest["schedule"]["randomization_key_recomputation"] = randomization_recomputation_status()
    manifest["review"]["artifact_hashes"] = {
        name: sha256_file(REVIEW_ROOT / name)
        for name in (
            "test_report.json",
            "prompt_capture_audit.json",
            "dom_geometry_audit.json",
            "protected_file_hashes.json",
            "rendered_risk_actions.csv",
            "implementation_completion_memo.md",
        )
        if (REVIEW_ROOT / name).is_file()
    }
    screenshots = list(SCREENSHOT_ROOT.rglob("*.png"))
    manifest["review"]["screenshot_count"] = len(screenshots)
    manifest["review"]["screenshot_tree_sha256"] = sha256_tree(SCREENSHOT_ROOT, "*.png")
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(manifest, handle, sort_keys=False, allow_unicode=True)


def main() -> int:
    raise SystemExit(
        "Retired bulk generator: use audit_structural_metrics.py, "
        "audit_scientific_validity.py, capture_pre_api_visuals.py, and "
        "run_pre_api_verification.py."
    )


if __name__ == "__main__":
    raise SystemExit(main())
