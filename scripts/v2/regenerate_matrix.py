"""Regenerate the canonical Protocol v2 schedule from the frozen hash contract."""

from __future__ import annotations

import csv
import hashlib

from src.utils.io import project_root
from src.v2.matrix import AGENT_CONFIG_ID, INTERFACE_DESIGN, SEED_LABEL, raw_key_string
from src.v2.registry import load_registry
from src.v2.safeguards import CONDITIONS


FIELDS = (
    "planned_order",
    "scheduled_run_id",
    "agent_config_id",
    "task_id",
    "task_version",
    "pattern_family",
    "interface_design",
    "safeguard_condition",
    "repeat_id",
    "randomization_seed",
    "randomization_key",
)


def main() -> None:
    rows: list[dict[str, str | int]] = []
    for task in load_registry():
        for condition in CONDITIONS:
            for repeat_id in (1, 2, 3):
                raw = raw_key_string(
                    randomization_seed=SEED_LABEL,
                    agent_config_id=AGENT_CONFIG_ID,
                    task_id=task.task_id,
                    task_version=task.task_version,
                    interface_design=INTERFACE_DESIGN,
                    safeguard_condition=condition,
                    repeat_id=repeat_id,
                )
                rows.append(
                    {
                        "planned_order": 0,
                        "scheduled_run_id": (
                            f"v2__{task.task_id}__{condition}__r{repeat_id}"
                        ),
                        "agent_config_id": AGENT_CONFIG_ID,
                        "task_id": task.task_id,
                        "task_version": task.task_version,
                        "pattern_family": task.pattern_family,
                        "interface_design": INTERFACE_DESIGN,
                        "safeguard_condition": condition,
                        "repeat_id": repeat_id,
                        "randomization_seed": SEED_LABEL,
                        "randomization_key": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                    }
                )
    rows.sort(key=lambda row: str(row["randomization_key"]))
    for planned_order, row in enumerate(rows, start=1):
        row["planned_order"] = planned_order

    destination = project_root() / "docs" / "experiment_matrix_v2.csv"
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
