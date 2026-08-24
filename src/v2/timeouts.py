"""Frozen Protocol v2 timeout taxonomy and enforceable attempt wall-clock limit."""

from __future__ import annotations

import signal
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


LIMITER_PRECEDENCE = (
    "wall_clock_timeout",
    "max_steps",
    "agent_step_timeout",
    "llm_request_timeout",
    "page_or_browser_action_timeout",
)
LIMITER_TYPES = frozenset(LIMITER_PRECEDENCE)


class AttemptWallClockTimeout(TimeoutError):
    """Raised by the real process timer when an attempt exceeds its wall limit."""


def highest_precedence_limiter(triggered: set[str]) -> str:
    unknown = set(triggered) - LIMITER_TYPES
    if unknown:
        raise ValueError(f"Unknown limiter types: {sorted(unknown)}")
    for limiter in LIMITER_PRECEDENCE:
        if limiter in triggered:
            return limiter
    raise ValueError("At least one limiter must be triggered")


@contextmanager
def enforce_wall_clock_timeout(seconds: float) -> Iterator[None]:
    """Interrupt synchronous work in the main POSIX thread using a real timer."""

    if seconds <= 0:
        raise ValueError("Wall-clock timeout must be positive")
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("Signal-based wall-clock enforcement requires the main thread")

    def _raise_timeout(_signum, _frame):
        raise AttemptWallClockTimeout(f"Attempt exceeded {seconds} seconds")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _raise_timeout)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)
        signal.signal(signal.SIGALRM, previous_handler)
