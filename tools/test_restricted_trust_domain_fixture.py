#!/usr/bin/env python3
"""Validate restricted trust-domain semantics and content-free fixtures."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/restricted-trust-domain-v0.json"
SCHEMA = ROOT / "research/pre-normative-profiles/schemas/restricted-trust-domain-v0.schema.json"
PROFILE = ROOT / "research/pre-normative-profiles/restricted-trust-domain-v0.md"

REASON_ORDER = (
    "invalid_input",
    "unsupported_required_profile",
    "local_only_external_forbidden",
    "public_fallback_forbidden",
    "authentication_required",
    "replay_detected",
    "membership_missing",
    "membership_expired",
    "membership_revoked",
    "wrong_trust_domain",
    "federation_untrusted",
    "federation_scope_denied",
    "policy_denied",
    "route_authorization_required",
    "allowed",
)


def evaluate(value: dict) -> dict:
    """Apply the portable first-match admission semantics."""

    mode = value.get("mode")
    operation = value.get("operation")
    external = value.get("external_network", True)
    profile_support = value.get("profile_support", "supported")

    if mode not in {"public", "private", "federated_private", "local_only", "custom"}:
        reason = "invalid_input"
    elif profile_support == "unknown_required" or (
        profile_support == "unknown_optional" and mode != "public"
    ):
        reason = "unsupported_required_profile"
    elif mode == "local_only" and external:
        reason = "local_only_external_forbidden"
    elif mode in {"private", "federated_private", "local_only"} and value.get("public_fallback", False):
        reason = "public_fallback_forbidden"
    elif mode == "public":
        reason = "allowed"
    elif not value.get("authenticated", False):
        reason = "authentication_required"
    elif value.get("replayed", False):
        reason = "replay_detected"
    elif value.get("membership", "missing") == "missing":
        reason = "membership_missing"
    elif value["membership"] == "expired":
        reason = "membership_expired"
    elif value["membership"] == "revoked":
        reason = "membership_revoked"
    elif value["membership"] == "wrong_domain":
        reason = "wrong_trust_domain"
    elif operation == "federation" and not value.get("federation_trusted", False):
        reason = "federation_untrusted"
    elif operation == "federation" and not value.get("federation_scope_allowed", False):
        reason = "federation_scope_denied"
    elif not value.get("policy_allowed", False):
        reason = "policy_denied"
    elif operation in {"relay", "execution", "cip", "federation"} and not value.get(
        "route_authorized", False
    ):
        reason = "route_authorization_required"
    else:
        reason = "allowed"

    allowed = reason == "allowed"
    return {
        "decision": "allow" if allowed else "deny",
        "reason": reason,
        "network_activity_permitted": allowed and external,
    }


class RestrictedTrustDomainFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.schema = json.loads(SCHEMA.read_text())
        cls.profile = PROFILE.read_text()

    def test_schema_and_identity(self) -> None:
        jsonschema.Draft202012Validator.check_schema(self.schema)
        jsonschema.validate(self.fixture, self.schema)
        self.assertEqual("0.1.0-draft", self.fixture["fixture_version"])
        self.assertEqual("pre-normative", self.fixture["status"])
        self.assertEqual("urn:iicp:profile:restricted-trust-domain:v1", self.fixture["profile"])

    def test_reason_order_is_stable_and_documented(self) -> None:
        self.assertEqual(REASON_ORDER, tuple(self.fixture["reason_order"]))
        for index, reason in enumerate(REASON_ORDER, start=1):
            self.assertIn(f"{index}. `{reason}`", self.profile)

    def test_every_base_case_has_allow_and_deny_evidence(self) -> None:
        by_case: dict[str, set[str]] = {}
        for vector in self.fixture["vectors"]:
            by_case.setdefault(vector["case"], set()).add(vector["expected"]["decision"])
        self.assertEqual({f"CUG-{number:02d}" for number in range(1, 11)}, set(by_case))
        for case, decisions in by_case.items():
            with self.subTest(case=case):
                self.assertEqual({"allow", "deny"}, decisions)

    def test_vectors_follow_first_match_semantics(self) -> None:
        for vector in self.fixture["vectors"]:
            with self.subTest(vector=vector["id"]):
                self.assertEqual(vector["expected"], evaluate(vector["input"]))

    def test_required_adversarial_coverage(self) -> None:
        reasons = {vector["expected"]["reason"] for vector in self.fixture["vectors"]}
        self.assertTrue(
            {
                "invalid_input",
                "unsupported_required_profile",
                "public_fallback_forbidden",
                "authentication_required",
                "replay_detected",
                "membership_missing",
                "membership_expired",
                "membership_revoked",
                "wrong_trust_domain",
                "federation_untrusted",
                "federation_scope_denied",
                "policy_denied",
                "route_authorization_required",
            }.issubset(reasons)
        )
        self.assertTrue(any(v["input"].get("after_restart") for v in self.fixture["vectors"]))
        self.assertTrue(any(v["input"].get("cached_authority") for v in self.fixture["vectors"]))

    def test_fixture_contains_no_secrets_payloads_or_concrete_topology(self) -> None:
        forbidden_keys = {
            "token",
            "credential",
            "secret",
            "private_key",
            "payload",
            "prompt",
            "response",
            "node_id",
            "client_id",
            "endpoint",
            "hostname",
            "ip_address",
        }
        forbidden_value = re.compile(r"https?://|(?:^|\s)(?:\d{1,3}\.){3}\d{1,3}(?:$|\s)")

        def walk(value: object) -> None:
            if isinstance(value, dict):
                self.assertTrue(forbidden_keys.isdisjoint(value))
                for nested in value.values():
                    walk(nested)
            elif isinstance(value, list):
                for nested in value:
                    walk(nested)
            elif isinstance(value, str):
                self.assertIsNone(forbidden_value.search(value))

        walk(self.fixture)


if __name__ == "__main__":
    unittest.main()
