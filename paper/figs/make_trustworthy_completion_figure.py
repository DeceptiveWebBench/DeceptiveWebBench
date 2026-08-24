"""Generate the vector Trustworthy Completion pipeline figure.

Run from the paper directory with:
  python figs/make_trustworthy_completion_figure.py
"""

from pathlib import Path

from matplotlib.font_manager import FontProperties, findfont
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas


OUT = Path(__file__).with_name("trustworthy_completion_cs_pipeline.pdf")
PAGE_W, PAGE_H = 960, 390
SLATE = HexColor("#31445A")
REGULAR_FONT = "FigureSans"
BOLD_FONT = "FigureSansBold"
pdfmetrics.registerFont(TTFont(REGULAR_FONT, findfont(FontProperties(family="DejaVu Sans"))))
pdfmetrics.registerFont(TTFont(BOLD_FONT, findfont(FontProperties(family="DejaVu Sans", weight="bold"))))


def centered(c, text, x, y, size=12, font=REGULAR_FONT):
    c.setFont(font, size)
    c.setFillColor(SLATE)
    c.drawString(x - stringWidth(text, font, size) / 2, y, text)


def box(c, x, y, w, h, fill, title, lines):
    c.setStrokeColor(SLATE)
    c.setLineWidth(1.2)
    c.setFillColor(HexColor(fill))
    c.roundRect(x, y, w, h, 5, stroke=1, fill=1)
    centered(c, title, x + w / 2, y + h - 22, 12, BOLD_FONT)
    for i, line in enumerate(lines):
        centered(c, line, x + w / 2, y + h - 42 - i * 15, 10.5)


def arrow(c, x1, y1, x2, y2, dashed=False):
    c.setStrokeColor(SLATE)
    c.setFillColor(SLATE)
    c.setLineWidth(1.3)
    c.setDash(4, 3) if dashed else c.setDash()
    c.line(x1, y1, x2, y2)
    c.setDash()
    dx, dy = x2 - x1, y2 - y1
    length = (dx * dx + dy * dy) ** 0.5
    if not length:
        return
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    base_x, base_y = x2 - 8 * ux, y2 - 8 * uy
    c.line(x2, y2, base_x + 4 * px, base_y + 4 * py)
    c.line(x2, y2, base_x - 4 * px, base_y - 4 * py)


def quadrant(c, x, y, w, h, fill, title, cs):
    c.setStrokeColor(SLATE)
    c.setLineWidth(1)
    c.setFillColor(HexColor(fill))
    c.rect(x, y, w, h, stroke=1, fill=1)
    centered(c, title, x + w / 2, y + h / 2 + 6, 10.5, BOLD_FONT)
    centered(c, cs, x + w / 2, y + h / 2 - 12, 10)


def main():
    c = canvas.Canvas(
        str(OUT), pagesize=(PAGE_W, PAGE_H), invariant=1,
        initialFontName=REGULAR_FONT, initialFontSize=10,
    )
    c.setTitle("Trustworthy Completion C/S framework and evaluation pipeline")
    c.setAuthor("Anonymous")
    c.setFillColor(white)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    y, w, h, gap, x0 = 275, 205, 76, 28, 20
    specs = [
        ("#E8EEF3", "1. Risk annotation", ["stakeholder and protected interest", "unsafe commitment boundary"]),
        ("#EAF3F8", "2. Safeguard delivery", ["No safeguard, System-delivered,", "or Interface-delivered"]),
        ("#F2F2F2", "3. Agent response", ["action sequence and", "trajectory record"]),
        ("#F8EFE1", "4. Deterministic scoring", ["endpoint state -> C", "boundary history -> S"]),
    ]
    xs = []
    for i, (fill, title, lines) in enumerate(specs):
        x = x0 + i * (w + gap)
        xs.append(x)
        box(c, x, y, w, h, fill, title, lines)
        if i:
            arrow(c, x - gap + 4, y + h / 2, x - 5, y + h / 2)

    qx, qy, qw, qh = 500, 52, 205, 68
    centered(c, "Run-level outcome for every valid trajectory", qx + qw, qy + 2 * qh + 15, 10)
    quadrant(c, qx, qy + qh, qw, qh, "#E6E6E6", "Safe non-completion", "C=0, S=1")
    quadrant(c, qx + qw, qy + qh, qw, qh, "#D9EFF8", "Trustworthy completion", "C=1, S=1")
    quadrant(c, qx, qy, qw, qh, "#C7C7C7", "Unsafe failure", "C=0, S=0")
    quadrant(c, qx + qw, qy, qw, qh, "#F6DFC9", "Unsafe completion", "C=1, S=0")
    centered(c, "Completion C", qx + qw, qy - 18, 10)
    c.saveState()
    c.translate(qx - 18, qy + qh)
    c.rotate(90)
    centered(c, "Safety S", 0, 0, 10)
    c.restoreState()

    score_center = xs[-1] + w / 2
    c.setStrokeColor(SLATE)
    c.setLineWidth(1.3)
    c.line(score_center, y, score_center, qy + 2 * qh + 28)
    c.line(score_center, qy + 2 * qh + 28, qx + 2 * qw, qy + 2 * qh + 28)
    arrow(c, qx + 2 * qw, qy + 2 * qh + 28, qx + 2 * qw, qy + 2 * qh + 3)

    box(c, 26, 84, 250, 62, "#FFFFFF", "Outside the C/S matrix",
        ["infrastructure-invalid attempts", "are reported separately"])
    arrow(c, xs[0] + w / 2, y, xs[0] + w / 2, 151, dashed=True)

    c.showPage()
    c.save()
    print(OUT)


if __name__ == "__main__":
    main()
