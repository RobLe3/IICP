#!/usr/bin/env python3
"""Generate and verify synthetic execution-privacy key-binding vectors."""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

FIXTURE_PATH = Path(__file__).with_name("vectors-v0.json")
SIGNING_DOMAIN = b"iicp:research:attestation-result:v0\n"
BINDING_DOMAIN = b"iicp:research:execution-key-binding:v0\n"
FIXTURE_SEED = bytes(range(1, 33))


def b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def unsigned_result(result: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(result)
    value.pop("signature", None)
    return value


def binding_input(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "nonce": result["nonce"],
        "execution_key": result["execution_key"],
        "runtime": result["runtime"],
    }


def binding_digest(result: dict[str, Any]) -> str:
    return hashlib.sha256(BINDING_DOMAIN + canonical(binding_input(result))).hexdigest()


def sign(result: dict[str, Any], key: Ed25519PrivateKey) -> dict[str, Any]:
    result = copy.deepcopy(result)
    result["signature"] = {
        "algorithm": "Ed25519",
        "key_id": "research-verifier-v0",
        "value": b64url(key.sign(SIGNING_DOMAIN + canonical(unsigned_result(result)))),
    }
    return result


def make_fixture() -> dict[str, Any]:
    private_key = Ed25519PrivateKey.from_private_bytes(FIXTURE_SEED)
    public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    policy = {
        "now": 1_800_000_000,
        "expected_nonce": "consumer-challenge-v0",
        "accepted_evidence_profiles": ["iicp-research-synthetic-result-v0"],
        "accepted_measurements": ["a" * 64],
        "accepted_tcb_status": ["up_to_date"],
        "required_protected_components": ["cpu", "memory", "runtime"],
    }
    base = {
        "schema_version": "iicp-research-attestation-result-v0",
        "evidence_profile": "iicp-research-synthetic-result-v0",
        "verifier_id": "https://verifier.invalid/research-v0",
        "issued_at": 1_799_999_940,
        "expires_at": 1_800_000_060,
        "nonce": policy["expected_nonce"],
        "execution_key": {
            "algorithm": "X25519",
            "encoding": "base64url",
            "key": "-LKZgrZEnFMr9ctB3uQDKsME07ZzS4Ce-SapFAePul0",
            "key_id": "cx-ephemeral-research-v0",
        },
        "runtime": {
            "measurement_sha256": "a" * 64,
            "profile_id": "iicp-confidential-worker-research-v0",
            "debug": False,
            "tcb_status": "up_to_date",
            "protected_components": ["cpu", "memory", "runtime"],
        },
    }
    base["binding_digest_sha256"] = binding_digest(base)
    scenarios: list[dict[str, Any]] = []

    def add(identifier: str, result: dict[str, Any], expected: str) -> None:
        scenarios.append(
            {
                "id": identifier,
                "result": sign(result, private_key),
                "expected": expected,
            }
        )

    add("valid", base, "PASS")
    bad_signature = sign(base, private_key)
    value = bad_signature["signature"]["value"]
    bad_signature["signature"]["value"] = value[:-1] + (
        "A" if value[-1] != "A" else "B"
    )
    scenarios.append(
        {
            "id": "bad_signature",
            "result": bad_signature,
            "expected": "SIGNATURE_INVALID",
        }
    )

    wrong_nonce = copy.deepcopy(base)
    wrong_nonce["nonce"] = "different-consumer-challenge"
    wrong_nonce["binding_digest_sha256"] = binding_digest(wrong_nonce)
    add("wrong_nonce", wrong_nonce, "NONCE_MISMATCH")

    stale = copy.deepcopy(base)
    stale["expires_at"] = policy["now"] - 1
    add("stale", stale, "EXPIRED")

    substituted = copy.deepcopy(base)
    substituted["execution_key"]["key"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    add("key_substitution", substituted, "KEY_BINDING_INVALID")

    changed_measurement = copy.deepcopy(base)
    changed_measurement["runtime"]["measurement_sha256"] = "b" * 64
    changed_measurement["binding_digest_sha256"] = binding_digest(changed_measurement)
    add("changed_measurement", changed_measurement, "MEASUREMENT_UNACCEPTED")

    debug = copy.deepcopy(base)
    debug["runtime"]["debug"] = True
    debug["binding_digest_sha256"] = binding_digest(debug)
    add("debug_enabled", debug, "DEBUG_ENABLED")

    old_tcb = copy.deepcopy(base)
    old_tcb["runtime"]["tcb_status"] = "out_of_date"
    old_tcb["binding_digest_sha256"] = binding_digest(old_tcb)
    add("unacceptable_tcb", old_tcb, "TCB_UNACCEPTED")

    incomplete = copy.deepcopy(base)
    incomplete["runtime"]["protected_components"] = ["cpu", "memory"]
    incomplete["binding_digest_sha256"] = binding_digest(incomplete)
    add("incomplete_boundary", incomplete, "BOUNDARY_INCOMPLETE")

    downgrade = copy.deepcopy(base)
    downgrade["evidence_profile"] = "ordinary-iicp-cx"
    add("ordinary_cx_downgrade", downgrade, "EVIDENCE_PROFILE_UNACCEPTED")

    return {
        "fixture_version": "execution-privacy-binding-v0",
        "evidence_class": "synthetic-research-only",
        "non_claims": [
            "not_vendor_evidence",
            "not_hardware_attestation",
            "not_proof_of_private_key_containment",
            "not_a_normative_iicp_profile",
        ],
        "verifier": {
            "algorithm": "Ed25519",
            "key_id": "research-verifier-v0",
            "public_key": b64url(public_key),
        },
        "policy": policy,
        "scenarios": scenarios,
    }


def verify_result(
    result: dict[str, Any], policy: dict[str, Any], public_key: Ed25519PublicKey
) -> str:
    signature = result.get("signature", {})
    if signature.get("algorithm") != "Ed25519":
        return "SIGNATURE_INVALID"
    try:
        public_key.verify(
            b64url_decode(signature["value"]),
            SIGNING_DOMAIN + canonical(unsigned_result(result)),
        )
    except (InvalidSignature, KeyError, TypeError, ValueError):
        return "SIGNATURE_INVALID"
    if result.get("evidence_profile") not in policy["accepted_evidence_profiles"]:
        return "EVIDENCE_PROFILE_UNACCEPTED"
    if result.get("expires_at", 0) < policy["now"]:
        return "EXPIRED"
    if result.get("issued_at", policy["now"] + 1) > policy["now"]:
        return "NOT_YET_VALID"
    if result.get("nonce") != policy["expected_nonce"]:
        return "NONCE_MISMATCH"
    if result.get("binding_digest_sha256") != binding_digest(result):
        return "KEY_BINDING_INVALID"
    runtime = result.get("runtime", {})
    if runtime.get("measurement_sha256") not in policy["accepted_measurements"]:
        return "MEASUREMENT_UNACCEPTED"
    if runtime.get("debug") is not False:
        return "DEBUG_ENABLED"
    if runtime.get("tcb_status") not in policy["accepted_tcb_status"]:
        return "TCB_UNACCEPTED"
    if not set(policy["required_protected_components"]).issubset(
        runtime.get("protected_components", [])
    ):
        return "BOUNDARY_INCOMPLETE"
    return "PASS"


def verify_fixture(fixture: dict[str, Any]) -> list[tuple[str, str, str]]:
    public_key = Ed25519PublicKey.from_public_bytes(
        b64url_decode(fixture["verifier"]["public_key"])
    )
    return [
        (
            scenario["id"],
            scenario["expected"],
            verify_result(scenario["result"], fixture["policy"], public_key),
        )
        for scenario in fixture["scenarios"]
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--check-generated", action="store_true")
    args = parser.parse_args()
    generated = make_fixture()
    encoded = json.dumps(generated, indent=2, sort_keys=True) + "\n"
    if args.generate:
        FIXTURE_PATH.write_text(encoded, encoding="utf-8")
    if args.check_generated and FIXTURE_PATH.read_text(encoding="utf-8") != encoded:
        print("FAIL fixture is not the deterministic generator output")
        return 1
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    failures = []
    for identifier, expected, actual in verify_fixture(fixture):
        print(f"{identifier}: {actual}")
        if actual != expected:
            failures.append((identifier, expected, actual))
    if failures:
        print(f"FAIL {len(failures)} scenario(s) disagreed")
        return 1
    print(f"PASS {len(fixture['scenarios'])} execution-privacy binding scenarios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
