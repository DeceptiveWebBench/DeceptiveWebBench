"""Protocol v2 attempt-artifact schema and integrity checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.v2.costs import USAGE_COST_SCHEMA_VERSION
from src.v2.matrix import ScheduledCell, schedule_sha256
from src.v2.scorer import score_attempt


ARTIFACT_SCHEMA_VERSION = "protocol-v2-attempt-artifact-2.0"
REQUIRED_METADATA_FIELDS = {
    "artifact_schema_version",
    "run_id",
    "scheduled_run_id",
    "attempt_id",
    "task_id",
    "task_version",
    "safeguard_condition",
    "repeat_id",
    "formal_run",
    "synthetic_fixture",
    "agent_model_call",
    "clean_context_id",
    "schedule_sha256",
    "site_url",
    "prompt_capture",
    "delivery_evidence",
    "adapter_status",
    "configuration",
    "sampling",
    "execution_limits",
    "retry",
    "timing",
    "usage_cost_summary",
    "collection_scope",
    "collection_id",
    "safeguard_version",
    "safeguard_config_sha256",
    "screenshot_manifest",
}

FORBIDDEN_SECRET_KEYS = {
    "api_key",
    "aws_access_key_id",
    "aws_secret_access_key",
    "aws_session_token",
    "authorization",
    "billing_identifier",
    "account_id",
    "secret_access_key",
}
SECRET_VALUE_MARKERS = ("-----BEGIN PRIVATE KEY-----", "-----BEGIN RSA PRIVATE KEY-----")


class ArtifactContractError(ValueError):
    """Raised when saved evidence cannot satisfy the v2 artifact contract."""


def assert_no_secret_material(value: Any, path: str = "artifact") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).strip().lower() in FORBIDDEN_SECRET_KEYS:
                raise ArtifactContractError(f"Forbidden credential/billing field in {path}: {key}")
            assert_no_secret_material(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_secret_material(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if value.startswith("AKIA") and len(value) == 20:
            raise ArtifactContractError(f"Possible AWS access-key value in {path}")
        if any(marker in value for marker in SECRET_VALUE_MARKERS):
            raise ArtifactContractError(f"Private-key material in {path}")


def validate_usage_cost_record(record: dict[str, Any], *, metadata: dict[str, Any]) -> None:
    if record.get("usage_cost_schema_version") != USAGE_COST_SCHEMA_VERSION:
        raise ArtifactContractError("Unknown usage/cost schema version")
    calls = record.get("model_calls_usage")
    totals = record.get("trajectory_totals")
    if not isinstance(calls, list) or not isinstance(totals, dict):
        raise ArtifactContractError("Usage record requires call list and trajectory totals")
    if totals.get("model_calls") != len(calls):
        raise ArtifactContractError("model_calls does not match per-call usage records")
    if metadata["agent_model_call"] and len(calls) < 1:
        raise ArtifactContractError("A real agent-model attempt requires at least one call record")
    if metadata["synthetic_fixture"] and calls:
        raise ArtifactContractError("Synthetic fixtures cannot contain provider model calls")
    for call in calls:
        if not isinstance(call, dict) or not str(call.get("call_id") or "").strip():
            raise ArtifactContractError("Every model call requires a call_id")
        if call.get("reasoning_tokens") is not None:
            raise ArtifactContractError("Hidden reasoning tokens must not be inferred")
    if record.get("cost_currency") != "USD" or record.get("pricing_unit") != "per_1m_tokens":
        raise ArtifactContractError("Cost units must be frozen as USD per 1M tokens")
    if record.get("cost_status") not in {
        "authoritative",
        "authoritative_reconstruction_partial",
        "reconstructed",
        "partial",
        "unavailable",
        "synthetic_no_model_call",
    }:
        raise ArtifactContractError("Unknown cost_status")


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_attempt_bundle(
    *,
    metadata: dict[str, Any],
    raw_state: dict[str, Any],
    scored_outcome: dict[str, Any],
    usage_cost: dict[str, Any],
    cell: ScheduledCell | None = None,
) -> None:
    missing = sorted(REQUIRED_METADATA_FIELDS - set(metadata))
    if missing:
        raise ArtifactContractError(f"Attempt metadata is missing fields: {missing}")
    if metadata["artifact_schema_version"] != ARTIFACT_SCHEMA_VERSION:
        raise ArtifactContractError("Unknown artifact schema version")
    for flag in ("formal_run", "synthetic_fixture", "agent_model_call"):
        if not isinstance(metadata[flag], bool):
            raise ArtifactContractError(f"{flag} must be boolean")
        if raw_state.get(flag) is not metadata[flag]:
            raise ArtifactContractError(f"Metadata/raw mismatch for {flag}")
    if not str(metadata["clean_context_id"]).strip():
        raise ArtifactContractError("clean_context_id is required")
    if metadata["schedule_sha256"] != schedule_sha256():
        raise ArtifactContractError("Attempt was not produced from the canonical matrix hash")

    if metadata["formal_run"]:
        if metadata["synthetic_fixture"] or not metadata["agent_model_call"]:
            raise ArtifactContractError("Formal artifacts cannot be synthetic or model-free")
    elif metadata["synthetic_fixture"] and metadata["agent_model_call"]:
        raise ArtifactContractError("Synthetic fixtures cannot claim a model call")
    if metadata["collection_scope"] == "calibration_pilot":
        if metadata["formal_run"] or metadata["synthetic_fixture"]:
            raise ArtifactContractError("Calibration pilot must be real, nonformal evidence")
        if not str(metadata.get("collection_id") or "").strip():
            raise ArtifactContractError("Calibration pilot requires collection_id")
        if metadata.get("safeguard_version") != "protocol-v2-generic-safeguard-v0.1":
            raise ArtifactContractError("Calibration pilot safeguard version mismatch")

    assert_no_secret_material(metadata, "metadata")
    assert_no_secret_material(raw_state, "raw_state")
    assert_no_secret_material(usage_cost, "usage_cost")
    validate_usage_cost_record(usage_cost, metadata=metadata)
    if metadata["usage_cost_summary"] != usage_cost["trajectory_totals"]:
        raise ArtifactContractError("Metadata usage summary does not match usage/cost artifact")
    if raw_state.get("usage_cost") != usage_cost:
        raise ArtifactContractError("Raw state usage/cost evidence does not match saved artifact")
    configuration = metadata.get("configuration") or {}
    if configuration.get("model_provider") != "aws_bedrock":
        raise ArtifactContractError("Artifact provider must match active v2 configuration")
    if configuration.get("model_id") != "qwen.qwen3-vl-235b-a22b":
        raise ArtifactContractError("Artifact model ID must match the frozen candidate")
    if metadata.get("sampling", {}).get("top_p") != "provider_default_omitted":
        raise ArtifactContractError("top_p must remain omitted/provider default")

    if raw_state.get("run_validity") == "valid":
        for field, expected_type in (
            ("trajectory", list),
            ("actions", list),
            ("screenshots", list),
            ("dom_state_evidence", dict),
        ):
            if not isinstance(raw_state.get(field), expected_type):
                raise ArtifactContractError(f"Valid attempt requires {field} evidence")
        if metadata["formal_run"] and not raw_state["screenshots"]:
            raise ArtifactContractError("Formal valid attempts require screenshot evidence")
        if metadata["collection_scope"] == "calibration_pilot" and not raw_state["screenshots"]:
            raise ArtifactContractError("Calibration pilot valid attempts require screenshots")
        if not isinstance(metadata.get("prompt_capture"), dict):
            raise ArtifactContractError("Valid attempt requires prompt capture")
        if not isinstance(metadata.get("delivery_evidence"), dict):
            raise ArtifactContractError("Valid attempt requires delivery evidence")
        if not str(metadata.get("site_url") or "").strip():
            raise ArtifactContractError("Valid attempt requires site_url")
        if not str(metadata.get("adapter_status") or "").strip():
            raise ArtifactContractError("Valid attempt requires adapter status")
    screenshot_manifest = metadata.get("screenshot_manifest")
    if not isinstance(screenshot_manifest, list):
        raise ArtifactContractError("screenshot_manifest must be a list")
    if metadata["collection_scope"] in {"calibration_pilot", "formal"} and (
        [item.get("path") for item in screenshot_manifest] != raw_state.get("screenshots", [])
    ):
        raise ArtifactContractError("Screenshot manifest/raw references differ")

    if cell is not None:
        expected = {
            "scheduled_run_id": cell.scheduled_run_id,
            "task_id": cell.task_id,
            "task_version": cell.task_version,
            "safeguard_condition": cell.safeguard_condition,
            "repeat_id": cell.repeat_id,
        }
        for field, value in expected.items():
            if metadata.get(field) != value:
                raise ArtifactContractError(f"Artifact/cell mismatch for {field}")

    rescored = score_attempt(raw_state).to_dict()
    for field in (
        "scheduled_run_id",
        "attempt_id",
        "run_validity",
        "C_r",
        "S_r",
        "outcome_label",
        "termination_class",
        "termination_reason",
    ):
        if rescored.get(field) != scored_outcome.get(field):
            raise ArtifactContractError(f"Saved scorer output cannot be recomputed: {field}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactContractError(f"Unreadable JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise ArtifactContractError(f"Artifact must be a JSON object: {path}")
    return value


def validate_attempt_directory(path: Path, *, cell: ScheduledCell | None = None) -> None:
    required = (
        "run_metadata.json",
        "raw_state.json",
        "scored_outcome.json",
        "usage_cost.json",
    )
    missing = [name for name in required if not (path / name).is_file()]
    if missing:
        raise ArtifactContractError(f"Attempt directory is incomplete: {missing}")
    metadata = read_json(path / "run_metadata.json")
    raw_state = read_json(path / "raw_state.json")
    validate_attempt_bundle(
        metadata=metadata,
        raw_state=raw_state,
        scored_outcome=read_json(path / "scored_outcome.json"),
        usage_cost=read_json(path / "usage_cost.json"),
        cell=cell,
    )
    for item in metadata.get("screenshot_manifest") or []:
        relative = item.get("path")
        if not isinstance(relative, str) or relative.startswith("/") or ".." in Path(relative).parts:
            raise ArtifactContractError("Unsafe screenshot artifact path")
        target = path / relative
        if not target.is_file():
            raise ArtifactContractError(f"Missing persisted screenshot: {relative}")
        payload = target.read_bytes()
        if hashlib.sha256(payload).hexdigest() != item.get("sha256"):
            raise ArtifactContractError(f"Screenshot hash mismatch: {relative}")
