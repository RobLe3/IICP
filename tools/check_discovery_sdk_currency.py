#!/usr/bin/env python3
"""Fail when discovery SDK-currency evidence drifts from release truth."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SDK_IDS = ("client-python", "client-typescript", "client-rust")


def release_versions(root: Path) -> set[str]:
    data = json.loads((root / "ecosystem/releases.json").read_text())
    versions = {entry["version"] for entry in data["releases"] if entry["id"] in SDK_IDS}
    if len(versions) != 1:
        raise ValueError(f"coordinated SDK releases disagree: {sorted(versions)}")
    return versions


def fixture_version(root: Path) -> str:
    data = json.loads((root / "research/pre-normative-profiles/fixtures/discovery-evidence-v1.json").read_text())
    return str(data["invariants"]["sdk_latest_known_version"])


def directory_fixture_version(root: Path) -> str:
    data = json.loads((root / "parity/discovery-evidence-v1.json").read_text())
    return str(data["invariants"]["sdk_latest_known_version"])


def extracted(path: Path, pattern: str) -> str:
    match = re.search(pattern, path.read_text())
    if not match:
        raise ValueError(f"could not find SDK currency default in {path}")
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--php-directory", type=Path)
    parser.add_argument("--rust-directory", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    expected = next(iter(release_versions(root)))
    observed = {"release catalog": expected, "discovery fixture": fixture_version(root)}
    if args.php_directory:
        observed["PHP default"] = extracted(
            args.php_directory / "config/app.php",
            r"iicp_sdk_latest_known_version'\s*=>\s*env\([^,]+,\s*'([^']+)'",
        )
        observed["PHP fixture"] = directory_fixture_version(args.php_directory)
    if args.rust_directory:
        observed["Rust default"] = extracted(
            args.rust_directory / "src/discovery.rs",
            r'SDK_LATEST_KNOWN_VERSION:\s*&str\s*=\s*"([^"]+)"',
        )
        observed["Rust fixture"] = directory_fixture_version(args.rust_directory)
    drift = {name: value for name, value in observed.items() if value != expected}
    if drift:
        for name, value in drift.items():
            print(f"DRIFT: {name}={value}; expected {expected}")
        return 1
    print(f"discovery SDK currency aligned: {expected} ({', '.join(observed)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
