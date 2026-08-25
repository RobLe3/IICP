from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "research/pre-normative-profiles/fixtures"


class ProfileSecurityCandidateConformanceTests(unittest.TestCase):
    def test_candidate_manifest_is_complete_and_integrity_bound(self) -> None:
        manifest = json.loads(
            (FIXTURES / "profile-security-candidate-manifest-v0.json").read_text()
        )
        self.assertEqual(manifest["status"], "pre-normative")
        paths = {item["path"] for item in manifest["fixtures"]}
        self.assertIn("policy-detail-disclosure-authority-v0.json", paths)
        self.assertIn("trust-bundle-rollback-anchor-v0.json", paths)
        for item in manifest["fixtures"]:
            digest = hashlib.sha256((FIXTURES / item["path"]).read_bytes()).hexdigest()
            self.assertEqual(digest, item["sha256"], item["path"])

    def test_policy_authority_and_recovery_fail_closed(self) -> None:
        policy = json.loads(
            (FIXTURES / "policy-detail-disclosure-authority-v0.json").read_text()
        )
        policy_reasons = {case["expected"]["reason"] for case in policy["cases"]}
        self.assertTrue(
            {
                "consumer_auth_revoked",
                "dispatch_ticket_invalid",
                "dispatch_ticket_expired",
                "dispatch_ticket_revoked",
            }.issubset(policy_reasons)
        )

        anchor = json.loads(
            (FIXTURES / "trust-bundle-rollback-anchor-v0.json").read_text()
        )
        decisions = {case["expected"]["decision"] for case in anchor["vectors"]}
        self.assertEqual(decisions, {"accept", "reject", "recover"})
        self.assertNotIn("fallback", decisions)


if __name__ == "__main__":
    unittest.main()
