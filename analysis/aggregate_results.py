from __future__ import annotations

import argparse
import csv
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


OUTCOMES = ["safe_completion", "unsafe_completion", "safe_abort", "other_failure"]
SCORABLE_OUTCOMES = OUTCOMES[:-1]
EXPECTED_CONDITIONS = ("no_warning", "system_warning", "ui_warning")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _outcome(row: dict[str, str]) -> str:
    return (row.get("outcome_label") or "").strip()


def _scorable_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if _outcome(row) in SCORABLE_OUTCOMES]


def _rate(rows: list[dict[str, str]], outcome: str) -> float:
    return sum(_outcome(row) == outcome for row in rows) / len(rows) if rows else 0.0


def _scorable_rate(rows: list[dict[str, str]], outcome: str) -> float:
    return _rate(_scorable_rows(rows), outcome)


def validate_run_matrix(rows: list[dict[str, str]]) -> dict[str, Any]:
    """Validate the observed task × condition × repeat matrix without changing it."""
    required = ("task_id", "condition", "repeat_id", "outcome_label")
    missing_columns = [name for name in required if not rows or name not in rows[0]]
    if missing_columns:
        raise ValueError(f"Run-level CSV is missing required columns: {missing_columns}")

    keys = [(row["task_id"], row["condition"], row["repeat_id"]) for row in rows]
    duplicate_keys = sorted(key for key, n in Counter(keys).items() if n != 1)
    tasks = sorted({row["task_id"] for row in rows})
    conditions = sorted({row["condition"] for row in rows})
    repeats_by_cell: dict[tuple[str, str], set[str]] = defaultdict(set)
    for task_id, condition, repeat_id in keys:
        repeats_by_cell[(task_id, condition)].add(repeat_id)
    expected_repeats = sorted({row["repeat_id"] for row in rows})
    missing_cells = [
        (task_id, condition)
        for task_id in tasks
        for condition in EXPECTED_CONDITIONS
        if (task_id, condition) not in repeats_by_cell
    ]
    irregular_repeats = {
        f"{task_id}|{condition}": sorted(repeats)
        for (task_id, condition), repeats in sorted(repeats_by_cell.items())
        if sorted(repeats) != expected_repeats
    }
    valid_outcomes = sorted({_outcome(row) for row in rows} - set(OUTCOMES))
    expected_rows = len(tasks) * len(EXPECTED_CONDITIONS) * len(expected_repeats)
    is_complete_unique = (
        not duplicate_keys
        and not missing_cells
        and not irregular_repeats
        and not valid_outcomes
        and len(rows) == expected_rows
        and set(conditions) == set(EXPECTED_CONDITIONS)
    )
    return {
        "n_rows": len(rows),
        "n_tasks": len(tasks),
        "conditions": ";".join(conditions),
        "repeat_ids": ";".join(expected_repeats),
        "expected_rows": expected_rows,
        "duplicate_key_count": len(duplicate_keys),
        "missing_cell_count": len(missing_cells),
        "irregular_repeat_cell_count": len(irregular_repeats),
        "unknown_outcome_count": len(valid_outcomes),
        "is_complete_unique": is_complete_unique,
        "duplicate_keys": duplicate_keys,
        "missing_cells": missing_cells,
        "irregular_repeats": irregular_repeats,
        "unknown_outcomes": valid_outcomes,
    }


def _task_stratified_ci(
    rows: list[dict[str, str]], outcome: str, n_boot: int, seed: int, alpha: float = 0.05
) -> tuple[float, float]:
    """Cluster bootstrap: resample tasks, retaining each sampled task's repeated runs."""
    by_task: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_task[row["task_id"]].append(row)
    tasks = sorted(by_task)
    if not tasks:
        return 0.0, 0.0
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(n_boot):
        sampled_rows = [row for _ in tasks for row in by_task[rng.choice(tasks)]]
        estimates.append(_scorable_rate(sampled_rows, outcome))
    estimates.sort()
    return (
        estimates[int((alpha / 2) * (n_boot - 1))],
        estimates[int((1 - alpha / 2) * (n_boot - 1))],
    )


def _group_by_condition(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["condition"]].append(row)
    return grouped


def build_summary_by_condition(rows: list[dict[str, str]], n_boot: int, seed: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for condition, bucket in sorted(_group_by_condition(rows).items()):
        scorable = _scorable_rows(bucket)
        counts = Counter(_outcome(row) for row in bucket)
        lo, hi = _task_stratified_ci(bucket, "unsafe_completion", n_boot, seed)
        record: dict[str, Any] = {
            "condition": condition,
            "n_all_runs": len(bucket),
            "n_scorable": len(scorable),
            "n_other_failure": counts["other_failure"],
            "other_failure_rate_all_runs": round(_rate(bucket, "other_failure"), 6),
            "unsafe_completion_rate_task_stratified_ci_lower": round(lo, 6),
            "unsafe_completion_rate_task_stratified_ci_upper": round(hi, 6),
        }
        for outcome in SCORABLE_OUTCOMES:
            record[f"n_{outcome}"] = counts[outcome]
            record[f"{outcome}_rate_scorable"] = round(_scorable_rate(bucket, outcome), 6)
        out.append(record)
    return out


def build_task_by_condition(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["task_id"], row["condition"])].append(row)
    out: list[dict[str, Any]] = []
    for (task_id, condition), bucket in sorted(groups.items()):
        counts = Counter(_outcome(row) for row in bucket)
        scorable = _scorable_rows(bucket)
        record: dict[str, Any] = {
            "task_id": task_id,
            "pattern_family": bucket[0]["pattern_family"],
            "condition": condition,
            "n_all_runs": len(bucket),
            "n_scorable": len(scorable),
        }
        for outcome in OUTCOMES:
            record[f"n_{outcome}"] = counts[outcome]
            denominator = len(bucket) if outcome == "other_failure" else len(scorable)
            record[f"{outcome}_rate_{'all_runs' if outcome == 'other_failure' else 'scorable'}"] = round(counts[outcome] / denominator, 6) if denominator else 0.0
        out.append(record)
    return out


def build_summary_system_vs_ui(rows: list[dict[str, str]], n_boot: int, seed: int) -> list[dict[str, Any]]:
    grouped = _group_by_condition(rows)
    system = grouped["system_warning"]
    ui = grouped["ui_warning"]
    by_task_system: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_task_ui: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in system:
        by_task_system[row["task_id"]].append(row)
    for row in ui:
        by_task_ui[row["task_id"]].append(row)
    tasks = sorted(set(by_task_system) & set(by_task_ui))
    rng = random.Random(seed + 17)
    differences: list[float] = []
    for _ in range(n_boot):
        sampled_tasks = [rng.choice(tasks) for _ in tasks]
        sampled_system = [row for task in sampled_tasks for row in by_task_system[task]]
        sampled_ui = [row for task in sampled_tasks for row in by_task_ui[task]]
        differences.append(_scorable_rate(sampled_system, "unsafe_completion") - _scorable_rate(sampled_ui, "unsafe_completion"))
    differences.sort()
    return [{
        "n_system_all_runs": len(system), "n_ui_all_runs": len(ui),
        "n_system_scorable": len(_scorable_rows(system)), "n_ui_scorable": len(_scorable_rows(ui)),
        "unsafe_completion_rate_system_scorable": round(_scorable_rate(system, "unsafe_completion"), 6),
        "unsafe_completion_rate_ui_scorable": round(_scorable_rate(ui, "unsafe_completion"), 6),
        "rate_diff_system_minus_ui": round(_scorable_rate(system, "unsafe_completion") - _scorable_rate(ui, "unsafe_completion"), 6),
        "rate_diff_task_stratified_ci_lower": round(differences[int(.025 * (n_boot - 1))], 6),
        "rate_diff_task_stratified_ci_upper": round(differences[int(.975 * (n_boot - 1))], 6),
    }]


def build_interface_perm_sensitivity(
    rows: list[dict[str, str]], n_boot: int, seed: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Supplementary sensitivity view excluding interface_perm_001 only.

    The complete 81-run analysis remains primary. This function is descriptive and
    exists to quantify the documented historical warning-wording deviation.
    """
    subset = [row for row in rows if row["task_id"] != "interface_perm_001"]
    return (
        build_summary_by_condition(subset, n_boot=n_boot, seed=seed),
        build_summary_system_vs_ui(subset, n_boot=n_boot, seed=seed),
    )


def write_all_outputs(rows: list[dict[str, str]], output_dir: Path, n_boot: int, seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    audit = validate_run_matrix(rows)
    if not audit["is_complete_unique"]:
        raise ValueError(f"Formal run matrix is not complete and unique: {audit}")
    condition = build_summary_by_condition(rows, n_boot, seed)
    task_condition = build_task_by_condition(rows)
    comparison = build_summary_system_vs_ui(rows, n_boot, seed)
    sensitivity, sensitivity_comparison = build_interface_perm_sensitivity(rows, n_boot, seed)
    _write_csv(output_dir / "summary_by_condition.csv", list(condition[0]), condition)
    _write_csv(output_dir / "task_by_condition.csv", list(task_condition[0]), task_condition)
    _write_csv(output_dir / "summary_system_vs_ui.csv", list(comparison[0]), comparison)
    _write_csv(output_dir / "sensitivity_without_interface_perm_001.csv", list(sensitivity[0]), sensitivity)
    _write_csv(
        output_dir / "sensitivity_system_vs_ui_without_interface_perm_001.csv",
        list(sensitivity_comparison[0]),
        sensitivity_comparison,
    )
    _write_csv(output_dir / "run_matrix_audit.csv", [key for key in audit if not isinstance(audit[key], (list, dict))], [{key: value for key, value in audit.items() if not isinstance(value, (list, dict))}])
    return condition, task_condition, audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and aggregate the frozen 81-run pilot CSV.")
    parser.add_argument("--input-csv", default="logs/experiment_runs/results_run_level.csv")
    parser.add_argument("--output-dir", default="analysis/outputs")
    parser.add_argument("--bootstrap-samples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = _read_csv(Path(args.input_csv))
    condition, task_condition, audit = write_all_outputs(rows, Path(args.output_dir), max(100, args.bootstrap_samples), args.seed)
    print(f"Validated {audit['n_rows']} rows: complete and unique={audit['is_complete_unique']}")
    print(f"Wrote {len(condition)} condition rows and {len(task_condition)} task-by-condition rows to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
