from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/pre-normative-profiles/fixtures/profile-security-candidate-manifest-v0.json"


class ProfileSecurityCandidateTests(unittest.TestCase):
    def test_manifest_is_candidate_not_release_authority(self) -> None:
        data = json.loads(MANIFEST.read_text())
        self.assertEqual(data["status"], "pre-normative")
        self.assertIn("not a protocol release manifest", data["purpose"])

    def test_policy_and_dispatch_evidence_are_both_bound(self) -> None:
        paths = {item["path"] for item in json.loads(MANIFEST.read_text())["fixtures"]}
        self.assertIn("policy-detail-disclosure-authority-v0.json", paths)
        self.assertIn("trust-bundle-rollback-anchor-v0.json", paths)


if __name__ == "__main__":
    unittest.main()
