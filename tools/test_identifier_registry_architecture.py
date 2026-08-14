from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/architecture/identifier-registry-v1.json"
SEMANTICS = ROOT / "spec/v1.9/iicp-semantics.md"
CORE = ROOT / "spec/v1.9/iicp-core.md"


class IdentifierRegistryArchitectureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text())
        cls.semantics = SEMANTICS.read_text()
        cls.core = CORE.read_text()

    def test_registration_status_is_not_overclaimed(self) -> None:
        self.assertFalse(self.contract["iana_nid_registered"])
        self.assertFalse(self.contract["submission_authorized"])
        self.assertEqual("stable-project-defined-identifier", self.contract["current_identifier_status"])
        self.assertIn("pending formal namespace registration", " ".join(self.core.split()))

    def test_released_values_are_preserved_as_opaque(self) -> None:
        compatibility = self.contract["compatibility"]
        self.assertTrue(compatibility["preserve_released_values"])
        self.assertEqual("opaque-case-sensitive-exact", compatibility["comparison"])
        self.assertFalse(compatibility["bulk_rewrite_allowed"])

    def test_private_use_is_project_convention(self) -> None:
        allocation = self.contract["private_and_experimental"]
        self.assertFalse(allocation["ietf_practice_claim"])
        self.assertIn("IICP Private Use allocation rule", self.semantics)
        self.assertNotIn("follows IETF practice", self.semantics)

    def test_registry_matrix_covers_public_identifier_families(self) -> None:
        policies = self.contract["registry_policies"]
        for family in ("intent", "capability", "profile", "binding", "error_code", "security_mechanism"):
            self.assertIn(family, policies)

    def test_implementation_inventory_covers_maintained_surfaces(self) -> None:
        components = {entry["component"] for entry in self.contract["implementation_inventory"]}
        self.assertEqual(
            {"python-sdk", "typescript-sdk", "rust-sdk", "php-directory", "rust-directory", "browser-node"},
            components,
        )


if __name__ == "__main__":
    unittest.main()
