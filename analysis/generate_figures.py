"""Generate paper-facing figures from frozen analysis CSV outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


CONDITIONS = ("no_warning", "system_warning", "ui_warning")
CONDITION_LABELS = ("No warning", "System", "UI")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", default="analysis/outputs/task_by_condition.csv")
    parser.add_argument("--output", default="paper/figs/task_condition_heatmap.png")
    parser.add_argument("--framework-output", default="paper/figs/trustworthy_completion_framework.png")
    return parser.parse_args()


def write_framework_figure(path: Path) -> None:
    """Render the conceptual outcome/layer factorization required by the Guide."""
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.15))
    left, right = axes
    for ax in axes:
        ax.set_axis_off()

    left.set_title("Completion outcomes", fontsize=10, fontweight="bold")
    boxes = [
        (.04, .58, .42, .25, "Safe completion\n(trustworthy)", "#d8f3dc"),
        (.54, .58, .42, .25, "Unsafe completion\n(nominal only)", "#ffd6d6"),
        (.04, .16, .42, .25, "Safe abort\n(protective, incomplete)", "#fff1bf"),
        (.54, .16, .42, .25, "Other failure\n(unscorable)", "#e7e9ed"),
    ]
    for x, y, w, h, label, color in boxes:
        left.add_patch(plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#30445b", linewidth=1))
        left.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8)

    right.set_title("Evaluation layers", fontsize=10, fontweight="bold")
    layers = [
        (.02, "1. Risk\ndetection", "future detector-\ncoupled"),
        (.36, "2. Safeguard\ndelivery", "System or UI\nchannel"),
        (.70, "3. Agent\nresponse", "current oracle-\ntrigger pilot"),
    ]
    for x, title, subtitle in layers:
        right.add_patch(plt.Rectangle((x, .34), .27, .36, facecolor="#eaf0f8", edgecolor="#30445b", linewidth=1))
        right.text(x + .135, .59, title, ha="center", va="center", fontsize=7.2, fontweight="bold")
        right.text(x + .135, .43, subtitle, ha="center", va="center", fontsize=6.5)
    for x in (.30, .64):
        right.annotate("", xy=(x + .04, .52), xytext=(x, .52), arrowprops={"arrowstyle": "->", "lw": 1.2})

    fig.tight_layout(w_pad=1.4)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    args = parse_args()
    with Path(args.input_csv).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    tasks = sorted({row["task_id"] for row in rows})
    indexed = {(row["task_id"], row["condition"]): row for row in rows}
    values = np.full((len(tasks), len(CONDITIONS)), np.nan)
    labels: list[list[str]] = [["" for _ in CONDITIONS] for _ in tasks]
    for i, task in enumerate(tasks):
        for j, condition in enumerate(CONDITIONS):
            row = indexed[(task, condition)]
            scorable = int(row["n_scorable"])
            unsafe = int(row["n_unsafe_completion"])
            values[i, j] = unsafe / scorable if scorable else np.nan
            labels[i][j] = f"{unsafe}/{scorable}" if scorable else "0/0"

    fig, ax = plt.subplots(figsize=(6.6, 5.2))
    image = ax.imshow(values, vmin=0, vmax=1, cmap="RdYlGn_r", aspect="auto")
    ax.set_xticks(range(len(CONDITIONS)), CONDITION_LABELS)
    ax.set_yticks(range(len(tasks)), [task.replace("_", " ") for task in tasks])
    ax.set_xlabel("Warning condition")
    ax.set_title("Unsafe completions among scorable runs (count/denominator)")
    ax.tick_params(axis="both", labelsize=8)
    for i in range(len(tasks)):
        for j in range(len(CONDITIONS)):
            ax.text(j, i, labels[i][j], ha="center", va="center", fontsize=8,
                    color="white" if np.isfinite(values[i, j]) and (values[i, j] < .18 or values[i, j] > .82) else "black")
    colorbar = fig.colorbar(image, ax=ax, fraction=.035, pad=.03)
    colorbar.set_label("Unsafe-completion rate", fontsize=8)
    colorbar.ax.tick_params(labelsize=8)
    fig.tight_layout()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {output}")
    framework_output = Path(args.framework_output)
    write_framework_figure(framework_output)
    print(f"Wrote {framework_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
