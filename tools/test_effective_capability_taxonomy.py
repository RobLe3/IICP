from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "research/pre-normative-profiles/fixtures/effective-capability-taxonomy-v0.json"
)


class EffectiveCapabilityTaxonomyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads(FIXTURE.read_text())
        cls.cases = {case["name"]: case for case in cls.document["cases"]}

    def test_fixture_is_research_only_and_not_a_wire_contract(self) -> None:
        self.assertEqual("research-only", self.document["status"])
        self.assertFalse(self.document["wire_contract"])

    def test_cases_use_known_classes(self) -> None:
        classes = set(self.document["classes"])
        for case in self.document["cases"]:
            statement = case.get("statement")
            if statement:
                self.assertIn(statement["class"], classes, case["name"])

    def test_effective_path_requires_every_layer(self) -> None:
        valid = self.cases["vision_chat_is_a_modality"]
        invalid = self.cases["theoretical_vision_is_not_effective"]
        self.assertTrue(all(valid["statement"]["path"].values()))
        self.assertFalse(all(invalid["statement"]["path"].values()))
        self.assertTrue(valid["expected"]["advertise"])
        self.assertFalse(invalid["expected"]["advertise"])

    def test_tool_calling_does_not_imply_execution(self) -> None:
        exclusions = self.cases["tool_calling_is_generation_not_execution"]["expected"]["does_not_imply"]
        self.assertIn("tool_execution", exclusions)
        self.assertIn("mcp_binding", exclusions)

    def test_agent_flag_is_rejected_in_favor_of_decomposition(self) -> None:
        expected = self.cases["agentic_is_decomposed"]["expected"]
        self.assertFalse(expected["advertise"])
        self.assertEqual("ambiguous_composite_capability", expected["reason"])
        self.assertGreaterEqual(len(expected["required_decomposition"]), 3)

    def test_unknown_required_and_preferred_semantics_differ(self) -> None:
        required = self.cases["unknown_required_capability_fails_closed"]["expected"]
        preferred = self.cases["unknown_preferred_capability_preserves_eligibility"]["expected"]
        self.assertFalse(required["eligible"])
        self.assertTrue(preferred["eligible"])

    def test_heuristic_fallback_is_not_verified_evidence(self) -> None:
        case = self.cases["model_name_is_only_a_fallback_claim"]
        self.assertEqual("heuristic_fallback", case["statement"]["provenance"])
        self.assertFalse(case["expected"]["advertise_as_verified"])


if __name__ == "__main__":
    unittest.main()
