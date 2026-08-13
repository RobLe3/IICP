#!/usr/bin/env python3
"""Validate the blank or completed standards-governance decision record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "standards/submission-governance-decision-v1.json"
REQUIRED_GATES = {"security-review", "independent-interoperability", "service-port-decision"}


def validate(record: dict) -> list[str]:
    errors: list[str] = []
    present = record.get("decision_present")
    if present not in {True, False}:
        return ["decision_present must be boolean"]
    privacy = record.get("privacy", {})
    if not privacy or any(value is not False for value in privacy.values()):
        errors.append("public governance record must exclude private data")
    if set(record.get("open_gates", [])) != REQUIRED_GATES:
        errors.append("technical submission gates must remain explicit")
    submission = record.get("submission", {})
    if submission.get("explicit_maintainer_authorization_required") is not True:
        errors.append("submission must require a separate maintainer authorization")
    if submission.get("authorized_now") is not False:
        errors.append("this governance record cannot authorize submission")
    change = record.get("change_control", {})
    if change.get("implementation_behavior_is_normative") is not False:
        errors.append("implementation behavior cannot become normative authority")
    succession = record.get("succession", {})
    if succession.get("backup_may_unilaterally_redefine_protocol") is not False:
        errors.append("backup cannot unilaterally redefine the protocol")
    if not present:
        if record.get("status") != "blank-maintainer-decision-template":
            errors.append("empty decision must identify itself as a blank template")
        return errors

    if not record.get("decided_at"):
        errors.append("completed record requires decision date")
    for role in ("lead_editor", "backup_editor"):
        entry = record.get(role, {})
        if not entry.get("public_name") or not entry.get("public_contact"):
            errors.append(f"completed record requires {role} name and contact")
        if entry.get("publication_consent") is not True:
            errors.append(f"completed record requires {role} publication consent")
    if record.get("backup_editor", {}).get("maintenance_consent") is not True:
        errors.append("backup editor must consent to maintenance responsibility")
    for field in ("controller", "public_issue_process", "errata_process"):
        if not change.get(field):
            errors.append(f"completed record requires change_control {field}")
    for field in ("copyright_treatment", "ipr_treatment", "contributor_consent_record"):
        if not record.get("contributions", {}).get(field):
            errors.append(f"completed record requires contributions {field}")
    for field in ("temporary_unavailability_process", "permanent_succession_process"):
        if not succession.get(field):
            errors.append(f"completed record requires succession {field}")
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
    print("submission-governance decision valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
