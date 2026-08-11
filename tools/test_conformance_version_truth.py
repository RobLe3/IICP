#!/usr/bin/env python3
"""Tests for the conformance-suite version-truth gate."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).with_name("check_conformance_version_truth.py")
SPEC = importlib.util.spec_from_file_location("check_conformance_version_truth", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ConformanceVersionTruthTest(unittest.TestCase):
    def test_repository_state_is_consistent(self) -> None:
        self.assertEqual(MODULE.check(), [])

    def _check_fixture(self, fixture: dict) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            fixture_dir = Path(directory)
            (fixture_dir / "case.json").write_text(json.dumps(fixture), encoding="utf-8")
            return MODULE.check(fixture_dir=fixture_dir)

    def test_explicit_pre_normative_fixture_needs_no_suite_version(self) -> None:
        self.assertEqual(
            self._check_fixture({"profile": "research-v0", "status": "pre-normative"}),
            [],
        )
        self.assertEqual(
            self._check_fixture(
                {"profile": "research-v0", "status": "pre-normative-semantic-vectors"}
            ),
            [],
        )

    def test_released_fixture_requires_known_suite_version(self) -> None:
        errors = self._check_fixture({"profile": "released-v1", "suite_version": "99.0.0"})
        self.assertEqual(len(errors), 1)
        self.assertIn("suite version 99.0.0 is absent", errors[0])

    def test_ambiguous_fixture_fails_closed(self) -> None:
        errors = self._check_fixture({"profile": "ambiguous-v0"})
        self.assertEqual(
            errors,
            ["case.json: missing suite_version and explicit pre-normative status"],
        )

    def test_unknown_status_fails_closed(self) -> None:
        errors = self._check_fixture({"profile": "draft-v0", "status": "draft"})
        self.assertEqual(errors, ["case.json: unrecognized fixture status 'draft'"])

    def test_contradictory_released_and_pre_normative_metadata_fails_closed(self) -> None:
        errors = self._check_fixture(
            {
                "profile": "contradictory-v0",
                "suite_version": "4.50.0",
                "status": "pre-normative",
            }
        )
        self.assertEqual(
            errors,
            ["case.json: released fixture must not also declare status 'pre-normative'"],
        )


if __name__ == "__main__":
    unittest.main()
