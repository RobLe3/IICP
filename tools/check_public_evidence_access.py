#!/usr/bin/env python3
"""Validate the static public-evidence access manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "evidence/public-evidence-access-v1.json"
CLASSES = {"source-and-release", "immutable-release", "live-runtime"}


def validate(manifest: dict, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    http = manifest.get("http_contract", {})
    if set(http.get("methods", [])) != {"GET", "HEAD"}:
        errors.append("HTTP contract must require GET and HEAD")
    if http.get("credentials_required") is not False:
        errors.append("public evidence must not require credentials")
    if http.get("html_challenge_is_success") is not False:
        errors.append("HTML challenges must not count as successful evidence")

    artifacts = manifest.get("artifacts", [])
    ids = [artifact.get("id") for artifact in artifacts]
    if not ids or None in ids or len(ids) != len(set(ids)):
        errors.append("artifact ids must be unique and non-empty")

    for artifact in artifacts:
        artifact_id = artifact.get("id", "<missing>")
        artifact_class = artifact.get("class")
        if artifact_class not in CLASSES:
            errors.append(f"{artifact_id}: invalid class")
        if artifact.get("media_type") not in {"application/json", "text/markdown", "text/plain"}:
            errors.append(f"{artifact_id}: unsupported public media type")
        repository_path = artifact.get("repository_path")
        static_url = artifact.get("static_url")
        if artifact_class in {"source-and-release", "immutable-release"}:
            if not repository_path or not (root / repository_path).is_file():
                errors.append(f"{artifact_id}: static repository fallback is missing")
            if not static_url or urlparse(static_url).scheme != "https":
                errors.append(f"{artifact_id}: HTTPS static URL is missing")
            if artifact.get("fallback_equivalent") is not True:
                errors.append(f"{artifact_id}: source fallback must be equivalent")
            static_media_types = set(artifact.get("static_media_types", []))
            if not {"application/json", "text/plain"}.intersection(static_media_types):
                errors.append(f"{artifact_id}: static fallback media type is missing")
        if artifact_class == "live-runtime":
            if artifact.get("fallback_equivalent") is not False:
                errors.append(f"{artifact_id}: live fallback cannot claim equivalence")
            if artifact.get("unavailable_behavior") != "report-live-state-unavailable":
                errors.append(f"{artifact_id}: live unavailability must remain explicit")

    privacy = manifest.get("privacy", {})
    for key in (
        "task_payloads_allowed",
        "credentials_allowed",
        "private_topology_allowed",
        "raw_operator_identifiers_allowed",
    ):
        if privacy.get(key) is not False:
            errors.append(f"privacy boundary {key} must be false")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate(manifest, ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"public evidence access valid: {len(manifest['artifacts'])} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
