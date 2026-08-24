"""Generate publication figures from the locked Protocol v2 review tables.

The audited analysis figures are read-only. This script reads their source CSV
tables and writes a separate, vector-first publication figure set.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts/v2/formal_v02_108/author_insight_review"
FIGS = ROOT / "paper/figs"
AUDIT_OUT = ROOT / "artifacts/v2/submission_review"

CONDITIONS = ("no_warning", "system_warning", "ui_warning")
CONDITION_LABELS = {
    "no_warning": "No safeguard",
    "system_warning": "System-delivered safeguard",
    "ui_warning": "Interface-delivered safeguard",
}
CONDITION_SHORT = {
    "no_warning": "No safeguard",
    "system_warning": "System-delivered",
    "ui_warning": "Interface-delivered",
}
CONDITION_COLORS = {
    "no_warning": "#7A7A7A",
    "system_warning": "#0072B2",
    "ui_warning": "#E69F00",
}
CONDITION_HATCHES = {
    "no_warning": "",
    "system_warning": "///",
    "ui_warning": "xxx",
}
OUTCOME_ORDER = (
    "trustworthy_completion",
    "unsafe_completion",
    "safe_non_completion",
    "unsafe_failure",
)
OUTCOME_LABELS = {
    "trustworthy_completion": "Trustworthy completion",
    "unsafe_completion": "Unsafe completion",
    "safe_non_completion": "Safe non-completion",
    "unsafe_failure": "Unsafe failure",
}
OUTCOME_COLORS = {
    "trustworthy_completion": "#4C78A8",
    "unsafe_completion": "#D97941",
    "safe_non_completion": "#B8C4CE",
    "unsafe_failure": "#555B66",
}
TASK_LABELS = {
    "forced_account_gate_002": "Account gate",
    "forced_action_sub_001": "Membership",
    "forced_contact_share_003": "Contact sharing",
    "forced_identity_upload_004": "Identity upload",
    "interface_confirmshame_newsletter_002": "Newsletter",
    "interface_contact_import_004": "Contact import",
    "interface_location_access_003": "Location access",
    "interface_perm_001": "Cookie consent",
    "sneaking_gift_wrap_003": "Gift wrap",
    "sneaking_pay_001": "Product protection",
    "sneaking_travel_bundle_004": "Travel bundle",
    "sneaking_trial_renewal_002": "Trial renewal",
}


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCE / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure_style() -> None:
    mpl.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "figure.titlesize": 10,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.4,
        "patch.linewidth": 0.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.04,
    })


def clean_axes(ax: plt.Axes, *, grid_axis: str = "y") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, color="#E6E8EB", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)


def contrasting_text_color(fill: str) -> str:
    """Choose black or white by WCAG contrast against a solid fill."""
    rgb = mpl.colors.to_rgb(fill)
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
              for value in rgb]
    luminance = 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    white_contrast = 1.05 / (luminance + 0.05)
    black_contrast = (luminance + 0.05) / 0.05
    return "#FFFFFF" if white_contrast >= black_contrast else "#111111"


def save_pdf(fig: plt.Figure, name: str) -> Path:
    path = FIGS / name
    fig.savefig(
        path,
        format="pdf",
        metadata={"Title": name, "Author": "Anonymous", "Creator": "Protocol v2 publication figure generator",
                  "CreationDate": None, "ModDate": None},
    )
    plt.close(fig)
    return path


def figure_outcomes(condition_rows: list[dict[str, str]]) -> Path:
    fig, ax = plt.subplots(figsize=(6.9, 3.05), facecolor="white")
    ax.set_facecolor("white")
    x = np.arange(len(CONDITIONS))
    bottoms = np.zeros(len(CONDITIONS))
    lookup = {row["condition"]: row for row in condition_rows}
    for outcome in OUTCOME_ORDER:
        counts = np.array([int(lookup[c][outcome]) for c in CONDITIONS])
        values = np.array([count / int(lookup[c]["n_valid"]) for count, c in zip(counts, CONDITIONS)])
        bars = ax.bar(
            x, values, bottom=bottoms, width=0.68,
            color=OUTCOME_COLORS[outcome], edgecolor="#FFFFFF", linewidth=0.8,
            label=OUTCOME_LABELS[outcome], zorder=3,
        )
        for bar, count, value, bottom in zip(bars, counts, values, bottoms):
            if value >= 0.075:
                percentage = int(round(value * 100))
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bottom + value / 2,
                    f"{count} ({percentage}%)",
                    ha="center",
                    va="center",
                    color=contrasting_text_color(OUTCOME_COLORS[outcome]),
                    fontsize=7.7,
                    fontweight="bold",
                )
        bottoms += values
    ax.set_ylim(0, 1.08)
    ax.set_yticks(np.linspace(0, 1, 6), [f"{int(v * 100)}%" for v in np.linspace(0, 1, 6)])
    ax.set_ylabel("Share of valid runs")
    ax.set_xticks(x, [CONDITION_SHORT[c] for c in CONDITIONS])
    ax.set_title("Completion-safety outcomes by safeguard condition", pad=40)
    for idx, condition in enumerate(CONDITIONS):
        row = lookup[condition]
        ax.text(idx, 1.025, f"n={row['n_valid']}", ha="center", va="bottom",
                fontsize=7.1, color="#555B66")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.18), frameon=False,
              handlelength=1.7, columnspacing=1.2, handletextpad=0.5)
    clean_axes(ax)
    fig.subplots_adjust(bottom=0.16, top=0.76, left=0.10, right=0.99)
    return save_pdf(fig, "protocol_v2_cs_quadrants_publication.pdf")


def figure_tradeoff(contrast_rows: list[dict[str, str]]) -> Path:
    wanted = {
        (row["contrast"], row["metric"]): row
        for row in contrast_rows
        if row["contrast"] in ("system_warning_minus_no_warning", "ui_warning_minus_no_warning")
    }
    fig, ax = plt.subplots(figsize=(6.8, 3.15))
    metrics = ("S", "C", "TC")
    labels = ("Safety (S)", "Completion (C)", "Trustworthy\ncompletion (TC)")
    x = np.arange(len(metrics))
    offsets = {"system_warning": -0.12, "ui_warning": 0.12}
    markers = {"system_warning": "o", "ui_warning": "s"}
    for condition in ("system_warning", "ui_warning"):
        contrast = f"{condition}_minus_no_warning"
        rows = [wanted[(contrast, metric)] for metric in metrics]
        estimates = np.array([float(row["estimate"]) * 100 for row in rows])
        lower = np.array([(float(row["estimate"]) - float(row["ci95_low"])) * 100 for row in rows])
        upper = np.array([(float(row["ci95_high"]) - float(row["estimate"])) * 100 for row in rows])
        positions = x + offsets[condition]
        ax.errorbar(
            positions, estimates, yerr=np.vstack([lower, upper]),
            fmt=markers[condition], markersize=6.2, markeredgecolor="#222222", markeredgewidth=0.6,
            color=CONDITION_COLORS[condition], ecolor=CONDITION_COLORS[condition],
            elinewidth=1.6, capsize=4, capthick=1.2, label=CONDITION_LABELS[condition], zorder=3,
        )
        for pos, estimate in zip(positions, estimates):
            ax.annotate(f"{estimate:+.1f}", (pos, estimate), xytext=(0, 7 if estimate >= 0 else -11),
                        textcoords="offset points", ha="center", fontsize=7.5, color="#222222")
    ax.axhline(0, color="#222222", linewidth=0.9)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Difference from No safeguard (percentage points)")
    ax.set_title("Safeguards change both safety and completion")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.19), ncol=2, frameon=False)
    clean_axes(ax)
    fig.subplots_adjust(bottom=0.27, top=0.88, left=0.12, right=0.99)
    return save_pdf(fig, "protocol_v2_tradeoff_publication.pdf")


def figure_task_profiles(task_rows: list[dict[str, str]]) -> Path:
    tasks = sorted({row["task_id"] for row in task_rows})
    lookup = {(row["task_id"], row["condition"]): row for row in task_rows}
    cmap = ListedColormap(["#F7F7F7", "#D9D9D9", "#969696", "#3F3F3F"])
    norm = BoundaryNorm([-0.01, 0.17, 0.50, 0.84, 1.01], cmap.N)
    fig, axes = plt.subplots(1, 3, figsize=(7.3, 5.6), sharey=True)
    metrics = (("TC_rate", "Trustworthy completion"), ("S_rate", "Safety"), ("C_rate", "Completion"))
    for ax, (metric, title) in zip(axes, metrics):
        matrix = np.array([[float(lookup[(task, condition)][metric]) for condition in CONDITIONS] for task in tasks])
        ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto", interpolation="nearest")
        ax.set_title(title, pad=8)
        ax.set_xticks(range(3), [CONDITION_SHORT[c] for c in CONDITIONS], rotation=35, ha="right")
        for tick, condition in zip(ax.get_xticklabels(), CONDITIONS):
            tick.set_color(CONDITION_COLORS[condition])
            tick.set_fontweight("bold")
        for row_idx, task in enumerate(tasks):
            for col_idx, condition in enumerate(CONDITIONS):
                value = matrix[row_idx, col_idx]
                label = f"{value:.2f}"
                ax.text(col_idx, row_idx, label, ha="center", va="center",
                        color="white" if value >= 0.67 else "#111111", fontsize=7.2, fontweight="bold")
        ax.set_xticks(np.arange(-0.5, 3, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(tasks), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.2)
        ax.tick_params(which="minor", bottom=False, left=False)
        for spine in ax.spines.values():
            spine.set_color("#444444")
            spine.set_linewidth(0.8)
    axes[0].set_yticks(range(len(tasks)), [TASK_LABELS[task] for task in tasks])
    fig.suptitle("Task-level rates across repeated runs", y=0.995)
    fig.text(0.5, 0.02, "Direct labels show rates across three valid repeats per task-condition cell.",
             ha="center", fontsize=7.5)
    fig.subplots_adjust(left=0.22, right=0.995, bottom=0.23, top=0.91, wspace=0.08)
    return save_pdf(fig, "protocol_v2_task_profiles_publication.pdf")


def figure_transitions(transition_rows: list[dict[str, str]]) -> Path:
    transition_counts = Counter(
        (row["condition"], row["baseline_outcome"], row["safeguard_outcome"])
        for row in transition_rows
    )
    categories = (
        ("Unsafe →\ntrustworthy", "unsafe_completion", "trustworthy_completion"),
        ("Unsafe → safe\nnon-completion", "unsafe_completion", "safe_non_completion"),
        ("Unsafe →\nunsafe", "unsafe_completion", "unsafe_completion"),
        ("Trustworthy →\nnon-completion", "trustworthy_completion", "noncompletion"),
    )
    fig, ax = plt.subplots(figsize=(7.0, 3.15))
    x = np.arange(len(categories))
    width = 0.34
    for idx, condition in enumerate(("system_warning", "ui_warning")):
        values = []
        for _, before, after in categories:
            if after == "noncompletion":
                values.append(sum(
                    count for (observed_condition, observed_before, observed_after), count in transition_counts.items()
                    if observed_condition == condition and observed_before == before
                    and observed_after in ("safe_non_completion", "unsafe_failure")
                ))
            else:
                values.append(transition_counts[(condition, before, after)])
        positions = x + (-width / 2 if idx == 0 else width / 2)
        bars = ax.bar(
            positions, values, width, color=CONDITION_COLORS[condition], edgecolor="#222222",
            hatch=CONDITION_HATCHES[condition], label=CONDITION_LABELS[condition], zorder=3,
        )
        ax.bar_label(bars, labels=[str(value) for value in values], padding=2, fontsize=8)
    ax.set_xticks(x, [label for label, _, _ in categories])
    ax.set_ylabel("Paired task-repeat cells")
    ax.set_ylim(0, 22)
    ax.set_title("Paired transitions relative to No safeguard")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=2, frameon=False)
    clean_axes(ax)
    fig.subplots_adjust(bottom=0.29, top=0.88, left=0.11, right=0.99)
    return save_pdf(fig, "protocol_v2_paired_transitions_publication.pdf")


def figure_cost(cost_rows: list[dict[str, str]]) -> Path:
    lookup = {row["group"]: row for row in cost_rows if row["grouping"] == "condition"}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.15))
    panels = (
        ("cost_median_usd", "Median reconstructed cost", "USD per valid run"),
        ("wall_clock_median_seconds", "Median wall-clock latency", "Seconds per valid run"),
    )
    for ax, (field, title, ylabel) in zip(axes, panels):
        values = [float(lookup[c][field]) for c in CONDITIONS]
        bars = ax.bar(
            range(3), values,
            color=[CONDITION_COLORS[c] for c in CONDITIONS],
            edgecolor="#222222",
            hatch=[CONDITION_HATCHES[c] for c in CONDITIONS],
            zorder=3,
        )
        labels = [f"{value:.3f}" if field == "cost_median_usd" else f"{value:.1f}" for value in values]
        ax.bar_label(bars, labels=labels, padding=2, fontsize=7.5)
        ax.set_xticks(range(3), [CONDITION_SHORT[c] for c in CONDITIONS], rotation=30, ha="right")
        for tick, condition in zip(ax.get_xticklabels(), CONDITIONS):
            tick.set_color(CONDITION_COLORS[condition])
            tick.set_fontweight("bold")
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, max(values) * 1.23)
        clean_axes(ax)
    fig.suptitle("Operational cost and latency (descriptive)", y=0.995)
    fig.subplots_adjust(bottom=0.25, top=0.80, left=0.10, right=0.99, wspace=0.35)
    return save_pdf(fig, "protocol_v2_cost_latency_publication.pdf")


def main() -> int:
    configure_style()
    FIGS.mkdir(parents=True, exist_ok=True)
    AUDIT_OUT.mkdir(parents=True, exist_ok=True)
    outputs = [
        figure_outcomes(read_csv("condition_summary.csv")),
        figure_tradeoff(read_csv("contrast_bootstrap.csv")),
        figure_task_profiles(read_csv("task_condition_summary.csv")),
        figure_transitions(read_csv("paired_transitions.csv")),
        figure_cost(read_csv("cost_summary.csv")),
    ]
    source_names = (
        "condition_summary.csv", "contrast_bootstrap.csv", "task_condition_summary.csv",
        "paired_transitions.csv", "cost_summary.csv",
    )
    manifest = {
        "figure_set": "protocol-v2-publication-figures-1.1",
        "source_files": {name: sha256(SOURCE / name) for name in source_names},
        "outputs": {str(path.relative_to(ROOT)): sha256(path) for path in outputs},
        "condition_palette": CONDITION_COLORS,
        "outcome_palette": OUTCOME_COLORS,
        "vector_output": True,
        "data_modified": False,
    }
    (AUDIT_OUT / "publication_figure_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
