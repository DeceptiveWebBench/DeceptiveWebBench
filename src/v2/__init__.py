"""Isolated Protocol v2 implementation.

Nothing in this package reads or mutates the historical task registry or pilot
results. Formal execution remains guarded by the author-approved freeze manifest.
"""

from src.v2.registry import TaskV2, load_registry, load_task
from src.v2.scorer import ScoredOutcome, score_attempt
from src.v2.termination_adapter import TerminationSignal, apply_termination_signal

__all__ = [
    "ScoredOutcome",
    "TaskV2",
    "TerminationSignal",
    "apply_termination_signal",
    "load_registry",
    "load_task",
    "score_attempt",
]
