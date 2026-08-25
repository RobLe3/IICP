from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "research/pre-normative-profiles/fixtures"
AUTHORITY = FIXTURES / "policy-detail-disclosure-authority-v0.json"
HISTORICAL = FIXTURES / "policy-detail-disclosure-v0.json"


class PolicyDetailDisclosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(AUTHORITY.read_text())
        self.historical = json.loads(HISTORICAL.read_text())

    def test_revoked_and_expired_authority_fail_before_disclosure(self) -> None:
        by_id = {case["id"]: case for case in self.fixture["cases"]}
        expected = {
            "POLICY-DISCLOSURE-09": "consumer_auth_revoked",
            "POLICY-DISCLOSURE-10": "dispatch_ticket_invalid",
            "POLICY-DISCLOSURE-11": "dispatch_ticket_expired",
            "POLICY-DISCLOSURE-12": "dispatch_ticket_revoked",
        }
        for case_id, reason in expected.items():
            self.assertEqual(by_id[case_id]["expected"], {"status": 401, "reason": reason})

    def test_success_output_remains_allow_listed(self) -> None:
        success = next(
            case for case in self.historical["cases"] if case["id"] == "POLICY-DISCLOSURE-01"
        )
        details = success["context"]["details"]
        projected = {
            key: value
            for key, value in details.items()
            if key in self.historical["allowed_detail_fields"]
        }
        self.assertEqual(set(projected), set(self.historical["allowed_detail_fields"]))
        self.assertNotIn("prompt", projected)


if __name__ == "__main__":
    unittest.main()
