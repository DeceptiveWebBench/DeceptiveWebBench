from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.scorer.outcome import score_state_dict, summarize
from src.utils.io import project_root


CSV_COLUMNS = [
    "run_id",
    "task_id",
    "pattern_family",
    "condition",
    "repeat_id",
    "task_goal_source",
    "system_warning_source",
    "terminal_state",
    "outcome_label",
    "risk_taken",
    "safe_path",
    "completed",
]

STATE_CANDIDATE_FILES = [
    "terminal_state.json",
    "state_terminal.json",
    "state.json",
]


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_metadata(run_dir: Path) -> dict[str, Any] | None:
    metadata_path = run_dir / "run_metadata.json"
    if not metadata_path.exists():
        print(f"[WARN] Missing run_metadata.json: {run_dir}")
        return None
    try:
        return _read_json(metadata_path)
    except Exception as exc:
        print(f"[WARN] Failed to read run_metadata.json at {run_dir}: {type(exc).__name__}: {exc}")
        return None


def _resolve_run_identity(run_dir: Path, metadata: dict[str, Any] | None) -> dict[str, Any]:
    metadata = metadata or {}
    return {
        "run_id": str(metadata.get("run_id") or run_dir.name),
        "task_id": str(metadata.get("task_id") or "unknown_task"),
        "pattern_family": str(metadata.get("pattern_family") or "unknown_pattern_family"),
        "condition": str(metadata.get("condition") or "unknown_condition"),
        "repeat_id": str(metadata.get("repeat_idx") or "unknown_repeat"),
        "task_goal_source": str(metadata.get("task_goal_source") or "unknown_task_goal_source"),
        "system_warning_source": str(metadata.get("system_warning_source") or "unknown_system_warning_source"),
    }


def _infer_default_state(identity: dict[str, Any]) -> dict[str, Any]:
    task_id = identity["task_id"]
    condition = identity["condition"]
    return {
        "session_id": identity["run_id"],
        "active_task": task_id,
        "condition": condition,
        "task_progress": {
            task_id: {
                "completed": False,
                "risk_taken": False,
                "safe_path": False,
                "terminal_state": "other_failure",
                "reason": "missing_or_unreadable_state",
                "last_action": None,
            }
        },
    }


def _load_best_effort_state(run_dir: Path, identity: dict[str, Any]) -> dict[str, Any]:
    for filename in STATE_CANDIDATE_FILES:
        candidate = run_dir / filename
        if not candidate.exists():
            continue
        try:
            payload = _read_json(candidate)
            if isinstance(payload, dict):
                return payload
            print(f"[WARN] Non-dict state payload in {candidate}; fallback to other_failure for {identity['run_id']}")
            return _infer_default_state(identity)
        except Exception as exc:
            print(
                f"[WARN] Failed to read state file {candidate}: {type(exc).__name__}: {exc}; "
                f"fallback to other_failure for {identity['run_id']}"
            )
            return _infer_default_state(identity)

    final_result_path = run_dir / "final_result.json"
    if not final_result_path.exists():
        print(f"[WARN] Missing state and final_result.json for {identity['run_id']}; fallback to other_failure")
        return _infer_default_state(identity)

    try:
        final_payload = _read_json(final_result_path)
        if str(final_payload.get("status")) != "completed":
            print(f"[WARN] Non-completed run {identity['run_id']}; fallback to other_failure")
            return _infer_default_state(identity)
    except Exception as exc:
        print(
            f"[WARN] Failed to read final_result.json for {identity['run_id']}: "
            f"{type(exc).__name__}: {exc}; fallback to other_failure"
        )
        return _infer_default_state(identity)

    # Formal runner may persist full sandbox state as terminal_state.json (localStorage snapshot).
    # If still missing, keep a deterministic fallback aligned to protocol schema.
    print(f"[WARN] No terminal state JSON for {identity['run_id']}; fallback to other_failure")
    return _infer_default_state(identity)


def _score_run_dir(run_dir: Path) -> dict[str, Any] | None:
    if not run_dir.is_dir():
        return None

    metadata = _load_metadata(run_dir)
    identity = _resolve_run_identity(run_dir, metadata)
    state_dict = _load_best_effort_state(run_dir, identity)
    outcome_summary = summarize(score_state_dict(state_dict))

    terminal_state = str(outcome_summary.get("terminal_state") or "other_failure")
    return {
        "run_id": identity["run_id"],
        "task_id": identity["task_id"],
        "pattern_family": identity["pattern_family"],
        "condition": identity["condition"],
        "repeat_id": identity["repeat_id"],
        "task_goal_source": identity["task_goal_source"],
        "system_warning_source": identity["system_warning_source"],
        "terminal_state": terminal_state,
        "outcome_label": terminal_state,
        "risk_taken": bool(outcome_summary.get("risk_taken", False)),
        "safe_path": bool(outcome_summary.get("safe_path", False)),
        "completed": bool(outcome_summary.get("completed", False)),
    }


def build_rows(runs_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run_dir in sorted(runs_root.iterdir()):
        row = _score_run_dir(run_dir)
        if row:
            rows.append(row)
    return rows


def write_csv(rows: list[dict[str, Any]], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Batch-score experiment run directories into a run-level CSV. "
            "For merged formal logs across shoplane/enterprise/retry, use `python -m analysis` instead."
        )
    )
    parser.add_argument(
        "--runs-root",
        default="logs/experiment_runs",
        help="Run output root directory produced by formal runner.",
    )
    parser.add_argument(
        "--output-csv",
        default=None,
        help="Output CSV path. Default: <runs_root>/results_run_level.csv",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    runs_root = Path(args.runs_root)
    if not runs_root.is_absolute():
        runs_root = project_root() / runs_root
    runs_root = runs_root.resolve()

    if not runs_root.exists() or not runs_root.is_dir():
        raise FileNotFoundError(f"Run root does not exist or is not a directory: {runs_root}")

    if args.output_csv:
        output_csv = Path(args.output_csv)
        if not output_csv.is_absolute():
            output_csv = project_root() / output_csv
    else:
        output_csv = runs_root / "results_run_level.csv"
    output_csv = output_csv.resolve()

    rows = build_rows(runs_root)
    write_csv(rows, output_csv)
    print(f"Scored runs: {len(rows)}")
    print(f"Wrote CSV: {output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

