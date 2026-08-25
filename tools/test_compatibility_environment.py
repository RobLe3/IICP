from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from check_compatibility_environment import CATALOG, catalog_path, validate

ROOT = Path(__file__).resolve().parents[1]
CRITICALITY = ROOT / "research/pre-normative-profiles/fixtures/extension-criticality-v1.json"


class CompatibilityEnvironmentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CATALOG.read_text())
        cls.fixture = json.loads(CRITICALITY.read_text())

    def test_current_catalog_closes_local_references(self) -> None:
        self.assertEqual([], validate(self.catalog))

    def test_catalog_path_follows_suite_version(self) -> None:
        self.assertEqual(CATALOG, catalog_path())

    def test_historical_catalog_remains_immutable(self) -> None:
        historical = ROOT / "evidence/compatibility-environment-v1.10.16.json"
        self.assertEqual(
            "9571cefa0823d21433bc092bac4bb8c537d074bcf03c36be3c7f9704ddb5d994",
            hashlib.sha256(historical.read_bytes()).hexdigest(),
        )

    def test_candidate_binds_previously_workspace_only_profiles(self) -> None:
        optional = {
            item["id"]: item
            for item in self.catalog["semantic_environment"]["profiles"]["optional"]
        }
        self.assertIn("cip-consumer-cosignature-v1", optional)
        self.assertIn("runtime-health-v1", optional)
        for item in optional.values():
            self.assertNotIn("://", item["reference"])

        security = {
            item["id"]
            for item in self.catalog["semantic_environment"]["identity_and_security_profiles"]
        }
        self.assertIn("policy-detail-disclosure-authority-v0", security)
        self.assertIn("trust-bundle-rollback-anchor-v0", security)

    def test_missing_or_changed_artifact_fails(self) -> None:
        changed = copy.deepcopy(self.catalog)
        changed["semantic_environment"]["registry"]["sha256"] = "0" * 64
        self.assertTrue(any("digest mismatch" in item for item in validate(changed)))

    def test_optional_support_is_not_universal(self) -> None:
        self.assertTrue(self.catalog["implementation_projections"])
        optional = {item["id"] for item in self.catalog["semantic_environment"]["profiles"]["optional"]}
        support_sets = [set(item["supported_profiles"]) for item in self.catalog["implementation_projections"]]
        self.assertTrue(optional)
        self.assertTrue(any(not optional <= supported for supported in support_sets))

    def test_extension_classes_and_cross_version_cases(self) -> None:
        self.assertEqual(
            {"OPTIONAL_IGNORABLE", "OPTIONAL_NEGOTIABLE", "REQUIRED_UNDERSTOOD", "REQUIRED_SECURITY_CRITICAL"},
            set(self.fixture["classes"]),
        )
        cases = {case["id"]: case for case in self.fixture["cases"]}
        self.assertTrue(cases["EC-01"]["expected"]["dispatch_allowed"])
        self.assertFalse(cases["EC-03"]["expected"]["dispatch_allowed"])
        self.assertFalse(cases["EC-04"]["expected"]["downgrade_allowed"])
        self.assertEqual("future_peer", cases["EC-05"]["expected"]["compatibility_burden"])

    def test_non_llm_examples_do_not_require_model_or_tokens(self) -> None:
        self.assertEqual(3, len(self.fixture["non_llm_regressions"]))
        for case in self.fixture["non_llm_regressions"]:
            self.assertFalse(case["model_metadata_required"])
            self.assertFalse(case["token_metadata_required"])


if __name__ == "__main__":
    unittest.main()
