"""Pre-registered adapter contract for structured scaffold termination signals.

This module does not claim a BrowserUse integration.  It defines the mapping
that a future smoke executor must call after receiving a structured scaffold
action.  Free-text model reasoning is retained only as untrusted diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.v2.state_machine import TaskRunState


ASK_USER_ACTIONS = frozenset({"ask_user", "request_confirmation", "request_user_input"})
ORDINARY_STOP_ACTIONS = frozenset({"done", "stop"})
LIMIT_ACTIONS = frozenset(
    {
        "timeout",
        "step_limit",
        "page_or_browser_action_timeout",
        "llm_request_timeout",
        "agent_step_timeout",
        "wall_clock_timeout",
        "max_steps",
    }
)
GROUNDING_FAILURE_ACTIONS = frozenset({"navigation_failure", "grounding_failure"})


@dataclass(frozen=True)
class TerminationSignal:
    action: str
    reason: str | None = None
    evidence: str | None = None
    reasoning_text: str | None = None


def apply_termination_signal(state: TaskRunState, signal: TerminationSignal) -> None:
    """Apply one structured signal without inferring intent from free text."""

    action = str(signal.action).strip().lower()
    if action == "benchmark_stop_control":
        state.benchmark_stop()
    elif action == "safe_abort":
        state.safe_abort(signal.reason or "")
    elif action in ASK_USER_ACTIONS:
        state.request_human_confirmation(signal.reason or "Agent requested confirmation.")
    elif action in ORDINARY_STOP_ACTIONS:
        state.unclassified_agent_stop(signal.reasoning_text)
    elif action in LIMIT_ACTIONS:
        state.timeout(action)
    elif action in GROUNDING_FAILURE_ACTIONS:
        state.navigation_or_grounding_failure(signal.evidence or "")
    else:
        raise ValueError(f"Unsupported structured termination action: {signal.action!r}")
