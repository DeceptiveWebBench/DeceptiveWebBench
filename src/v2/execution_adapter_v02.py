"""Version-explicit v0.2 execution adapter; no provider call occurs here."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from src.v2.execution_adapter import ADAPTER_STATUS, AdapterContractError
from src.v2.matrix import ScheduledCell, schedule_sha256
from src.v2.safeguards import PromptBundleV2
from src.v2.safeguards_v02 import (
    WARNING_VERSION,
    build_prompt_bundle,
    payload_sha256,
    render_warning,
)
from src.v2.sites import site_index_path


@dataclass(frozen=True)
class AttemptPlanV02:
    cell: ScheduledCell
    attempt_id: int
    clean_context_id: str
    site_url: str
    prompt_bundle: PromptBundleV2
    schedule_sha256: str
    safeguard_version: str = WARNING_VERSION
    adapter_status: str = ADAPTER_STATUS


def build_site_url(cell: ScheduledCell, *, base_url: str) -> str:
    query = urlencode({
        "task": cell.task_id,
        "condition": cell.safeguard_condition,
        "scheduled_run_id": cell.scheduled_run_id,
        "safeguard_version": WARNING_VERSION,
        "new_run": "1",
    })
    return f"{base_url.rstrip('/')}/{site_index_path(cell.task_id)}?{query}"


def build_attempt_plan(cell: ScheduledCell, *, attempt_id: int, clean_context_id: str, base_url: str) -> AttemptPlanV02:
    if attempt_id not in (1, 2):
        raise AdapterContractError("attempt_id must be 1 or 2")
    if not str(clean_context_id).strip():
        raise AdapterContractError("clean_context_id is required")
    url = build_site_url(cell, base_url=base_url)
    return AttemptPlanV02(
        cell=cell,
        attempt_id=attempt_id,
        clean_context_id=clean_context_id,
        site_url=url,
        prompt_bundle=build_prompt_bundle(
            task_id=cell.task_id,
            condition=cell.safeguard_condition,
            page_url=url,
            scheduled_run_id=cell.scheduled_run_id,
        ),
        schedule_sha256=schedule_sha256(),
    )


def verify_pre_action_exposure(plan: AttemptPlanV02, evidence: dict[str, Any]) -> None:
    if evidence.get("agent_action_count") != 0:
        raise AdapterContractError("Safeguard exposure must precede the first action")
    if evidence.get("scheduled_run_id") != plan.cell.scheduled_run_id:
        raise AdapterContractError("Exposure scheduled cell mismatch")
    if evidence.get("condition") != plan.cell.safeguard_condition:
        raise AdapterContractError("Exposure condition mismatch")
    if evidence.get("safeguard_version") not in (None, WARNING_VERSION):
        raise AdapterContractError("Exposure safeguard version mismatch")
    payload = render_warning(plan.cell.task_id)
    dom = evidence.get("dom_warning_text") or ""
    privileged = evidence.get("privileged_warning_text") or ""
    condition = plan.cell.safeguard_condition
    if condition == "ui_warning":
        if dom != payload or privileged or not evidence.get("panel_visible"):
            raise AdapterContractError("Interface delivery evidence is not exact")
    elif condition == "system_warning":
        if privileged != payload or dom:
            raise AdapterContractError("System delivery evidence is not exact")
    elif privileged or dom:
        raise AdapterContractError("No-safeguard condition is contaminated")
    if not evidence.get("stop_visible"):
        raise AdapterContractError("Stop task must be visible before action 1")
    if evidence.get("payload_sha256") not in (None, payload_sha256(payload)):
        raise AdapterContractError("Payload hash mismatch")


def artifact_context(plan: AttemptPlanV02, evidence: dict[str, Any]) -> dict[str, Any]:
    verify_pre_action_exposure(plan, evidence)
    capture = dict(plan.prompt_bundle.capture)
    return {
        "site_url": plan.site_url,
        "schedule_sha256": plan.schedule_sha256,
        "prompt_capture": capture,
        "delivery_evidence": dict(evidence),
        "adapter_status": plan.adapter_status,
        "safeguard_version": WARNING_VERSION,
        "prompt_capture_sha256": hashlib.sha256(repr(sorted(capture.items())).encode()).hexdigest(),
    }
