from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/environmental-independence-v0.json"


class EnvironmentalIndependenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads(FIXTURE.read_text())
        cls.cases = {case["name"]: case for case in cls.document["cases"]}

    def test_fixture_is_research_only(self) -> None:
        self.assertEqual("research-only", self.document["status"])
        self.assertFalse(self.document["wire_contract"])
        self.assertIn("no_space_mission_readiness", self.document["explicit_non_claims"])

    def test_extension_classes_are_distinct(self) -> None:
        self.assertEqual(
            {"core", "profile", "binding", "registry", "implementation_extension"},
            set(self.document["extension_classes"]),
        )

    def test_transport_and_fragmentation_do_not_change_semantics(self) -> None:
        transport = self.cases["transport_change_keeps_intent"]["expected"]
        fragments = self.cases["fragmentation_keeps_task_semantics"]["expected"]
        self.assertFalse(transport["intent_changed"])
        self.assertEqual("binding", transport["extension_class"])
        self.assertEqual(1, fragments["task_count"])
        self.assertFalse(fragments["lifecycle_changed"])

    def test_identity_reachability_and_capability_are_separate(self) -> None:
        locator = self.cases["locator_rotation_keeps_identity"]["expected"]
        offline = self.cases["valid_advertisement_provider_temporarily_offline"]["expected"]
        self.assertFalse(locator["node_id_changed"])
        self.assertTrue(offline["capability_exists"])
        self.assertFalse(offline["default_dispatch_eligible"])

    def test_logical_task_survives_attempt_retry(self) -> None:
        valid = self.cases["retry_keeps_task_and_changes_call"]["expected"]
        invalid = self.cases["transport_retry_must_not_create_task"]["expected"]
        self.assertTrue(valid["same_logical_task"])
        self.assertTrue(valid["valid_attempt_identity"])
        self.assertFalse(invalid["valid"])

    def test_time_axes_do_not_collapse(self) -> None:
        expected = self.cases["execution_and_delivery_time_are_separate"]["expected"]
        self.assertFalse(expected["represent_as_one_timeout_ms"])
        self.assertTrue(expected["requires_additive_profile_review"])

    def test_required_extensions_fail_closed(self) -> None:
        required = self.cases["unknown_required_profile_rejects"]["expected"]
        optional = self.cases["unknown_optional_profile_preserves_baseline"]["expected"]
        modifier = self.cases["unknown_required_intent_modifier_must_not_fail_open"]["expected"]
        self.assertFalse(required["dispatch_allowed"])
        self.assertTrue(optional["baseline_allowed"])
        self.assertFalse(optional["profile_applied"])
        self.assertFalse(modifier["route_as_base_intent"])

    def test_environment_is_not_qos(self) -> None:
        expected = self.cases["environment_name_is_not_qos"]["expected"]
        self.assertFalse(expected["valid"])

    def test_new_capability_and_behavior_do_not_require_core_change(self) -> None:
        capability = self.cases["new_domain_capability_is_registry_work"]["expected"]
        behavior = self.cases["new_semantic_behavior_is_profile_work"]["expected"]
        self.assertEqual("registry", capability["extension_class"])
        self.assertEqual("profile", behavior["extension_class"])
        self.assertFalse(capability["core_revision_required"])
        self.assertFalse(behavior["core_revision_required"])


if __name__ == "__main__":
    unittest.main()
