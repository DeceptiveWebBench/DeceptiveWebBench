from __future__ import annotations

import unittest

from src.utils.io import project_root
from src.v2.formal_action_schema_adjudication import verify_adjudication


class ProtectedScopeTests(unittest.TestCase):
    def test_formal_tree_protocol_scoped_after_authoring_begins(self) -> None:
        # The pre-API baseline froze paper/archive only during collection.
        # After explicit author approval to write results, the active paper is
        # expected to change.  The durable invariant is that formal artifacts
        # remain in the versioned collection and canonical repeat roots.
        formal_root = project_root() / "logs/v2/formal"
        formal_files = [path for path in formal_root.rglob("*") if path.is_file()] if formal_root.exists() else []
        allowed = formal_root / "protocol-v2-generic-safeguard-v0.2"
        for path in formal_files:
            relative = path.relative_to(allowed)
            self.assertIn(relative.parts[0], {"repeat_1", "repeat_2", "repeat_3"})
        record = verify_adjudication()
        self.assertTrue(record["original_artifacts_unchanged"])
        self.assertFalse(record["rerun_performed"])


if __name__ == "__main__":
    unittest.main()
