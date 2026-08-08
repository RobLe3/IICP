#!/usr/bin/env python3
"""Validate the canonical intent registry with Draft 2020-12 jsonschema."""
from __future__ import annotations
import json
from pathlib import Path
import sys
try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise SystemExit("jsonschema>=4.23,<5 is required; install tools/requirements.txt") from exc
ROOT = Path(__file__).resolve().parents[1]
schema = json.loads((ROOT / "registry/schemas/intent-registry-v1.4.json").read_text())
document = json.loads((ROOT / "registry/intents.json").read_text())
errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document), key=str)
if errors:
    for error in errors:
        location = "/".join(str(part) for part in error.absolute_path) or "registry"
        print(f"schema {location}: {error.message}", file=sys.stderr)
    raise SystemExit(1)
print("intent registry Draft 2020-12 validation passed")
