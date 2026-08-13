#!/usr/bin/env python3
"""Validate the blank or completed newcomer validation record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "evidence/newcomer-validation-record-v1.json"
ROLES = {"non_technical_reader", "developer", "node_operator"}
OUTCOMES = {"pass", "hint", "fail"}
SCENARIOS = {
    "empty_discovery",
    "live_not_ready",
    "new_release_available",
    "evidence_rate_limited",
    "evidence_unavailable",
}


def validate(record: dict) -> list[str]:
    errors: list[str] = []
    result_present = record.get("result_present")
    if result_present not in {True, False}:
        errors.append("result_present must be boolean")
        return errors
    privacy = record.get("privacy", {})
    if not privacy or any(value is not False for value in privacy.values()):
        errors.append("participant record must exclude every forbidden data class")
    claims = record.get("claim_boundary", {})
    if not claims or any(value is not False for value in claims.values()):
        errors.append("newcomer record cannot claim certification or independence")
    if not result_present:
        if record.get("status") != "blank-participant-template":
            errors.append("an empty record must identify itself as a blank template")
        if record.get("participant_role") is not None:
            errors.append("a blank record cannot contain a participant role")
        return errors

    if record.get("consent_confirmed") is not True:
        errors.append("a completed record requires confirmed consent")
    if record.get("participant_role") not in ROLES:
        errors.append("a completed record requires one bounded participant role")
    observation = record.get("observation", {})
    if not observation.get("observed_at_utc") or not observation.get("device_class"):
        errors.append("a completed record requires UTC time and device class")
    outcomes = record.get("outcomes", {})
    if set(outcomes.values()) - OUTCOMES or None in outcomes.values():
        errors.append("all completed outcomes must be pass, hint or fail")
    if record.get("failure_scenario") not in SCENARIOS:
        errors.append("a completed record requires one bounded failure scenario")
    if record.get("participant_reviewed_summary") is not True:
        errors.append("participant must review the retained summary")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", nargs="?", type=Path, default=DEFAULT)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    errors = validate(record)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    state = "completed result" if record["result_present"] else "blank template"
    print(f"newcomer validation record valid: {state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

