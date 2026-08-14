from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "research/pre-normative-profiles/fixtures/runtime-identity-context-v0.json"
)


class RuntimeIdentityContextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads(FIXTURE.read_text())
        cls.cases = {case["name"]: case for case in cls.document["cases"]}

    def test_fixture_is_research_only_and_not_wire(self) -> None:
        self.assertEqual("research-only", self.document["status"])
        self.assertFalse(self.document["wire_contract"])

    def test_base_capsule_preserves_identity_boundary(self) -> None:
        capsule = self.document["base_capsule"]
        self.assertIn("Intent-based Inter-agent Communication Protocol", capsule)
        self.assertIn("not IICP", capsule)
        self.assertIn("do not guess missing facts", capsule)
        self.assertNotIn("assistant persona", capsule.lower())

    def test_only_chat_is_initially_applicable(self) -> None:
        self.assertEqual(
            ["urn:iicp:intent:llm:chat:v1"],
            self.document["initial_applicability"],
        )
        for name in (
            "embedding_never_receives_identity_text",
            "audio_transcription_never_receives_identity_text",
            "mcp_call_never_receives_identity_text",
            "raw_completion_is_deferred",
        ):
            self.assertEqual("no_change", self.cases[name]["expected"]["action"])

    def test_disabled_mode_is_byte_equivalent(self) -> None:
        expected = self.cases["disabled_mode_preserves_chat_payload"]["expected"]
        self.assertEqual("no_change", expected["action"])
        self.assertEqual("byte_equivalent", expected["application_messages"])

    def test_unknown_model_is_not_rendered(self) -> None:
        expected = self.cases["unknown_model_is_omitted"]["expected"]
        self.assertIsNone(expected["rendered_model"])
        self.assertIn("unavailable", expected["answer_rule"])

    def test_private_fields_are_never_injected(self) -> None:
        prohibited = set(self.document["never_inject_fields"])
        case = self.cases["private_route_facts_are_rejected"]
        self.assertTrue(set(case["facts"]).issubset(prohibited))
        self.assertEqual(
            "reject_prohibited_facts_before_composition",
            case["expected"]["action"],
        )

    def test_user_text_does_not_expand_disclosure(self) -> None:
        expected = self.cases["user_request_does_not_widen_disclosure"]["expected"]
        self.assertEqual("unchanged", expected["allowed_fields"])
        self.assertEqual("informational_not_injection_proof", expected["security_claim"])

    def test_optional_and_required_unsupported_behavior_differ(self) -> None:
        optional = self.cases[
            "unsupported_instruction_channel_degrades_in_optional_mode"
        ]["expected"]
        required = self.cases[
            "required_mode_refuses_before_dispatch_when_unsupported"
        ]["expected"]
        self.assertTrue(optional["dispatch_allowed"])
        self.assertFalse(required["prompt_sent"])

    def test_capability_rendering_is_blocked_on_canonical_projection(self) -> None:
        expected = self.cases[
            "capabilities_wait_for_canonical_projection"
        ]["expected"]
        self.assertEqual("omit_fact", expected["action"])
        self.assertEqual("blocked_on_iicp_156_projection", expected["reason"])

    def test_base_capsule_measurement_is_bounded_and_explicitly_local(self) -> None:
        measurement = self.document["base_capsule_measurement"]
        self.assertEqual(
            measurement["capsule_prompt_tokens"] - measurement["baseline_prompt_tokens"],
            measurement["measured_overhead_tokens"],
        )
        self.assertLessEqual(measurement["measured_overhead_tokens"], 64)
        self.assertIn("not a tokenizer-independent guarantee", measurement["scope"])


if __name__ == "__main__":
    unittest.main()
