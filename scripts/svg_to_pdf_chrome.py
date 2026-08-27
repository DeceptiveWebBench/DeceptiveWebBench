"""Convert a local SVG to a tightly sized vector PDF with headless Chrome."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from pypdf import PdfReader


CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def svg_size(svg: str) -> tuple[int, int]:
    width = re.search(r'\bwidth="([0-9.]+)px"', svg)
    height = re.search(r'\bheight="([0-9.]+)px"', svg)
    if not width or not height:
        raise ValueError("SVG must declare pixel width and height")
    return round(float(width.group(1))), round(float(height.group(1)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--audit", type=Path)
    args = parser.parse_args()
    svg_path = args.input.resolve()
    pdf_path = args.output.resolve()
    svg = svg_path.read_text(encoding="utf-8")
    width, height = svg_size(svg)
    temp_dir = svg_path.parents[2] / "tmp" / "pdfs" / "svg_to_pdf"
    temp_dir.mkdir(parents=True, exist_ok=True)
    html_path = temp_dir / f"{svg_path.stem}.html"
    html_path.write_text(
        "<!doctype html><meta charset='utf-8'><style>"
        f"@page{{size:{width}px {height}px;margin:0}}"
        f"html,body{{margin:0;width:{width}px;height:{height}px;background:white;overflow:hidden}}"
        f"svg{{display:block;width:{width}px!important;height:{height}px!important}}"
        "</style>" + svg,
        encoding="utf-8",
    )
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(CHROME),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--run-all-compositor-stages-before-draw",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    reader = PdfReader(pdf_path)
    if len(reader.pages) != 1:
        raise RuntimeError(f"Expected one page, got {len(reader.pages)}")
    page = reader.pages[0]
    actual = (round(float(page.mediabox.width), 1), round(float(page.mediabox.height), 1))
    expected = (round(width * 0.75, 1), round(height * 0.75, 1))
    if any(abs(a - b) > 1 for a, b in zip(actual, expected)):
        raise RuntimeError(f"Unexpected PDF size: {actual}; expected approximately {expected}")
    resources = page.get("/Resources", {})
    xobjects = resources.get("/XObject") or {}
    raster_images = []
    for name, reference in xobjects.items():
        item = reference.get_object()
        if item.get("/Subtype") == "/Image":
            raster_images.append(str(name))
    if args.audit:
        audit_path = args.audit.resolve()
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(
            json.dumps(
                {
                    "source_svg": str(svg_path),
                    "source_svg_sha256": hashlib.sha256(svg_path.read_bytes()).hexdigest(),
                    "output_pdf": str(pdf_path),
                    "output_pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
                    "pages": len(reader.pages),
                    "page_size_points": list(actual),
                    "raster_image_xobjects": raster_images,
                    "vector_only": not raster_images,
                    "converter": "local headless Google Chrome",
                    "model_or_api_call": False,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    print(f"{pdf_path} ({actual[0]} x {actual[1]} pt)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
