"""Single source of truth for the active Protocol v2 runtime configuration."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.utils.io import project_root
from src.v2.matrix import schedule_sha256


RUNTIME_CONFIG_VERSION = "protocol-v2-active-runtime-1.1"


class RuntimeConfigError(ValueError):
    """Raised when the active runtime file is missing, stale, or ambiguous."""


@dataclass(frozen=True)
class RuntimeConfig:
    raw: dict[str, Any]
    path: Path
    sha256: str

    @property
    def model(self) -> dict[str, Any]:
        return self.raw["model"]

    @property
    def sampling(self) -> dict[str, Any]:
        return self.raw["sampling"]

    @property
    def execution(self) -> dict[str, Any]:
        return self.raw["execution"]

    @property
    def limits(self) -> dict[str, int]:
        return self.raw["limits"]

    @property
    def retry(self) -> dict[str, Any]:
        return self.raw["retry"]

    @property
    def smoke_budget(self) -> dict[str, Any]:
        return self.raw["smoke_budget"]

    @property
    def formal(self) -> dict[str, Any]:
        return self.raw["formal"]


def runtime_config_path() -> Path:
    return project_root() / "configs/v2/runtime.yaml"


def _require(mapping: dict[str, Any], path: str, expected: Any) -> None:
    current: Any = mapping
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise RuntimeConfigError(f"Missing active runtime field: {path}")
        current = current[part]
    if current != expected:
        raise RuntimeConfigError(f"Frozen runtime mismatch for {path}: {current!r} != {expected!r}")


def validate_runtime_config(raw: dict[str, Any]) -> None:
    frozen = {
        "runtime_config_version": RUNTIME_CONFIG_VERSION,
        "active_protocol": "v2",
        "design.tasks": 12,
        "design.repeats": 3,
        "design.scheduled_cells": 108,
        "design.matrix_sha256": schedule_sha256(),
        "model.provider": "aws_bedrock",
        "model.intended_model_family": "qwen3_vl_235b_a22b",
        "model.documented_model_identifier": "qwen.qwen3-vl-235b-a22b",
        "model.endpoint_region": "us-east-1",
        "model.endpoint_service": "bedrock-runtime",
        "model.request_path": "bedrock_converse",
        "model.request_schema": "bedrock_converse",
        "scaffold.name": "browser_use",
        "scaffold.version": "0.12.6",
        "model.authentication": "bedrock_bearer_token",
        "model.credential_environment_variable": "AWS_BEARER_TOKEN_BEDROCK",
        "sampling.temperature": "provider_default_omitted",
        "sampling.top_p": "provider_default_omitted",
        "sampling.max_output_tokens": 4096,
        "sampling.thinking_mode": "not_requested",
        "sampling.effort": None,
        "sampling.seed": None,
        "sampling.seed_support": "unsupported_by_selected_endpoint",
        "sampling.stop_sequences": [],
        "execution.concurrency": 1,
        "execution.smoke_mode": "headless",
        "execution.formal_mode": "headless",
        "execution.viewport.width": 1280,
        "execution.viewport.height": 720,
        "execution.viewport.device_scale_factor": 1,
        "execution.locale": "en-US",
        "execution.clean_browser_context_per_attempt": True,
        "execution.reuse_cookies_or_storage": False,
        "limits.max_steps": 30,
        "limits.page_or_browser_action_timeout_seconds": 45,
        "limits.llm_request_timeout_seconds": 120,
        "limits.agent_step_timeout_seconds": 180,
        "limits.wall_clock_timeout_seconds": 900,
        "retry.provider_sdk_total_attempts": 1,
        "retry.agent_consecutive_llm_failure_limit": 1,
        "retry.final_response_after_failure": False,
        "retry.protocol_infrastructure_retry_limit": 1,
        "retry.maximum_attempts_per_cell": 2,
        "retry.retry_requires_new_browser_context": True,
        "smoke_budget.maximum_usd": 10.0,
        "formal.authorization": False,
        "formal.budget_usd": None,
    }
    for path, expected in frozen.items():
        _require(raw, path, expected)
    if raw["design"].get("conditions") != ["no_warning", "system_warning", "ui_warning"]:
        raise RuntimeConfigError("Conditions must preserve the frozen three-condition order")
    if raw["limits"]["page_or_browser_action_timeout_seconds"] >= raw["limits"]["llm_request_timeout_seconds"]:
        raise RuntimeConfigError("Browser-action timeout must be shorter than LLM request timeout")
    if raw["limits"]["llm_request_timeout_seconds"] >= raw["limits"]["agent_step_timeout_seconds"]:
        raise RuntimeConfigError("LLM request timeout must be shorter than full agent-step timeout")
    if raw["limits"]["agent_step_timeout_seconds"] >= raw["limits"]["wall_clock_timeout_seconds"]:
        raise RuntimeConfigError("Agent-step timeout must be shorter than attempt wall-clock timeout")
    serialized = yaml.safe_dump(raw).lower()
    for stale in ("nova lite", "nova_lite", "max_steps: 15", "wall_clock_timeout_seconds: 1800"):
        if stale in serialized:
            raise RuntimeConfigError(f"Legacy v1 runtime value leaked into active v2 config: {stale}")


def load_runtime_config(path: Path | None = None) -> RuntimeConfig:
    selected = path or runtime_config_path()
    payload = selected.read_bytes()
    raw = yaml.safe_load(payload) or {}
    if not isinstance(raw, dict):
        raise RuntimeConfigError("Active runtime config must be a YAML object")
    validate_runtime_config(raw)
    return RuntimeConfig(raw=raw, path=selected, sha256=hashlib.sha256(payload).hexdigest())
