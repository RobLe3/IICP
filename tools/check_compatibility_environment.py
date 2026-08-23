#!/usr/bin/env python3
"""Validate an IICP compatibility environment and its local artifact closure."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/compatibility-environment-v1.json"
CATALOG = ROOT / "evidence/compatibility-environment-v1.10.16.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_entries(value: object):
    if isinstance(value, dict):
        if set(("reference", "sha256")) <= value.keys():
            yield value
        for child in value.values():
            yield from artifact_entries(child)
    elif isinstance(value, list):
        for child in value:
            yield from artifact_entries(child)


def validate(catalog: dict) -> list[str]:
    schema = json.loads(SCHEMA.read_text())
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(catalog)]
    for artifact in artifact_entries(catalog):
        reference = artifact["reference"]
        if "://" in reference:
            errors.append(f"mutable or remote artifact reference is not allowed: {reference}")
            continue
        path = ROOT / reference
        if not path.is_file():
            errors.append(f"missing artifact: {reference}")
        elif sha256(path) != artifact["sha256"]:
            errors.append(f"digest mismatch: {reference}")
    manifest = catalog["protocol_release"]["integrity_manifest"]
    if not (ROOT / manifest).is_file():
        errors.append(f"missing integrity manifest: {manifest}")
    return errors


def main() -> int:
    errors = validate(json.loads(CATALOG.read_text()))
    if errors:
        print("compatibility environment check failed:", *errors, sep="\n- ", file=sys.stderr)
        return 1
    print("compatibility environment check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
