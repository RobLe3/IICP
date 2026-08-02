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


@dataclass(frozen=True)
class Response:
    status: int
    body: bytes


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


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
        "canonicalization": "JCS-compatible restricted result profile",
        "public_key": public_key.hex(),
        "value": signature.hex(),
    }
    return signed
