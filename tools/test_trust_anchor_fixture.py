from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/trust-bundle-rollback-anchor-v0.json"
MODULE_PATH = ROOT / "tools/rollback_anchor_simulation.py"
SPEC = importlib.util.spec_from_file_location("rollback_anchor_simulation", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RollbackAnchorTests(unittest.TestCase):
    def test_all_vectors_pass(self) -> None:
        result = MODULE.run(FIXTURE)
        self.assertEqual((result["passed"], result["failed"]), (7, 0))

    def test_anchor_state_is_content_free(self) -> None:
        fixture = json.loads(FIXTURE.read_text())
        fields = json.dumps(fixture["anchor_state_fields"]).lower()
        for forbidden in fixture["forbidden_state_fields"]:
            self.assertNotIn(forbidden, fields)

    def test_recovery_is_explicit_and_no_fallback_exists(self) -> None:
        fixture = json.loads(FIXTURE.read_text())
        outcomes = {case["expected"]["decision"] for case in fixture["vectors"]}
        self.assertEqual(outcomes, {"accept", "reject", "recover"})
        self.assertNotIn("fallback", outcomes)


if __name__ == "__main__":
    unittest.main()
