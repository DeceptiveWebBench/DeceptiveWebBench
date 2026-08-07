"""Verify that paper-facing numerical claims match frozen analysis outputs."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_one(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(text: str, fragment: str, source: str) -> None:
    if fragment not in text:
        raise AssertionError(f"Missing from {source}: {fragment}")


def three(value: str) -> str:
    return f"{float(value):.3f}".lstrip("0")


def main() -> int:
    main_tex = (ROOT / "paper/neurips_2026.tex").read_text(encoding="utf-8")
    supplement_tex = (ROOT / "paper/supplement_v1_2026-08-09.tex").read_text(encoding="utf-8")
    main_table = (ROOT / "paper/tabs/tab_main.tex").read_text(encoding="utf-8")
    task_table = (ROOT / "paper/tabs/tab_task_condition_supp.tex").read_text(encoding="utf-8")
    sensitivity_table = (ROOT / "paper/tabs/tab_sensitivity_supp.tex").read_text(encoding="utf-8")

    labels = {"no_warning": "No Warning", "system_warning": "System Warning", "ui_warning": "UI Warning"}
    short = {"no_warning": "No", "system_warning": "System", "ui_warning": "UI"}
    for row in read_one("analysis/outputs/summary_by_condition.csv"):
        line = (
            f"{labels[row['condition']]} & {row['n_all_runs']} & {row['n_scorable']} & "
            f"{row['n_safe_completion']}/{row['n_scorable']} ({three(row['safe_completion_rate_scorable'])}) & "
            f"{row['n_unsafe_completion']}/{row['n_scorable']} ({three(row['unsafe_completion_rate_scorable'])}) "
            f"[{three(row['unsafe_completion_rate_task_stratified_ci_lower'])},{three(row['unsafe_completion_rate_task_stratified_ci_upper'])}] & "
            f"{row['n_safe_abort']}/{row['n_scorable']} ({three(row['safe_abort_rate_scorable'])}) & "
            f"{row['n_other_failure']}/{row['n_all_runs']} ({three(row['other_failure_rate_all_runs'])})"
        )
        require(main_table, line, "tab_main.tex")

    previous_task = None
    for row in read_one("analysis/outputs/task_by_condition.csv"):
        task = rf"\path{{{row['task_id']}}}" if row["task_id"] != previous_task else ""
        line = (
            f"{task} & {short[row['condition']]} & {row['n_all_runs']} & {row['n_scorable']} & "
            f"{row['n_safe_completion']} & {row['n_unsafe_completion']} & {row['n_safe_abort']} & {row['n_other_failure']}"
        )
        require(task_table, line, "tab_task_condition_supp.tex")
        previous_task = row["task_id"]

    for row in read_one("analysis/outputs/sensitivity_without_interface_perm_001.csv"):
        line = (
            f"{labels[row['condition']]} & {row['n_all_runs']} & {row['n_scorable']} & "
            f"{row['n_safe_completion']}/{row['n_scorable']} ({three(row['safe_completion_rate_scorable'])}) & "
            f"{row['n_unsafe_completion']}/{row['n_scorable']} ({three(row['unsafe_completion_rate_scorable'])}) "
            f"[{three(row['unsafe_completion_rate_task_stratified_ci_lower'])},{three(row['unsafe_completion_rate_task_stratified_ci_upper'])}]"
        )
        require(sensitivity_table, line, "tab_sensitivity_supp.tex")

    diff = read_one("analysis/outputs/summary_system_vs_ui.csv")[0]
    sens_diff = read_one("analysis/outputs/sensitivity_system_vs_ui_without_interface_perm_001.csv")[0]
    require(main_tex, "$+1.7$ percentage points", "neurips_2026.tex")
    require(main_tex, "$[-33.6,+36.6]$ points", "neurips_2026.tex")
    require(supplement_tex, "$-13.7$ points", "supplement_v1_2026-08-09.tex")
    require(supplement_tex, "$[-43.3,+12.3]$ points", "supplement_v1_2026-08-09.tex")
    assert round(float(diff["rate_diff_system_minus_ui"]) * 100, 1) == 1.7
    assert round(float(sens_diff["rate_diff_system_minus_ui"]) * 100, 1) == -13.7

    manifest = read_one("analysis/outputs/run_manifest_v1.csv")
    assert len(manifest) == 81
    assert len({(r["task_id"], r["condition"], r["repeat_id"]) for r in manifest}) == 81
    print("PASS: paper tables and stated estimates match frozen analysis outputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
