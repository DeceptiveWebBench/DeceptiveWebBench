"""Load and validate the canonical 108-cell Protocol v2 schedule."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from src.utils.io import project_root
from src.v2.registry import load_registry
from src.v2.safeguards import CONDITIONS


SEED_LABEL = "tc-v2-order-20260807-deceptive-only"
AGENT_CONFIG_ID = "consumer_web_agent_frozen_v2"
INTERFACE_DESIGN = "deceptive"


@dataclass(frozen=True)
class ScheduledCell:
    planned_order: int
    scheduled_run_id: str
    agent_config_id: str
    task_id: str
    task_version: str
    pattern_family: str
    interface_design: str
    safeguard_condition: str
    repeat_id: int
    randomization_seed: str
    randomization_key: str

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "ScheduledCell":
        return cls(
            planned_order=int(row["planned_order"]),
            scheduled_run_id=row["scheduled_run_id"],
            agent_config_id=row["agent_config_id"],
            task_id=row["task_id"],
            task_version=row["task_version"],
            pattern_family=row["pattern_family"],
            interface_design=row["interface_design"],
            safeguard_condition=row["safeguard_condition"],
            repeat_id=int(row["repeat_id"]),
            randomization_seed=row["randomization_seed"],
            randomization_key=row["randomization_key"],
        )

    @property
    def expected_run_id(self) -> str:
        return f"v2__{self.task_id}__{self.safeguard_condition}__r{self.repeat_id}"

    @property
    def raw_key_string(self) -> str:
        return raw_key_string(
            randomization_seed=self.randomization_seed,
            agent_config_id=self.agent_config_id,
            task_id=self.task_id,
            task_version=self.task_version,
            interface_design=self.interface_design,
            safeguard_condition=self.safeguard_condition,
            repeat_id=self.repeat_id,
        )

    @property
    def expected_randomization_key(self) -> str:
        return hashlib.sha256(self.raw_key_string.encode("utf-8")).hexdigest()


def raw_key_string(
    *,
    randomization_seed: str,
    agent_config_id: str,
    task_id: str,
    task_version: str,
    interface_design: str,
    safeguard_condition: str,
    repeat_id: int,
) -> str:
    """Serialize one schedule cell using the frozen Goal 2B.1 byte contract."""

    return "|".join(
        (
            randomization_seed,
            agent_config_id,
            task_id,
            task_version,
            interface_design,
            safeguard_condition,
            str(int(repeat_id)),
        )
    )


def schedule_path() -> Path:
    return project_root() / "docs" / "experiment_matrix_v2.csv"


def schedule_sha256() -> str:
    return hashlib.sha256(schedule_path().read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def load_schedule() -> tuple[ScheduledCell, ...]:
    with schedule_path().open("r", encoding="utf-8", newline="") as handle:
        cells = tuple(ScheduledCell.from_row(row) for row in csv.DictReader(handle))
    validate_schedule(cells)
    return cells


def validate_schedule(cells: tuple[ScheduledCell, ...]) -> None:
    if len(cells) != 108:
        raise ValueError(f"Canonical schedule must contain exactly 108 rows; got {len(cells)}")
    if [cell.planned_order for cell in cells] != list(range(1, 109)):
        raise ValueError("planned_order must be contiguous 1..108")
    if len({cell.scheduled_run_id for cell in cells}) != 108:
        raise ValueError("scheduled_run_id values must be unique")
    if len({cell.randomization_key for cell in cells}) != 108:
        raise ValueError("randomization_key values must be unique")
    if [cell.randomization_key for cell in cells] != sorted(cell.randomization_key for cell in cells):
        raise ValueError("planned order must be the ascending SHA-256 randomization-key order")

    tasks = {task.task_id: task for task in load_registry()}
    counts = Counter((cell.task_id, cell.safeguard_condition, cell.repeat_id) for cell in cells)
    expected = {
        (task_id, condition, repeat)
        for task_id in tasks
        for condition in CONDITIONS
        for repeat in (1, 2, 3)
    }
    if set(counts) != expected or any(count != 1 for count in counts.values()):
        raise ValueError("Schedule must contain each task × condition × repeat cell exactly once")

    for cell in cells:
        task = tasks.get(cell.task_id)
        if task is None:
            raise ValueError(f"Schedule references unknown task: {cell.task_id}")
        if cell.expected_run_id != cell.scheduled_run_id:
            raise ValueError(f"Malformed scheduled_run_id: {cell.scheduled_run_id}")
        if cell.task_version != task.task_version or cell.pattern_family != task.pattern_family:
            raise ValueError(f"Schedule metadata differs from registry for {cell.task_id}")
        if cell.agent_config_id != AGENT_CONFIG_ID:
            raise ValueError(f"Unexpected agent_config_id: {cell.agent_config_id}")
        if cell.interface_design != INTERFACE_DESIGN:
            raise ValueError(f"Unexpected interface_design: {cell.interface_design}")
        if cell.randomization_seed != SEED_LABEL:
            raise ValueError(f"Unexpected randomization seed: {cell.randomization_seed}")
        if len(cell.randomization_key) != 64:
            raise ValueError(f"Malformed SHA-256 key: {cell.randomization_key}")
        int(cell.randomization_key, 16)
        if cell.randomization_key != cell.expected_randomization_key:
            raise ValueError(f"Randomization key does not recompute for {cell.scheduled_run_id}")


def randomization_recomputation_status() -> dict[str, str]:
    return {
        "status": "verified",
        "contract": (
            "randomization_seed|agent_config_id|task_id|task_version|"
            "interface_design|safeguard_condition|repeat_id"
        ),
        "seed_label": SEED_LABEL,
    }
