#!/usr/bin/env python3
"""Validate the implementation-backed native framing fixture manifest.

This dependency-free check validates fixture digests and the 12-byte header
layout. Optional SDK fixture paths must be byte-identical copies of the
canonical fixture; this makes copied conformance data auditable without
requiring one repository to import another at test time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "research/native-ai-infrastructure/fixtures"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--copy", action="append", default=[], type=Path,
                        help="SDK-local copy that must match native-framing-v1.json")
    args = parser.parse_args()

    fixture = FIXTURES / "native-framing-v1.json"
    manifest = json.loads((FIXTURES / "native-framing-fixture-manifest-v1.json").read_text())
    data = json.loads(fixture.read_text())
    digest = sha256(fixture)
    pinned = manifest["fixtures"][0]["sha256"]
    errors: list[str] = []

    if pinned != digest:
        errors.append(f"manifest digest mismatch: expected {pinned}, got {digest}")
    frame = data.get("frame", {})
    layout = frame.get("layout", [])
    if frame.get("header_bytes") != 12:
        errors.append("header_bytes must be 12")
    if sum(item.get("bytes", 0) for item in layout) != 12:
        errors.append("frame layout does not sum to 12 bytes")
    expected = [("magic", 0, 4), ("version", 4, 1), ("type", 5, 1),
                ("flags", 6, 1), ("reserved", 7, 1), ("payload_length", 8, 4)]
    actual = [(item.get("name"), item.get("offset"), item.get("bytes")) for item in layout]
    if actual != expected:
        errors.append(f"unexpected canonical layout: {actual!r}")
    for copy in args.copy:
        if not copy.is_file():
            errors.append(f"missing SDK fixture copy: {copy}")
        elif copy.read_bytes() != fixture.read_bytes():
            errors.append(f"SDK fixture copy differs: {copy}")

    if errors:
        print("native framing fixture check failed:", *errors, sep="\n- ", file=sys.stderr)
        return 1
    print(f"native framing fixture check passed: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
