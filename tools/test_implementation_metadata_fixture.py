#!/usr/bin/env python3
"""Validate the implementation-identity compatibility fixture."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/directory-implementation-metadata-v1.json"


class ImplementationMetadataFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_required_cases_are_present(self) -> None:
        names = {case["name"] for case in self.data["cases"]}
        self.assertEqual(
            names,
            {
                "legacy_alias_only",
                "preferred_field_only",
                "matching_dual_fields",
                "conflicting_dual_fields",
                "invalid_private_path_identity",
            },
        )

    def test_accepted_cases_follow_precedence(self) -> None:
        for case in self.data["cases"]:
            values = case["input"]
            if not case["accepted"]:
                continue
            effective = values.get("sdk_compatibility_version") or values.get("sdk_version")
            self.assertEqual(case["effective_sdk_compatibility_version"], effective)
            if values.get("sdk_compatibility_version") and values.get("sdk_version"):
                self.assertEqual(values["sdk_compatibility_version"], values["sdk_version"])

    def test_field_grammar_matches_positive_fixture_values(self) -> None:
        grammar = self.data["field_grammar"]
        for case in self.data["cases"]:
            if not case["accepted"]:
                continue
            for field, pattern in grammar.items():
                if field in case["input"]:
                    self.assertIsNotNone(re.fullmatch(pattern, case["input"][field]))

    def test_private_path_case_is_rejected_by_name_grammar(self) -> None:
        case = next(c for c in self.data["cases"] if c["name"] == "invalid_private_path_identity")
        pattern = self.data["field_grammar"]["implementation_name"]
        self.assertIsNone(re.fullmatch(pattern, case["input"]["implementation_name"]))
        self.assertEqual(case["status"], 422)


if __name__ == "__main__":
    unittest.main()
