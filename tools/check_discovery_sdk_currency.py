#!/usr/bin/env python3
"""Fail when discovery SDK-currency evidence drifts from release truth."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from pathlib import Path

SDK_IDS = ("client-python", "client-typescript", "client-rust")


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key in source binding")
        result[key] = value
    return result


def source_object(root: Path, path: Path) -> dict:
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("source manifest escapes selected Directory")
    result = json.loads(path.read_text(), object_pairs_hook=unique_object)
    if not isinstance(result, dict):
        raise ValueError("source manifest must be an object")
    return result


def release_versions(root: Path) -> dict[str, str]:
    data = json.loads((root / "ecosystem/releases.json").read_text())
    versions = {entry["id"]: entry["version"] for entry in data["releases"] if entry["id"] in SDK_IDS}
    if set(versions) != set(SDK_IDS):
        raise ValueError(f"SDK release catalog is incomplete: {versions}")
    return versions


def coordinated_baseline(root: Path) -> str:
    """Return the highest release shared by every official SDK line.

    Component packages are independently versioned. A language-specific patch may
    advance one package without changing the common compatibility baseline used by
    discovery evidence.
    """
    versions = release_versions(root)
    return min(versions.values(), key=lambda version: tuple(int(part) for part in version.split(".")))


def fixture_version(root: Path) -> str:
    data = json.loads((root / "research/pre-normative-profiles/fixtures/discovery-evidence-v1.json").read_text())
    return str(data["invariants"]["sdk_latest_known_version"])


def bound_json(root: Path, parent: Path, name: str, expected: str) -> tuple[Path, dict]:
    """Read a selected source binding, never a guessed historical fallback."""
    relative = Path(name)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("fixture path must be a safe relative path")
    path = (parent / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("fixture path must resolve inside the selected Directory")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("fixture digest must be lowercase SHA-256")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("selected fixture digest mismatch")
    payload = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(payload, dict):
        raise ValueError("selected fixture must be an object")
    return path, payload


def verify_fixture_tree(root: Path, path: Path, manifest: dict, seen: set[Path]) -> None:
    fixtures = manifest.get("fixtures", {})
    if not isinstance(fixtures, dict):
        raise ValueError("fixture map must be an object")
    for name, digest in fixtures.items():
        child, payload = bound_json(root, path.parent, name, digest)
        if child not in seen:
            seen.add(child)
            verify_fixture_tree(root, child, payload, seen)


def parity_fixture(root: Path, path: Path, manifest: dict) -> tuple[Path, dict]:
    name = manifest["discovery_evidence_fixture"]
    if not isinstance(name, str) or not isinstance(manifest["fixtures"], dict):
        raise ValueError("explicit discovery fixture role is required")
    verify_fixture_tree(root, path, manifest, {path.resolve()})
    return bound_json(root, path.parent, name, manifest["fixtures"][name])


def directory_fixture_version(root: Path, flavor: str) -> str:
    if flavor == "php":
        version = (root / "VERSION").read_text().strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:\.\d+)?", version):
            raise ValueError("invalid PHP source version")
        path = root / "parity" / f"contract-v{version}.json"
        manifest = source_object(root, path)
        if manifest["contract_version"] != f"v{version}" or manifest["authority"]["runtime_version"] != f"v{version}":
            raise ValueError("PHP current parity identity differs from source version")
        _, data = parity_fixture(root, path, manifest)
    elif flavor == "rust":
        version = tomllib.loads((root / "Cargo.toml").read_text())["package"]["version"]
        if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
            raise ValueError("invalid Rust source version")
        manifest = source_object(root, root / "compatibility" / f"v{version}.json")
        if manifest["implementation"] != {"flavor": "rust", "version": version, "status": "operator_preview"}:
            raise ValueError("Rust current compatibility identity differs from source version")
        contracts = manifest["contracts"]
        parity = contracts["parity_manifest"]
        path, payload = bound_json(root, root, parity["path"], parity["sha256"])
        php_version = manifest["php_parity_baseline"]["version"]
        if not isinstance(php_version, str) or not re.fullmatch(r"\d+\.\d+\.\d+(?:\.\d+)?", php_version):
            raise ValueError("invalid declared PHP parity baseline version")
        if payload["contract_version"] != f"v{php_version}" or payload["authority"]["runtime_version"] != f"v{php_version}":
            raise ValueError("Rust nested PHP parity identity differs from declared baseline")
        nested_path, data = parity_fixture(root, path, payload)
        direct = contracts["discovery_evidence"]
        direct_path, direct_data = bound_json(root, root, direct["path"], direct["sha256"])
        if direct_path != nested_path or direct_data != data:
            raise ValueError("direct and parity discovery fixture bindings disagree")
    else:
        raise ValueError("unsupported Directory flavor")
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
    expected = coordinated_baseline(root)
    observed = {"release catalog": expected, "discovery fixture": fixture_version(root)}
    if args.php_directory:
        observed["PHP default"] = extracted(
            args.php_directory / "config/app.php",
            r"iicp_sdk_latest_known_version'\s*=>\s*env\([^,]+,\s*'([^']+)'",
        )
        observed["PHP fixture"] = directory_fixture_version(args.php_directory, "php")
    if args.rust_directory:
        observed["Rust default"] = extracted(
            args.rust_directory / "src/discovery.rs",
            r'SDK_LATEST_KNOWN_VERSION:\s*&str\s*=\s*"([^"]+)"',
        )
        observed["Rust fixture"] = directory_fixture_version(args.rust_directory, "rust")
    drift = {name: value for name, value in observed.items() if value != expected}
    if drift:
        for name, value in drift.items():
            print(f"DRIFT: {name}={value}; expected {expected}")
        return 1
    print(f"discovery SDK currency aligned: {expected} ({', '.join(observed)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
