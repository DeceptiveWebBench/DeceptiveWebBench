from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.v2.audit_structural_metrics import PATH_METRICS, generate_metrics
from src.v2.registry import load_registry


class StructuralMetricsTests(unittest.TestCase):
    def test_metrics_cover_12_tasks_and_are_browser_verified(self) -> None:
        self.assertEqual({task.task_id for task in load_registry()}, set(PATH_METRICS))
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "metrics.csv"
            rows = generate_metrics(destination)
            self.assertEqual(12, len(rows))
            self.assertEqual(12, len({row["task_id"] for row in rows}))
            self.assertTrue(all(row["viewport_overflow_occlusion_result"] == "pass" for row in rows))
            self.assertTrue(all(row["safe_unsafe_endpoint_equivalence_result"] == "pass" for row in rows))
            self.assertTrue(all(row["stop_task_available_pages"].split("/")[0] == row["stop_task_available_pages"].split("/")[1] for row in rows))
            self.assertTrue(all(row["warning_exposure_pages"].split("/")[0] == row["warning_exposure_pages"].split("/")[1] for row in rows))
            with destination.open(newline="", encoding="utf-8") as handle:
                self.assertEqual(12, len(list(csv.DictReader(handle))))


if __name__ == "__main__":
    unittest.main()
