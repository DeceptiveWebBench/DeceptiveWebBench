"""Create focused, annotated Figure 2 crops from the actual Protocol v2 sites.

This is a deterministic browser fixture workflow. It does not invoke an agent,
change benchmark state semantics, or encode any experimental outcome.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

from PIL import Image, ImageDraw, ImageFont
from matplotlib.font_manager import FontProperties, findfont
from playwright.sync_api import Locator, Page, sync_playwright

from src.utils.site_http_server import serve_project_root
from src.utils.io import project_root
from src.v2.sites import site_index_path


ROOT = project_root()
FIGS = ROOT / "paper" / "figs"
TMP = ROOT / "tmp" / "figure2_crops"
VIEWPORT = {"width": 1280, "height": 720}
CANVAS = (1000, 275)
TOP_BAND = 54
UNSAFE = "#D97941"
SAFE = "#4C78A8"
INK = "#2F3742"


def canvas_size(task_id: str) -> tuple[int, int]:
    # The two wide plan cards need full-width rows for their disclosure text to
    # remain readable at the manuscript's normal scale.
    return (1000, 420) if task_id == "sneaking_trial_renewal_002" else CANVAS


@dataclass(frozen=True)
class Example:
    task_id: str
    family: str
    output: str
    root_selector: str
    unsafe_selector: str
    safe_selector: str
    unsafe_label: str
    safe_label: str


EXAMPLES = (
    Example(
        "forced_account_gate_002",
        "Forced action",
        "task_family_forced_action_crop.png",
        ".jr-card:has(.jr-option.prominent)",
        ".museum-account-review button[data-action='commit-unsafe']",
        ".jr-guest-route button[data-action='commit-safe']",
        "Unsafe boundary: create account",
        "Safe route: guest checkout",
    ),
    Example(
        "sneaking_trial_renewal_002",
        "Sneaking",
        "task_family_sneaking_crop.png",
        ".dg-panel:has(.plan-card)",
        ".plan-card.featured",
        ".plan-card:not(.featured)",
        "Unsafe commitment: auto-renewing trial",
        "Safe route: one-time rental",
    ),
    Example(
        "interface_perm_001",
        "Interface interference",
        "task_family_interface_crop.png",
        ".sl-cookie",
        "button[data-action='cookie-accept']",
        "button[data-action='cookie-necessary']",
        "Unsafe boundary: accept all",
        "Safe route: necessary only",
    ),
)


def box_relative(locator: Locator, root: Locator) -> tuple[float, float, float, float]:
    box = locator.bounding_box()
    root_box = root.bounding_box()
    if not box or not root_box:
        raise RuntimeError("Figure 2 locator is not visible")
    return (
        box["x"] - root_box["x"],
        box["y"] - root_box["y"],
        box["width"],
        box["height"],
    )


def prepare(page: Page, example: Example) -> None:
    if example.task_id == "interface_perm_001":
        page.wait_for_function("() => typeof window.V2Benchmark?.fixtureSelectUnsafe === 'function'")
        page.evaluate("() => window.V2Benchmark.fixtureSelectUnsafe()")
    else:
        page.wait_for_function("() => typeof window.V2Benchmark?.fixtureSetRoute === 'function'")
        page.evaluate("() => window.V2Benchmark.fixtureSetRoute('risk')")
    if example.task_id == "forced_account_gate_002":
        page.locator("button[data-action='select-unsafe']").click()
        page.locator("details.jr-guest-route").evaluate("element => { element.open = true; }")
    elif example.task_id == "interface_perm_001":
        page.locator("details.sl-cookie__prefs").evaluate("element => { element.open = true; }")
    page.wait_for_timeout(150)


def snippet_bounds(
    image: Image.Image,
    task_id: str,
    box: tuple[float, float, float, float],
    *,
    safe: bool,
) -> tuple[int, int, int, int]:
    """Keep enough surrounding merchant copy to make each control interpretable."""
    x, y, width, height = box
    padding = {
        "forced_account_gate_002": (36, 112 if not safe else 86, 36, 30),
        "sneaking_trial_renewal_002": (12, 14, 12, 14),
        "interface_perm_001": (120, 78 if not safe else 112, 30, 28),
    }[task_id]
    left, top, right, bottom = padding
    return (
        max(0, round(x - left)),
        max(0, round(y - top)),
        min(image.width, round(x + width + right)),
        min(image.height, round(y + height + bottom)),
    )


def annotate(
    source: Path,
    destination: Path,
    task_id: str,
    unsafe_box: tuple[float, float, float, float],
    safe_box: tuple[float, float, float, float],
    unsafe_label: str,
    safe_label: str,
) -> None:
    image = Image.open(source).convert("RGB")
    snippets = (
        image.crop(snippet_bounds(image, task_id, unsafe_box, safe=False)),
        image.crop(snippet_bounds(image, task_id, safe_box, safe=True)),
    )
    canvas_width, canvas_height = canvas_size(task_id)
    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)
    font_path = findfont(FontProperties(family="DejaVu Sans", weight="bold"))
    font = ImageFont.truetype(font_path, 18)
    if task_id == "sneaking_trial_renewal_002":
        positions = (
            (8, 54, 984, 145, 8, UNSAFE, unsafe_label),
            (8, 264, 984, 145, 218, SAFE, safe_label),
        )
    else:
        positions = (
            (8, TOP_BAND, 486, canvas_height - TOP_BAND - 10, 8, UNSAFE, unsafe_label),
            (506, TOP_BAND, 486, canvas_height - TOP_BAND - 10, 8, SAFE, safe_label),
        )
    for snippet, (left, top, panel_width, panel_height, header_top, color, label) in zip(snippets, positions):
        scale = min(panel_width / snippet.width, panel_height / snippet.height)
        resized = snippet.resize(
            (round(snippet.width * scale), round(snippet.height * scale)),
            Image.Resampling.LANCZOS,
        )
        offset_x = left + (panel_width - resized.width) // 2
        offset_y = top + (panel_height - resized.height) // 2
        canvas.paste(resized, (offset_x, offset_y))
        draw.rounded_rectangle(
            (left, top, left + panel_width, top + panel_height),
            radius=5,
            outline=color,
            width=3,
        )
        draw.rounded_rectangle((left, header_top, left + panel_width, header_top + 38), radius=6, fill="#F5F6F8")
        draw.rectangle((left, header_top, left + 7, header_top + 38), fill=color)
        font_size = 18
        font_small = font
        while draw.textlength(label, font=font_small) > panel_width - 30 and font_size > 13:
            font_size -= 1
            font_small = ImageFont.truetype(font_path, font_size)
        draw.text((left + 18, header_top + 9), label, font=font_small, fill=INK)
    if task_id != "sneaking_trial_renewal_002":
        draw.line((500, 8, 500, canvas_height - 2), fill="#E6E8EB", width=2)
    canvas.save(destination, dpi=(300, 300), optimize=True)


def main() -> int:
    FIGS.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    records = []
    with serve_project_root(ROOT) as base_url, sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )
        for example in EXAMPLES:
            context = browser.new_context(viewport=VIEWPORT, locale="en-US", color_scheme="light")
            page = context.new_page()
            query = urlencode(
                {
                    "task": example.task_id,
                    "condition": "no_warning",
                    "scheduled_run_id": f"publication_figure__{example.task_id}",
                    "new_run": "1",
                }
            )
            page.goto(f"{base_url}/{site_index_path(example.task_id)}?{query}", wait_until="networkidle")
            page.wait_for_function("() => window.V2Benchmark && window.__TC_V2_STATE__")
            prepare(page, example)
            root = page.locator(example.root_selector)
            unsafe = page.locator(example.unsafe_selector)
            safe = page.locator(example.safe_selector)
            unsafe_box = box_relative(unsafe, root)
            safe_box = box_relative(safe, root)
            raw = TMP / f"{example.task_id}.png"
            root.screenshot(path=raw)
            output = FIGS / example.output
            annotate(
                raw,
                output,
                example.task_id,
                unsafe_box,
                safe_box,
                example.unsafe_label,
                example.safe_label,
            )
            records.append(
                {
                    "task_id": example.task_id,
                    "family": example.family,
                    "condition": "no_warning",
                    "fixture_only": True,
                    "agent_model_call": False,
                    "source_is_actual_benchmark_ui": True,
                    "output": str(output.relative_to(ROOT)),
                    "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                    "pixels": list(canvas_size(example.task_id)),
                }
            )
            context.close()
        browser.close()
    audit = ROOT / "artifacts" / "publication_polish" / "figure2_crop_audit.json"
    audit.parent.mkdir(parents=True, exist_ok=True)
    import json

    audit.write_text(json.dumps({"examples": records}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"outputs": len(records), "audit": str(audit.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
