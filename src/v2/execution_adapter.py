"""Pre-API execution contract for a future BrowserUse-backed v2 executor.

No model SDK is imported here.  The bridge protocol is exercised with local
mocks; provider/scaffold event shapes remain a first-smoke verification item.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlencode

from src.v2.matrix import ScheduledCell, schedule_sha256
from src.v2.safeguards import PromptBundleV2, build_prompt_bundle, payload_sha256, render_warning
from src.v2.sites import site_index_path


ADAPTER_STATUS = "QWEN_BEDROCK_CONVERSE_NONFORMAL_SMOKE_VERIFIED_2026-08-17"


class AdapterContractError(ValueError):
    """Raised when pre-action exposure or lifecycle evidence is inconsistent."""


class BrowserExecutionBridge(Protocol):
    """Minimal interface the future BrowserUse executor must implement."""

    def open_clean_context(self, clean_context_id: str) -> None: ...
    def navigate(self, url: str) -> None: ...
    def capture_pre_action_exposure(self) -> dict[str, Any]: ...
    def read_state(self) -> dict[str, Any]: ...
    def close_context(self) -> None: ...


@dataclass(frozen=True)
class AttemptPlan:
    cell: ScheduledCell
    attempt_id: int
    clean_context_id: str
    site_url: str
    prompt_bundle: PromptBundleV2
    schedule_sha256: str
    adapter_status: str = ADAPTER_STATUS


def build_site_url(cell: ScheduledCell, *, base_url: str) -> str:
    query = urlencode(
        {
            "task": cell.task_id,
            "condition": cell.safeguard_condition,
            "scheduled_run_id": cell.scheduled_run_id,
            "new_run": "1",
        }
    )
    return f"{base_url.rstrip('/')}/{site_index_path(cell.task_id)}?{query}"


def build_attempt_plan(
    cell: ScheduledCell,
    *,
    attempt_id: int,
    clean_context_id: str,
    base_url: str,
) -> AttemptPlan:
    if attempt_id not in (1, 2):
        raise AdapterContractError("attempt_id must be 1 or 2")
    if not str(clean_context_id).strip():
        raise AdapterContractError("clean_context_id is required")
    url = build_site_url(cell, base_url=base_url)
    bundle = build_prompt_bundle(
        task_id=cell.task_id,
        condition=cell.safeguard_condition,
        page_url=url,
        scheduled_run_id=cell.scheduled_run_id,
    )
    return AttemptPlan(
        cell=cell,
        attempt_id=attempt_id,
        clean_context_id=clean_context_id,
        site_url=url,
        prompt_bundle=bundle,
        schedule_sha256=schedule_sha256(),
    )


def verify_pre_action_exposure(plan: AttemptPlan, evidence: dict[str, Any]) -> None:
    if evidence.get("agent_action_count") != 0:
        raise AdapterContractError("Warning exposure must be verified before the first action")
    if evidence.get("scheduled_run_id") != plan.cell.scheduled_run_id:
        raise AdapterContractError("Exposure evidence belongs to another scheduled cell")
    if evidence.get("condition") != plan.cell.safeguard_condition:
        raise AdapterContractError("Exposure condition mismatch")

    expected_payload = render_warning(plan.cell.task_id)
    expected_hash = payload_sha256(expected_payload)
    dom_text = evidence.get("dom_warning_text") or ""
    prompt_text = evidence.get("privileged_warning_text") or ""
    condition = plan.cell.safeguard_condition
    if condition == "ui_warning":
        if dom_text != expected_payload or prompt_text:
            raise AdapterContractError("UI warning must be exact in DOM and absent from prompt")
        if not evidence.get("panel_visible") or not evidence.get("stop_visible"):
            raise AdapterContractError("UI warning and Stop task must be visible at step 0")
    elif condition == "system_warning":
        if prompt_text != expected_payload or dom_text:
            raise AdapterContractError("System warning must be exact in prompt and absent from DOM")
        if not evidence.get("stop_visible"):
            raise AdapterContractError("Stop task must be visible in System condition")
    else:
        if prompt_text or dom_text:
            raise AdapterContractError("No Warning condition contains safeguard contamination")
        if not evidence.get("stop_visible"):
            raise AdapterContractError("Stop task must be visible in No Warning condition")
    if evidence.get("payload_sha256") not in (None, expected_hash):
        raise AdapterContractError("Exposure payload hash mismatch")


def artifact_context(plan: AttemptPlan, evidence: dict[str, Any]) -> dict[str, Any]:
    verify_pre_action_exposure(plan, evidence)
    prompt_capture = dict(plan.prompt_bundle.capture)
    return {
        "site_url": plan.site_url,
        "schedule_sha256": plan.schedule_sha256,
        "prompt_capture": prompt_capture,
        "delivery_evidence": dict(evidence),
        "adapter_status": plan.adapter_status,
        "prompt_capture_sha256": hashlib.sha256(
            repr(sorted(prompt_capture.items())).encode("utf-8")
        ).hexdigest(),
    }


def exercise_bridge_lifecycle(plan: AttemptPlan, bridge: BrowserExecutionBridge) -> dict[str, Any]:
    """Exercise context/open/exposure/state/close without invoking an agent."""

    bridge.open_clean_context(plan.clean_context_id)
    try:
        bridge.navigate(plan.site_url)
        evidence = bridge.capture_pre_action_exposure()
        context = artifact_context(plan, evidence)
        context["initial_state"] = bridge.read_state()
        return context
    finally:
        bridge.close_context()
