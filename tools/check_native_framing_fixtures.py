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
    if frame.get("max_payload_bytes") != 16 * 1024 * 1024:
        errors.append("max_payload_bytes must be the payload-only 16 MiB limit")
    if frame.get("length_semantics") != "payload_bytes_excluding_12_byte_header":
        errors.append("Length semantics must exclude the 12-byte header")
    if frame.get("decode_contract", {}).get("framing_version") != "exactly_1":
        errors.append("framing version contract must require exactly version 1")
    if sum(item.get("bytes", 0) for item in layout) != 12:
        errors.append("frame layout does not sum to 12 bytes")
    expected = [("magic", 0, 4), ("version", 4, 1), ("type", 5, 1),
                ("flags", 6, 1), ("reserved", 7, 1), ("payload_length", 8, 4)]
    actual = [(item.get("name"), item.get("offset"), item.get("bytes")) for item in layout]
    if actual != expected:
        errors.append(f"unexpected canonical layout: {actual!r}")
    scenarios = data.get("scenarios", [])
    names = [scenario.get("name") for scenario in scenarios]
    if len(names) != len(set(names)):
        errors.append("scenario names must be unique")
    required = {
        "unsupported_framing_version": "unsupported_version",
        "payload_length_exceeds_limit_before_body_read": "payload_too_large",
    }
    by_name = {scenario.get("name"): scenario for scenario in scenarios}
    for name, reason in required.items():
        scenario = by_name.get(name)
        if scenario is None:
            errors.append(f"missing required negative vector: {name}")
        elif scenario.get("expected", {}).get("reason") != reason:
            errors.append(f"{name}: expected reason must be {reason}")
    task_profile = data.get("stable_task_profile", {})
    if task_profile.get("accepted_message_types") != [*range(1, 11), 13, 14]:
        errors.append("stable task accepted types must be 0x01-0x0A and 0x0D-0x0E")
    if task_profile.get("conflicted_message_types") != [11, 12]:
        errors.append("stable task conflicted types must be 0x0B and 0x0C")
    if task_profile.get("production_security_disposition") != "excluded_from_stable_baseline":
        errors.append("production security disposition must remain excluded from the stable baseline")
    if task_profile.get("plaintext_scope") != "development_only":
        errors.append("plaintext native TCP must remain development-only")
    if task_profile.get("stable_claim") != "not_admitted":
        errors.append("native TCP must not be admitted to the stable claim by this fixture")
    type_scenarios = data.get("stable_task_type_scenarios", [])
    type_names = [scenario.get("name") for scenario in type_scenarios]
    if len(type_names) != len(set(type_names)):
        errors.append("stable task type scenario names must be unique")
    by_type = {scenario.get("message_type"): scenario for scenario in type_scenarios}
    required_types = {
        0: "invalid_type",
        1: None,
        5: None,
        11: "conflicted_type",
        12: "conflicted_type",
        13: None,
        15: "unknown_type",
        240: "unsupported_extension",
        255: "invalid_type",
    }
    for message_type, reason in required_types.items():
        scenario = by_type.get(message_type)
        if scenario is None:
            errors.append(f"missing stable task type vector: 0x{message_type:02x}")
            continue
        expected_result = scenario.get("expected", {})
        expected_outcome = "accept" if reason is None else "reject"
        if expected_result.get("outcome") != expected_outcome:
            errors.append(
                f"type 0x{message_type:02x}: expected outcome must be {expected_outcome}"
            )
        if expected_result.get("reason") != reason:
            errors.append(f"type 0x{message_type:02x}: expected reason must be {reason}")
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
