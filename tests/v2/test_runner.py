from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.v2.matrix import load_schedule
from src.v2.runner import FormalRunGuardError, ProtocolV2Runner
from src.v2.state_machine import fixture_for


class RunnerContractTests(unittest.TestCase):
    def test_one_infrastructure_retry_preserves_both_attempts(self) -> None:
        calls: list[tuple[int, str]] = []

        def executor(cell, attempt_id: int, clean_context_id: str):
            calls.append((attempt_id, clean_context_id))
            if attempt_id == 1:
                return {"run_validity": "browser_transport_failure", "events": []}
            return fixture_for(cell.task_id, 1, 1)

        with tempfile.TemporaryDirectory() as temp:
            runner = ProtocolV2Runner(executor=executor, output_root=Path(temp))
            result = runner.run(load_schedule()[:1])[0]
            self.assertEqual(2, len(result["attempts"]))
            self.assertEqual([1, 2], [attempt["attempt_id"] for attempt in result["attempts"]])
            self.assertNotEqual(calls[0][1], calls[1][1])
            run_dir = Path(temp) / load_schedule()[0].scheduled_run_id
            self.assertTrue((run_dir / "attempt_1" / "raw_state.json").is_file())
            self.assertTrue((run_dir / "attempt_2" / "raw_state.json").is_file())

    def test_valid_agent_failure_is_not_retried(self) -> None:
        calls = 0

        def executor(cell, _attempt_id: int, _clean_context_id: str):
            nonlocal calls
            calls += 1
            return fixture_for(cell.task_id, 0, 1)

        with tempfile.TemporaryDirectory() as temp:
            result = ProtocolV2Runner(executor=executor, output_root=Path(temp)).run(
                load_schedule()[:1]
            )[0]
        self.assertEqual(1, calls)
        self.assertEqual(1, len(result["attempts"]))
        self.assertEqual("safe_non_completion", result["attempts"][0]["outcome_label"])

    def test_no_third_retry(self) -> None:
        calls = 0

        def executor(_cell, _attempt_id: int, _clean_context_id: str):
            nonlocal calls
            calls += 1
            return {"run_validity": "model_service_unavailable", "events": []}

        with tempfile.TemporaryDirectory() as temp:
            result = ProtocolV2Runner(executor=executor, output_root=Path(temp)).run(
                load_schedule()[:1]
            )[0]
        self.assertEqual(2, calls)
        self.assertEqual(2, len(result["attempts"]))

    def test_clean_context_isolation_across_consecutive_cells(self) -> None:
        context_ids: list[str] = []

        def executor(cell, _attempt_id: int, clean_context_id: str):
            context_ids.append(clean_context_id)
            return fixture_for(cell.task_id, 1, 1)

        with tempfile.TemporaryDirectory() as temp:
            ProtocolV2Runner(executor=executor, output_root=Path(temp)).run(load_schedule()[:3])
        self.assertEqual(3, len(set(context_ids)))

    def test_repeated_smoke_invocation_is_append_only(self) -> None:
        cell = load_schedule()[0]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = ProtocolV2Runner(
                executor=lambda current, attempt, context: fixture_for(current.task_id, 1, 1),
                output_root=root,
            ).run([cell])[0]
            first_bytes = (root / cell.scheduled_run_id / "attempt_1" / "raw_state.json").read_bytes()
            second = ProtocolV2Runner(
                executor=lambda current, attempt, context: fixture_for(current.task_id, 1, 1),
                output_root=root,
            ).run([cell])[0]
            self.assertEqual(1, first["attempts"][0]["attempt_id"])
            self.assertEqual(2, second["attempts"][0]["attempt_id"])
            self.assertEqual(
                first_bytes,
                (root / cell.scheduled_run_id / "attempt_1" / "raw_state.json").read_bytes(),
            )
            self.assertTrue((root / cell.scheduled_run_id / "attempt_2" / "raw_state.json").is_file())

    def test_formal_guard_fails_before_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            requested = Path(temp) / "formal"
            with self.assertRaises(FormalRunGuardError):
                ProtocolV2Runner(
                    executor=lambda *_args: {},
                    formal_run=True,
                    explicit_author_confirmation=False,
                    output_root=requested,
                )
            self.assertFalse(requested.exists())


if __name__ == "__main__":
    unittest.main()
