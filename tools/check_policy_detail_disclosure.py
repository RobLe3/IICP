#!/usr/bin/env python3
"""Validate the pre-normative authenticated policy-detail boundary."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "research/pre-normative-profiles/fixtures/policy-detail-disclosure-authority-v0.json"
)


def main() -> int:
    fixture = json.loads(FIXTURE.read_text())
    if fixture["status"] != "pre-normative":
        raise SystemExit("policy-detail fixture must remain pre-normative")
    if fixture["fixture_version"] != "0.2.0-draft":
        raise SystemExit("unexpected policy-detail fixture version")

    outcomes = {
        (case["expected"]["status"], case["expected"]["reason"])
        for case in fixture["cases"]
    }
    required = {
        (200, "compatible"),
        (401, "consumer_auth_required"),
        (401, "consumer_auth_invalid"),
        (401, "consumer_auth_expired"),
        (401, "consumer_auth_revoked"),
        (401, "dispatch_ticket_invalid"),
        (401, "dispatch_ticket_expired"),
        (401, "dispatch_ticket_revoked"),
        (403, "disclosure_forbidden"),
        (404, "resource_concealed"),
    }
    missing = required - outcomes
    if missing:
        raise SystemExit(f"missing policy-detail outcomes: {sorted(missing)}")

    forbidden = {
        "prompt",
        "response",
        "credential",
        "endpoint",
        "natural_person_contact",
        "backend_topology",
    }
    leaked = forbidden.intersection(fixture["allowed_detail_fields"])
    if leaked:
        raise SystemExit(f"unsafe allowed detail fields: {sorted(leaked)}")

    precedence = fixture["reason_precedence"]
    if precedence.index("dispatch_ticket_revoked") > precedence.index(
        "disclosure_forbidden"
    ):
        raise SystemExit("ticket authorization must precede disclosure permission")

    print(f"PASS {len(fixture['cases'])} policy-detail disclosure cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
