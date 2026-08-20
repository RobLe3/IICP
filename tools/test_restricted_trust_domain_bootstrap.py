#!/usr/bin/env python3
"""Validate the restricted bootstrap projection and its fail-closed boundaries."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import jsonschema

from test_restricted_trust_domain_membership import verify

ROOT = Path(__file__).resolve().parents[1]
PROFILE_ROOT = ROOT / "research/pre-normative-profiles"
FIXTURE = PROFILE_ROOT / "fixtures/restricted-trust-domain-bootstrap-v0.json"
SCHEMA = PROFILE_ROOT / "schemas/restricted-trust-domain-bootstrap-v0.schema.json"
MEMBERSHIP_FIXTURE = PROFILE_ROOT / "fixtures/restricted-trust-domain-membership-v0.json"
PROFILE = PROFILE_ROOT / "restricted-trust-domain-membership-v0.md"


class RestrictedTrustDomainBootstrapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.schema = json.loads(SCHEMA.read_text())
        membership = json.loads(MEMBERSHIP_FIXTURE.read_text())
        cls.authority_key = membership["authority_public_key_ed25519"]
        cls.memberships = {vector["id"]: vector for vector in membership["vectors"]}

    def test_schema(self) -> None:
        jsonschema.Draft202012Validator.check_schema(self.schema)
        jsonschema.validate(self.fixture, self.schema)

    def test_vectors(self) -> None:
        for vector in self.fixture["vectors"]:
            admitted: list[str] = []
            reason = "public_legacy" if vector["mode"] == "public" else "membership_missing"
            for peer in vector["response"]["peers"]:
                if vector["mode"] == "public":
                    admitted.append(peer["node_id"])
                    continue
                membership_id = peer.get("membership_vector")
                if not membership_id:
                    continue
                envelope = self.memberships[membership_id]["envelope"]
                assertion = envelope["assertion"]
                signature_valid = verify(self.authority_key, envelope["signature"]["value"], b"IICP-RTD-MEMBERSHIP-V0\n", assertion)
                if assertion["subject"]["id"] != peer["node_id"]:
                    reason = "subject_mismatch"
                elif vector["now"] > assertion["expires_at"]:
                    reason = "expired"
                elif assertion["generation"] < vector["minimum_generation"]:
                    reason = "generation_stale"
                elif signature_valid and ({"peers", "bootstrap"} & set(assertion["scopes"])):
                    admitted.append(peer["node_id"])
                    reason = "valid"
            if not vector["response"]["peers"] and vector.get("previously_admitted"):
                reason = "partial_absence_is_not_revocation"
            with self.subTest(vector=vector["id"]):
                self.assertEqual(vector["expected"]["admitted"], admitted)
                self.assertEqual(vector["expected"]["reason"], reason)
                self.assertEqual([], vector["expected"]["evicted"])

    def test_profile_states_non_eviction_boundary(self) -> None:
        profile = PROFILE.read_text()
        self.assertIn("Absence from one response", profile)
        self.assertIn("MUST NOT be interpreted as revocation", profile)


if __name__ == "__main__":
    unittest.main()
