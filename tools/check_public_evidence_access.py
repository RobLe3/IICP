#!/usr/bin/env python3
"""Validate the static public-evidence access manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "evidence/public-evidence-access-v1.json"
CLASSES = {"source-and-release", "immutable-release", "live-runtime"}
LIVE_ORIGIN = "https://iicp.network"


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


def probe_url(url: str, method: str, timeout: float) -> dict:
    request = Request(
        url,
        method=method,
        headers={"User-Agent": "IICP-Evidence-Probe/1"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            sample = response.read(256) if method == "GET" else b""
            return {
                "status": response.status,
                "media_type": response.headers.get_content_type(),
                "html_challenge": b"<html" in sample.lower(),
                "error": None,
            }
    except HTTPError as error:
        return {
            "status": error.code,
            "media_type": error.headers.get_content_type(),
            "html_challenge": False,
            "error": "http_error",
        }
    except (URLError, TimeoutError) as error:
        return {
            "status": None,
            "media_type": None,
            "html_challenge": False,
            "error": type(error).__name__,
        }


def validate_live(manifest: dict, origin: str, timeout: float) -> tuple[list[str], list[dict]]:
    errors: list[str] = []
    observations: list[dict] = []
    paths = [manifest["discovery_path"]]
    paths.extend(
        artifact["website_path"]
        for artifact in manifest["artifacts"]
        if artifact.get("website_path")
    )
    for path in dict.fromkeys(paths):
        url = f"{origin.rstrip('/')}{path}"
        for method in ("HEAD", "GET"):
            result = probe_url(url, method, timeout)
            observation = {"method": method, "url": url, **result}
            observations.append(observation)
            if result["status"] != 200:
                errors.append(f"{method} {path}: expected 200, got {result['status']}")
            if result["media_type"] != "application/json":
                errors.append(
                    f"{method} {path}: expected application/json, got {result['media_type']}"
                )
            if result["html_challenge"]:
                errors.append(f"{method} {path}: returned an HTML challenge")
    return errors, observations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--origin", default=LIVE_ORIGIN)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate(manifest, ROOT)
    observations: list[dict] = []
    if not errors and args.live:
        live_errors, observations = validate_live(manifest, args.origin, args.timeout)
        errors.extend(live_errors)
    if args.json:
        json.dump(
            {"passed": not errors, "errors": errors, "observations": observations},
            sys.stdout,
            indent=2,
        )
        print()
        return 1 if errors else 0
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    suffix = f", {len(observations)} live requests" if observations else ""
    print(
        f"public evidence access valid: {len(manifest['artifacts'])} artifacts{suffix}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
