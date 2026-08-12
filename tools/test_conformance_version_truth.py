#!/usr/bin/env python3
"""Tests for the conformance-suite version-truth gate."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).with_name("check_conformance_version_truth.py")
SPEC = importlib.util.spec_from_file_location("check_conformance_version_truth", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ConformanceVersionTruthTest(unittest.TestCase):
    def test_repository_state_is_consistent(self) -> None:
        self.assertEqual(MODULE.check(), [])

    def test_released_fixture_requires_known_suite_version(self) -> None:
        path = Path("released.json")
        self.assertEqual(MODULE.check_fixture(path, {"profile": "x", "suite_version": "4.50.0"}, ["4.50.0"], "4.50.0"), [])
        self.assertIn("absent from the changelog", MODULE.check_fixture(path, {"profile": "x", "suite_version": "9.9.9"}, ["4.50.0"], "4.50.0")[0])

    def test_explicit_pre_normative_fixture_may_omit_suite_version(self) -> None:
        path = Path("draft.json")
        self.assertEqual(MODULE.check_fixture(path, {"status": "pre-normative"}, ["4.50.0"], "4.50.0"), [])

    def test_ambiguous_fixture_fails_closed(self) -> None:
        errors = MODULE.check_fixture(Path("ambiguous.json"), {"profile": "x"}, ["4.50.0"], "4.50.0")
        self.assertIn("explicit pre-normative status", errors[0])

    def test_pre_normative_fixture_cannot_claim_release_suite(self) -> None:
        errors = MODULE.check_fixture(Path("mixed.json"), {"status": "pre-normative", "suite_version": "4.50.0"}, ["4.50.0"], "4.50.0")
        self.assertIn("must not claim suite_version", errors[0])


if __name__ == "__main__":
    unittest.main()
