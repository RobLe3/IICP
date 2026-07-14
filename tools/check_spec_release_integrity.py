#!/usr/bin/env python3
"""Fail-closed integrity gate for a reviewed spec-only release candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "spec/v1.9/release-integrity-manifest.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    errors: list[str] = []
    if (ROOT / "spec/v1.9/VERSION").read_text().strip() != manifest["protocol_suite_version"]:
        errors.append("suite version differs from release manifest")
    registry = json.loads((ROOT / "registry/intents.json").read_text())
    if registry.get("version") != manifest["registry_version"]:
        errors.append("registry version differs from release manifest")
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
        elif digest(path) != expected:
            errors.append(f"digest mismatch: {relative}")
    if errors:
        print("spec release integrity check failed:", *errors, sep="\n- ", file=sys.stderr)
        return 1
    print(
        "spec release integrity check passed: "
        f"suite v{manifest['protocol_suite_version']}, registry v{manifest['registry_version']}, "
        f"{len(manifest['files'])} pinned artifacts"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
