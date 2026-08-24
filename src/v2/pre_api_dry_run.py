"""Deterministic, model-free traversal of the complete Protocol v2 schedule."""

from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from src.utils.io import ensure_dir, project_root, write_json
from src.v2.artifacts import ARTIFACT_SCHEMA_VERSION, validate_attempt_directory
from src.v2.execution_adapter import artifact_context, build_attempt_plan
from src.v2.matrix import ScheduledCell, load_schedule, schedule_sha256
from src.v2.runner import ProtocolV2Runner
from src.v2.safeguards import render_warning
from src.v2.state_machine import fixture_for


DRY_RUN_SCHEMA_VERSION = "protocol-v2-pre-api-dry-run-1.0"
RETRY_ORDERS = frozenset({1, 54, 108})
FIXTURE_PAIRS = ((1, 1), (1, 0), (0, 1), (0, 0))


def _context_id(cell: ScheduledCell, attempt_id: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"pre-api:{cell.scheduled_run_id}:{attempt_id}"))


def _exposure(cell: ScheduledCell) -> dict[str, Any]:
    payload = render_warning(cell.task_id)
    condition = cell.safeguard_condition
    return {
        "scheduled_run_id": cell.scheduled_run_id,
        "condition": condition,
        "agent_action_count": 0,
        "panel_visible": True,
        "stop_visible": True,
        "dom_warning_text": payload if condition == "ui_warning" else "",
        "privileged_warning_text": payload if condition == "system_warning" else "",
        "payload_sha256": (
            hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if condition != "no_warning"
            else None
        ),
        "evidence_kind": "synthetic_pre_action_fixture",
    }


def scripted_executor(cell: ScheduledCell, attempt_id: int, clean_context_id: str) -> dict[str, Any]:
    plan = build_attempt_plan(
        cell,
        attempt_id=attempt_id,
        clean_context_id=clean_context_id,
        base_url="http://127.0.0.1:8000",
    )
    context = artifact_context(plan, _exposure(cell))
    common = {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "formal_run": False,
        "synthetic_fixture": True,
        "agent_model_call": False,
        **context,
    }
    if cell.planned_order in RETRY_ORDERS and attempt_id == 1:
        return {
            "run_validity": "browser_transport_failure",
            "events": [],
            "synthetic_failure_injection": True,
            **common,
        }
    pair = FIXTURE_PAIRS[(cell.planned_order - 1) % len(FIXTURE_PAIRS)]
    raw = fixture_for(cell.task_id, *pair)
    raw.update(common)
    raw["warning_delivery_status"] = (
        "not_applicable" if cell.safeguard_condition == "no_warning" else "verified"
    )
    raw["synthetic_path"] = f"fixture_c{pair[0]}s{pair[1]}"
    raw["trajectory"] = list(raw.get("events") or [])
    raw["actions"] = [event.get("event_id") for event in raw["trajectory"]]
    raw["screenshots"] = []
    raw["dom_state_evidence"] = {
        "kind": "synthetic_fixture_hash_only",
        "sha256": hashlib.sha256(plan.site_url.encode("utf-8")).hexdigest(),
    }
    return raw


def run_pre_api_dry_run(output_root: Path | None = None) -> dict[str, Any]:
    root = output_root or project_root() / "artifacts" / "v2" / "pre_api_dry_run"
    formal_root = (project_root() / "logs" / "v2" / "formal").resolve()
    if root.resolve() == formal_root or formal_root in root.resolve().parents:
        raise ValueError("Pre-API dry run cannot write into the formal output tree")
    if root.exists():
        shutil.rmtree(root)
    ensure_dir(root)
    runner = ProtocolV2Runner(
        executor=scripted_executor,
        formal_run=False,
        output_root=root / "runs",
        context_id_factory=_context_id,
    )
    cells = load_schedule()
    results = runner.run(cells)
    by_id = {cell.scheduled_run_id: cell for cell in cells}
    attempts = 0
    retries = 0
    valid_cells = 0
    for result in results:
        cell = by_id[result["scheduled_run_id"]]
        attempts += len(result["attempts"])
        retries += int(len(result["attempts"]) == 2)
        if any(attempt["run_validity"] == "valid" for attempt in result["attempts"]):
            valid_cells += 1
        for attempt in result["attempts"]:
            attempt_dir = root / "runs" / cell.scheduled_run_id / f"attempt_{attempt['attempt_id']}"
            validate_attempt_directory(attempt_dir, cell=cell)
    manifest = {
        "dry_run_schema_version": DRY_RUN_SCHEMA_VERSION,
        "purpose": "pipeline_and_schema_validation_only",
        "treatment_analysis_permitted": False,
        "formal_run": False,
        "synthetic_fixture": True,
        "agent_model_call": False,
        "schedule_sha256": schedule_sha256(),
        "scheduled_cells": len(cells),
        "unique_scheduled_cells": len({cell.scheduled_run_id for cell in cells}),
        "valid_dry_run_records": valid_cells,
        "attempts": attempts,
        "infrastructure_retries_exercised": retries,
        "retry_planned_orders": sorted(RETRY_ORDERS),
        "all_raw_states_rescored": True,
        "formal_directory_written": False,
        "model_or_api_calls": 0,
    }
    write_json(root / "manifest.json", manifest)
    return manifest

