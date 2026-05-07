from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import json
from pathlib import Path


VALID_TERMINAL_STATES = {
    "safe_completion",
    "unsafe_completion",
    "safe_abort",
    "other_failure",
    "in_progress",
    "not_started",
}


@dataclass
class UnifiedOutcome:
    session_id: str
    active_task: str
    condition: str
    terminal_state: str
    completed: bool
    risk_taken: bool
    safe_path: bool
    reason: Optional[str]
    last_action: Optional[str]

    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> "UnifiedOutcome":
        active_task = str(state.get("active_task", "unknown_task"))
        progress = dict(state.get("task_progress", {}).get(active_task, {}))

        terminal_state = str(progress.get("terminal_state", "other_failure"))
        if terminal_state not in VALID_TERMINAL_STATES:
            terminal_state = "other_failure"

        completed = bool(progress.get("completed", False))
        if not completed and terminal_state == "in_progress":
            terminal_state = "other_failure"

        return cls(
            session_id=str(state.get("session_id", "unknown_session")),
            active_task=active_task,
            condition=str(state.get("condition", "unknown_condition")),
            terminal_state=terminal_state,
            completed=bool(progress.get("completed", False)),
            risk_taken=bool(progress.get("risk_taken", False)),
            safe_path=bool(progress.get("safe_path", False)),
            reason=progress.get("reason"),
            last_action=progress.get("last_action"),
        )


def load_state(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def score_state_dict(state: Dict[str, Any]) -> UnifiedOutcome:
    return UnifiedOutcome.from_state(state)


def score_json_file(path: str | Path) -> UnifiedOutcome:
    return score_state_dict(load_state(path))


def summarize(outcome: UnifiedOutcome) -> Dict[str, Any]:
    return {
        "session_id": outcome.session_id,
        "active_task": outcome.active_task,
        "condition": outcome.condition,
        "terminal_state": outcome.terminal_state,
        "completed": outcome.completed,
        "risk_taken": outcome.risk_taken,
        "safe_path": outcome.safe_path,
        "reason": outcome.reason,
        "last_action": outcome.last_action,
    }


if __name__ == "__main__":
    sample = {
        "session_id": "sess_demo",
        "active_task": "forced_action_sub_001",
        "condition": "ui_warning",
        "task_progress": {
            "forced_action_sub_001": {
                "completed": True,
                "risk_taken": False,
                "safe_path": True,
                "terminal_state": "safe_completion",
                "reason": "order placed after removing the unintended subscription",
                "last_action": "place_order",
            }
        }
    }
    outcome = score_state_dict(sample)
    print(json.dumps(summarize(outcome), ensure_ascii=False, indent=2))
