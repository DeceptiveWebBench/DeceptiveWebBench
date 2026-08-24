from __future__ import annotations

import unittest

from src.v2.formal_later_repeats_v02 import (
    FORMAL_BASE, authorization_template, collection_id, repeat_cells, tranche_hash,
    verify_repeat1_freeze,
)


class FormalV02LaterRepeatContractTests(unittest.TestCase):
    def test_repeat2_and_repeat3_are_complete_disjoint_tranches(self):
        second, third = repeat_cells(2), repeat_cells(3)
        self.assertEqual(36, len(second)); self.assertEqual(36, len(third))
        self.assertFalse({c.scheduled_run_id for c in second} & {c.scheduled_run_id for c in third})
        self.assertTrue(all(c.repeat_id == 2 for c in second))
        self.assertTrue(all(c.repeat_id == 3 for c in third))

    def test_authorizations_are_single_repeat_and_eight_dollar_scoped(self):
        for repeat_id in (2, 3):
            auth=authorization_template(repeat_id)
            self.assertEqual([repeat_id], auth["repeat_ids"])
            self.assertEqual(36, auth["authorized_cell_count"])
            self.assertEqual(8.0, auth["hard_new_cost_limit_usd"])
            self.assertEqual(collection_id(repeat_id), auth["collection_id"])
            self.assertEqual(64, len(tranche_hash(repeat_id)))

    def test_repeat1_frozen_components_are_unchanged(self):
        if not (FORMAL_BASE / "repeat_1/formal_manifest.json").exists():
            self.skipTest("raw formal interaction tree is intentionally omitted from the public package")
        verify_repeat1_freeze()


if __name__ == "__main__":
    unittest.main()
