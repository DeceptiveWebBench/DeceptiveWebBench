"""Load per-task metadata from env/tasks/<task_id>/task.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from src.utils.io import project_root


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    pattern_family: str
    start_page: str
    user_goal: str
    risk_slot: str
    conditions: tuple[str, ...]


@lru_cache
def _task_yaml(task_id: str) -> dict[str, Any] | None:
    path = project_root() / "env" / "tasks" / task_id / "task.yaml"
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _normalize(task_id: str) -> str:
    return (task_id or "").strip().lower()


def _task_value(data: dict[str, Any], key: str, fallback: str) -> str:
    value = data.get(key)
    if value is None:
        return fallback
    return " ".join(str(value).split())


def load_task_spec(task_id: str) -> TaskSpec:
    tid = _normalize(task_id)
    data = _task_yaml(tid)
    if not data:
        return TaskSpec(
            task_id=tid,
            pattern_family="unknown_pattern_family",
            start_page="product",
            user_goal=f"Complete the benchmark task {tid}.",
            risk_slot="an unsafe action",
            conditions=("no_warning", "system_warning", "ui_warning"),
        )
    conditions = tuple(str(x).strip().lower() for x in (data.get("condition_support") or []))
    if not conditions:
        conditions = ("no_warning", "system_warning", "ui_warning")
    return TaskSpec(
        task_id=tid,
        pattern_family=_task_value(data, "pattern_family", "unknown_pattern_family"),
        start_page=_task_value(data, "start_page", "env/site/product.html"),
        user_goal=_task_value(data, "user_goal", f"Complete the benchmark task {tid}."),
        risk_slot=_task_value(data, "risk_slot", "an unsafe action"),
        conditions=conditions,
    )


def list_task_ids() -> list[str]:
    root = project_root() / "env" / "tasks"
    if not root.is_dir():
        return []
    task_ids: list[str] = []
    for task_yaml in sorted(root.glob("*/task.yaml")):
        task_ids.append(task_yaml.parent.name.strip().lower())
    return task_ids


def user_goal_for_task(task_id: str) -> str:
    return load_task_spec(task_id).user_goal
