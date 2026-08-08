#!/usr/bin/env python3
"""Validate the compatibility intent registry without external dependencies."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/intents.json"
URN = re.compile(r"^urn:iicp:intent:[a-z0-9_:/.-]+:v[1-9][0-9]*$")
STATUSES = {"active", "reserved", "deprecated"}


def validate(document: object) -> list[str]:
    if not isinstance(document, dict):
        return ["registry root must be an object"]
    errors: list[str] = []
    entries = document.get("intents")
    if not isinstance(entries, list) or not entries:
        return ["intents must be a non-empty array"]

    urns: set[str] = set()
    deprecated: list[tuple[str, str | None]] = []
    for index, entry in enumerate(entries):
        prefix = f"intents[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        urn = entry.get("urn")
        if not isinstance(urn, str) or not URN.fullmatch(urn):
            errors.append(f"{prefix}.urn is not a canonical versioned intent URN")
        elif urn in urns:
            errors.append(f"duplicate intent URN: {urn}")
        else:
            urns.add(urn)
        if not isinstance(entry.get("name"), str) or not entry["name"].strip():
            errors.append(f"{prefix}.name must be a non-empty string")
        if not isinstance(entry.get("description"), str) or not entry["description"].strip():
            errors.append(f"{prefix}.description must be a non-empty string")
        if not isinstance(entry.get("payload_schema"), dict) or not entry["payload_schema"]:
            errors.append(f"{prefix}.payload_schema must be a non-empty object")
        status = entry.get("status")
        if status not in STATUSES:
            errors.append(f"{prefix}.status must be one of {sorted(STATUSES)}")
        if status == "deprecated":
            deprecated.append((urn if isinstance(urn, str) else prefix, entry.get("deprecated_by")))

    for urn, successor in deprecated:
        if not isinstance(successor, str) or successor not in urns:
            errors.append(f"deprecated intent {urn} must name an existing deprecated_by successor")
    return errors


def main() -> int:
    errors = validate(json.loads(REGISTRY.read_text()))
    if errors:
        print("intent registry validation failed:", *errors, sep="\n- ", file=sys.stderr)
        return 1
    print("intent registry validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
