#!/usr/bin/env python3
"""Validate a blank or externally completed relay-eligibility record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "evidence/relay-eligibility-record-v1.json"
REQUIRED_CASES = {
    "eligible-current-evidence",
    "stale-evidence",
    "forged-evidence",
    "replayed-evidence",
    "demoted-relay",
    "overloaded-relay",
    "partial-evidence",
    "browser-override",
}


def validate(record: dict) -> list[str]:
    errors: list[str] = []
    present = record.get("result_present")
    if present not in {True, False}:
        return ["result_present must be boolean"]
    for field in ("privacy", "claim_boundary"):
        values = record.get(field, {})
        if not values or any(value is not False for value in values.values()):
            errors.append(f"{field} must retain every fail-closed boundary")
    cases = record.get("cases", [])
    ids = [case.get("id") for case in cases]
    if set(ids) != REQUIRED_CASES or len(ids) != len(set(ids)):
        errors.append("record must contain every unique relay eligibility case")
    if not present:
        if record.get("status") != "blank-external-operator-template":
            errors.append("empty record must identify itself as a blank template")
        return errors

    operator = record.get("operator", {})
    if operator.get("independent_of_iicp") is not True:
        errors.append("completed independent record requires an external operator")
    for field in ("report_reference", "environment_class"):
        if not operator.get(field):
            errors.append(f"completed record requires operator {field}")
    if not record.get("fixed_inputs", {}).get("implementation_release"):
        errors.append("completed record requires a fixed implementation release")
    for case in cases:
        if case.get("passed") is not True:
            errors.append(f"{case.get('id')}: expected behavior must pass")
    for field, value in record.get("measurements", {}).items():
        if value is not True:
            errors.append(f"measurement {field} must be explicitly true")
    publication = record.get("publication", {})
    if publication.get("published_by_external_operator") is not True:
        errors.append("external operator must publish the completed record")
    if publication.get("evidence_class") != "independent":
        errors.append("completed record must retain the independent evidence class")
    if not publication.get("signed_bundle_reference"):
        errors.append("completed record requires a signed bundle reference")
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
    print("relay eligibility record valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
