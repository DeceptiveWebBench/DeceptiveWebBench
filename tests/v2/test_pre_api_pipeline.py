from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analysis.v2_pipeline import (
    FormalAnalysisEligibilityError,
    assert_formal_analysis_eligible,
    validate_pre_api_dry_run_only,
)
from analysis.v2_precision import precision_report
from src.v2.artifacts import ArtifactContractError, read_json, validate_attempt_directory
from src.v2.execution_adapter import (
    ADAPTER_STATUS,
    AdapterContractError,
    build_attempt_plan,
    exercise_bridge_lifecycle,
    verify_pre_action_exposure,
)
from src.v2.matrix import load_schedule
from src.v2.pre_api_dry_run import _exposure, run_pre_api_dry_run


class _MockBridge:
    def __init__(self, evidence):
        self.evidence = evidence
        self.opened = False
        self.closed = False
        self.url = None

    def open_clean_context(self, _clean_context_id): self.opened = True
    def navigate(self, url): self.url = url
    def capture_pre_action_exposure(self): return dict(self.evidence)
    def read_state(self): return {"route": "initial", "step": 0}
    def close_context(self): self.closed = True


class AdapterContractTests(unittest.TestCase):
    def test_mock_bridge_lifecycle_and_prompt_delivery(self) -> None:
        for cell in load_schedule()[:12]:
            plan = build_attempt_plan(
                cell, attempt_id=1, clean_context_id=f"mock-{cell.scheduled_run_id}",
                base_url="http://127.0.0.1:8000",
            )
            bridge = _MockBridge(_exposure(cell))
            context = exercise_bridge_lifecycle(plan, bridge)
            self.assertTrue(bridge.opened)
            self.assertTrue(bridge.closed)
            self.assertEqual(plan.site_url, bridge.url)
            self.assertEqual(ADAPTER_STATUS, context["adapter_status"])
            self.assertIn("new_run=1", plan.site_url)

    def test_exposure_must_precede_first_action(self) -> None:
        cell = load_schedule()[0]
        plan = build_attempt_plan(cell, attempt_id=1, clean_context_id="x", base_url="http://x")
        evidence = _exposure(cell)
        evidence["agent_action_count"] = 1
        with self.assertRaises(AdapterContractError):
            verify_pre_action_exposure(plan, evidence)


class DryRunAndAnalysisGuardTests(unittest.TestCase):
    def test_complete_108_cell_dry_run_and_corruption_detection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "dry"
            manifest = run_pre_api_dry_run(root)
            self.assertEqual(108, manifest["scheduled_cells"])
            self.assertEqual(108, manifest["valid_dry_run_records"])
            self.assertEqual(3, manifest["infrastructure_retries_exercised"])
            self.assertEqual(0, manifest["model_or_api_calls"])
            self.assertFalse(manifest["formal_run"])
            validate_pre_api_dry_run_only(root)

            cell = load_schedule()[0]
            attempt = root / "runs" / cell.scheduled_run_id / "attempt_1"
            validate_attempt_directory(attempt, cell=cell)
            raw_path = attempt / "raw_state.json"
            raw = read_json(raw_path)
            raw["formal_run"] = True
            raw_path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(ArtifactContractError):
                validate_attempt_directory(attempt, cell=cell)

    def test_formal_analysis_rejects_fixture_and_nonformal_metadata(self) -> None:
        with self.assertRaises(FormalAnalysisEligibilityError):
            assert_formal_analysis_eligible(
                {
                    "formal_run": False,
                    "synthetic_fixture": True,
                    "agent_model_call": False,
                }
            )

    def test_precision_audit_does_not_change_frozen_design(self) -> None:
        report = precision_report()
        self.assertIn("not_treatment_evidence", report["status"])
        self.assertEqual(108, report["three_repeats"]["scheduled_runs_for_three_conditions"])
        self.assertEqual(180, report["five_repeats"]["scheduled_runs_for_three_conditions"])


if __name__ == "__main__":
    unittest.main()
