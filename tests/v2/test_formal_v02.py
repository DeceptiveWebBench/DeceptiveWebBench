from __future__ import annotations

import hashlib
import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.v2.costs import normalize_bedrock_usage
from src.v2.execution_adapter_v02 import artifact_context, build_attempt_plan, verify_pre_action_exposure
from src.v2.formal_repeat1_v02 import COLLECTION_ID, CONDITIONS, FormalV02Runner, repeat1_cells, tranche_hash, validate_requested_tranche, validate_v02_attempt
from src.v2.matrix import load_schedule
from src.v2.pilot import PILOT_ROOT, verify_frozen_manifest
from src.v2.runner import FormalRunGuardError
from src.v2.state_machine import fixture_for
from src.v2.safeguards_v02 import EXPECTED_PAYLOAD, WARNING_VERSION, build_prompt_bundle, render_warning


class FormalV02ContractTests(unittest.TestCase):
    def test_v01_manifest_still_verifies(self):
        if not (PILOT_ROOT / "pilot_manifest.json").exists():
            self.skipTest("raw pilot interaction tree is intentionally omitted from the public package")
        verify_frozen_manifest()

    def test_exact_payload_and_delivery_byte_equality(self):
        task = repeat1_cells()[0]
        system = build_prompt_bundle(task_id=task.task_id, condition="system_warning", page_url="http://local", scheduled_run_id=task.scheduled_run_id)
        ui = build_prompt_bundle(task_id=task.task_id, condition="ui_warning", page_url="http://local", scheduled_run_id=task.scheduled_run_id)
        none = build_prompt_bundle(task_id=task.task_id, condition="no_warning", page_url="http://local", scheduled_run_id=task.scheduled_run_id)
        self.assertEqual(EXPECTED_PAYLOAD, render_warning(task.task_id))
        self.assertEqual(system.rendered_payload.encode("utf-8"), ui.rendered_payload.encode("utf-8"))
        self.assertNotIn(EXPECTED_PAYLOAD, none.privileged_system_message)
        self.assertIsNone(none.rendered_payload)

    def test_repeat1_is_exact_unique_tranche(self):
        cells = repeat1_cells()
        self.assertEqual(36, len(cells))
        self.assertEqual(36, len({(c.task_id, c.safeguard_condition) for c in cells}))
        self.assertTrue(all(c.repeat_id == 1 for c in cells))
        self.assertEqual(sorted(c.planned_order for c in cells), [c.planned_order for c in cells])
        self.assertEqual(64, len(tranche_hash()))

    def test_adapter_explicit_version_and_exposure(self):
        cell = repeat1_cells()[0]
        plan = build_attempt_plan(cell, attempt_id=1, clean_context_id="clean", base_url="http://127.0.0.1")
        self.assertIn("safeguard_version=protocol-v2-generic-safeguard-v0.2", plan.site_url)
        payload = render_warning(cell.task_id)
        evidence = {"agent_action_count":0, "scheduled_run_id":cell.scheduled_run_id, "condition":cell.safeguard_condition, "safeguard_version":WARNING_VERSION, "dom_warning_text":payload if cell.safeguard_condition=="ui_warning" else "", "privileged_warning_text":payload if cell.safeguard_condition=="system_warning" else "", "panel_visible":True, "stop_visible":True}
        verify_pre_action_exposure(plan, evidence)

    def test_repeat2_is_outside_selection(self):
        selected = {c.scheduled_run_id for c in repeat1_cells()}
        self.assertTrue(all(c.scheduled_run_id not in selected for c in load_schedule() if c.repeat_id in (2,3)))

    def test_scope_guard_rejects_repeat2_wrong_version_budget_and_duplicate(self):
        cells = repeat1_cells()
        validate_requested_tranche(cells, safeguard_version=WARNING_VERSION, collection_id=COLLECTION_ID, budget_usd=8.0)
        repeat2 = tuple(c for c in load_schedule() if c.repeat_id == 2)
        for kwargs in (
            {"cells": repeat2, "safeguard_version": WARNING_VERSION, "collection_id": COLLECTION_ID, "budget_usd": 8.0},
            {"cells": cells, "safeguard_version": "protocol-v2-generic-safeguard-v0.1", "collection_id": COLLECTION_ID, "budget_usd": 8.0},
            {"cells": cells, "safeguard_version": WARNING_VERSION, "collection_id": COLLECTION_ID, "budget_usd": 8.01},
            {"cells": cells, "safeguard_version": WARNING_VERSION, "collection_id": COLLECTION_ID, "budget_usd": 8.0, "existing_scheduled_run_ids": {cells[0].scheduled_run_id}},
        ):
            with self.assertRaises(FormalRunGuardError):
                validate_requested_tranche(**kwargs)

    def test_formal_runner_writes_rescorable_v02_bundle(self):
        cell = repeat1_cells()[0]
        png = base64.b64encode(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")).decode()
        def executor(current, attempt_id, clean_context_id):
            plan = build_attempt_plan(current, attempt_id=attempt_id, clean_context_id=clean_context_id, base_url="http://127.0.0.1")
            payload = render_warning(current.task_id)
            evidence = {"agent_action_count":0,"scheduled_run_id":current.scheduled_run_id,"condition":current.safeguard_condition,"safeguard_version":WARNING_VERSION,"dom_warning_text":payload if current.safeguard_condition=="ui_warning" else "","privileged_warning_text":payload if current.safeguard_condition=="system_warning" else "","panel_visible":True,"stop_visible":True}
            raw = fixture_for(current.task_id, 1, 1); raw.update(artifact_context(plan, evidence))
            raw.update({"synthetic_fixture":False,"agent_model_call":True,"trajectory":list(raw["events"]),"actions":[{"action":"contract_fixture"}],"screenshots":[],"_screenshot_payloads":[{"name":"step_000_initial","png_base64":png,"source_step":0}],"dom_state_evidence":{"final_url":plan.site_url},"model_calls_usage":[normalize_bedrock_usage({"inputTokens":100,"outputTokens":20},call_id="model_call_1",latency_seconds=0.5)],"provider_reported_cost":None})
            return raw
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # The real one-shot authorization is deliberately consumed after
            # Repeat 1.  This isolated writer-contract test supplies its own
            # scoped guard so it remains runnable without reauthorizing API use.
            with patch("src.v2.formal_repeat1_v02.assert_cell_authorized", return_value=None):
                result = FormalV02Runner(executor=executor, output_root=root).run([cell])[0]
            self.assertEqual("valid", result["attempts"][0]["run_validity"])
            attempt = root / cell.scheduled_run_id / "attempt_1"
            validate_v02_attempt(attempt, cell)


if __name__ == "__main__":
    unittest.main()
