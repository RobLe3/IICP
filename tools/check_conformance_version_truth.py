#!/usr/bin/env python3
"""Verify conformance-suite version authority and bundled profile metadata."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = ROOT / "spec/v1.9/conformance-test-suite.md"
FIXTURE_DIR = ROOT / "conformance-runner/src/iicp_conformance/fixtures"


def check_fixture(path: Path, fixture: dict[str, object], versions: list[str], header_version: str) -> list[str]:
    """Validate released-suite authority or an explicit pre-normative classification."""
    errors: list[str] = []
    suite_version = fixture.get("suite_version")
    status = fixture.get("status")
    profile = fixture.get("profile", path.stem)
    pre_normative = isinstance(status, str) and status.startswith("pre-normative")
    if pre_normative:
        if suite_version is not None:
            errors.append(f"{path.name}: pre-normative fixture must not claim suite_version")
        return errors
    if not isinstance(suite_version, str):
        errors.append(f"{path.name}: missing suite_version or explicit pre-normative status")
        return errors
    if suite_version not in versions:
        errors.append(f"{path.name}: suite version {suite_version} is absent from the changelog")
    if profile == "directory-lifecycle-v1" and suite_version != header_version:
        errors.append(f"{path.name}: current lifecycle profile must use suite {header_version}")
    return errors


def check() -> list[str]:
    text = SUITE_PATH.read_text(encoding="utf-8")
    errors: list[str] = []

    header = re.search(r"^\*\*Version\*\*:\s*([0-9]+(?:\.[0-9]+){2})\s*$", text, re.MULTILINE)
    if header is None:
        return ["conformance suite has no parseable Version header"]
    header_version = header.group(1)

    headings = list(re.finditer(r"^##\s+(?:11\.\s+)?Changelog\s*$", text, re.MULTILINE))
    if len(headings) != 1:
        errors.append(f"expected one conformance changelog, found {len(headings)}")
        return errors

    changelog = text[headings[0].end():]
    versions = re.findall(
        r"^\|\s*([0-9]+(?:\.[0-9]+){2})\s*\|",
        changelog,
        re.MULTILINE,
    )
    if not versions:
        errors.append("conformance changelog has no version entries")
        return errors
    current_series = [version for version in versions if tuple(map(int, version.split("."))) >= (4, 45, 0)]
    if len(current_series) != len(set(current_series)):
        errors.append("current conformance changelog contains duplicate version entries")
    if versions[0] != header_version:
        errors.append(
            f"suite header {header_version} differs from latest changelog entry {versions[0]}"
        )

    for path in sorted(FIXTURE_DIR.glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        errors.extend(check_fixture(path, fixture, versions, header_version))

    return errors


def main() -> int:
    errors = check()
    if errors:
        print("conformance version truth check failed:", *errors, sep="\n- ", file=sys.stderr)
        return 1
    print("conformance version truth check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
