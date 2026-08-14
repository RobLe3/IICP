from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/architecture/effective-service-capability-v1.json"
FORMAT = ROOT / "spec/v1.9/node-capability-format.md"
CORE = ROOT / "spec/v1.9/iicp-core.md"
DIRECTORY = ROOT / "spec/v1.9/iicp-dir.md"


class EffectiveServiceCapabilitySemanticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text())
        cls.format = FORMAT.read_text()
        cls.core = CORE.read_text()
        cls.directory = DIRECTORY.read_text()
        cls.cases = {case["name"]: case["expected"] for case in cls.contract["scenarios"]}

    def test_base_is_not_model_specific(self) -> None:
        self.assertEqual(["intent"], self.contract["base_object"]["required"])
        case = self.cases["non_model_tool_service"]
        self.assertTrue(case["valid_without_models"])
        self.assertTrue(case["valid_without_max_tokens"])
        self.assertIn("conditional fields", self.core)

    def test_same_intent_variants_are_valid_without_union(self) -> None:
        cardinality = self.contract["cardinality"]
        self.assertTrue(cardinality["multiple_variants_per_intent"])
        self.assertFalse(cardinality["cross_variant_field_union_allowed"])
        self.assertIn("MAY appear more than once", self.format)

    def test_unknown_extension_rules_are_fail_closed(self) -> None:
        self.assertEqual("ineligible", self.contract["extensions"]["unknown_required"])
        self.assertTrue(self.contract["extensions"]["accepted_extension_preserved"])
        self.assertFalse(self.contract["extensions"]["unknown_top_level_implies_support"])

    def test_required_preferred_and_limits_are_separate(self) -> None:
        matching = self.contract["matching"]
        self.assertEqual("eligibility", matching["requires"])
        self.assertEqual("post_eligibility_ranking", matching["prefers"])
        self.assertEqual("typed_numeric_comparison", matching["limits"])
        self.assertEqual("required_capability_unknown", self.cases["unknown_required"]["reason"])
        self.assertTrue(self.cases["unknown_preferred"]["eligible"])
        self.assertFalse(self.cases["absent_required"]["eligible"])
        self.assertTrue(self.cases["absent_optional"]["eligible"])

    def test_tool_calling_does_not_imply_execution(self) -> None:
        implied = set(self.cases["tool_call_generation"]["does_not_imply"])
        self.assertIn("tool_execution", implied)
        self.assertIn("mcp_binding", implied)

    def test_streaming_remains_profile_owned(self) -> None:
        streaming = self.cases["streaming"]
        self.assertEqual("service_lifecycle_profile", streaming["representation"])
        self.assertFalse(streaming["buffered_call_change"])

    def test_provenance_is_bounded_and_not_self_verifying(self) -> None:
        provenance = self.contract["provenance"]
        self.assertFalse(provenance["heuristic_is_verified"])
        self.assertFalse(provenance["operator_assertion_is_verified"])
        self.assertEqual("stale", provenance["expired"])

    def test_additive_profile_contract_does_not_change_http_binding(self) -> None:
        self.assertTrue(self.contract["wire_change"])
        self.assertEqual("urn:iicp:profile:effective-capability:v1", self.contract["profile_id"])
        self.assertIn("no_http_discovery_binding_change", self.contract["explicit_non_claims"])
        self.assertIn("Existing `?modality=` behavior remains unchanged", self.directory)


if __name__ == "__main__":
    unittest.main()
