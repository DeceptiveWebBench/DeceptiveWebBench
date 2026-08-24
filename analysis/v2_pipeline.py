"""Formal-only Protocol v2 analysis intake and future table-input builder."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from src.v2.artifacts import read_json, validate_attempt_directory
from src.v2.matrix import load_schedule, schedule_sha256


class FormalAnalysisEligibilityError(ValueError):
    """Raised before non-formal or incomplete evidence can enter analysis."""


def assert_formal_analysis_eligible(metadata: dict[str, Any]) -> None:
    if metadata.get("formal_run") is not True:
        raise FormalAnalysisEligibilityError("Analysis requires formal_run=true")
    if metadata.get("synthetic_fixture") is not False:
        raise FormalAnalysisEligibilityError("Synthetic fixtures are excluded from formal analysis")
    if metadata.get("agent_model_call") is not True:
        raise FormalAnalysisEligibilityError("Formal artifacts require an actual frozen agent call")
    if metadata.get("schedule_sha256") != schedule_sha256():
        raise FormalAnalysisEligibilityError("Matrix hash does not match the canonical schedule")


def load_formal_attempts(root: Path) -> list[dict[str, Any]]:
    """Load one selected valid attempt per canonical cell or fail closed."""

    selected: list[dict[str, Any]] = []
    for cell in load_schedule():
        run_dir = root / cell.scheduled_run_id
        attempt_dirs = sorted(
            (path for path in run_dir.glob("attempt_*") if path.is_dir()),
            key=lambda path: int(path.name.split("_")[-1]),
        )
        if not attempt_dirs:
            raise FormalAnalysisEligibilityError(f"Missing scheduled cell: {cell.scheduled_run_id}")
        if len(attempt_dirs) > 2:
            raise FormalAnalysisEligibilityError(f"More than one retry: {cell.scheduled_run_id}")
        candidate = None
        for index, attempt_dir in enumerate(attempt_dirs, start=1):
            if attempt_dir.name != f"attempt_{index}":
                raise FormalAnalysisEligibilityError(f"Non-contiguous attempts: {cell.scheduled_run_id}")
            metadata = read_json(attempt_dir / "run_metadata.json")
            assert_formal_analysis_eligible(metadata)
            validate_attempt_directory(attempt_dir, cell=cell)
            scored = read_json(attempt_dir / "scored_outcome.json")
            if scored.get("run_validity") == "valid":
                candidate = {
                    "cell": cell,
                    "metadata": metadata,
                    "scored": scored,
                    "attempt_dir": attempt_dir,
                }
                if index == 1 and len(attempt_dirs) == 2:
                    raise FormalAnalysisEligibilityError(
                        f"Valid first attempt was retried: {cell.scheduled_run_id}"
                    )
        if candidate is None:
            # Unavailable after an allowed retry is retained in accounting, never imputed.
            selected.append({"cell": cell, "metadata": None, "scored": None})
        else:
            selected.append(candidate)
    if len({item["cell"].scheduled_run_id for item in selected}) != 108:
        raise FormalAnalysisEligibilityError("Duplicate or missing scheduled cells")
    return selected


def build_future_table_inputs(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create raw condition counts without imputing unavailable cells."""

    rows: list[dict[str, Any]] = []
    for condition in ("no_warning", "system_warning", "ui_warning"):
        subset = [item for item in selected if item["cell"].safeguard_condition == condition]
        valid = [item["scored"] for item in subset if item["scored"] is not None]
        counts = Counter(item["outcome_label"] for item in valid)
        rows.append(
            {
                "condition": condition,
                "n_scheduled": len(subset),
                "n_valid": len(valid),
                "n_unavailable": len(subset) - len(valid),
                "trustworthy_completion": counts["trustworthy_completion"],
                "unsafe_completion": counts["unsafe_completion"],
                "safe_non_completion": counts["safe_non_completion"],
                "unsafe_failure": counts["unsafe_failure"],
            }
        )
    return rows


def validate_pre_api_dry_run_only(root: Path) -> dict[str, Any]:
    """Permit schema audit while explicitly refusing treatment analysis."""

    manifest = read_json(root / "manifest.json")
    if manifest.get("formal_run") is not False:
        raise FormalAnalysisEligibilityError("Dry-run manifest must be non-formal")
    if manifest.get("synthetic_fixture") is not True or manifest.get("agent_model_call") is not False:
        raise FormalAnalysisEligibilityError("Dry-run provenance flags are inconsistent")
    if manifest.get("treatment_analysis_permitted") is not False:
        raise FormalAnalysisEligibilityError("Dry-run data must prohibit treatment analysis")
    if manifest.get("scheduled_cells") != 108 or manifest.get("valid_dry_run_records") != 108:
        raise FormalAnalysisEligibilityError("Dry-run accounting is incomplete")
    return manifest
