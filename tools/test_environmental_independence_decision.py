from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/architecture/environmental-independence-v1.json"
SEMANTICS = ROOT / "spec/v1.9/iicp-semantics.md"


class EnvironmentalIndependenceDecisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text())
        cls.semantics = SEMANTICS.read_text()

    def test_decision_is_accepted_without_wire_change(self) -> None:
        self.assertEqual("accepted-architecture-boundary", self.contract["status"])
        self.assertFalse(self.contract["wire_change"])

    def test_extension_classes_are_complete_and_distinct(self) -> None:
        self.assertEqual(
            {"core", "profile", "binding", "registry", "implementation_extension"},
            set(self.contract["extension_classes"]),
        )
        self.assertEqual("binding", self.contract["current_classification"]["http_projection"])
        self.assertEqual("profile", self.contract["current_classification"]["service_lifecycle"])
        self.assertEqual("registry", self.contract["current_classification"]["capability_vocabulary"])

    def test_required_behavior_fails_closed(self) -> None:
        rules = self.contract["profile_rules"]
        modifiers = self.contract["legacy_modifier_rules"]
        self.assertEqual("reject_before_execution", rules["unknown_required"])
        self.assertEqual("reject", modifiers["unknown_modifier"])
        self.assertFalse(modifiers["strip_and_route_base_intent"])
        self.assertIn("An unknown modifier MUST be", self.semantics)
        self.assertNotIn("request SHOULD be routed normally (fail-open)", self.semantics)

    def test_phase_8_is_reserved_not_claimed(self) -> None:
        reservation = self.contract["phase_8_reservation"]
        self.assertFalse(reservation["implementation_authorized"])
        self.assertEqual(["bpv7"], reservation["potential_bindings"])

    def test_invariants_keep_identity_task_and_time_axes_separate(self) -> None:
        invariants = set(self.contract["invariants"])
        self.assertIn("identity_locator_distinct", invariants)
        self.assertIn("logical_task_attempt_distinct", invariants)
        self.assertIn("execution_delivery_deadline_result_wait_time_distinct", invariants)


if __name__ == "__main__":
    unittest.main()
