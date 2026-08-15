#!/usr/bin/env python3
"""Validate the pre-normative runtime identity composition fixture."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "research/pre-normative-profiles/fixtures/runtime-identity-context-v0.json"


class RuntimeIdentityContextFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_profile_and_composition_contract_are_explicit(self) -> None:
        self.assertEqual(self.fixture["profile_id"], "urn:iicp:profile:runtime-identity-context:v0")
        self.assertEqual(self.fixture["context_marker"], "IICP-RUNTIME-CONTEXT/1")
        self.assertEqual(self.fixture["modes"], ["auto", "disabled", "explicit", "required"])
        self.assertEqual(self.fixture["composition"]["default_chat_mode"], "auto")
        self.assertEqual(self.fixture["composition"]["raw_submit"], "no_change")
        composition = self.fixture["composition"]
        self.assertEqual(composition["eligible_intent"], "urn:iicp:intent:llm:chat:v1")
        self.assertEqual(composition["role"], "system")
        self.assertEqual(
            composition["placement"],
            "after_leading_system_or_developer_before_first_other_message",
        )
        self.assertEqual(composition["unsupported_optional"], "no_change")
        self.assertEqual(composition["unsupported_required"], "refuse_before_dispatch")
        self.assertLessEqual(len(self.fixture["base_capsule"].encode()), composition["max_rendered_utf8_bytes"])

    def test_cases_are_unique_and_cover_safety_boundaries(self) -> None:
        names = [case["name"] for case in self.fixture["cases"]]
        self.assertEqual(len(names), len(set(names)))
        required = {
            "omitted_chat_mode_defaults_to_auto",
            "disabled_mode_preserves_chat_payload",
            "explicit_disabled_mode_overrides_auto_default",
            "candidate_fallback_recomposes_from_original_messages",
            "local_browser_mode_is_not_described_as_remote_routing",
            "raw_submit_remains_byte_equivalent",
            "application_system_message_is_not_rewritten",
            "existing_marker_suppresses_duplicate",
            "private_route_facts_are_rejected",
            "unsupported_instruction_channel_degrades_in_auto_mode",
            "required_mode_refuses_before_dispatch_when_unsupported",
            "embedding_never_receives_identity_text",
            "mcp_call_never_receives_identity_text",
        }
        self.assertTrue(required.issubset(names))

    def test_stable_capsule_contains_no_prohibited_field_names(self) -> None:
        capsule = self.fixture["base_capsule"].lower()
        for field in self.fixture["never_inject_fields"]:
            self.assertNotIn(field.lower(), capsule)


if __name__ == "__main__":
    unittest.main()
