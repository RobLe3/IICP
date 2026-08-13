#!/usr/bin/env python3
"""Validate the signed-message-envelope research boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/signed-message-envelope-boundary-v0.json"
MECHANISMS = {
    "transport_authentication",
    "iicp_cx",
    "dispatch_ticket",
    "policy_manifest_signature",
    "federation_signature",
    "routing_and_task_receipts",
    "attestation_key_binding",
}
PROPERTIES = {
    "demonstrated_intermediary_integrity_gap",
    "no_existing_signature_covers_statement",
    "explicit_signer_verifier_and_purpose",
    "versioned_canonical_input_and_domain_separation",
    "bounded_freshness_replay_rotation_and_failure",
    "confidentiality_and_metadata_limits",
    "two_independent_implementations",
}


def validate(document: dict) -> list[str]:
    errors: list[str] = []
    if document.get("universal_envelope") != "rejected":
        errors.append("current research decision must reject a universal envelope")
    for field in ("wire_change", "authentication_default_change", "deployment_authorized"):
        if document.get(field) is not False:
            errors.append(f"research decision cannot set {field}")
    if set(document.get("existing_mechanisms", [])) != MECHANISMS:
        errors.append("purpose-specific mechanism inventory is incomplete")
    if set(document.get("required_future_profile_properties", [])) != PROPERTIES:
        errors.append("future profile admission properties are incomplete")
    claims = document.get("forbidden_claims", {})
    if not claims or any(value is not False for value in claims.values()):
        errors.append("forbidden envelope claims must remain false")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", type=Path, default=FIXTURE)
    args = parser.parse_args()
    errors = validate(json.loads(args.fixture.read_text(encoding="utf-8")))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("signed-message envelope boundary valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
