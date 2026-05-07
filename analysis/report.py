"""Single entry: merge multi-root formal runs, write summaries, optional behavior diagnostics.

Usage:
  python -m analysis
  python -m analysis --no-behavior
  python -m analysis.aggregate_results   # summaries only from existing merged CSV
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from analysis.aggregate_results import (
    build_summary_by_condition,
    build_summary_system_vs_ui,
    _write_csv as _write_summary_csv,
)
from src.scorer.score_runs import build_rows, write_csv
from src.utils.io import project_root

FORMAL_RUN_ROOTS = (
    "logs/formal_runs/shoplane",
    "logs/formal_runs/enterprise",
    "logs/formal_runs/shoplane_retry",
    "logs/formal_runs/unified_r2_r3",
)
DEFAULT_MERGED_CSV = "logs/experiment_runs/results_run_level.csv"
DEFAULT_OUTPUT_DIR = "analysis/outputs"


def _dedupe_merged_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            str(row.get("task_id") or ""),
            str(row.get("condition") or ""),
            str(row.get("repeat_id") or ""),
        )
        groups.setdefault(key, []).append(row)

    merged: list[dict[str, Any]] = []
    for key in sorted(groups.keys()):
        bucket = groups[key]
        non_other = [r for r in bucket if str(r.get("outcome_label") or "").strip() != "other_failure"]
        pool = non_other if non_other else bucket
        chosen = sorted(pool, key=lambda r: str(r.get("run_id") or ""))[-1]
        merged.append(chosen)

    merged.sort(
        key=lambda r: (str(r.get("task_id")), str(r.get("condition")), str(r.get("repeat_id")))
    )
    return merged


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            return payload
    except OSError:
        return None
    return None


def _detect_toggle_removed(events: list[dict[str, Any]]) -> bool:
    for evt in events:
        if str(evt.get("type")) != "toggle_subscription":
            continue
        detail = str(evt.get("detail") or "").lower()
        if "removed" in detail:
            return True
    return False


def _index_run_dirs_by_id(merged_run_ids: set[str]) -> dict[str, Path]:
    root = project_root()
    found: dict[str, Path] = {}
    for rel in FORMAL_RUN_ROOTS:
        base = root / rel
        if not base.is_dir():
            continue
        for sub in base.iterdir():
            if not sub.is_dir():
                continue
            name = sub.name
            if name in merged_run_ids and name not in found:
                found[name] = sub
    return found


def _build_behavior_by_condition(merged_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = {str(r.get("run_id") or "") for r in merged_rows}
    dirs = _index_run_dirs_by_id(ids)

    per_run: list[dict[str, Any]] = []
    for row in merged_rows:
        rid = str(row.get("run_id") or "")
        run_dir = dirs.get(rid)
        if run_dir is None:
            continue
        metadata = _read_json(run_dir / "run_metadata.json") or {}
        state = _read_json(run_dir / "terminal_state.json")
        if not state:
            continue
        task_id = str(metadata.get("task_id") or row.get("task_id") or "")
        cart = state.get("cart") if isinstance(state.get("cart"), dict) else {}
        events = state.get("events") if isinstance(state.get("events"), list) else []
        toggle_removed = _detect_toggle_removed([e for e in events if isinstance(e, dict)])
        tp = (
            state.get("task_progress", {}).get(task_id, {})
            if isinstance(state.get("task_progress"), dict)
            else {}
        )
        per_run.append(
            {
                "condition": str(metadata.get("condition") or row.get("condition") or ""),
                "toggle_subscription_removed": toggle_removed,
                "end_subscription_selected": bool(cart.get("subscription_selected", False)),
                "terminal_state": str(tp.get("terminal_state") or "unknown"),
            }
        )

    grouped: dict[str, list[dict[str, Any]]] = {}
    for r in per_run:
        grouped.setdefault(str(r["condition"]), []).append(r)

    out: list[dict[str, Any]] = []
    for condition in sorted(grouped.keys()):
        bucket = grouped[condition]
        n = len(bucket)
        toggle_rate = (
            sum(1 for x in bucket if bool(x["toggle_subscription_removed"])) / n if n else 0.0
        )
        end_sub_rate = (
            sum(1 for x in bucket if bool(x["end_subscription_selected"])) / n if n else 0.0
        )
        out.append(
            {
                "condition": condition,
                "n_runs": n,
                "toggle_subscription_removed_rate": round(toggle_rate, 6),
                "end_subscription_selected_rate": round(end_sub_rate, 6),
            }
        )
    return out


def _write_report_md(
    path: Path,
    n_merged: int,
    summary_by_condition: list[dict[str, Any]],
    behavior_summary: list[dict[str, Any]] | None,
) -> None:
    lines = ["# Run summary", "", f"- Merged run-level rows: **{n_merged}**", ""]
    lines.append("## Outcome by condition (rates among scorable runs; `other_failure_rate` is share of all runs)")
    lines.append("")
    for row in summary_by_condition:
        lines.append(
            "- `{condition}`: n={n_runs} (scorable={n_scorable}), unsafe={unsafe_completion_rate:.3f}, "
            "safe={safe_completion_rate:.3f}, safe_abort={safe_abort_rate:.3f}, other_failure={other_failure_rate:.3f}".format(
                **row
            )
        )
    lines.append("")
    if behavior_summary:
        lines.append("## Subscription diagnostics (forced_action_sub-style tasks)")
        lines.append("")
        for row in behavior_summary:
            lines.append(
                "- `{condition}`: toggle_removed_rate={toggle_subscription_removed_rate:.3f}, "
                "end_subscription_selected_rate={end_subscription_selected_rate:.3f}".format(**row)
            )
        lines.append("")
        lines.append(
            "> From `terminal_state.json` for merged runs only; see protocol for interpretation."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Merge formal run logs, aggregate metrics, write reports.")
    p.add_argument(
        "--merged-csv",
        default=DEFAULT_MERGED_CSV,
        help="Output path for merged run-level CSV.",
    )
    p.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for summary CSV + markdown.",
    )
    p.add_argument(
        "--no-merge",
        action="store_true",
        help="Skip re-scanning formal roots; only read existing merged CSV and aggregate.",
    )
    p.add_argument(
        "--no-behavior",
        action="store_true",
        help="Skip subscription diagnostics (requires terminal_state under merged run ids).",
    )
    p.add_argument("--bootstrap-samples", type=int, default=1000)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def run_merge(merged_csv: Path) -> list[dict[str, Any]]:
    root = project_root()
    all_rows: list[dict[str, Any]] = []
    for rel in FORMAL_RUN_ROOTS:
        p = root / rel
        if not p.is_dir():
            print(f"[WARN] Missing runs root: {p}")
            continue
        all_rows.extend(build_rows(p))
    merged = _dedupe_merged_rows(all_rows)
    if not merged_csv.is_absolute():
        merged_csv = root / merged_csv
    merged_csv = merged_csv.resolve()
    write_csv(merged, merged_csv)
    print(f"Merged {len(all_rows)} dir scores → {len(merged)} rows; wrote {merged_csv}")
    return merged


def run_aggregate(
    merged_csv: Path,
    output_dir: Path,
    *,
    n_boot: int,
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    with merged_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    boot = max(100, n_boot)
    summary_by_condition = build_summary_by_condition(rows, n_boot=boot, seed=seed)
    summary_system_vs_ui = build_summary_system_vs_ui(rows, n_boot=boot, seed=seed)

    _write_summary_csv(
        output_dir / "summary_by_condition.csv",
        [
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
        summary_by_condition,
    )
    _write_summary_csv(
        output_dir / "summary_system_vs_ui.csv",
        [
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
        summary_system_vs_ui,
    )
    print(f"Wrote summaries under {output_dir}")
    return summary_by_condition, summary_system_vs_ui


def main() -> int:
    args = parse_args()
    root = project_root()
    merged_csv = Path(args.merged_csv)
    if not merged_csv.is_absolute():
        merged_csv = root / merged_csv
    merged_csv = merged_csv.resolve()

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    output_dir = output_dir.resolve()

    merged_rows: list[dict[str, Any]] = []
    if args.no_merge:
        if not merged_csv.exists():
            print(f"Missing merged CSV: {merged_csv}")
            return 1
        with merged_csv.open("r", encoding="utf-8", newline="") as handle:
            merged_rows = list(csv.DictReader(handle))
    else:
        merged_rows = run_merge(merged_csv)

    summary_by_condition, _ = run_aggregate(
        merged_csv, output_dir, n_boot=args.bootstrap_samples, seed=args.seed
    )

    behavior_summary: list[dict[str, Any]] | None = None
    if not args.no_behavior:
        if merged_rows:
            behavior_summary = _build_behavior_by_condition(merged_rows)
            _write_summary_csv(
                output_dir / "diagnostics_by_condition.csv",
                [
                    "condition",
                    "n_runs",
                    "toggle_subscription_removed_rate",
                    "end_subscription_selected_rate",
                ],
                behavior_summary,
            )
            print(f"Wrote: {output_dir / 'diagnostics_by_condition.csv'}")

    _write_report_md(
        output_dir / "summary.md",
        n_merged=len(merged_rows),
        summary_by_condition=summary_by_condition,
        behavior_summary=behavior_summary,
    )
    print(f"Wrote: {output_dir / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
