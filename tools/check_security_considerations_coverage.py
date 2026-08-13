#!/usr/bin/env python3
"""Validate IICP security/operational topic and profile dispositions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "standards/security-considerations-coverage-v1.json"
REQUIRED_TOPICS = {
    "malicious_directory",
    "provider_plaintext",
    "relay_metadata",
    "route_harvesting",
    "authentication_replay_downgrade",
    "resource_exhaustion",
    "nat_and_exposure",
    "metadata_privacy",
    "federation_compromise",
    "operational_recovery",
}
REQUIRED_PROFILES = {"55", "56", "57", "58", "59", "60", "61", "63", "136"}


def validate(document: dict) -> list[str]:
    errors: list[str] = []
    if document.get("submission_authorized") is not False:
        errors.append("security review cannot authorize standards submission")
    if document.get("profile_promotion_authorized") is not False:
        errors.append("security review cannot promote pre-normative profiles")
    topics = document.get("topics", [])
    ids = [topic.get("id") for topic in topics]
    if set(ids) != REQUIRED_TOPICS or len(ids) != len(set(ids)):
        errors.append("security topic coverage must be complete and unique")
    if any(topic.get("status") != "documented" for topic in topics):
        errors.append("every required security topic needs a documented disposition")
    profiles = document.get("profile_dispositions", {})
    if set(profiles) != REQUIRED_PROFILES:
        errors.append("coordinated profile dispositions are incomplete")
    for issue in ("55", "56", "58"):
        if "external_evidence_required" not in profiles.get(issue, ""):
            errors.append(f"#{issue} cannot be promoted without external evidence")
    if profiles.get("57") != "research_only":
        errors.append("stateful admission must remain research only")
    if "hardware" not in profiles.get("136", ""):
        errors.append("execution privacy must retain its hardware gate")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", nargs="?", type=Path, default=MATRIX)
    args = parser.parse_args()
    document = json.loads(args.matrix.read_text(encoding="utf-8"))
    errors = validate(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"security considerations valid: {len(document['topics'])} topics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
