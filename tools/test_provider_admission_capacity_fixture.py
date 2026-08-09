#!/usr/bin/env python3
"""Validate portable provider admission/capacity profile vectors."""

from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/provider-admission-v1.json"
PROFILE = "urn:iicp:profile:provider-admission:v1"
ADVERTISEMENT_FIELDS = {
    "profile", "availability", "capacity_class", "supported_profiles",
    "observed_at", "valid_until", "retry_after_ms",
}
OUTCOME_FIELDS = {
    "task_id", "outcome", "accepted_until", "retry_after_ms", "capacity_class",
}


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def advertisement_result(value: dict) -> str:
    if set(value) - ADVERTISEMENT_FIELDS:
        return "reject_unknown_field"
    if value.get("profile") != PROFILE:
        return "reject_profile"
    if value.get("availability") not in {"ready", "draining", "unavailable"}:
        return "reject_availability"
    if value.get("capacity_class") not in {"limited", "standard", "high"}:
        return "reject_capacity_class"
    profiles = value.get("supported_profiles")
    if not isinstance(profiles, list) or len(profiles) > 32 or len(profiles) != len(set(profiles)):
        return "reject_profiles"
    validity = (instant(value["valid_until"]) - instant(value["observed_at"])).total_seconds()
    if validity <= 0 or validity > 300:
        return "reject_excessive_validity"
    retry = value.get("retry_after_ms")
    if value["availability"] == "unavailable" and retry is None:
        return "reject_missing_retry_after"
    if retry is not None and (not isinstance(retry, int) or not 100 <= retry <= 300000):
        return "reject_retry_after"
    return "accept"


def admission_result(value: dict, request_deadline: str) -> str:
    if set(value) - OUTCOME_FIELDS:
        return "reject_unknown_field"
    outcome = value.get("outcome")
    outcomes = {
        "accepted", "unsupported_profile", "deadline_unachievable",
        "capacity_exceeded", "temporarily_unavailable", "policy_rejected",
    }
    if outcome not in outcomes or not value.get("task_id"):
        return "reject_outcome"
    if value.get("capacity_class") not in {None, "limited", "standard", "high"}:
        return "reject_capacity_class"
    if outcome == "accepted":
        if "retry_after_ms" in value:
            return "reject_field_combination"
        if "accepted_until" not in value or instant(value["accepted_until"]) > instant(request_deadline):
            return "reject_deadline"
    else:
        if "accepted_until" in value:
            return "reject_field_combination"
    if outcome in {"capacity_exceeded", "temporarily_unavailable"} and "retry_after_ms" not in value:
        return "reject_missing_retry_after"
    if outcome not in {"capacity_exceeded", "temporarily_unavailable"} and "retry_after_ms" in value:
        return "reject_field_combination"
    retry = value.get("retry_after_ms")
    if retry is not None and (not isinstance(retry, int) or not 100 <= retry <= 300000):
        return "reject_retry_after"
    return "accept"


class ProviderAdmissionCapacityFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text())

    def test_identity(self) -> None:
        self.assertEqual(self.fixture["profile"], PROFILE)
        self.assertEqual(self.fixture["status"], "pre-normative")

    def test_advertisements(self) -> None:
        for vector in self.fixture["advertisement_vectors"]:
            with self.subTest(vector=vector["name"]):
                self.assertEqual(advertisement_result(vector["advertisement"]), vector["expected"])

    def test_admission_outcomes(self) -> None:
        for vector in self.fixture["admission_vectors"]:
            with self.subTest(vector=vector["name"]):
                self.assertEqual(
                    admission_result(vector["outcome"], vector["request_deadline"]),
                    vector["expected"],
                )


if __name__ == "__main__":
    unittest.main()
