"""Executable timeout helpers for the frozen Protocol v2 limit hierarchy."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import TypeVar


T = TypeVar("T")


class ExecutionLimitTimeout(TimeoutError):
    def __init__(self, limiter_trigger: str):
        super().__init__(limiter_trigger)
        self.limiter_trigger = limiter_trigger


async def with_limit(awaitable: Awaitable[T], seconds: float, limiter_trigger: str) -> T:
    """Apply a real async deadline and preserve the exact limiter in evidence."""

    try:
        return await asyncio.wait_for(awaitable, timeout=seconds)
    except TimeoutError as exc:
        raise ExecutionLimitTimeout(limiter_trigger) from exc

