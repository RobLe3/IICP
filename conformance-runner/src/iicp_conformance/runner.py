from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.resources import files
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EXPECTED_SCHEMA = "iicp.conformance_test_manifest.v1"
EXPECTED_SUITE = "4.45.0"
RESULT_SCHEMA = "iicp.conformance_result.v1"
VERIFICATION_SCHEMA = "iicp.conformance_verification.v1"
EVIDENCE_CLASSES = {"self-attested", "project-verified", "independent"}
PROHIBITED_KEYS = {
    "bindings",
    "credential",
    "credentials",
    "endpoint",
    "node_id",
    "payload",
    "response_body",
    "result_rows",
    "target",
    "target_url",
    "url",
}


@dataclass(frozen=True)
class Response:
    status: int
    body: bytes


def canonical_json(value: Any) -> bytes:
    try:
        import rfc8785
    except ImportError as error:
        raise RuntimeError(
            "install iicp-conformance[signing] for RFC 8785 canonicalization"
        ) from error
    try:
        return rfc8785.dumps(value)
    except (ValueError, TypeError) as error:
        raise ValueError("result cannot be represented by RFC 8785 JCS") from error


def bundled_manifest_bytes() -> bytes:
    return (
        files("iicp_conformance")
        .joinpath("fixtures/directory-public-v1.json")
        .read_bytes()
    )


def load_manifest(raw: bytes) -> dict[str, Any]:
    manifest = json.loads(raw)
    if manifest.get("schema") != EXPECTED_SCHEMA:
        raise ValueError("unsupported conformance manifest schema")
    if manifest.get("suite_version") != EXPECTED_SUITE:
        raise ValueError("mixed or unsupported conformance suite version")
    tests = manifest.get("tests")
    if not isinstance(tests, list) or not tests:
        raise ValueError("conformance manifest has no tests")
    if len({case.get("id") for case in tests}) != len(tests):
        raise ValueError("conformance manifest test IDs must be unique")
    return manifest


def request(target: str, case: dict[str, Any], timeout: float) -> Response:
    url = f"{target.rstrip('/')}{case['path']}"
    body = b"{}" if case["method"] == "POST" else None
    req = Request(
        url,
        data=body,
        method=case["method"],
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "iicp-conformance/0.1.0",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            return Response(response.status, response.read())
    except HTTPError as error:
        try:
            return Response(error.code, error.read())
        finally:
            error.close()
    except (URLError, TimeoutError, OSError) as error:
        raise RuntimeError("target request failed") from error


def assertion_passes(name: str, body: bytes) -> bool:
    if name == "none":
        return True
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    nodes = value.get("nodes") if isinstance(value, dict) else None
    if nodes is None and isinstance(value, dict):
        nodes = value.get("data", {}).get("nodes") if isinstance(value.get("data"), dict) else None
    if name == "discovery_shape":
        return isinstance(nodes, list) and isinstance(value.get("count"), int)
    if name == "score_range":
        return isinstance(nodes, list) and all(
            isinstance(node, dict)
            and isinstance(node.get("score"), (int, float))
            and 0.1 <= node["score"] <= 1.0
            for node in nodes
        )
    return False


def run(
    target: str,
    *,
    evidence_class: str = "self-attested",
    timeout: float = 5.0,
    manifest_raw: bytes | None = None,
) -> dict[str, Any]:
    raw = manifest_raw if manifest_raw is not None else bundled_manifest_bytes()
    manifest = load_manifest(raw)
    results: list[dict[str, Any]] = []
    started = datetime.now(timezone.utc)
    for case in manifest["tests"]:
        began = time.monotonic()
        observed_status: int | None = None
        outcome = "fail"
        reason = "request_failed"
        try:
            response = request(target, case, timeout)
            observed_status = response.status
            if response.status != case["status"]:
                reason = "unexpected_status"
            elif not assertion_passes(case["assertion"], response.body):
                reason = "assertion_failed"
            else:
                outcome = "pass"
                reason = "passed"
        except RuntimeError:
            pass
        results.append(
            {
                "test_id": case["id"],
                "outcome": outcome,
                "reason": reason,
                "observed_status": observed_status,
                "duration_ms": round((time.monotonic() - began) * 1000, 3),
            }
        )
    finished = datetime.now(timezone.utc)
    passed = sum(item["outcome"] == "pass" for item in results)
    return {
        "schema": RESULT_SCHEMA,
        "runner_version": "0.1.0",
        "suite_version": manifest["suite_version"],
        "fixture_digest": f"sha256:{hashlib.sha256(raw).hexdigest()}",
        "target_role": "directory",
        "evidence_class": evidence_class,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "finished_at": finished.isoformat().replace("+00:00", "Z"),
        "summary": {"total": len(results), "passed": passed, "failed": len(results) - passed},
        "results": results,
        "content_free": True,
    }


def sign_result(result: dict[str, Any], private_key_hex: str) -> dict[str, Any]:
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as error:
        raise RuntimeError("install iicp-conformance[signing] to sign results") from error
    try:
        private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex.strip()))
    except ValueError as error:
        raise ValueError("signing key must be a 32-byte Ed25519 private key in hex") from error
    signed = dict(result)
    signature = private_key.sign(canonical_json(result))
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    signed["signature"] = {
        "algorithm": "Ed25519",
        "canonicalization": "RFC8785-JCS",
        "public_key": public_key.hex(),
        "value": signature.hex(),
    }
    return signed


def _prohibited_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in PROHIBITED_KEYS:
                found.add(key)
            found.update(_prohibited_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_prohibited_keys(child))
    return found


def verify_result(
    result: dict[str, Any], *, require_signature: bool = False
) -> dict[str, Any]:
    raw = bundled_manifest_bytes()
    manifest = load_manifest(raw)
    errors: list[str] = []
    required = {
        "schema",
        "runner_version",
        "suite_version",
        "fixture_digest",
        "target_role",
        "evidence_class",
        "started_at",
        "finished_at",
        "summary",
        "results",
        "content_free",
    }
    allowed = required | {"signature"}
    missing = sorted(required - result.keys())
    unknown = sorted(result.keys() - allowed)
    if missing:
        errors.append(f"missing fields: {','.join(missing)}")
    if unknown:
        errors.append(f"unknown fields: {','.join(unknown)}")
    if result.get("schema") != RESULT_SCHEMA:
        errors.append("unsupported result schema")
    if result.get("suite_version") != EXPECTED_SUITE:
        errors.append("mixed or unsupported suite version")
    expected_digest = f"sha256:{hashlib.sha256(raw).hexdigest()}"
    if result.get("fixture_digest") != expected_digest:
        errors.append("fixture digest mismatch")
    if result.get("target_role") != "directory":
        errors.append("unsupported target role")
    if result.get("evidence_class") not in EVIDENCE_CLASSES:
        errors.append("unsupported evidence class")
    if result.get("content_free") is not True:
        errors.append("content_free must be true")
    prohibited = sorted(_prohibited_keys(result))
    if prohibited:
        errors.append(f"prohibited fields: {','.join(prohibited)}")

    results = result.get("results")
    expected_ids = [case["id"] for case in manifest["tests"]]
    if not isinstance(results, list):
        errors.append("results must be an array")
        results = []
    elif [item.get("test_id") for item in results if isinstance(item, dict)] != expected_ids:
        errors.append("result test IDs do not match the fixture manifest")
    item_fields = {"test_id", "outcome", "reason", "observed_status", "duration_ms"}
    reasons = {"passed", "request_failed", "unexpected_status", "assertion_failed"}
    for index, item in enumerate(results):
        if not isinstance(item, dict) or set(item) != item_fields:
            errors.append(f"result {index} has an invalid shape")
            continue
        if item.get("outcome") not in {"pass", "fail"}:
            errors.append(f"result {index} has an invalid outcome")
        if item.get("reason") not in reasons:
            errors.append(f"result {index} has an invalid reason")
        status = item.get("observed_status")
        if status is not None and (
            not isinstance(status, int) or not 100 <= status <= 599
        ):
            errors.append(f"result {index} has an invalid observed status")
        duration = item.get("duration_ms")
        if not isinstance(duration, (int, float)) or duration < 0:
            errors.append(f"result {index} has an invalid duration")
    passed = sum(
        isinstance(item, dict) and item.get("outcome") == "pass" for item in results
    )
    failed = sum(
        isinstance(item, dict) and item.get("outcome") == "fail" for item in results
    )
    summary = result.get("summary")
    if summary != {"total": len(results), "passed": passed, "failed": failed}:
        errors.append("summary does not match result outcomes")

    signature = result.get("signature")
    signed = signature is not None
    signer_fingerprint: str | None = None
    if require_signature and not signed:
        errors.append("signature is required")
    if signed:
        try:
            if not isinstance(signature, dict):
                raise ValueError("signature must be an object")
            if signature.get("algorithm") != "Ed25519":
                raise ValueError("unsupported signature algorithm")
            if signature.get("canonicalization") != "RFC8785-JCS":
                raise ValueError("unsupported signature canonicalization")
            public_raw = bytes.fromhex(signature["public_key"])
            signature_raw = bytes.fromhex(signature["value"])
            if len(public_raw) != 32 or len(signature_raw) != 64:
                raise ValueError("invalid Ed25519 key or signature length")
            try:
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            except ImportError as error:
                raise RuntimeError(
                    "install iicp-conformance[signing] to verify signed results"
                ) from error
            unsigned = dict(result)
            unsigned.pop("signature", None)
            Ed25519PublicKey.from_public_bytes(public_raw).verify(
                signature_raw, canonical_json(unsigned)
            )
            signer_fingerprint = f"sha256:{hashlib.sha256(public_raw).hexdigest()}"
        except (KeyError, ValueError, RuntimeError) as error:
            errors.append(str(error))
        except Exception:
            errors.append("signature verification failed")

    return {
        "schema": VERIFICATION_SCHEMA,
        "valid": not errors,
        "signed": signed,
        "signer_key_fingerprint": signer_fingerprint,
        "suite_version": result.get("suite_version"),
        "fixture_digest": result.get("fixture_digest"),
        "errors": errors,
        "content_free": True,
    }
