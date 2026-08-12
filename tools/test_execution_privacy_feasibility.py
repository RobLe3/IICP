#!/usr/bin/env python3
"""Regression tests for the synthetic execution-privacy binding fixture."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

try:
    import cryptography  # noqa: F401
except ModuleNotFoundError:
    HAS_CRYPTOGRAPHY = False
else:
    HAS_CRYPTOGRAPHY = True

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "research"
    / "strategic"
    / "execution-privacy-feasibility"
    / "verify_vectors.py"
)
FIXTURE_PATH = MODULE_PATH.with_name("vectors-v0.json")
if HAS_CRYPTOGRAPHY:
    SPEC = importlib.util.spec_from_file_location(
        "execution_privacy_vectors", MODULE_PATH
    )
    assert SPEC and SPEC.loader
    MODULE = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(MODULE)
else:
    MODULE = None


@unittest.skipUnless(
    HAS_CRYPTOGRAPHY, "optional cryptography dependency is unavailable"
)
class ExecutionPrivacyFixtureTests(unittest.TestCase):
    def test_all_vectors_match_expected_outcomes(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        results = MODULE.verify_fixture(fixture)
        self.assertEqual(len(results), 10)
        self.assertTrue(all(expected == actual for _, expected, actual in results))

    def test_fixture_is_deterministic(self) -> None:
        generated = json.dumps(MODULE.make_fixture(), indent=2, sort_keys=True) + "\n"
        self.assertEqual(FIXTURE_PATH.read_text(encoding="utf-8"), generated)

    def test_fixture_is_content_free_and_contains_no_private_key(self) -> None:
        fixture_text = FIXTURE_PATH.read_text(encoding="utf-8")
        lowered = fixture_text.lower()
        for forbidden in (
            "prompt",
            "response content",
            "route_ticket",
            "endpoint",
            "hardware_serial",
            "raw_vendor_quote",
        ):
            self.assertNotIn(forbidden, lowered)
        fixture = json.loads(fixture_text)

        def keys(value: object) -> set[str]:
            if isinstance(value, dict):
                return set(value) | set().union(
                    *(keys(item) for item in value.values())
                )
            if isinstance(value, list):
                return set().union(*(keys(item) for item in value))
            return set()

        self.assertNotIn("private_key", keys(fixture))
        self.assertEqual(fixture["evidence_class"], "synthetic-research-only")
        self.assertIn("not_hardware_attestation", fixture["non_claims"])


if __name__ == "__main__":
    unittest.main()
