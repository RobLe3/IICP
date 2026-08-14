from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/architecture/directory-state-semantics-v1.json"
DIRECTORY_SPEC = ROOT / "spec/v1.9/iicp-dir.md"
FEDERATION_SPEC = ROOT / "spec/v1.9/iicp-federated-directory.md"


class DirectoryStateSemanticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text())
        cls.directory_spec = DIRECTORY_SPEC.read_text()
        cls.federation_spec = FEDERATION_SPEC.read_text()
        cls.scenarios = {case["name"]: case["expected"] for case in cls.contract["scenarios"]}

    def test_axes_are_independent_and_complete(self) -> None:
        self.assertEqual(
            {"identity", "advertisement", "reachability", "availability", "dispatch"},
            set(self.contract["axes"]),
        )
        self.assertIn("superseded", self.contract["axes"]["advertisement"])
        self.assertIn("unknown", self.contract["axes"]["reachability"])

    def test_default_discovery_remains_current_only(self) -> None:
        self.assertFalse(self.contract["default_discovery_change"])
        self.assertEqual(
            "currently eligible candidates only",
            self.contract["views"]["default_dispatch"],
        )
        offline = self.scenarios["valid_but_offline"]
        self.assertTrue(offline["record_retained"])
        self.assertFalse(offline["default_discovery_contains"])
        self.assertIn("eligible now", self.directory_spec)

    def test_heartbeat_loss_does_not_revoke_identity(self) -> None:
        expired = self.scenarios["heartbeat_expired"]
        self.assertEqual("valid", expired["identity"])
        self.assertEqual("current", expired["advertisement"])
        self.assertEqual("stale", expired["reachability"])
        self.assertEqual("ineligible", expired["dispatch"])

    def test_recovery_recalculates_eligibility(self) -> None:
        recovered = self.scenarios["heartbeat_recovery"]
        self.assertEqual("recalculate", recovered["dispatch"])
        self.assertEqual("fresh_self_report", recovered["reachability"])

    def test_endpoint_rotation_is_fail_closed(self) -> None:
        rotation = self.scenarios["endpoint_rotation"]
        self.assertFalse(rotation["unverified_new_route_published"])
        self.assertIn("after_new_route_validation", rotation["old_advertisement"])

    def test_signed_state_does_not_imply_current_freshness(self) -> None:
        delayed = self.scenarios["delayed_federation_sync"]
        self.assertTrue(delayed["signature_may_remain_valid"])
        self.assertFalse(delayed["replica_serves_discovery"])
        self.assertIn("Signature validity does not extend", self.federation_spec)

    def test_provenance_is_bounded(self) -> None:
        evidence = self.contract["evidence_sources"]
        self.assertFalse(evidence["operator_assertion"]["proves_current_reachability"])
        self.assertEqual("heartbeat_window", evidence["authenticated_heartbeat"]["freshness"])

    def test_directory_parity_review_records_implemented_semantics(self) -> None:
        review = self.contract["implementation_review"]
        self.assertEqual("implemented_pending_release_evidence", review["parity_status"])
        self.assertEqual([], review["confirmed_rust_gaps"])
        self.assertIn("dormant_reactivation", review["rust_directory"])
        self.assertIn("confirmed_route_demotion_and_restore", review["rust_directory"])

    def test_no_phase_8_or_wire_claim(self) -> None:
        self.assertFalse(self.contract["wire_change"])
        claims = set(self.contract["explicit_non_claims"])
        self.assertIn("no_dtn_or_bpv7_support", claims)
        self.assertIn("no_default_discovery_expansion", claims)


if __name__ == "__main__":
    unittest.main()
