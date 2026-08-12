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

FIXTURE_PATH = Path(__file__).with_name("vectors-v1.json")
SIGNING_DOMAIN = b"iicp:research:attestation-result:v1\n"
BINDING_DOMAIN = b"iicp:research:execution-key-binding:v1\n"
FIXTURE_SEED = bytes(range(1, 33))
ALTERNATE_SEED = bytes(range(33, 65))
EAT_PROFILE = "tag:iicp.network,2026:execution-privacy-attestation-result-v0"


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
        "aud": result["aud"],
        "candidate_ref": result["candidate_ref"],
        "cnf": result["cnf"],
        "eat_nonce": result["eat_nonce"],
        "route_ticket_digest_sha256": result["route_ticket_digest_sha256"],
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
    alternate_key = Ed25519PrivateKey.from_private_bytes(ALTERNATE_SEED)
    public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    policy = {
        "now": 1_800_000_000,
        "expected_nonce": "consumer-challenge-v0",
        "expected_audience": "iicp-consumer-session-v0",
        "expected_candidate_ref": "sha256:" + "c" * 64,
        "expected_route_ticket_digest_sha256": "d" * 64,
        "accepted_eat_profiles": [EAT_PROFILE],
        "accepted_measurements": ["a" * 64],
        "accepted_tcb_status": ["up_to_date"],
        "required_protected_components": ["cpu", "memory", "runtime"],
    }
    base = {
        "schema_version": "iicp-research-attestation-result-v0",
        "eat_profile": EAT_PROFILE,
        "intuse": 5,
        "iss": "https://verifier.invalid/research-v0",
        "iat": 1_799_999_940,
        "exp": 1_800_000_060,
        "eat_nonce": policy["expected_nonce"],
        "aud": policy["expected_audience"],
        "candidate_ref": policy["expected_candidate_ref"],
        "route_ticket_digest_sha256": policy["expected_route_ticket_digest_sha256"],
        "cnf": {
            "COSE_Key": {
                "kty": "OKP",
                "crv": "X25519",
                "x": "-LKZgrZEnFMr9ctB3uQDKsME07ZzS4Ce-SapFAePul0",
                "kid": "cx-ephemeral-research-v0",
            }
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

    wrong_root = sign(base, alternate_key)
    scenarios.append(
        {
            "id": "wrong_trust_root",
            "result": wrong_root,
            "expected": "SIGNATURE_INVALID",
        }
    )

    wrong_nonce = copy.deepcopy(base)
    wrong_nonce["eat_nonce"] = "different-consumer-challenge"
    wrong_nonce["binding_digest_sha256"] = binding_digest(wrong_nonce)
    add("wrong_nonce", wrong_nonce, "NONCE_MISMATCH")

    stale = copy.deepcopy(base)
    stale["exp"] = policy["now"] - 1
    add("stale", stale, "EXPIRED")

    future = copy.deepcopy(base)
    future["iat"] = policy["now"] + 1
    add("not_yet_valid", future, "NOT_YET_VALID")

    scenarios.append(
        {
            "id": "replayed_result",
            "result": sign(base, private_key),
            "seen_before": True,
            "expected": "REPLAYED",
        }
    )

    substituted = copy.deepcopy(base)
    substituted["cnf"]["COSE_Key"]["x"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    add("key_substitution", substituted, "KEY_BINDING_INVALID")

    unsupported_key = copy.deepcopy(base)
    unsupported_key["cnf"]["COSE_Key"]["crv"] = "Ed25519"
    unsupported_key["binding_digest_sha256"] = binding_digest(unsupported_key)
    add("unsupported_execution_key", unsupported_key, "EXECUTION_KEY_UNSUPPORTED")

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
    downgrade["eat_profile"] = "ordinary-iicp-cx"
    add("ordinary_cx_downgrade", downgrade, "EAT_PROFILE_UNACCEPTED")

    wrong_audience = copy.deepcopy(base)
    wrong_audience["aud"] = "different-consumer-session"
    wrong_audience["binding_digest_sha256"] = binding_digest(wrong_audience)
    add("wrong_audience", wrong_audience, "AUDIENCE_MISMATCH")

    wrong_candidate = copy.deepcopy(base)
    wrong_candidate["candidate_ref"] = "sha256:" + "e" * 64
    wrong_candidate["binding_digest_sha256"] = binding_digest(wrong_candidate)
    add("wrong_candidate", wrong_candidate, "CANDIDATE_MISMATCH")

    wrong_ticket = copy.deepcopy(base)
    wrong_ticket["route_ticket_digest_sha256"] = "f" * 64
    wrong_ticket["binding_digest_sha256"] = binding_digest(wrong_ticket)
    add("wrong_route_ticket", wrong_ticket, "ROUTE_TICKET_MISMATCH")

    return {
        "fixture_version": "execution-privacy-binding-v1",
        "evidence_class": "synthetic-research-only",
        "selected_media_type": "application/eat+cwt",
        "non_claims": [
            "not_vendor_evidence",
            "not_hardware_attestation",
            "not_proof_of_private_key_containment",
            "not_a_normative_iicp_profile",
            "json_projection_not_cose_sign1",
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
    result: dict[str, Any],
    policy: dict[str, Any],
    public_key: Ed25519PublicKey,
    seen_evidence_refs: set[str] | None = None,
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
    if result.get("eat_profile") not in policy["accepted_eat_profiles"]:
        return "EAT_PROFILE_UNACCEPTED"
    if result.get("intuse") != 5:
        return "INTENDED_USE_UNACCEPTED"
    if result.get("exp", 0) < policy["now"]:
        return "EXPIRED"
    if result.get("iat", policy["now"] + 1) > policy["now"]:
        return "NOT_YET_VALID"
    if result.get("eat_nonce") != policy["expected_nonce"]:
        return "NONCE_MISMATCH"
    if result.get("aud") != policy["expected_audience"]:
        return "AUDIENCE_MISMATCH"
    if result.get("candidate_ref") != policy["expected_candidate_ref"]:
        return "CANDIDATE_MISMATCH"
    if (
        result.get("route_ticket_digest_sha256")
        != policy["expected_route_ticket_digest_sha256"]
    ):
        return "ROUTE_TICKET_MISMATCH"
    if result.get("binding_digest_sha256") != binding_digest(result):
        return "KEY_BINDING_INVALID"
    execution_key = result.get("cnf", {}).get("COSE_Key", {})
    if (
        execution_key.get("kty") != "OKP"
        or execution_key.get("crv") != "X25519"
        or not isinstance(execution_key.get("x"), str)
        or not isinstance(execution_key.get("kid"), str)
    ):
        return "EXECUTION_KEY_UNSUPPORTED"
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
    evidence_ref = hashlib.sha256(canonical(result)).hexdigest()
    if seen_evidence_refs is not None:
        if evidence_ref in seen_evidence_refs:
            return "REPLAYED"
        seen_evidence_refs.add(evidence_ref)
    return "PASS"


def verify_fixture(fixture: dict[str, Any]) -> list[tuple[str, str, str]]:
    public_key = Ed25519PublicKey.from_public_bytes(
        b64url_decode(fixture["verifier"]["public_key"])
    )
    results = []
    for scenario in fixture["scenarios"]:
        seen: set[str] = set()
        if scenario.get("seen_before"):
            seen.add(hashlib.sha256(canonical(scenario["result"])).hexdigest())
        results.append(
            (
                scenario["id"],
                scenario["expected"],
                verify_result(scenario["result"], fixture["policy"], public_key, seen),
            )
        )
    return results


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
