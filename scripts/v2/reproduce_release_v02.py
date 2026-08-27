"""Rebuild Protocol v2 aggregate analysis from the anonymous tabular release.

This entry point never reads ignored ``logs/`` trees and never calls a model.
It is the clean-release counterpart to the raw-attempt audit: it reconstructs
all aggregate CSVs used by the manuscript, checks the canonical matrix, and
verifies the released append-only adjudication evidence byte-for-byte.
"""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
from pathlib import Path

from analysis.formal_v02_author_insights import cost_analysis, summarize, write_csv
from src.utils.io import project_root
from src.v2.formal_action_schema_adjudication import verify_adjudication
from src.v2.matrix import load_schedule, schedule_sha256


ROOT = project_root()
SRC = ROOT / "artifacts/v2/formal_v02_108/author_insight_review"
ADJUDICATION = (
    ROOT
    / "artifacts/v2/formal_v02_108/adjudication_evidence"
    / "v2__forced_action_sub_001__ui_warning__r3/attempt_1"
)

AGGREGATES = {
    "condition_summary.csv": "condition",
    "task_condition_summary.csv": "task",
    "repeat_summary.csv": "repeat",
    "family_summary_exploratory.csv": "family",
    "contrast_bootstrap.csv": "contrasts",
    "paired_transitions.csv": "transitions",
    "leave_one_task_out_posthoc.csv": "loto",
    "missing_cell_sensitivity.csv": "missing",
    "termination_summary.csv": "termination",
    "repeat_consistency.csv": "consistency",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(name: str) -> list[dict[str, str]]:
    with (SRC / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def released_rows() -> list[dict]:
    rows: list[dict] = []
    integer_fields = {
        "planned_order", "repeat_id", "n_attempts", "selected_attempt", "valid", "unavailable",
        "C", "S", "TC", "model_calls", "input_tokens", "output_tokens", "total_tokens",
    }
    optional_integer_fields = {"unsafe_boundary_first_step", "termination_step"}
    float_fields = {"wall_clock_seconds", "model_latency_seconds", "known_cost_usd"}
    for raw in read_csv("analysis_dataset.csv"):
        row: dict = dict(raw)
        for field in integer_fields:
            row[field] = int(raw[field])
        for field in optional_integer_fields:
            row[field] = int(raw[field]) if raw[field] else None
        for field in float_fields:
            row[field] = float(raw[field]) if raw[field] else ""
        rows.append(row)
    return rows


def released_attempts() -> list[dict]:
    rows: list[dict] = []
    integer_fields = {"repeat_id", "attempt_id", "model_calls", "input_tokens", "output_tokens", "total_tokens"}
    float_fields = {"wall_clock_seconds", "model_latency_seconds"}
    for raw in read_csv("attempt_audit.csv"):
        row: dict = dict(raw)
        for field in integer_fields:
            row[field] = int(raw[field])
        for field in float_fields:
            row[field] = float(raw[field])
        row["known_cost_usd"] = float(raw["known_cost_usd"]) if raw["known_cost_usd"] else None
        row["cost_known"] = raw["cost_known"] == "1"
        rows.append(row)
    return rows


def main() -> int:
    rows = released_rows()
    attempts = released_attempts()
    schedule = load_schedule()
    expected = {
        (cell.scheduled_run_id, cell.task_id, cell.safeguard_condition, cell.repeat_id, cell.task_version)
        for cell in schedule
    }
    observed = {
        (row["scheduled_run_id"], row["task_id"], row["condition"], row["repeat_id"], row["task_version"])
        for row in rows
    }
    failures: list[str] = []
    if len(rows) != 108 or len({row["scheduled_run_id"] for row in rows}) != 108 or observed != expected:
        failures.append("released 108-row dataset does not match the canonical matrix")
    if not all(row["valid"] == 1 and row["unavailable"] == 0 for row in rows):
        failures.append("released dataset contains non-valid or unavailable selected cells")
    if len(attempts) != 112:
        failures.append(f"expected 112 attempt-audit rows, found {len(attempts)}")

    adjudication = verify_adjudication(ADJUDICATION)
    if adjudication.get("adjudicated_outcome") != "safe_non_completion" or adjudication.get("rerun_performed") is not False:
        failures.append("released append-only adjudication evidence did not verify")

    stats = summarize(rows)
    costs = cost_analysis(rows, attempts)
    regenerated: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="deceptivewebbench-release-repro-") as tmp:
        out = Path(tmp)
        for name, key in AGGREGATES.items():
            target = out / name
            write_csv(target, stats[key])
            regenerated[name] = sha256(target)
            if target.read_bytes() != (SRC / name).read_bytes():
                failures.append(f"aggregate mismatch: {name}")
        for name, values in (("cost_summary.csv", costs["summary"]), ("cost_by_task.csv", costs["task"])):
            target = out / name
            write_csv(target, values)
            regenerated[name] = sha256(target)
            if target.read_bytes() != (SRC / name).read_bytes():
                failures.append(f"aggregate mismatch: {name}")

    result = {
        "status": "PASS" if not failures else "FAIL",
        "mode": "released-tabular-data-no-raw-logs",
        "matrix_sha256": schedule_sha256(),
        "scheduled_cells": len(rows),
        "unique_cells": len({row["scheduled_run_id"] for row in rows}),
        "attempt_audit_rows": len(attempts),
        "adjudication_verified": not any("adjudication" in failure for failure in failures),
        "regenerated_aggregate_files": regenerated,
        "known_cost_usd": costs["known_cost"],
        "unknown_cost_attempts": costs["unknown_attempts"],
        "failures": failures,
        "model_api_calls": 0,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
