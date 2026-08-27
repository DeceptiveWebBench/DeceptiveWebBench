"""Export Figure 1 SVG to vector PDF and a temporary review preview."""

from __future__ import annotations

import re

from playwright.sync_api import sync_playwright

from src.utils.io import project_root


ROOT = project_root()
SVG = ROOT / "paper/figs/figure1.svg"
PDF = ROOT / "paper/figs/figure1.pdf"
PREVIEW = ROOT / "tmp/pdfs/figure1_preview.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main() -> int:
    svg = SVG.read_text(encoding="utf-8")
    match = re.search(r'<svg[^>]*width="([0-9.]+)px"[^>]*height="([0-9.]+)px"', svg)
    if not match:
        raise RuntimeError("Could not determine Figure 1 SVG dimensions")
    width, height = (float(match.group(1)), float(match.group(2)))
    html = (
        f"<style>@page{{size:{width}px {height}px;margin:0}}"
        f"html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:white}}</style>"
        + svg
    )
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(
            viewport={"width": round(width), "height": round(height)},
            color_scheme="light",
            device_scale_factor=2,
        )
        page.set_content(html, wait_until="domcontentloaded", timeout=10_000)
        page.screenshot(path=str(PREVIEW), full_page=False, timeout=10_000)
        page.pdf(
            path=str(PDF),
            width=f"{width}px",
            height=f"{height}px",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()
    print(f"Exported {PDF.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
