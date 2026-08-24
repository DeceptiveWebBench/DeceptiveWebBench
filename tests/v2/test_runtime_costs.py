from __future__ import annotations

import json
import asyncio
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from src.v2.artifacts import ArtifactContractError, validate_attempt_directory
from src.v2.bedrock_qwen import (
    API_INTEGRATION_STATUS,
    bedrock_client_config,
    build_converse_request,
    parse_converse_response,
    structured_actions,
    termination_signal_from_provider_action,
)
from src.v2.costs import (
    assess_smoke_budget,
    calculate_usage_cost,
    load_pricing_config,
    normalize_bedrock_usage,
)
from src.v2.execution_adapter import artifact_context, build_attempt_plan
from src.v2.matrix import load_schedule, schedule_sha256
from src.v2.pre_api_dry_run import _exposure
from src.v2.runner import ProtocolV2Runner, SmokeRunGuardError
from src.v2.runtime_config import load_runtime_config
from src.v2.state_machine import fixture_for
from src.v2.timeouts import (
    AttemptWallClockTimeout,
    enforce_wall_clock_timeout,
    highest_precedence_limiter,
)
from src.v2.execution_limits import ExecutionLimitTimeout, with_limit
from src.v2.smoke_executor import (
    UsageCapturingBearerBedrock,
    _history_action_records,
    _structured_limiter_from_history,
    _page_json_object,
    apply_browseruse_termination,
    build_browseruse_model,
)
from scripts.v2.preflight_api_smoke import credential_presence


def _mock_real_attempt(cell, attempt_id, clean_context_id, *, reported_cost=None):
    plan = build_attempt_plan(
        cell,
        attempt_id=attempt_id,
        clean_context_id=clean_context_id,
        base_url="http://127.0.0.1:8000",
    )
    raw = fixture_for(cell.task_id, 1, 1)
    raw.update(artifact_context(plan, _exposure(cell)))
    raw.update(
        {
            "synthetic_fixture": False,
            "agent_model_call": True,
            "trajectory": list(raw["events"]),
            "actions": [event["event_id"] for event in raw["events"]],
            "screenshots": ["screenshots/step_001.png"],
            "dom_state_evidence": {"sha256": "fixture-only-contract-hash"},
            "model_calls_usage": [
                normalize_bedrock_usage(
                    {"input_tokens": 1_000, "output_tokens": 500},
                    call_id=f"call-{attempt_id}",
                    latency_seconds=2.5,
                )
            ],
            "provider_reported_cost": reported_cost,
        }
    )
    return raw


class ActiveRuntimeConfigTests(unittest.TestCase):
    def test_single_active_config_is_exact_and_legacy_free(self) -> None:
        config = load_runtime_config()
        self.assertEqual(3, config.raw["design"]["repeats"])
        self.assertEqual(108, config.raw["design"]["scheduled_cells"])
        self.assertEqual(schedule_sha256(), config.raw["design"]["matrix_sha256"])
        self.assertEqual("qwen.qwen3-vl-235b-a22b", config.model["documented_model_identifier"])
        self.assertEqual("bedrock_bearer_token", config.model["authentication"])
        self.assertTrue(config.model["access_verified"])
        self.assertEqual("headless", config.execution["smoke_mode"])
        self.assertEqual("headless", config.execution["formal_mode"])
        self.assertEqual(30, config.limits["max_steps"])
        self.assertEqual([45, 120, 180, 900], [
            config.limits["page_or_browser_action_timeout_seconds"],
            config.limits["llm_request_timeout_seconds"],
            config.limits["agent_step_timeout_seconds"],
            config.limits["wall_clock_timeout_seconds"],
        ])

    def test_bedrock_request_omits_provider_default_fields_and_sdk_retries(self) -> None:
        request = build_converse_request(
            messages=[{"role": "user", "content": [{"text": "Inspect the page."}]}],
            system="System instructions",
            tools=[{"toolSpec": {"name": "safe_abort", "description": "Stop safely", "inputSchema": {"json": {"type": "object"}}}}],
        )
        self.assertEqual("qwen.qwen3-vl-235b-a22b", request["model_id"])
        inference = request["body"]["inferenceConfig"]
        self.assertEqual(4096, inference["maxTokens"])
        self.assertNotIn("temperature", inference)
        self.assertNotIn("topP", inference)
        self.assertNotIn("stopSequences", inference)
        self.assertEqual({"any": {}}, request["body"]["toolConfig"]["toolChoice"])
        self.assertTrue(request["access_verified"])
        self.assertEqual(API_INTEGRATION_STATUS, request["integration_status"])
        self.assertEqual(1, bedrock_client_config().retries["total_max_attempts"])

    def test_browseruse_model_has_no_hidden_retry_and_no_provider_default_fields(self) -> None:
        model = build_browseruse_model()
        invoke = model._get_inference_config()
        self.assertEqual({"maxTokens": 4096}, invoke)
        self.assertEqual(1, bedrock_client_config().retries["total_max_attempts"])
        self.assertEqual([], model.protocol_usage_calls)

    def test_credential_preflight_reports_names_only(self) -> None:
        status = credential_presence({"AWS_BEARER_TOKEN_BEDROCK": "x"})
        self.assertEqual({"AWS_BEARER_TOKEN_BEDROCK": True}, status)

    def test_bearer_model_builds_bedrock_runtime_client_without_access_key_fields(self) -> None:
        model = UsageCapturingBearerBedrock(model="qwen.qwen3-vl-235b-a22b", aws_region="us-east-1")
        sentinel = object()
        with patch.dict("os.environ", {"AWS_BEARER_TOKEN_BEDROCK": "test-only-secret"}), patch(
            "src.v2.smoke_executor.boto3.client", return_value=sentinel
        ) as client:
            self.assertIs(sentinel, model._get_client().client)
        kwargs = client.call_args.kwargs
        self.assertEqual("bedrock-runtime", kwargs["service_name"])
        self.assertNotIn("aws_access_key_id", kwargs)
        self.assertNotIn("aws_secret_access_key", kwargs)

    def test_bearer_client_forces_structured_tool_and_captures_usage(self) -> None:
        class FakeClient:
            def __init__(self):
                self.kwargs = None

            def converse(self, **kwargs):
                self.kwargs = kwargs
                return {
                    "output": {"message": {"content": []}},
                    "usage": {"inputTokens": 164, "outputTokens": 29, "totalTokens": 193},
                }

        model = UsageCapturingBearerBedrock(model="qwen.qwen3-vl-235b-a22b", aws_region="us-east-1")
        fake = FakeClient()
        with patch.dict("os.environ", {"AWS_BEARER_TOKEN_BEDROCK": "test-only-secret"}), patch(
            "src.v2.smoke_executor.boto3.client", return_value=fake
        ):
            client = model._get_client()
        client.converse(toolConfig={"tools": [{"toolSpec": {"name": "response"}}]})
        self.assertEqual({"any": {}}, fake.kwargs["toolConfig"]["toolChoice"])
        self.assertEqual(164, model.protocol_usage_calls[0]["input_tokens"])
        self.assertEqual(29, model.protocol_usage_calls[0]["output_tokens"])

    def test_browseruse_page_json_string_is_strictly_normalized(self) -> None:
        self.assertEqual({"route": "first"}, _page_json_object('{"route":"first"}', label="state"))
        with self.assertRaises(RuntimeError):
            _page_json_object([], label="state")

    def test_browseruse_history_envelope_is_normalized_to_action_list(self) -> None:
        class History:
            def model_dump(self, mode):
                self.mode = mode
                return {"history": [{"model_output": {"action": []}}]}

        self.assertEqual(
            [{"model_output": {"action": []}}],
            _history_action_records(History()),
        )

    def test_browseruse_structured_stop_mapping_ignores_prose(self) -> None:
        class History:
            def action_names(self): return ["done"]
            def is_done(self): return True
            def number_of_steps(self): return 2
        state = {"route": "risk", "step": 2, "events": [], "unsafe_boundary_crossed": False}
        apply_browseruse_termination(state, History(), max_steps=30)
        self.assertEqual("unclassified_agent_stop", state["termination_class"])
        self.assertNotIn("reasoning", state["events"][-1])

    def test_browseruse_structured_timeout_error_maps_without_prose_inference(self) -> None:
        class History:
            def action_names(self): return ["click"]
            def is_done(self): return False
            def number_of_steps(self): return 6
            def model_dump(self, mode):
                return {"history": [{"result": [{"error": "LLM call timed out after 120 seconds. Keep your thinking and output short."}]}]}
        history = History()
        self.assertEqual("llm_request_timeout", _structured_limiter_from_history(history))
        state = {"route": "risk", "step": 4, "events": [], "unsafe_boundary_crossed": True}
        apply_browseruse_termination(state, history, max_steps=30)
        self.assertEqual("timeout_or_step_limit", state["termination_class"])
        self.assertEqual("llm_request_timeout", state["events"][-1]["limiter_trigger"])

    def test_browseruse_exact_internal_server_error_maps_to_retryable_invalidity(self) -> None:
        class History:
            def action_names(self): return ["click"]
            def is_done(self): return False
            def number_of_steps(self): return 7
            def model_dump(self, mode):
                return {"history": [{"result": [{"error": "Internal Server Error"}]}]}

        state = {"route": "risk", "step": 4, "events": [], "run_validity": "valid"}
        apply_browseruse_termination(state, History(), max_steps=30)
        self.assertEqual("model_service_unavailable", state["run_validity"])
        self.assertNotIn("termination_class", state)

    def test_browseruse_done_cannot_overwrite_machine_verified_endpoint(self) -> None:
        class History:
            def action_names(self): return ["done"]
            def is_done(self): return True
            def number_of_steps(self): return 7

        endpoint_event = "shoplane_appliance_order_confirmation"
        state = {
            "step": 6,
            "events": [{"step": 6, "event_id": endpoint_event}],
            "nominal_endpoint_reached": True,
            "termination_event": endpoint_event,
            "termination_class": None,
            "termination_reason": None,
        }
        apply_browseruse_termination(state, History(), max_steps=30)
        self.assertTrue(state["nominal_endpoint_reached"])
        self.assertEqual(endpoint_event, state["termination_event"])
        self.assertIsNone(state["termination_class"])
        self.assertEqual(1, len(state["events"]))

    def test_structured_provider_action_mapping_never_uses_prose(self) -> None:
        parsed = parse_converse_response(
            {
                "output": {"message": {"content": [
                    {"text": "I should stop safely."},
                    {"toolUse": {"toolUseId": "tool-1", "name": "safe_abort", "input": {"reason": "No safe route"}}},
                ]}},
                "stopReason": "tool_use",
                "usage": {"inputTokens": 100, "outputTokens": 20},
            },
            call_id="call-1",
            latency_seconds=1.2,
        )
        actions = structured_actions(parsed)
        self.assertEqual(1, len(actions))
        signal = termination_signal_from_provider_action(actions[0])
        self.assertEqual("safe_abort", signal.action)
        self.assertEqual("No safe route", signal.reason)


class CostCalculatorTests(unittest.TestCase):
    def test_hand_checked_standard_token_example(self) -> None:
        call = normalize_bedrock_usage(
            {"input_tokens": 1_000, "output_tokens": 500},
            call_id="one",
            latency_seconds=2.0,
        )
        result = calculate_usage_cost([call])
        self.assertAlmostEqual(0.00186, result["reconstructed_cost"], places=9)
        self.assertEqual("reconstructed", result["cost_status"])
        self.assertIsNone(call["reasoning_tokens"])

    def test_hand_checked_cache_example(self) -> None:
        call = normalize_bedrock_usage(
            {
                "input_tokens": 100,
                "output_tokens": 50,
                "cache_read_input_tokens": 1_000,
                "cache_creation_input_tokens": 2_000,
                "cache_creation": {"ephemeral_5m_input_tokens": 2_000},
            },
            call_id="cache",
            latency_seconds=1.0,
        )
        result = calculate_usage_cost([call])
        self.assertIsNone(result["reconstructed_cost"])
        self.assertEqual("partial", result["cost_status"])

    def test_missing_usage_is_unavailable_and_authoritative_cost_is_preserved(self) -> None:
        missing = normalize_bedrock_usage({}, call_id="missing", latency_seconds=None)
        result = calculate_usage_cost([missing])
        self.assertIsNone(result["reconstructed_cost"])
        self.assertEqual("unavailable", result["cost_status"])
        authoritative = calculate_usage_cost([missing], provider_reported_cost=0.42)
        self.assertEqual(0.42, authoritative["provider_reported_cost"])
        self.assertEqual("authoritative_reconstruction_partial", authoritative["cost_status"])

    def test_pricing_date_and_official_source_are_frozen(self) -> None:
        pricing = load_pricing_config()
        self.assertEqual("2026-08-17", str(pricing["pricing_date"]))
        self.assertTrue(pricing["source"]["url"].startswith("https://aws.amazon.com/"))

    def test_budget_guard_uses_conservative_unknown_and_stops_before_equal_limit(self) -> None:
        known = calculate_usage_cost([], provider_reported_cost=9.0)
        decision = assess_smoke_budget([known], budget_usd=10.0, conservative_next_attempt_cost_usd=1.0)
        self.assertFalse(decision.allowed)
        self.assertEqual("budget_guard_stop", decision.event)
        unknown = calculate_usage_cost([])
        decision = assess_smoke_budget([unknown], budget_usd=10.0, conservative_next_attempt_cost_usd=1.0)
        self.assertTrue(decision.allowed)
        self.assertEqual(2.0, decision.projected_cost_usd)


class TimeoutAndRunnerTelemetryTests(unittest.TestCase):
    def test_timeout_precedence_and_real_wall_clock_interrupt(self) -> None:
        self.assertEqual(
            "wall_clock_timeout",
            highest_precedence_limiter({"llm_request_timeout", "wall_clock_timeout"}),
        )
        started = time.monotonic()
        with self.assertRaises(AttemptWallClockTimeout):
            with enforce_wall_clock_timeout(0.03):
                time.sleep(0.2)
        self.assertLess(time.monotonic() - started, 0.15)

    def test_async_limit_actually_interrupts_and_names_limiter(self) -> None:
        async def slow():
            await asyncio.sleep(0.2)
        with self.assertRaises(ExecutionLimitTimeout) as caught:
            asyncio.run(with_limit(slow(), 0.01, "llm_request_timeout"))
        self.assertEqual("llm_request_timeout", caught.exception.limiter_trigger)

    def test_mock_end_to_end_usage_artifact_and_retry_costs_are_separate(self) -> None:
        cell = load_schedule()[0]
        def executor(current, attempt_id, context_id):
            raw = _mock_real_attempt(current, attempt_id, context_id)
            if attempt_id == 1:
                raw.update({"run_validity": "model_service_unavailable", "events": []})
            return raw

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = ProtocolV2Runner(executor=executor, output_root=root).run([cell])[0]
            self.assertEqual(2, len(result["attempts"]))
            first = root / cell.scheduled_run_id / "attempt_1"
            second = root / cell.scheduled_run_id / "attempt_2"
            validate_attempt_directory(first, cell=cell)
            validate_attempt_directory(second, cell=cell)
            first_usage = json.loads((first / "usage_cost.json").read_text())
            second_usage = json.loads((second / "usage_cost.json").read_text())
            self.assertEqual("call-1", first_usage["model_calls_usage"][0]["call_id"])
            self.assertEqual("call-2", second_usage["model_calls_usage"][0]["call_id"])
            second_metadata = json.loads((second / "run_metadata.json").read_text())
            self.assertEqual("model_service_unavailable", second_metadata["retry"]["reason"])
            self.assertNotEqual(
                json.loads((first / "run_metadata.json").read_text())["clean_context_id"],
                second_metadata["clean_context_id"],
            )

    def test_smoke_requires_explicit_authorization_and_budget_stop_is_not_scored(self) -> None:
        cell = load_schedule()[0]
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(SmokeRunGuardError):
                ProtocolV2Runner(
                    executor=lambda *_: {},
                    smoke_api_run=True,
                    explicit_smoke_authorization=False,
                    output_root=Path(temp),
                )
            runner = ProtocolV2Runner(
                executor=lambda current, attempt, context: _mock_real_attempt(
                    current, attempt, context, reported_cost=9.2
                ),
                smoke_api_run=True,
                explicit_smoke_authorization=True,
                output_root=Path(temp),
            )
            results = runner.run(load_schedule()[:2])
            self.assertEqual(1, len(results[0]["attempts"]))
            self.assertEqual("budget_guard_stop", results[1]["operational_stop"]["event"])
            self.assertIsNone(results[1]["operational_stop"]["behavioral_outcome"])

    def test_secret_field_is_rejected(self) -> None:
        cell = load_schedule()[0]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ProtocolV2Runner(
                executor=lambda current, attempt, context: _mock_real_attempt(current, attempt, context),
                output_root=root,
            ).run([cell])
            attempt_dir = root / cell.scheduled_run_id / "attempt_1"
            metadata_path = attempt_dir / "run_metadata.json"
            metadata = json.loads(metadata_path.read_text())
            metadata["aws_secret_access_key"] = "must-never-be-saved"
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            with self.assertRaises(ArtifactContractError):
                validate_attempt_directory(attempt_dir, cell=cell)


if __name__ == "__main__":
    unittest.main()
