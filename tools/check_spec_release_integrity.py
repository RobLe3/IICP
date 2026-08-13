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
    from check_intent_registry import validate as validate_intent_registry
    errors.extend(f"intent registry: {error}" for error in validate_intent_registry(registry))
    ecosystem = json.loads((ROOT / "ecosystem/repositories.json").read_text())
    specification = next(
        (item for item in ecosystem["repositories"] if item["id"] == "specification"),
        None,
    )
    if specification is None or specification.get("release") != manifest["protocol_suite_version"]:
        errors.append("ecosystem specification release differs from suite version")
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
        elif digest(path) != expected:
            errors.append(f"digest mismatch: {relative}")
    required = {
        "CHANGELOG.md",
        "ecosystem/repositories.json",
        "SPEC_STATUS.md",
        "VERSIONING.md",
        "registry/intents.json",
        "registry/README.md",
        "spec/v1.9/VERSION",
        "spec/v1.9/iicp-core.md",
        "spec/v1.9/iicp-framing.md",
        "spec/v1.9/conformance-test-suite.md",
        "tools/check_intent_registry.py",
        "tools/test_intent_registry.py",
        "registry/schemas/intent-registry-v1.4.json",
        "tools/requirements.txt",
        "tools/check_intent_registry_schema.py",
        "spec/v1.9/iicp-service-lifecycle-profile.md",
        "research/native-ai-infrastructure/fixtures/service-profiles-v1.json",
        "tools/test_service_lifecycle_fixture.py",
        "docs/operator-onboarding-recovery.md",
        "research/pre-normative-profiles/fixtures/operator-onboarding-recovery-v1.json",
        "tools/check_operator_onboarding_recovery.py",
        "tools/test_operator_onboarding_recovery.py",
    }
    missing_pins = sorted(required - set(manifest["files"]))
    if missing_pins:
        errors.append("required release artifacts are not pinned: " + ", ".join(missing_pins))
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
