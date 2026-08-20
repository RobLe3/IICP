#!/usr/bin/env python3
"""Validate the restricted trust-domain signed-membership binding."""

from __future__ import annotations

import base64
import hashlib
import json
import unittest
from pathlib import Path

import jsonschema
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/restricted-trust-domain-membership-v0.json"
SCHEMA = ROOT / "research/pre-normative-profiles/schemas/restricted-trust-domain-membership-v0.schema.json"
PROFILE = ROOT / "research/pre-normative-profiles/restricted-trust-domain-membership-v0.md"


def decode_base64url(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def canonical_json(value: dict) -> bytes:
    """Return the RFC 8785 representation needed by these integer-only vectors."""

    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def verify(public_key: str, signature: str, domain: bytes, value: dict) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(decode_base64url(public_key)).verify(
            decode_base64url(signature), domain + canonical_json(value)
        )
        return True
    except InvalidSignature:
        return False


class RestrictedTrustDomainMembershipTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.schema = json.loads(SCHEMA.read_text())
        cls.profile = PROFILE.read_text()

    def test_schema_and_binding_identity(self) -> None:
        jsonschema.Draft202012Validator.check_schema(self.schema)
        jsonschema.validate(self.fixture, self.schema)
        self.assertEqual("0.1.0-draft", self.fixture["fixture_version"])
        self.assertEqual("pre-normative", self.fixture["status"])
        self.assertEqual("RFC8785-JCS", self.fixture["canonicalization"])

    def test_authority_signature_vectors(self) -> None:
        authority_key = self.fixture["authority_public_key_ed25519"]
        for vector in self.fixture["vectors"]:
            envelope = vector["envelope"]
            valid = verify(
                authority_key,
                envelope["signature"]["value"],
                b"IICP-RTD-MEMBERSHIP-V0\n",
                envelope["assertion"],
            )
            with self.subTest(vector=vector["id"]):
                self.assertEqual(vector["expected"] == "valid", valid)

    def test_gossip_signature_digest_and_replay_vectors(self) -> None:
        authority_key = self.fixture["authority_public_key_ed25519"]
        seen: set[str] = set()
        for vector in self.fixture["gossip_vectors"]:
            assertion = vector["membership"]["assertion"]
            membership_valid = verify(
                authority_key,
                vector["membership"]["signature"]["value"],
                b"IICP-RTD-MEMBERSHIP-V0\n",
                assertion,
            )
            proof = vector["gossip"]["proof"]
            digest_valid = hashlib.sha256(vector["payload_utf8"].encode()).hexdigest() == proof[
                "payload_sha256"
            ]
            sender_valid = verify(
                assertion["subject"]["public_key_ed25519"],
                vector["gossip"]["signature"]["value"],
                b"IICP-RTD-GOSSIP-V0\n",
                proof,
            )
            replayed = proof["replay_id"] in set(vector.get("seen_replay_ids", [])) | seen
            result = "replay_detected" if replayed else "valid"
            with self.subTest(vector=vector["id"]):
                self.assertTrue(membership_valid)
                self.assertTrue(digest_valid)
                self.assertTrue(sender_valid)
                self.assertEqual(vector["expected"], result)
            seen.add(proof["replay_id"])

    def test_assertion_is_bounded_and_scoped(self) -> None:
        assertion = self.fixture["vectors"][0]["envelope"]["assertion"]
        self.assertLess(assertion["issued_at"], assertion["expires_at"])
        self.assertGreater(assertion["generation"], 0)
        self.assertIn(assertion["domain_id"], assertion["audience"])
        self.assertIn("peers", assertion["scopes"])
        self.assertEqual(assertion["subject"]["id"], self.fixture["gossip_vectors"][0]["gossip"]["proof"]["sender_id"])

    def test_binding_keeps_bearer_credentials_out_of_peer_artifacts(self) -> None:
        serialized = json.dumps(self.fixture).lower()
        for forbidden in ("iicp_mem_", "bearer ", "private_key", "client_secret"):
            self.assertNotIn(forbidden, serialized)
        self.assertIn("MUST NOT appear in discovery, bootstrap, gossip or portable configuration", self.profile)
        self.assertIn("Public mode is unchanged", self.profile)


if __name__ == "__main__":
    unittest.main()
