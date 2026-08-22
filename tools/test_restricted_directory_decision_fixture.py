#!/usr/bin/env python3
"""Validate the bounded restricted-directory decision projection."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/restricted-trust-domain-directory-decision-v0.json"
SCHEMA = ROOT / "research/pre-normative-profiles/schemas/restricted-trust-domain-directory-decision-v0.schema.json"


def classify(required: dict | None, projection: object, schema: dict) -> str:
    if required is None:
        return "not_required" if projection is None else "unexpected"
    if projection is None:
        return "missing"
    try:
        jsonschema.validate(projection, schema)
    except jsonschema.ValidationError:
        return "malformed"
    assert isinstance(projection, dict)
    if any(projection[key] != required[key] for key in ("operation", "domain_id", "authority_id")):
        return "mismatch"
    if projection["membership_generation"] < required["minimum_membership_generation"]:
        return "stale"
    if projection["membership_expires_at"] <= required["now"]:
        return "expired"
    return "eligible"


class RestrictedDirectoryDecisionFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.schema = json.loads(SCHEMA.read_text())

    def test_schema_is_valid(self) -> None:
        jsonschema.Draft202012Validator.check_schema(self.schema)

    def test_vectors_have_unique_ids_and_expected_coverage(self) -> None:
        vectors = self.fixture["vectors"]
        self.assertEqual(len(vectors), len({vector["id"] for vector in vectors}))
        self.assertTrue(
            {"eligible", "not_required", "missing", "mismatch", "stale", "expired", "malformed"}
            .issubset({vector["expected"] for vector in vectors})
        )

    def test_vectors_follow_fail_closed_semantics(self) -> None:
        for vector in self.fixture["vectors"]:
            with self.subTest(vector=vector["id"]):
                self.assertEqual(
                    vector["expected"],
                    classify(vector["required"], vector["projection"], self.schema),
                )

    def test_valid_projection_contains_no_subject_or_secret_material(self) -> None:
        forbidden = {"subject_id", "token", "credential", "secret", "membership", "nodes", "endpoint"}
        for vector in self.fixture["vectors"]:
            if vector["expected"] != "eligible":
                continue
            projection = vector["projection"]
            self.assertTrue(forbidden.isdisjoint(projection))


if __name__ == "__main__":
    unittest.main()
