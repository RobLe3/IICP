#!/usr/bin/env python3
"""Validate the offline DNS-AID import/export decision fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/dns-aid-import-export-v0.json"


def evaluate(vector: dict) -> str:
    if vector["dnssec"] == "bogus":
        return "reject_dnssec_bogus"
    if vector["require_dnssec"] and vector["dnssec"] != "secure":
        return "reject_dnssec_required"
    if not vector["mandatory_understood"]:
        return "reject_unknown_mandatory"
    if not vector["fresh"]:
        return "reject_stale"
    if vector["endpoint_policy"] != "allow":
        return "reject_endpoint_policy"
    if not vector["digest_match"]:
        return "reject_capability_digest"
    if vector["require_dane"] and vector["dane"] != "secure":
        return "reject_dane_required"
    return "candidate_untrusted_pending_iicp_eligibility"


def validate(document: dict) -> list[str]:
    errors: list[str] = []
    decision = document.get("decision", {})
    if decision != {"dns_aid": "prototype_offline_mapping", "ans": "monitor_defer", "runtime_default": False, "publication_authorized": False}:
        errors.append("decision must remain offline, non-default, and non-publishing")

    descriptor = document["export"]["descriptor"]
    record = document["export"]["candidate_record"]
    endpoint = urlparse(descriptor["endpoint_origin"])
    capability = urlparse(descriptor["capability_url"])
    if endpoint.scheme != "https" or capability.scheme != "https":
        errors.append("export endpoints must use HTTPS")
    if endpoint.username or endpoint.password or capability.username or capability.password:
        errors.append("export endpoints cannot contain user information")
    if endpoint.hostname != record["target"].rstrip("."):
        errors.append("SVCB target must match endpoint host")
    if record["type"] != "SVCB" or record["priority"] < 1 or not record["owner"].endswith(f".{descriptor['domain']}."):
        errors.append("export record must be scoped SVCB ServiceMode")
    if record["params"].get("alpn") != ["h2"]:
        errors.append("fixture must not claim an unregistered IICP or QUIC ALPN")
    if set(record["params"]["mandatory"]) != {"alpn", "port", "keyNNNNN", "keyMMMMM"}:
        errors.append("provisional metadata must remain mandatory")

    seen: set[str] = set()
    for vector in document.get("import_vectors", []):
        if vector["id"] in seen:
            errors.append("import vector ids must be unique")
        seen.add(vector["id"])
        actual = evaluate(vector)
        if actual != vector["expected"]:
            errors.append(f"{vector['id']}: expected {vector['expected']}, found {actual}")

    boundaries = document.get("boundaries", {})
    if any(boundaries.values()):
        errors.append("DNS-derived candidates cannot establish authority or carry sensitive material")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", type=Path, default=FIXTURE)
    args = parser.parse_args()
    document = json.loads(args.fixture.read_text(encoding="utf-8"))
    errors = validate(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"DNS-AID mapping valid: {len(document['import_vectors'])} vectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

