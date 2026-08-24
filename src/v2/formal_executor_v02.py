"""Formal v0.2 BrowserUse executor assembled without altering frozen v0.1 code."""

from __future__ import annotations

import asyncio
from threading import Lock

import src.v2.smoke_executor as _base
from src.v2.execution_adapter_v02 import artifact_context, build_attempt_plan


FORMAL_V02_ADAPTER_STATUS = (
    "QWEN_BEDROCK_CONVERSE_FORMAL_V02_REPEAT1; provider event shapes previously "
    "verified by non-formal API smoke; v0.2 delivery is verified before action 1"
)
_SERIAL_PATCH_LOCK = Lock()


def make_formal_executor(*, base_url: str):
    """Reuse the frozen provider bridge while replacing only versioned plan functions.

    The scoped patch is safe because the formal protocol mandates concurrency=1.
    """

    def executor(cell, attempt_id: int, clean_context_id: str):
        with _SERIAL_PATCH_LOCK:
            old_plan = _base.build_attempt_plan
            old_context = _base.artifact_context
            try:
                _base.build_attempt_plan = build_attempt_plan
                _base.artifact_context = artifact_context
                raw = asyncio.run(
                    _base._execute(
                        cell,
                        attempt_id,
                        clean_context_id,
                        base_url=base_url,
                    )
                )
                raw["adapter_status"] = FORMAL_V02_ADAPTER_STATUS
                return raw
            finally:
                _base.build_attempt_plan = old_plan
                _base.artifact_context = old_context

    return executor
