"""Contract checks for task and warning source-of-truth configs."""

from __future__ import annotations

from dataclasses import dataclass

from src.utils.task_config import list_task_ids, load_task_spec
from src.utils.warning_config import warning_conditions, warning_rendered_text_for_task, warning_risk_slot_for_task


@dataclass(frozen=True)
class ContractIssue:
    task_id: str
    message: str


def collect_contract_issues() -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    expected_conditions = set(warning_conditions())

    for task_id in list_task_ids():
        task = load_task_spec(task_id)

        if not set(task.conditions).issubset(expected_conditions):
            issues.append(
                ContractIssue(
                    task_id=task_id,
                    message=f"task conditions {task.conditions!r} not subset of warnings conditions {tuple(sorted(expected_conditions))!r}",
                )
            )

        try:
            warning_slot = warning_risk_slot_for_task(task_id)
            if warning_slot != task.risk_slot:
                issues.append(
                    ContractIssue(
                        task_id=task_id,
                        message=f"risk_slot mismatch: task={task.risk_slot!r} warnings={warning_slot!r}",
                    )
                )
        except KeyError as exc:
            issues.append(ContractIssue(task_id=task_id, message=str(exc)))

        try:
            warning_rendered_text_for_task(task_id)
        except KeyError as exc:
            issues.append(ContractIssue(task_id=task_id, message=str(exc)))

    return issues

