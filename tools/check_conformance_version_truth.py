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


def _fixture_classification(fixture: dict, path: Path) -> tuple[str | None, str | None]:
    """Return (classification, error) without guessing ambiguous metadata."""
    suite_version = fixture.get("suite_version")
    status = fixture.get("status")

    if isinstance(suite_version, str):
        if status is not None:
            return None, f"{path.name}: released fixture must not also declare status {status!r}"
        return "released", None

    if isinstance(status, str) and (
        status == "pre-normative" or status.startswith("pre-normative-")
    ):
        return "pre-normative", None

    if status is None:
        return None, f"{path.name}: missing suite_version and explicit pre-normative status"
    return None, f"{path.name}: unrecognized fixture status {status!r}"


def check(
    suite_path: Path = SUITE_PATH,
    fixture_dir: Path = FIXTURE_DIR,
) -> list[str]:
    text = suite_path.read_text(encoding="utf-8")
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

    for path in sorted(fixture_dir.glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        suite_version = fixture.get("suite_version")
        profile = fixture.get("profile", path.stem)
        classification, classification_error = _fixture_classification(fixture, path)
        if classification_error is not None:
            errors.append(classification_error)
            continue
        if classification == "pre-normative":
            continue
        assert classification == "released" and isinstance(suite_version, str)
        if suite_version not in versions:
            errors.append(
                f"{path.name}: suite version {suite_version} is absent from the changelog"
            )
        if profile == "directory-lifecycle-v1" and suite_version != header_version:
            errors.append(
                f"{path.name}: current lifecycle profile must use suite {header_version}"
            )

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
