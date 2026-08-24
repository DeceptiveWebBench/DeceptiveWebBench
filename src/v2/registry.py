"""Protocol v2 task registry and structural validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.utils.io import project_root


REQUIRED_TUPLE_FIELDS = ("G", "E", "D", "R", "A_safe", "A_unsafe", "S_T", "H")
REQUIRED_TASK_FIELDS = (
    "task_id",
    "task_version",
    "pattern_family",
    *REQUIRED_TUPLE_FIELDS,
    "risk_action",
    "endpoint_id",
    "unsafe_event_id",
    "state_fields",
    "shell",
    "mechanism",
    "boundary_stage",
    "safe_value",
    "unsafe_value",
    "floor_ceiling_risk",
    "goal_item",
    "merchant",
    "choice_heading",
    "unsafe_label",
    "safe_label",
    "disclosure",
    "review_copy",
    "confirmation_copy",
    "necessity_basis",
    "safe_route_equivalence",
    "incremental_consequence",
)
ALLOWED_FAMILIES = {"forced_action", "sneaking", "interface_interference"}
ALLOWED_CONSEQUENCE_TYPES = {
    "recurring_commitment",
    "optional_charge",
    "additional_data_disclosure",
    "marketing_consent",
    "non_essential_tracking",
    "broader_permission",
}


@dataclass(frozen=True)
class TaskV2:
    task_id: str
    task_version: str
    pattern_family: str
    G: str
    E: str
    D: str
    R: str
    A_safe: str
    A_unsafe: str
    S_T: str
    H: str
    risk_action: str
    endpoint_id: str
    unsafe_event_id: str
    state_fields: dict[str, Any]
    shell: str
    mechanism: str
    boundary_stage: str
    safe_value: str
    unsafe_value: str
    floor_ceiling_risk: str
    goal_item: str
    merchant: str
    choice_heading: str
    unsafe_label: str
    safe_label: str
    disclosure: str
    review_copy: str
    confirmation_copy: str
    necessity_basis: str
    safe_route_equivalence: dict[str, Any]
    incremental_consequence: dict[str, Any]

    @property
    def tuple_fields(self) -> dict[str, str]:
        return {field: getattr(self, field) for field in REQUIRED_TUPLE_FIELDS}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TaskV2":
        missing = [field for field in REQUIRED_TASK_FIELDS if not raw.get(field)]
        if missing:
            raise ValueError(f"Task registry entry is missing fields {missing}: {raw.get('task_id')}")
        values = {
            field: (
                dict(raw[field])
                if field in {"state_fields", "safe_route_equivalence", "incremental_consequence"}
                else str(raw[field]).strip()
            )
            for field in REQUIRED_TASK_FIELDS
        }
        return cls(**values)


def registry_path() -> Path:
    return project_root() / "configs" / "v2" / "task_registry.json"


@lru_cache(maxsize=1)
def load_registry() -> tuple[TaskV2, ...]:
    with registry_path().open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    tasks = tuple(TaskV2.from_dict(item) for item in payload.get("tasks", []))
    validate_registry(tasks)
    return tasks


def validate_registry(tasks: tuple[TaskV2, ...]) -> None:
    if len(tasks) != 12:
        raise ValueError(f"Protocol v2 requires 12 tasks; got {len(tasks)}")
    ids = [task.task_id for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("Protocol v2 task IDs must be unique")
    family_counts = {family: 0 for family in ALLOWED_FAMILIES}
    for task in tasks:
        if task.pattern_family not in ALLOWED_FAMILIES:
            raise ValueError(f"Unknown pattern family for {task.task_id}: {task.pattern_family}")
        family_counts[task.pattern_family] += 1
        if not task.task_version.endswith("-proposed"):
            raise ValueError(f"Unapproved task version must remain proposed: {task.task_id}")
        if "\n" in task.risk_action or "[RISK_ACTION]" in task.risk_action:
            raise ValueError(f"risk_action must be one plain action slot: {task.task_id}")
        if task.A_safe == task.A_unsafe:
            raise ValueError(f"Safe and unsafe routes cannot be identical: {task.task_id}")
        required_state_roles = {"commitment", "commit_step", "endpoint"}
        if not required_state_roles.issubset(task.state_fields):
            raise ValueError(f"Missing task-specific state roles for {task.task_id}")
        if task.shell not in {"commerce", "booking", "permission", "digital_service"}:
            raise ValueError(f"Unknown reusable shell for {task.task_id}: {task.shell}")
        event_field, separator, event_value = task.unsafe_event_id.partition("=")
        if not separator or task.state_fields["commitment"] != event_field:
            raise ValueError(f"Unsafe event/state-field mismatch for {task.task_id}")
        if event_value != task.unsafe_value:
            raise ValueError(f"Unsafe event/value mismatch for {task.task_id}")
        if any(phrase in task.necessity_basis.lower() for phrase in ("author believes", "authors believe", "author considers")):
            raise ValueError(f"Necessity basis cannot rely on author opinion: {task.task_id}")
        equivalence = task.safe_route_equivalence
        required_equivalence = {
            "endpoint_id",
            "same_core_good_or_service",
            "same_base_price",
            "same_core_rights",
            "evidence",
        }
        if not required_equivalence.issubset(equivalence):
            raise ValueError(f"Incomplete safe-route equivalence contract: {task.task_id}")
        if equivalence["endpoint_id"] != task.endpoint_id:
            raise ValueError(f"Safe/unsafe endpoint mismatch: {task.task_id}")
        for field in ("same_core_good_or_service", "same_base_price", "same_core_rights"):
            if not isinstance(equivalence[field], bool):
                raise ValueError(f"Equivalence field {field} must be boolean: {task.task_id}")
        if not str(equivalence["evidence"]).strip():
            raise ValueError(f"Equivalence requires frozen UI/state evidence: {task.task_id}")
        consequence = task.incremental_consequence
        if consequence.get("event_id") != task.unsafe_event_id:
            raise ValueError(f"Incremental consequence must match unsafe event: {task.task_id}")
        consequence_types = consequence.get("types")
        if (
            not isinstance(consequence_types, list)
            or not consequence_types
            or not set(consequence_types).issubset(ALLOWED_CONSEQUENCE_TYPES)
        ):
            raise ValueError(f"Unknown or empty incremental consequence type: {task.task_id}")
        if not str(consequence.get("description") or "").strip():
            raise ValueError(f"Incremental consequence requires a description: {task.task_id}")
    if set(family_counts.values()) != {4}:
        raise ValueError(f"Protocol v2 requires four tasks per family: {family_counts}")


def load_task(task_id: str) -> TaskV2:
    normalized = str(task_id).strip().lower()
    for task in load_registry():
        if task.task_id == normalized:
            return task
    raise KeyError(f"Unknown Protocol v2 task_id: {task_id!r}")
