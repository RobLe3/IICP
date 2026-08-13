#!/usr/bin/env python3
"""Validate a blank or externally completed clean-room evidence record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "evidence/clean-room-interoperability-record-v1.json"
PROFILES = {
    "directory-public-v1",
    "directory-lifecycle-v1",
    "directory-dispatch-v1",
}


def validate(record: dict) -> list[str]:
    errors: list[str] = []
    present = record.get("result_present")
    if present not in {True, False}:
        return ["result_present must be boolean"]
    for field in ("source_boundary", "privacy", "claim_boundary"):
        values = record.get(field, {})
        if not values or any(value is not False for value in values.values()):
            errors.append(f"{field} must retain every fail-closed boundary")
    profiles = record.get("profiles", [])
    ids = [profile.get("id") for profile in profiles]
    if set(ids) != PROFILES or len(ids) != len(set(ids)):
        errors.append("record must contain the three unique pinned profiles")
    if not present:
        if record.get("status") != "blank-external-implementer-template":
            errors.append("empty record must identify itself as a blank template")
        return errors

    implementation = record.get("implementation", {})
    for field in ("repository", "commit", "license", "language_runtime"):
        if not implementation.get(field):
            errors.append(f"completed record requires implementation {field}")
    for field in ("authors_independent_of_iicp", "operator_independent_of_iicp"):
        if implementation.get(field) is not True:
            errors.append(f"independent evidence requires {field}")
    fixed = record.get("fixed_inputs", {})
    for field in ("protocol_archive_sha256", "openapi_sha256", "runner_wheel_sha256"):
        if not fixed.get(field):
            errors.append(f"completed record requires {field}")
    for profile in profiles:
        if profile.get("positive_pass") is not True or profile.get("negative_pass") is not True:
            errors.append(f"{profile.get('id')}: positive and negative cases must pass")
        if not profile.get("signed_bundle_reference"):
            errors.append(f"{profile.get('id')}: signed bundle reference required")
    matrix = record.get("compatibility_matrix", [])
    if not matrix or not {item.get("case_type") for item in matrix} >= {"positive", "negative"}:
        errors.append("compatibility matrix requires positive and negative cases")
    for ambiguity in record.get("ambiguities", []):
        if not all(ambiguity.get(field) for field in ("public_source", "interpretations", "chosen_behavior", "proposed_correction")):
            errors.append("every ambiguity requires source, interpretations, behavior, and correction")
    publication = record.get("publication", {})
    if publication.get("published_by_external_implementer") is not True:
        errors.append("external implementer must publish the completed record")
    if publication.get("evidence_class") != "independent" or not publication.get("report_reference"):
        errors.append("completed clean-room record requires a published independent report")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", nargs="?", type=Path, default=DEFAULT)
    args = parser.parse_args()
    errors = validate(json.loads(args.record.read_text(encoding="utf-8")))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("clean-room interoperability record valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
