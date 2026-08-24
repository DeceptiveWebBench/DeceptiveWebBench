"""Static Qwen-on-Bedrock Converse request/response contract; never invokes AWS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from botocore.config import Config

from src.v2.costs import normalize_bedrock_usage
from src.v2.runtime_config import RuntimeConfig, load_runtime_config
from src.v2.termination_adapter import TerminationSignal


PROVIDER_ADAPTER_VERSION = "protocol-v2-bedrock-qwen-converse-adapter-1.1"
API_INTEGRATION_STATUS = "VERIFIED_BY_NONFORMAL_QWEN_API_SMOKE_2026-08-17"


class ProviderAdapterError(ValueError):
    """Raised when a request or response violates the frozen provider contract."""


def bedrock_client_config(config: RuntimeConfig | None = None) -> Config:
    """Return a client config with one SDK request and no hidden retries."""

    active = config or load_runtime_config()
    return Config(
        connect_timeout=active.limits["page_or_browser_action_timeout_seconds"],
        read_timeout=active.limits["llm_request_timeout_seconds"],
        retries={"mode": "standard", "total_max_attempts": 1},
        user_agent_extra="trustworthy-completion-protocol-v2",
    )


def build_converse_request(
    *,
    messages: list[dict[str, Any]],
    system: str,
    tools: list[dict[str, Any]],
    config: RuntimeConfig | None = None,
) -> dict[str, Any]:
    """Build the auditable Converse request without credentials or network access."""

    active = config or load_runtime_config()
    if not isinstance(messages, list) or not messages:
        raise ProviderAdapterError("At least one message is required")
    if not isinstance(tools, list):
        raise ProviderAdapterError("tools must be a list")
    body: dict[str, Any] = {
        "modelId": active.model["documented_model_identifier"],
        "messages": messages,
        "system": [{"text": system}],
        "inferenceConfig": {"maxTokens": active.sampling["max_output_tokens"]},
    }
    if tools:
        # BrowserUse requires one structured action on every turn. Qwen's
        # default is `auto`, which may return prose even when tools are present.
        body["toolConfig"] = {"tools": tools, "toolChoice": {"any": {}}}
    inference = body["inferenceConfig"]
    if any(field in inference for field in ("temperature", "topP", "stopSequences")):
        raise ProviderAdapterError("Provider-default sampling fields must remain omitted")
    return {
        "service": active.model["endpoint_service"],
        "region": active.model["endpoint_region"],
        "model_id": active.model["documented_model_identifier"],
        "operation": "Converse",
        "body": body,
        "provider_adapter_version": PROVIDER_ADAPTER_VERSION,
        "authentication": active.model["authentication"],
        "credential_environment_variable": active.model["credential_environment_variable"],
        "access_verified": active.model["access_verified"],
        "integration_status": API_INTEGRATION_STATUS,
    }


def parse_converse_response(
    response: dict[str, Any],
    *,
    call_id: str,
    latency_seconds: float | None,
) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise ProviderAdapterError("Bedrock Converse response must be an object")
    message = (response.get("output") or {}).get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), list):
        raise ProviderAdapterError("Converse response must contain output.message.content")
    return {
        "response_id": (response.get("ResponseMetadata") or {}).get("RequestId"),
        "model": response.get("modelId"),
        "stop_reason": response.get("stopReason"),
        "content": message["content"],
        "usage": normalize_bedrock_usage(
            response.get("usage"), call_id=call_id, latency_seconds=latency_seconds
        ),
        "provider_reported_cost": None,
    }


@dataclass(frozen=True)
class StructuredProviderAction:
    kind: str
    name: str
    tool_use_id: str | None
    arguments: dict[str, Any]


def structured_actions(parsed_response: dict[str, Any]) -> list[StructuredProviderAction]:
    actions: list[StructuredProviderAction] = []
    for block in parsed_response.get("content") or []:
        if not isinstance(block, dict) or not isinstance(block.get("toolUse"), dict):
            continue
        tool_use = block["toolUse"]
        arguments = tool_use.get("input") or {}
        if not isinstance(arguments, dict):
            raise ProviderAdapterError("toolUse input must be an object")
        actions.append(
            StructuredProviderAction(
                kind="tool_use",
                name=str(tool_use.get("name") or ""),
                tool_use_id=tool_use.get("toolUseId"),
                arguments=arguments,
            )
        )
    return actions


def termination_signal_from_provider_action(action: StructuredProviderAction) -> TerminationSignal | None:
    """Map only explicit tool names; never infer intent from response prose."""

    name = action.name.strip().lower()
    if name in {"safe_abort", "ask_user", "request_confirmation", "done", "stop"}:
        return TerminationSignal(
            action=name,
            reason=action.arguments.get("reason"),
            evidence=action.arguments.get("evidence"),
        )
    return None
