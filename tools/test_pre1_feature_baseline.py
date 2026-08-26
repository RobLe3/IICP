#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/check_pre1_feature_baseline.py"
spec = importlib.util.spec_from_file_location("pre1_feature_baseline", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


class Pre1FeatureBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.value = json.loads(module.DEFAULT_BASELINE.read_text())

    def test_current_baseline_is_valid_and_open(self) -> None:
        self.assertEqual(module.validate(self.value), [])
        result = module.evaluate(self.value)
        self.assertEqual(result["capabilities"], 27)
        self.assertEqual(len(result["open_component_reviews"]), 6)
        self.assertFalse(result["strict_ready"])

    def test_all_reviews_and_freeze_make_boundary_ready(self) -> None:
        value = copy.deepcopy(self.value)
        value["status"] = "CANDIDATE_BOUNDARY_FROZEN"
        for row in value["component_reviews"]:
            row["status"] = "PASS"
        self.assertEqual(module.validate(value), [])
        self.assertTrue(module.evaluate(value)["strict_ready"])

    def test_digest_and_duplicate_changes_fail(self) -> None:
        value = copy.deepcopy(self.value)
        value["capabilities"].append(copy.deepcopy(value["capabilities"][0]))
        errors = module.validate(value)
        self.assertIn("capability ids must be unique", errors)
        self.assertTrue(any("capability_ids_sha256" in row for row in errors))

    def test_required_capability_needs_fixture_and_implementation(self) -> None:
        value = copy.deepcopy(self.value)
        row = next(row for row in value["capabilities"] if row["classification"] == "REQUIRED_STABLE")
        row["fixture_refs"] = []
        row["implementations"] = []
        errors = module.validate(value)
        self.assertTrue(any("has no fixture" in error for error in errors))
        self.assertTrue(any("has no implementation" in error for error in errors))

    def test_missing_local_reference_fails(self) -> None:
        value = copy.deepcopy(self.value)
        value["capabilities"][0]["authority_refs"] = ["spec/does-not-exist.md"]
        errors = module.validate(value)
        self.assertTrue(any("missing referenced artifact" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
