#!/usr/bin/env python3
"""Validate the dated, machine-readable protocol comparison."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "standards/protocol-comparison-v1.json"


def validate(path: Path = DATA) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "iicp.protocol-comparison.v1":
        errors.append("unexpected schema")
    dimensions = data.get("dimensions", [])
    values = set(data.get("comparison_values", []))
    entries = data.get("entries", [])
    if len(entries) < 6:
        errors.append("comparison must include at least six subjects")
    ids: set[str] = set()
    for entry in entries:
        ident = entry.get("id", "<missing>")
        if ident in ids:
            errors.append(f"duplicate id: {ident}")
        ids.add(ident)
        for field in (
            "name", "category", "version", "formal_status", "updated",
            "source", "role", "dimensions",
        ):
            if not entry.get(field):
                errors.append(f"{ident}: missing {field}")
        source = urlparse(entry.get("source", ""))
        if source.scheme != "https" or not source.netloc:
            errors.append(f"{ident}: source must be an absolute HTTPS URL")
        mapping = entry.get("dimensions", {})
        if set(mapping) != set(dimensions):
            errors.append(f"{ident}: dimension keys do not match contract")
        unknown = set(mapping.values()) - values
        if unknown:
            errors.append(f"{ident}: unknown comparison values {sorted(unknown)}")
        if "internet_draft" in entry.get("formal_status", "") and "not_ietf_endorsed" not in entry["formal_status"]:
            errors.append(f"{ident}: Internet-Draft status must deny endorsement")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("protocol comparison invalid:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS protocol comparison dataset")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

