#!/usr/bin/env python3
"""Validate the public external-participation campaign contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "evidence/external-participation-campaign-v1.json"
LANES = {
    "clean-room-directory",
    "newcomer-validation",
    "linux-systemd-operator",
    "relay-operator",
    "qualified-eu-review",
    "standards-governance",
}
LOCAL_RECORDS = {
    "clean-room-directory": "evidence/clean-room-interoperability-record-v1.json",
    "newcomer-validation": "evidence/newcomer-validation-record-v1.json",
    "relay-operator": "evidence/relay-eligibility-record-v1.json",
    "standards-governance": "standards/submission-governance-decision-v1.json",
}


def validate(record: dict, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if record.get("schema_version") != "iicp-external-participation-campaign-v1":
        errors.append("unexpected campaign schema version")
    if record.get("status") != "open-for-participation":
        errors.append("campaign must remain open-for-participation until a reviewed update")
    boundary = record.get("claim_boundary", {})
    if not boundary or any(value is not False for value in boundary.values()):
        errors.append("campaign claim boundary must remain entirely fail-closed")
    lanes = record.get("lanes", [])
    ids = [lane.get("id") for lane in lanes]
    if set(ids) != LANES or len(ids) != len(set(ids)):
        errors.append("campaign must contain the six unique participation lanes")
    for lane in lanes:
        lane_id = lane.get("id")
        for field in ("tracker", "participant", "fixed_inputs", "record", "validator", "submission"):
            if not lane.get(field):
                errors.append(f"{lane_id}: {field} is required")
        if lane.get("state") not in {"awaiting-participant", "accepted", "declined"}:
            errors.append(f"{lane_id}: invalid campaign state")
        if lane.get("state") != "awaiting-participant":
            errors.append(f"{lane_id}: repository campaign must not infer acceptance or decline")
        if not str(lane.get("tracker", "")).startswith("https://github.com/RobLe3/"):
            errors.append(f"{lane_id}: tracker must be repository-qualified")
        local = LOCAL_RECORDS.get(lane_id)
        if local and lane.get("record") != local:
            errors.append(f"{lane_id}: record path differs from the canonical template")
        if local and not (root / local).is_file():
            errors.append(f"{lane_id}: canonical template is missing")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign", nargs="?", type=Path, default=DEFAULT)
    args = parser.parse_args()
    errors = validate(json.loads(args.campaign.read_text(encoding="utf-8")))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("external participation campaign valid: 6 awaiting-participant lanes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
