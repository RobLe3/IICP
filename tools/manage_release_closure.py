#!/usr/bin/env python3
"""Prepare or validate the complete derived release-metadata closure."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import importlib.util
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def release_versions(root: Path) -> dict[str, str]:
    catalog = json.loads((root / "ecosystem/releases.json").read_text())
    return {entry["id"]: entry["version"] for entry in catalog["releases"]}


def sync_repository_versions(root: Path) -> None:
    versions = release_versions(root)
    path = root / "ecosystem/repositories.json"
    manifest = json.loads(path.read_text())
    for repository in manifest["repositories"]:
        if repository["id"] in versions:
            repository["release"] = versions[repository["id"]]
    write_json(path, manifest)


def sync_campaign(root: Path) -> None:
    current = json.loads((root / "ecosystem/current-versions.json").read_text())
    expected = f"iicp-client-rust {current['components']['client-rust']['release']}"
    path = root / "evidence/external-participation-campaign-v1.json"
    campaign = json.loads(path.read_text())
    lane = next(item for item in campaign["lanes"] if item["id"] == "linux-systemd-operator")
    lane["fixed_inputs"] = [
        expected if value.startswith("iicp-client-rust ") else value
        for value in lane["fixed_inputs"]
    ]
    write_json(path, campaign)


def sync_fixture_manifest(root: Path) -> None:
    directory = root / "research/pre-normative-profiles/fixtures"
    path = directory / "profile-fixture-manifest-v0.json"
    manifest = json.loads(path.read_text())
    for fixture in manifest["fixtures"]:
        fixture["sha256"] = sha256(directory / fixture["path"])
    write_json(path, manifest)


def artifact_entries(value: object):
    if isinstance(value, dict):
        if {"reference", "sha256"} <= value.keys():
            yield value
        for child in value.values():
            yield from artifact_entries(child)
    elif isinstance(value, list):
        for child in value:
            yield from artifact_entries(child)


def sync_compatibility_catalog(root: Path) -> None:
    path = root / "evidence/compatibility-environment-v1.10.16.json"
    catalog = json.loads(path.read_text())
    for artifact in artifact_entries(catalog):
        reference = artifact["reference"]
        if "://" not in reference:
            artifact["sha256"] = sha256(root / reference)
    write_json(path, catalog)


def sync_release_integrity(root: Path) -> None:
    path = root / "spec/v1.9/release-integrity-manifest.json"
    manifest = json.loads(path.read_text())
    for relative in manifest["files"]:
        manifest["files"][relative] = sha256(root / relative)
    write_json(path, manifest)


def prepare(root: Path, *, promote_published: bool = False) -> None:
    # Release notes may describe a prepared candidate before every registry has
    # accepted it.  Only an explicit post-publication action may advance the
    # public "current" projection.
    if promote_published:
        sync_repository_versions(root)
    subprocess.run([sys.executable, "tools/generate_implementations.py"], cwd=root, check=True)
    sync_campaign(root)
    sync_fixture_manifest(root)
    sync_compatibility_catalog(root)
    sync_release_integrity(root)


CHECKS = (
    ("generated ecosystem projections", "tools/generate_implementations.py", "--check"),
    ("profile fixture digests", "tools/check_profile_fixture_manifest.py"),
    ("compatibility environment", "tools/check_compatibility_environment.py"),
    ("external participation inputs", "tools/check_external_participation_campaign.py"),
    ("discovery SDK currency", "tools/check_discovery_sdk_currency.py"),
    ("release integrity", "tools/check_spec_release_integrity.py"),
)


def check(root: Path) -> list[dict[str, object]]:
    results = []
    for name, *command in CHECKS:
        invocation = [sys.executable, *command]
        if command[0] == "tools/check_compatibility_environment.py" and importlib.util.find_spec("jsonschema") is None:
            uv = shutil.which("uv")
            if uv:
                invocation = [uv, "run", "--with", "jsonschema", "python", *command]
        process = subprocess.run(invocation, cwd=root, text=True, capture_output=True)
        results.append({
            "name": name,
            "status": "pass" if process.returncode == 0 else "fail",
            "returncode": process.returncode,
            "output": (process.stdout + process.stderr).strip(),
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument(
        "--promote-published",
        action="store_true",
        help="with --prepare, advance current versions from the release catalog after registry verification",
    )
    args = parser.parse_args()
    if args.promote_published and not args.prepare:
        parser.error("--promote-published requires --prepare")
    if args.prepare:
        prepare(ROOT, promote_published=args.promote_published)
    results = check(ROOT)
    passed = all(result["status"] == "pass" for result in results)
    if args.json_output:
        print(json.dumps({"status": "pass" if passed else "fail", "checks": results}, indent=2))
    else:
        for result in results:
            print(f"[{'PASS' if result['status'] == 'pass' else 'FAIL'}] {result['name']}")
            if result["output"]:
                print(result["output"])
    if not passed and not args.prepare:
        print("Run: python3 tools/manage_release_closure.py --prepare", file=sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
