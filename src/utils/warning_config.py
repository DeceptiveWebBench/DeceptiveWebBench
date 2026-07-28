"""Load canonical warning text from configs/warnings.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from src.utils.io import project_root


@lru_cache
def _warnings_yaml() -> dict[str, Any]:
    path: Path = project_root() / "configs" / "warnings.yaml"
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def warning_rendered_text_for_task(task_id: str) -> str:
    """Multiline string for the task (same text as UI warning semantics)."""
    data = _warnings_yaml()
    rendered = data.get("rendered_text") or {}
    key = (task_id or "").strip().lower()
    text = rendered.get(key)
    if not text:
        raise KeyError(f"No rendered_text for task_id={task_id!r} in warnings.yaml")
    return str(text).strip()


def warning_conditions() -> tuple[str, ...]:
    data = _warnings_yaml()
    conditions = data.get("warning_policy", {}).get("conditions") or []
    normalized = tuple(str(x).strip().lower() for x in conditions if str(x).strip())
    return normalized or ("no_warning", "system_warning", "ui_warning")


def warning_risk_slot_for_task(task_id: str) -> str:
    data = _warnings_yaml()
    slots = data.get("risk_slots") or {}
    key = (task_id or "").strip().lower()
    value = slots.get(key)
    if not value:
        raise KeyError(f"No risk_slots entry for task_id={task_id!r} in warnings.yaml")
    return str(value).strip()
