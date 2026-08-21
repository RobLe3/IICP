#!/usr/bin/env python3
"""Validate the additive published/deployed/adopted version-truth projection."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "ecosystem-version-truth-v1.json"
SAMPLES = ROOT / "schemas" / "samples"

def validate(document: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [error.message for error in sorted(validator.iter_errors(document), key=lambda item: list(item.path))]
    for axis in ("published_release", "deployed_release", "observed_adoption"):
        observation = document.get(axis, {})
        status = observation.get("status")
        if status == "unavailable":
            if observation.get("data") is not None:
                errors.append(f"{axis}: unavailable observations must have null data")
            if observation.get("observed_at") is not None:
                errors.append(f"{axis}: unavailable observations must have null observed_at")
        elif status in {"observed", "stale"}:
            if observation.get("data") is None:
                errors.append(f"{axis}: {status} observations require data")
            if not observation.get("observed_at"):
                errors.append(f"{axis}: {status} observations require observed_at")
            if not observation.get("evidence"):
                errors.append(f"{axis}: {status} observations require evidence")
        if status == "stale" and not observation.get("limitations"):
            errors.append(f"{axis}: stale observations require a limitation")
    adoption = document.get("observed_adoption", {})
    if adoption.get("status") in {"observed", "stale"} and isinstance(adoption.get("data"), dict):
        data = adoption["data"]
        if sum(group.get("count", 0) for group in data.get("groups", [])) != data.get("sample_size"):
            errors.append("observed_adoption: group counts must equal sample_size")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or sorted(SAMPLES.glob("ecosystem-version-truth-*.json"))
    failed = False
    for path in paths:
        errors = validate(json.loads(path.read_text(encoding="utf-8")))
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {path}")
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
