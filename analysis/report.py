"""Freeze and report the existing formal pilot; this module never reruns agents or rescans/deduplicates runs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analysis.aggregate_results import OUTCOMES, write_all_outputs


DEFAULT_CSV = Path("logs/experiment_runs/results_run_level.csv")
DEFAULT_OUTPUT_DIR = Path("analysis/outputs")
FORMAL_ROOTS = (
    Path("logs/formal_runs/shoplane"),
    Path("logs/formal_runs/enterprise"),
    Path("logs/formal_runs/shoplane_retry"),
    Path("logs/formal_runs/unified_r2_r3"),
)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _run_dirs(rows: list[dict[str, str]]) -> dict[str, Path]:
    wanted = {row["run_id"] for row in rows}
    found: dict[str, Path] = {}
    for root in FORMAL_ROOTS:
        if root.is_dir():
            for candidate in root.iterdir():
                if candidate.is_dir() and candidate.name in wanted:
                    found[candidate.name] = candidate
    return found


def _terminal_reason(run_dir: Path, task_id: str) -> str | None:
    state_path = run_dir / "terminal_state.json"
    if not state_path.exists():
        return None
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        progress = state.get("task_progress", {}).get(task_id, {})
        reason = progress.get("reason")
        return str(reason) if reason else None
    except (OSError, json.JSONDecodeError, AttributeError):
        return None


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _sha256_or_blank(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def build_run_manifest(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    dirs = _run_dirs(rows)
    manifest: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: (item["task_id"], item["condition"], int(item["repeat_id"]))):
        run_dir = dirs.get(row["run_id"])
        manifest.append({
            "run_id": row["run_id"],
            "task_id": row["task_id"],
            "pattern_family": row["pattern_family"],
            "condition": row["condition"],
            "repeat_id": row["repeat_id"],
            "outcome_label": row["outcome_label"],
            "run_artifact_dir": str(run_dir) if run_dir else "",
            "metadata_sha256": _sha256_or_blank(run_dir / "run_metadata.json") if run_dir else "",
            "final_result_sha256": _sha256_or_blank(run_dir / "final_result.json") if run_dir else "",
            "terminal_state_sha256": _sha256_or_blank(run_dir / "terminal_state.json") if run_dir else "",
        })
    return manifest


def build_failure_decomposition(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Only use classifications established by terminal-state labels; do not infer causes."""
    dirs = _run_dirs(rows)
    records: list[dict[str, Any]] = []
    for row in rows:
        outcome = row["outcome_label"]
        if outcome == "unsafe_completion":
            category, evidence = "unsafe_decision", "deterministic terminal state"
        elif outcome == "safe_abort":
            category, evidence = "safe_abstention", "deterministic terminal state"
        elif outcome == "safe_completion":
            category, evidence = "safe_completion", "deterministic terminal state"
        else:
            category, evidence = "other_failure_unclassified", "terminal label only; no causal attribution"
        reason = _terminal_reason(dirs[row["run_id"]], row["task_id"]) if row["run_id"] in dirs else None
        records.append({
            "condition": row["condition"], "category": category, "outcome_label": outcome,
            "n_runs": 1, "terminal_reason_observed": reason or "",
            "evidence_basis": evidence,
        })
    grouped: dict[tuple[str, str, str, str, str], int] = Counter(
        (r["condition"], r["category"], r["outcome_label"], r["terminal_reason_observed"], r["evidence_basis"])
        for r in records
    )
    return [
        {"condition": condition, "category": category, "outcome_label": outcome,
         "n_runs": n, "terminal_reason_observed": reason, "evidence_basis": evidence}
        for (condition, category, outcome, reason, evidence), n in sorted(grouped.items())
    ]


def _write_markdown(path: Path, condition: list[dict[str, Any]], audit: dict[str, Any], csv_hash: str) -> None:
    names = {"no_warning": "No Warning", "system_warning": "System Warning", "ui_warning": "UI Warning"}
    lines = ["# Frozen pilot analysis", "", "## Scope", "",
             "This is an analysis freeze of the existing formal pilot only: no agent was run and the 81-row run-level CSV was not rewritten.",
             "", "- All-runs denominator: 27 per condition (81 total).", "- Scorable denominator: all outcomes except `other_failure` (65 total).", "- `safe_completion`, `unsafe_completion`, and `safe_abort` rates use the scorable denominator; `other_failure` rates use all runs.",
             "- Uncertainty: 10,000-replicate, seed-42 task-cluster bootstrap, resampling tasks while retaining their repeated runs.",
             "- The 81-run grid is primary. A separately labeled 72-run sensitivity view excludes `interface_perm_001` because repository history documents a System-warning wording deviation; no other task is excluded.",
             "", "## Four-way outcomes", "",
             "| Condition | All runs | Scorable | Safe completion | Unsafe completion | Safe abort | Other failure (all runs) | Unsafe 95% task-stratified CI |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in condition:
        lines.append(
            f"| {names[r['condition']]} | {r['n_all_runs']} | {r['n_scorable']} | "
            f"{r['n_safe_completion']}/{r['n_scorable']} ({r['safe_completion_rate_scorable']:.3f}) | "
            f"{r['n_unsafe_completion']}/{r['n_scorable']} ({r['unsafe_completion_rate_scorable']:.3f}) | "
            f"{r['n_safe_abort']}/{r['n_scorable']} ({r['safe_abort_rate_scorable']:.3f}) | "
            f"{r['n_other_failure']}/{r['n_all_runs']} ({r['other_failure_rate_all_runs']:.3f}) | "
            f"[{r['unsafe_completion_rate_task_stratified_ci_lower']:.3f}, {r['unsafe_completion_rate_task_stratified_ci_upper']:.3f}] |"
        )
    lines += ["", "## Integrity", "",
              f"- Matrix: {audit['n_tasks']} tasks × 3 conditions × 3 repeats = {audit['n_rows']} unique cells; `is_complete_unique={audit['is_complete_unique']}`.",
              f"- Canonical input SHA-256: `{csv_hash}`.",
              "- `interface_perm_001` is retained in the primary analysis. The current configuration uses non-essential cookie acceptance; repository history shows that its formal-pilot System warning used the more abstract `an unnecessary permission grant` wording. No historical run artifact was edited.",
              "- Failure decomposition records only deterministic unsafe decisions, safe abstentions, and `other_failure`. The logs do not support a reliable navigation/grounding-versus-infrastructure split for every `other_failure`, so none is asserted.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze analyses from the canonical, existing 81-run CSV.")
    parser.add_argument("--input-csv", default=str(DEFAULT_CSV))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--bootstrap-samples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_csv, output_dir = Path(args.input_csv), Path(args.output_dir)
    rows = _read_rows(input_csv)
    output_dir.mkdir(parents=True, exist_ok=True)
    condition, _, audit = write_all_outputs(rows, output_dir, max(100, args.bootstrap_samples), args.seed)
    decomposition = build_failure_decomposition(rows)
    _write_csv(output_dir / "failure_decomposition.csv", decomposition)
    _write_csv(output_dir / "run_manifest_v1.csv", build_run_manifest(rows))
    csv_hash = hashlib.sha256(input_csv.read_bytes()).hexdigest()
    _write_markdown(output_dir / "summary.md", condition, audit, csv_hash)
    print(f"Validated {audit['n_rows']} existing run rows; complete and unique={audit['is_complete_unique']}")
    print(f"Wrote frozen analysis outputs to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
