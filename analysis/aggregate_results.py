from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from typing import Any


PRIMARY_OUTCOMES = ["safe_completion", "unsafe_completion", "safe_abort"]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _rate(rows: list[dict[str, str]], label: str) -> float:
    if not rows:
        return 0.0
    hits = sum(1 for r in rows if (r.get("outcome_label") or "").strip() == label)
    return hits / len(rows)


def _scorable_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [r for r in rows if (r.get("outcome_label") or "").strip() != "other_failure"]


def _rate_among_scorable(rows: list[dict[str, str]], label: str) -> float:
    bucket = _scorable_rows(rows)
    if not bucket:
        return 0.0
    hits = sum(1 for r in bucket if (r.get("outcome_label") or "").strip() == label)
    return hits / len(bucket)


def _bootstrap_ci(
    rows: list[dict[str, str]],
    label: str,
    n_boot: int,
    seed: int,
    alpha: float = 0.05,
) -> tuple[float, float]:
    if not rows:
        return 0.0, 0.0
    if len(rows) == 1:
        v = _rate(rows, label)
        return v, v

    rng = random.Random(seed)
    boot_rates: list[float] = []
    n = len(rows)
    for _ in range(n_boot):
        sample = [rows[rng.randrange(n)] for _ in range(n)]
        boot_rates.append(_rate(sample, label))
    boot_rates.sort()
    lo_idx = int((alpha / 2.0) * (n_boot - 1))
    hi_idx = int((1.0 - alpha / 2.0) * (n_boot - 1))
    return boot_rates[lo_idx], boot_rates[hi_idx]


def _group_by_condition(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        condition = (row.get("condition") or "unknown_condition").strip()
        grouped.setdefault(condition, []).append(row)
    return grouped


def build_summary_by_condition(rows: list[dict[str, str]], n_boot: int, seed: int) -> list[dict[str, Any]]:
    grouped = _group_by_condition(rows)
    out_rows: list[dict[str, Any]] = []
    for condition in sorted(grouped.keys()):
        bucket = grouped[condition]
        scorable = _scorable_rows(bucket)
        result: dict[str, Any] = {
            "condition": condition,
            "n_runs": len(bucket),
            "n_scorable": len(scorable),
        }
        # other_failure: share of all runs (infra / non-terminal)
        result["other_failure_rate"] = round(_rate(bucket, "other_failure"), 6)
        # Primary outcomes: rates among scorable runs only (excludes other_failure)
        for label in PRIMARY_OUTCOMES:
            result[f"{label}_rate"] = round(_rate_among_scorable(bucket, label), 6)
        unsafe_rate = _rate_among_scorable(bucket, "unsafe_completion")
        ci_lo, ci_hi = _bootstrap_ci(scorable, "unsafe_completion", n_boot=n_boot, seed=seed)
        result["unsafe_completion_rate"] = round(unsafe_rate, 6)
        result["unsafe_completion_rate_ci_lower"] = round(ci_lo, 6)
        result["unsafe_completion_rate_ci_upper"] = round(ci_hi, 6)
        out_rows.append(result)
    return out_rows


def build_summary_system_vs_ui(rows: list[dict[str, str]], n_boot: int, seed: int) -> list[dict[str, Any]]:
    grouped = _group_by_condition(rows)
    sys_rows = grouped.get("system_warning", [])
    ui_rows = grouped.get("ui_warning", [])
    sys_scorable = _scorable_rows(sys_rows)
    ui_scorable = _scorable_rows(ui_rows)

    sys_rate = _rate_among_scorable(sys_rows, "unsafe_completion")
    ui_rate = _rate_among_scorable(ui_rows, "unsafe_completion")
    sys_lo, sys_hi = _bootstrap_ci(sys_scorable, "unsafe_completion", n_boot=n_boot, seed=seed + 17)
    ui_lo, ui_hi = _bootstrap_ci(ui_scorable, "unsafe_completion", n_boot=n_boot, seed=seed + 29)

    return [
        {
            "n_system": len(sys_rows),
            "n_ui": len(ui_rows),
            "n_system_scorable": len(sys_scorable),
            "n_ui_scorable": len(ui_scorable),
            "unsafe_completion_rate_system": round(sys_rate, 6),
            "unsafe_completion_rate_system_ci_lower": round(sys_lo, 6),
            "unsafe_completion_rate_system_ci_upper": round(sys_hi, 6),
            "unsafe_completion_rate_ui": round(ui_rate, 6),
            "unsafe_completion_rate_ui_ci_lower": round(ui_lo, 6),
            "unsafe_completion_rate_ui_ci_upper": round(ui_hi, 6),
            "rate_diff_system_minus_ui": round(sys_rate - ui_rate, 6),
        }
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate run-level CSV into report-ready condition summaries."
    )
    parser.add_argument(
        "--input-csv",
        default="logs/experiment_runs/results_run_level.csv",
        help="Path to run-level CSV produced by src.scorer.score_runs.",
    )
    parser.add_argument(
        "--output-dir",
        default="analysis/outputs",
        help="Directory for summary CSV outputs.",
    )
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=1000,
        help="Number of bootstrap samples for CI estimation.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for bootstrap resampling.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_csv = Path(args.input_csv).resolve()
    output_dir = Path(args.output_dir).resolve()

    rows = _read_csv(input_csv)

    summary_by_condition = build_summary_by_condition(
        rows, n_boot=max(100, args.bootstrap_samples), seed=args.seed
    )
    summary_system_vs_ui = build_summary_system_vs_ui(
        rows, n_boot=max(100, args.bootstrap_samples), seed=args.seed
    )

    by_condition_path = output_dir / "summary_by_condition.csv"
    system_vs_ui_path = output_dir / "summary_system_vs_ui.csv"

    _write_csv(
        by_condition_path,
        fieldnames=[
            "condition",
            "n_runs",
            "n_scorable",
            "safe_completion_rate",
            "unsafe_completion_rate",
            "safe_abort_rate",
            "other_failure_rate",
            "unsafe_completion_rate_ci_lower",
            "unsafe_completion_rate_ci_upper",
        ],
        rows=summary_by_condition,
    )

    _write_csv(
        system_vs_ui_path,
        fieldnames=[
            "n_system",
            "n_ui",
            "n_system_scorable",
            "n_ui_scorable",
            "unsafe_completion_rate_system",
            "unsafe_completion_rate_system_ci_lower",
            "unsafe_completion_rate_system_ci_upper",
            "unsafe_completion_rate_ui",
            "unsafe_completion_rate_ui_ci_lower",
            "unsafe_completion_rate_ui_ci_upper",
            "rate_diff_system_minus_ui",
        ],
        rows=summary_system_vs_ui,
    )

    print(f"Read run-level rows: {len(rows)}")
    print(f"Wrote: {by_condition_path}")
    print(f"Wrote: {system_vs_ui_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

