#!/usr/bin/env python3
"""Audit a published official MCP TypeScript SDK without changing IICP defaults.

This deliberately records the SDK's declared wire revisions instead of assuming
that an MCP documentation page and a released SDK move in lockstep.  It does
not publish packages, contact a running MCP endpoint, or treat project-run
results as independent interoperability evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

PACKAGE = "@modelcontextprotocol/sdk"
DEFAULT_VERSION = "1.30.0"
IICP_LEGACY = "2025-11-25"
IICP_MODERN = "2026-07-28"
TYPES_PATH = "package/dist/esm/types.js"


def supported_versions(types_source: str) -> list[str]:
    """Return the SDK's declared JSON-RPC protocol revisions."""
    latest = re.search(r"LATEST_PROTOCOL_VERSION\s*=\s*['\"]([^'\"]+)['\"]", types_source)
    match = re.search(r"SUPPORTED_PROTOCOL_VERSIONS\s*=\s*\[([^\]]*)\]", types_source)
    if not latest or not match:
        raise ValueError("official SDK does not expose its supported protocol versions")
    versions = re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))
    if "LATEST_PROTOCOL_VERSION" in match.group(1):
        versions.insert(0, latest.group(1))
    return versions


def inspect_tarball(tarball: Path) -> list[str]:
    with tarfile.open(tarball, "r:gz") as archive:
        member = archive.getmember(TYPES_PATH)
        source = archive.extractfile(member)
        if source is None:
            raise ValueError(f"official SDK tarball lacks {TYPES_PATH}")
        return supported_versions(source.read().decode("utf-8"))


def npm_pack(package: str, version: str, directory: Path) -> Path:
    completed = subprocess.run(
        ["npm", "pack", f"{package}@{version}", "--json"],
        cwd=directory,
        check=True,
        capture_output=True,
        text=True,
    )
    records = json.loads(completed.stdout)
    if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
        raise ValueError("npm pack did not return exactly one package record")
    filename = records[0].get("filename")
    if not isinstance(filename, str) or not filename:
        raise ValueError("npm pack result lacks tarball filename")
    tarball = directory / filename
    if not tarball.is_file():
        raise ValueError("npm pack did not create the declared tarball")
    return tarball


def report(package: str, version: str, versions: list[str]) -> dict[str, Any]:
    return {
        "status": "passed",
        "evidence_class": "project_verified_external_sdk_metadata",
        "package": package,
        "package_version": version,
        "declared_protocol_versions": versions,
        "iicp_revision_support": {
            IICP_LEGACY: "supported" if IICP_LEGACY in versions else "not_supported_by_sdk",
            IICP_MODERN: "supported" if IICP_MODERN in versions else "not_supported_by_sdk",
        },
        "interpretation": (
            "This checks the released SDK tarball only. It does not prove endpoint interoperability, "
            "authorization compliance, independent implementation, or a change to IICP's default profile."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", default=PACKAGE)
    parser.add_argument("--version", default=DEFAULT_VERSION)
    args = parser.parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix="iicp-mcp-sdk-audit-") as temporary:
            versions = inspect_tarball(npm_pack(args.package, args.version, Path(temporary)))
        print(json.dumps(report(args.package, args.version, versions), sort_keys=True))
    except (OSError, subprocess.CalledProcessError, ValueError, json.JSONDecodeError, tarfile.TarError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
