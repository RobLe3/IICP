#!/usr/bin/env python3
"""Validate the portable managed-operator policy vectors."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/managed-operator-v1.json"


def evaluate(value: dict) -> dict:
    mode = value.get("mode", "convenience")
    if mode == "convenience":
        return {"accepted": True, "reason": "convenience_mode"}
    if mode != "managed":
        return {"accepted": False, "reason": "invalid_operator_profile"}
    checks = (
        (not value.get("authentication_configured"), "authentication_required"),
        (not value.get("identity_storage_protected"), "protected_identity_storage_required"),
        (value.get("auto_update_requested") and not value.get("update_authenticated"), "authenticated_update_required"),
        (value.get("auto_update_requested") and not value.get("rollback_verified"), "rollback_required"),
        (value.get("upnp_requested") and not value.get("upnp_approved"), "upnp_approval_required"),
        (value.get("tunnel_requested") and not value.get("tunnel_approved"), "tunnel_approval_required"),
    )
    for failed, reason in checks:
        if failed:
            return {"accepted": False, "reason": reason}
    return {"accepted": True, "reason": "managed_requirements_met"}


class ManagedOperatorFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text())

    def test_fixture_identity(self) -> None:
        self.assertEqual(self.fixture["profile"], "urn:iicp:profile:managed-operator:v1")
        self.assertEqual(self.fixture["status"], "pre-normative")

    def test_vectors(self) -> None:
        for vector in self.fixture["vectors"]:
            with self.subTest(vector=vector["name"]):
                self.assertEqual(evaluate(vector["input"]), vector["expected"])


if __name__ == "__main__":
    unittest.main()
