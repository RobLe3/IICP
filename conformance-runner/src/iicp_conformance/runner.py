from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.resources import files
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

EXPECTED_SCHEMA = "iicp.conformance_test_manifest.v1"
RESULT_SCHEMA = "iicp.conformance_result.v1"
VERIFICATION_SCHEMA = "iicp.conformance_verification.v1"
DEFAULT_PROFILE = "directory-public-v1"
RUNNER_VERSION = "0.3.0"
PROFILE_FILES = {
    DEFAULT_PROFILE: "directory-public-v1.json",
    "directory-dispatch-v1": "directory-dispatch-v1.json",
    "directory-lifecycle-v1": "directory-lifecycle-v1.json",
}
PROFILE_SUITES = {
    DEFAULT_PROFILE: "4.45.0",
    "directory-dispatch-v1": "4.49.0",
    "directory-lifecycle-v1": "4.50.0",
}
OFFLINE_PROFILE_FILES = {
    "dispatch-route-ticket-v1": "dispatch-route-ticket-v1.json",
    "dispatch-ticket-trust-v2": "dispatch-ticket-trust-v2.json",
    "dispatch-ticket-trust-v2-crypto": "dispatch-ticket-trust-v2-crypto.json",
    "profile-compatibility-v0-policy-refusal": "profile-compatibility-v0.json",
    "federation-chain-v0": "federation-chain-v0.json",
}
OFFLINE_PROFILE_METADATA = {
    "dispatch-route-ticket-v1": {
        "vector_key": "validation_vectors",
        "id_key": "name",
        "target_role": "offline_ticket_verifier",
    },
    "dispatch-ticket-trust-v2-crypto": {
        "vector_key": "vectors",
        "id_key": "id",
        "target_role": "offline_ticket_trust_verifier",
    },
    "dispatch-ticket-trust-v2": {
        "vector_key": "cases",
        "id_key": "id",
        "target_role": "offline_ticket_trust_semantic_verifier",
    },
    "profile-compatibility-v0-policy-refusal": {
        "vector_key": "scenarios",
        "id_key": "name",
        "target_role": "offline_policy_refusal_verifier",
        "expected_reason": "policy_refusal",
    },
    "federation-chain-v0": {"vector_key": "cases", "id_key": "id", "target_role": "offline_federation_chain_verifier"},
}
DISPATCH_TICKET_DOMAIN = b"iicp:dispatch-route-ticket:v1\n"
DISPATCH_TICKET_AUDIENCE = "iicp.directory.dispatch"
STATE_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
STATE_REFERENCE = re.compile(r"\$\{([a-z][a-z0-9_]{0,63})\}")
CAPTURE_PATH = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
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


def bundled_manifest_bytes(profile: str = DEFAULT_PROFILE) -> bytes:
    try:
        fixture = PROFILE_FILES[profile]
    except KeyError as error:
        raise ValueError("unsupported conformance profile") from error
    return (
        files("iicp_conformance")
        .joinpath(f"fixtures/{fixture}")
        .read_bytes()
    )


def bundled_offline_fixture_bytes(profile: str) -> bytes:
    try:
        fixture = OFFLINE_PROFILE_FILES[profile]
    except KeyError as error:
        raise ValueError("unsupported offline conformance profile") from error
    return files("iicp_conformance").joinpath(f"fixtures/{fixture}").read_bytes()


def _b64url_decode(value: str) -> bytes:
    padded = value + "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _ticket_vector_token(fixture: dict[str, Any], reference: str) -> str:
    if reference == "valid":
        return fixture["valid"]["token"]
    if reference == "valid+0":
        return f"{fixture['valid']['token']}0"
    if reference == "wrong_audience":
        return fixture["wrong_audience"]["token"]
    return reference


def verify_dispatch_route_ticket(
    token: str,
    public_key_hex: str,
    issuer: str,
    node_id: str,
    intent: str,
    now_s: int,
) -> bool:
    """Verify the disclosed-route v1 ticket contract without retaining claims."""
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as error:
        raise RuntimeError(
            "install iicp-conformance[signing] to verify dispatch ticket vectors"
        ) from error
    payload_b64, separator, signature_hex = token.partition(".")
    if not separator or len(signature_hex) != 128:
        return False
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex)).verify(
            bytes.fromhex(signature_hex), DISPATCH_TICKET_DOMAIN + payload_b64.encode("ascii")
        )
        claims = json.loads(_b64url_decode(payload_b64))
    except (ValueError, binascii.Error, InvalidSignature, json.JSONDecodeError, UnicodeEncodeError):
        return False
    if not isinstance(claims, dict):
        return False
    jti = claims.get("jti")
    policy_digest = claims.get("policy_manifest_sha256")
    return (
        claims.get("v") == 1
        and claims.get("typ") == "dispatch-route-ticket"
        and claims.get("iss") == issuer
        and claims.get("aud") == DISPATCH_TICKET_AUDIENCE
        and claims.get("node_id") == node_id
        and claims.get("intent") == intent
        and isinstance(claims.get("iat"), int)
        and isinstance(claims.get("exp"), int)
        and claims["exp"] > now_s
        and isinstance(jti, str)
        and bool(re.fullmatch(r"[0-9a-f]{24}", jti))
        and (
            policy_digest is None
            or isinstance(policy_digest, str)
            and bool(re.fullmatch(r"[0-9a-f]{64}", policy_digest))
        )
    )


def run_dispatch_ticket_fixture(
    *, evidence_class: str = "self-attested"
) -> dict[str, Any]:
    """Execute canonical offline ticket vectors and emit only aggregate outcomes."""
    if evidence_class not in EVIDENCE_CLASSES:
        raise ValueError("unsupported evidence class")
    profile = "dispatch-route-ticket-v1"
    raw = bundled_offline_fixture_bytes(profile)
    fixture = json.loads(raw)
    if fixture.get("fixture_version") != "1.0.0-draft":
        raise ValueError("mixed or unsupported dispatch ticket fixture version")
    vectors = fixture.get("validation_vectors")
    if not isinstance(vectors, list) or not vectors:
        raise ValueError("dispatch ticket fixture has no validation vectors")
    started = datetime.now(timezone.utc)
    results: list[dict[str, Any]] = []
    for vector in vectors:
        began = time.monotonic()
        valid = verify_dispatch_route_ticket(
            _ticket_vector_token(fixture, vector["token"]),
            fixture["public_key_hex"],
            vector["issuer"],
            vector["node_id"],
            vector["intent"],
            vector["now_s"],
        )
        expected_valid = vector.get("expected") == "valid"
        results.append(
            {
                "test_id": vector["name"],
                "outcome": "pass" if valid == expected_valid else "fail",
                "reason": "passed" if valid == expected_valid else "assertion_failed",
                "observed_status": None,
                "duration_ms": round((time.monotonic() - began) * 1000, 3),
            }
        )
    finished = datetime.now(timezone.utc)
    passed = sum(item["outcome"] == "pass" for item in results)
    return {
        "schema": RESULT_SCHEMA,
        "runner_version": RUNNER_VERSION,
        "suite_version": fixture["fixture_version"],
        "profile": profile,
        "fixture_digest": f"sha256:{hashlib.sha256(raw).hexdigest()}",
        "target_role": "offline_ticket_verifier",
        "evidence_class": evidence_class,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "finished_at": finished.isoformat().replace("+00:00", "Z"),
        "summary": {"total": len(results), "passed": passed, "failed": len(results) - passed},
        "results": results,
        "content_free": True,
    }


def _verify_dispatch_ticket_trust_v2_vector(
    vector: dict[str, Any], keys: dict[str, dict[str, Any]], domain: bytes
) -> str:
    """Evaluate one portable v2 crypto vector without retaining ticket claims.

    This intentionally covers the vector's local replay flag only. It does not
    implement a persistent trust store, global redemption, or key distribution.
    """
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as error:
        raise RuntimeError(
            "install iicp-conformance[signing] to verify dispatch ticket trust vectors"
        ) from error
    claims = vector["claims"]
    key_id = claims["key_id"]
    if key_id not in vector["trust_bundle_key_ids"] or key_id not in keys:
        return "reject_unknown_key"
    key = keys[key_id]
    if key["state"] == "revoked":
        return "reject_key_revoked"
    if not key["valid_from"] <= vector["now"] <= key["valid_until"]:
        return "reject_key_expired"
    try:
        public_key = Ed25519PublicKey.from_public_bytes(
            _b64url_decode(key["public_key_b64url"])
        )
        public_key.verify(
            _b64url_decode(vector["signature_b64url"]),
            domain + json.dumps(
                claims, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8"),
        )
    except (ValueError, binascii.Error, InvalidSignature, UnicodeEncodeError):
        return "reject_signature"
    if vector["jti_seen"]:
        return "reject_local_replay"
    return "accept_anchored"


def run_dispatch_ticket_trust_v2_fixture(
    *, evidence_class: str = "self-attested"
) -> dict[str, Any]:
    """Execute the pre-normative v2 crypto/replay fixture offline.

    The result carries only vector identifiers and aggregate outcomes. A pass
    proves fixture execution, not runtime enablement, trust-store persistence,
    global redemption, or independently operated conformance.
    """
    if evidence_class not in EVIDENCE_CLASSES:
        raise ValueError("unsupported evidence class")
    profile = "dispatch-ticket-trust-v2-crypto"
    raw = bundled_offline_fixture_bytes(profile)
    fixture = json.loads(raw)
    if (
        fixture.get("fixture_version") != "0.2.0-draft"
        or fixture.get("status") != "pre-normative"
    ):
        raise ValueError("mixed or unsupported dispatch ticket trust fixture version")
    vectors = fixture.get("vectors")
    if not isinstance(vectors, list) or not vectors:
        raise ValueError("dispatch ticket trust fixture has no vectors")
    try:
        domain = _b64url_decode(fixture["domain_separator_b64url"])
        keys = {key["key_id"]: key for key in fixture["keys"]}
    except (KeyError, TypeError, binascii.Error) as error:
        raise ValueError("dispatch ticket trust fixture is malformed") from error
    started = datetime.now(timezone.utc)
    results: list[dict[str, Any]] = []
    for vector in vectors:
        began = time.monotonic()
        observed = _verify_dispatch_ticket_trust_v2_vector(vector, keys, domain)
        expected = vector.get("expected")
        results.append(
            {
                "test_id": vector["id"],
                "outcome": "pass" if observed == expected else "fail",
                "reason": "passed" if observed == expected else "assertion_failed",
                "observed_status": None,
                "duration_ms": round((time.monotonic() - began) * 1000, 3),
            }
        )
    finished = datetime.now(timezone.utc)
    passed = sum(item["outcome"] == "pass" for item in results)
    return {
        "schema": RESULT_SCHEMA,
        "runner_version": RUNNER_VERSION,
        "suite_version": fixture["fixture_version"],
        "profile": profile,
        "fixture_digest": f"sha256:{hashlib.sha256(raw).hexdigest()}",
        "target_role": "offline_ticket_trust_verifier",
        "evidence_class": evidence_class,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "finished_at": finished.isoformat().replace("+00:00", "Z"),
        "summary": {"total": len(results), "passed": passed, "failed": len(results) - passed},
        "results": results,
        "content_free": True,
    }


def _dispatch_ticket_trust_v2_semantic_decision(case: dict[str, Any]) -> str:
    """Evaluate the canonical pre-normative trust decision table.

    This is deliberately a fixture decision evaluator, not an implementation of
    ticket parsing, persistent trust storage, or global redemption.
    """
    mode = case.get("mode")
    profile = case.get("ticket_profile")
    if mode == "strict_pinned" and profile != "v2":
        return "reject_required_profile_downgrade"
    if mode == "open_compat" and profile == "v1":
        return (
            "accept_same_origin_unanchored"
            if case.get("same_origin_key_valid") is True
            else "reject_signature"
        )
    if mode not in {"strict_pinned", "open_compat"} or profile != "v2":
        return "reject_required_profile_downgrade"
    if case.get("key_known") is not True:
        return "reject_unknown_v2_key" if mode == "open_compat" else "reject_unknown_key"
    if case.get("bundle_version", 0) < case.get("minimum_bundle_version", 0):
        return "reject_bundle_rollback"
    if case.get("key_state") == "revoked":
        return "reject_key_revoked"
    if case.get("key_time_valid") is not True:
        return "reject_key_expired"
    if case.get("signature_valid") is not True:
        return "reject_signature"
    if case.get("claims_match") is not True:
        return "reject_claim_mismatch"
    if case.get("jti_seen") is True:
        return "reject_local_replay"
    return "accept_anchored"


def run_dispatch_ticket_trust_v2_semantics_fixture(
    *, evidence_class: str = "self-attested"
) -> dict[str, Any]:
    """Execute v2 trust downgrade and compatibility semantics offline."""
    if evidence_class not in EVIDENCE_CLASSES:
        raise ValueError("unsupported evidence class")
    profile = "dispatch-ticket-trust-v2"
    raw = bundled_offline_fixture_bytes(profile)
    fixture = json.loads(raw)
    if (
        fixture.get("fixture_version") != "0.1.0-draft"
        or not str(fixture.get("status", "")).startswith("pre-normative")
    ):
        raise ValueError("mixed or unsupported dispatch ticket trust fixture version")
    cases = fixture.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("dispatch ticket trust fixture has no cases")
    started = datetime.now(timezone.utc)
    results: list[dict[str, Any]] = []
    for case in cases:
        began = time.monotonic()
        observed = _dispatch_ticket_trust_v2_semantic_decision(case)
        expected = case.get("expected")
        results.append(
            {
                "test_id": case["id"],
                "outcome": "pass" if observed == expected else "fail",
                "reason": "passed" if observed == expected else "assertion_failed",
                "observed_status": None,
                "duration_ms": round((time.monotonic() - began) * 1000, 3),
            }
        )
    finished = datetime.now(timezone.utc)
    passed = sum(item["outcome"] == "pass" for item in results)
    return {
        "schema": RESULT_SCHEMA,
        "runner_version": RUNNER_VERSION,
        "suite_version": fixture["fixture_version"],
        "profile": profile,
        "fixture_digest": f"sha256:{hashlib.sha256(raw).hexdigest()}",
        "target_role": "offline_ticket_trust_semantic_verifier",
        "evidence_class": evidence_class,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "finished_at": finished.isoformat().replace("+00:00", "Z"),
        "summary": {"total": len(results), "passed": passed, "failed": len(results) - passed},
        "results": results,
        "content_free": True,
    }


def run_policy_refusal_fixture(
    *, evidence_class: str = "self-attested"
) -> dict[str, Any]:
    """Execute the canonical profile fixture's explicit policy-refusal cases.

    The runner intentionally does not become a general eligibility engine. It
    evaluates only scenarios whose canonical expected reason is policy_refusal.
    """
    if evidence_class not in EVIDENCE_CLASSES:
        raise ValueError("unsupported evidence class")
    profile = "profile-compatibility-v0-policy-refusal"
    raw = bundled_offline_fixture_bytes(profile)
    fixture = json.loads(raw)
    if (
        fixture.get("fixture_version") != "0.4.0-draft"
        or fixture.get("status") != "pre-normative"
    ):
        raise ValueError("mixed or unsupported policy-refusal fixture version")
    scenarios = [
        scenario
        for scenario in fixture.get("scenarios", [])
        if scenario.get("expected_reason") == "policy_refusal"
    ]
    if not scenarios:
        raise ValueError("policy-refusal fixture has no refusal scenarios")
    started = datetime.now(timezone.utc)
    results: list[dict[str, Any]] = []
    for scenario in scenarios:
        began = time.monotonic()
        request = scenario.get("request", {})
        observed = "policy_refusal" if request.get("policy") == "deny" else "compatible"
        results.append(
            {
                "test_id": scenario["name"],
                "outcome": "pass" if observed == "policy_refusal" else "fail",
                "reason": "passed" if observed == "policy_refusal" else "assertion_failed",
                "observed_status": None,
                "duration_ms": round((time.monotonic() - began) * 1000, 3),
            }
        )
    finished = datetime.now(timezone.utc)
    passed = sum(item["outcome"] == "pass" for item in results)
    return {
        "schema": RESULT_SCHEMA,
        "runner_version": RUNNER_VERSION,
        "suite_version": fixture["fixture_version"],
        "profile": profile,
        "fixture_digest": f"sha256:{hashlib.sha256(raw).hexdigest()}",
        "target_role": "offline_policy_refusal_verifier",
        "evidence_class": evidence_class,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "finished_at": finished.isoformat().replace("+00:00", "Z"),
        "summary": {"total": len(results), "passed": passed, "failed": len(results) - passed},
        "results": results,
        "content_free": True,
    }


def run_federation_chain_fixture(*, evidence_class: str = "self-attested") -> dict[str, Any]:
    """Verify portable pre-normative signed event-chain cases offline."""
    if evidence_class not in EVIDENCE_CLASSES:
        raise ValueError("unsupported evidence class")
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as error:
        raise RuntimeError("install iicp-conformance[signing] to verify federation vectors") from error
    profile = "federation-chain-v0"; raw = bundled_offline_fixture_bytes(profile); fixture = json.loads(raw)
    if fixture.get("fixture_version") != "0.1.0-draft" or fixture.get("status") != "pre-normative":
        raise ValueError("mixed or unsupported federation-chain fixture version")
    def decision(case: dict[str, Any]) -> str:
        auth = case.get("replica_authorization")
        if auth == "expired": return "reject_replica_authorization_expired"
        if auth != "active": return "reject_replica_authorization"
        key_hex = fixture["trusted_roots"].get(case.get("root_id"))
        if not key_hex: return "reject_untrusted_root"
        previous = fixture["genesis_root"]; sequence = 0
        for event in case["events"]:
            if event["seq"] <= sequence: return "reject_sequence"
            sequence = event["seq"]
            if event["prev_hash"] != previous: return "reject_chain_link"
            payload_hash = hashlib.sha256(json.dumps(event["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
            message = hashlib.sha256(f'{event["event_id"]}:{event["event_type"]}:{event["seq"]}:{event["ts_ms"]}:{payload_hash}:{event["prev_hash"]}'.encode()).digest()
            try: Ed25519PublicKey.from_public_bytes(bytes.fromhex(key_hex)).verify(bytes.fromhex(event["sig"]), message)
            except (ValueError, InvalidSignature): return "reject_signature"
            previous = hashlib.sha256(event["sig"].encode()).hexdigest()
        return "accept"
    cases = fixture.get("cases")
    if not isinstance(cases, list) or not cases: raise ValueError("federation-chain fixture has no cases")
    started=datetime.now(timezone.utc); results=[]
    for case in cases:
        began=time.monotonic(); observed=decision(case); expected=case.get("expected")
        results.append({"test_id":case["id"],"outcome":"pass" if observed == expected else "fail","reason":"passed" if observed == expected else "assertion_failed","observed_status":None,"duration_ms":round((time.monotonic()-began)*1000,3)})
    finished=datetime.now(timezone.utc); passed=sum(x["outcome"]=="pass" for x in results)
    return {"schema":RESULT_SCHEMA,"runner_version":RUNNER_VERSION,"suite_version":fixture["fixture_version"],"profile":profile,"fixture_digest":f"sha256:{hashlib.sha256(raw).hexdigest()}","target_role":"offline_federation_chain_verifier","evidence_class":evidence_class,"started_at":started.isoformat().replace("+00:00","Z"),"finished_at":finished.isoformat().replace("+00:00","Z"),"summary":{"total":len(results),"passed":passed,"failed":len(results)-passed},"results":results,"content_free":True}


def load_manifest(raw: bytes) -> dict[str, Any]:
    manifest = json.loads(raw)
    if manifest.get("schema") != EXPECTED_SCHEMA:
        raise ValueError("unsupported conformance manifest schema")
    profile = manifest.get("profile")
    if profile not in PROFILE_FILES:
        raise ValueError("unsupported conformance profile")
    if manifest.get("suite_version") != PROFILE_SUITES[profile]:
        raise ValueError("mixed or unsupported conformance suite version")
    tests = manifest.get("tests")
    if not isinstance(tests, list) or not tests:
        raise ValueError("conformance manifest has no tests")
    if len({case.get("id") for case in tests}) != len(tests):
        raise ValueError("conformance manifest test IDs must be unique")
    available_state: set[str] = set()
    for case in tests:
        if not isinstance(case, dict):
            raise ValueError("conformance manifest test must be an object")
        if case.get("method") not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            raise ValueError("conformance manifest has an unsupported method")
        path = case.get("path")
        if not isinstance(path, str) or not path.startswith("/") or path.startswith("//"):
            raise ValueError("conformance manifest has an invalid relative path")
        headers = case.get("headers", {})
        if not isinstance(headers, dict) or any(
            key != "Authorization" or not isinstance(value, str)
            for key, value in headers.items()
        ):
            raise ValueError("conformance manifest has an unsupported request header")
        references = _state_references(
            {key: case.get(key) for key in ("path", "headers", "body")}
        )
        unresolved = references - available_state
        if unresolved:
            raise ValueError("conformance manifest contains an unresolved state variable")
        capture = case.get("capture", {})
        if not isinstance(capture, dict):
            raise ValueError("conformance manifest capture must be an object")
        for name, path in capture.items():
            if not isinstance(name, str) or not STATE_NAME.fullmatch(name):
                raise ValueError("conformance manifest has an invalid capture name")
            if not isinstance(path, str) or not CAPTURE_PATH.fullmatch(path):
                raise ValueError("conformance manifest has an invalid capture path")
            if name in available_state:
                raise ValueError("conformance manifest capture names must not be reused")
        available_state.update(capture)
    return manifest


def _state_references(value: Any) -> set[str]:
    if isinstance(value, str):
        return set(STATE_REFERENCE.findall(value))
    if isinstance(value, dict):
        return set().union(*(_state_references(child) for child in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_state_references(child) for child in value), set())
    return set()


def _resolve_state(value: Any, state: dict[str, str]) -> Any:
    if isinstance(value, str):
        def replace(match: re.Match[str]) -> str:
            try:
                return state[match.group(1)]
            except KeyError as error:
                raise RuntimeError("request state is unavailable") from error
        return STATE_REFERENCE.sub(replace, value)
    if isinstance(value, dict):
        return {key: _resolve_state(child, state) for key, child in value.items()}
    if isinstance(value, list):
        return [_resolve_state(child, state) for child in value]
    return value


def request(target: str, case: dict[str, Any], timeout: float) -> Response:
    url = f"{target.rstrip('/')}{case['path']}"
    body = (
        json.dumps(case.get("body", {}), separators=(",", ":")).encode()
        if case["method"] in {"POST", "PUT", "PATCH", "DELETE"}
        else None
    )
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": f"iicp-conformance/{RUNNER_VERSION}",
    }
    headers.update(case.get("headers", {}))
    req = Request(
        url,
        data=body,
        method=case["method"],
        headers=headers,
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
    if name.startswith("error_code:"):
        expected = name.split(":", 1)[1]
        return (
            isinstance(value, dict)
            and isinstance(value.get("error"), dict)
            and value["error"].get("code") == expected
        )
    if name == "json_error":
        return (
            isinstance(value, dict)
            and isinstance(value.get("error"), dict)
            and isinstance(value["error"].get("code"), str)
        )
    if name == "json_error_without_fixture_content":
        return (
            isinstance(value, dict)
            and isinstance(value.get("error"), dict)
            and isinstance(value["error"].get("code"), str)
            and b"fixture-only" not in body
        )
    if name == "dispatch_ticket_shape":
        return (
            isinstance(value, dict)
            and isinstance(value.get("ticket"), str)
            and bool(value["ticket"])
            and isinstance(value.get("route"), dict)
            and value.get("data_class") == "ticketed_route_dispatch"
            and value.get("route_fields_present") is True
            and value.get("prompt_payload_accepted") is False
        )
    if name == "registration_shape":
        return (
            isinstance(value, dict)
            and isinstance(value.get("node_id"), str)
            and bool(value["node_id"])
            and isinstance(value.get("node_token"), str)
            and bool(value["node_token"])
        )
    if name == "heartbeat_shape":
        return (
            isinstance(value, dict)
            and value.get("ok") is True
            and isinstance(value.get("next_heartbeat_ms"), int)
            and value["next_heartbeat_ms"] > 0
        )
    if name == "deregister_shape":
        return isinstance(value, dict) and value.get("deregistered") is True
    return False


def _capture_response(body: bytes, capture: dict[str, str]) -> dict[str, str]:
    if not capture:
        return {}
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("response capture failed") from error
    captured: dict[str, str] = {}
    for name, path in capture.items():
        current: Any = value
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                raise RuntimeError("response capture failed")
            current = current[part]
        if not isinstance(current, str) or not current:
            raise RuntimeError("response capture failed")
        captured[name] = current
    return captured


def _is_loopback_target(target: str) -> bool:
    parsed = urlsplit(target)
    return (
        parsed.scheme in {"http", "https"}
        and parsed.hostname in {"127.0.0.1", "::1", "localhost"}
        and parsed.username is None
        and parsed.password is None
    )


def run(
    target: str,
    *,
    evidence_class: str = "self-attested",
    timeout: float = 5.0,
    manifest_raw: bytes | None = None,
    profile: str = DEFAULT_PROFILE,
) -> dict[str, Any]:
    raw = manifest_raw if manifest_raw is not None else bundled_manifest_bytes(profile)
    manifest = load_manifest(raw)
    if manifest.get("profile") != profile:
        raise ValueError("manifest profile does not match requested profile")
    if manifest.get("loopback_only") is True and not _is_loopback_target(target):
        raise ValueError("this conformance profile is restricted to loopback targets")
    results: list[dict[str, Any]] = []
    state: dict[str, str] = {}
    started = datetime.now(timezone.utc)
    for case in manifest["tests"]:
        began = time.monotonic()
        observed_status: int | None = None
        outcome = "fail"
        reason = "request_failed"
        try:
            resolved_case = _resolve_state(case, state)
            response = request(target, resolved_case, timeout)
            observed_status = response.status
            if response.status != case["status"]:
                reason = "unexpected_status"
            elif not assertion_passes(case["assertion"], response.body):
                reason = "assertion_failed"
            else:
                state.update(_capture_response(response.body, case.get("capture", {})))
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
        "runner_version": RUNNER_VERSION,
        "suite_version": manifest["suite_version"],
        "profile": manifest["profile"],
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
    profile = result.get("profile", DEFAULT_PROFILE)
    try:
        if profile in PROFILE_FILES:
            raw = bundled_manifest_bytes(profile)
            manifest = load_manifest(raw)
            expected_version = manifest["suite_version"]
            expected_ids = [case["id"] for case in manifest["tests"]]
            expected_target_role = "directory"
        elif profile in OFFLINE_PROFILE_FILES:
            raw = bundled_offline_fixture_bytes(profile)
            fixture = json.loads(raw)
            expected_version = fixture["fixture_version"]
            metadata = OFFLINE_PROFILE_METADATA[profile]
            vectors = fixture.get(metadata["vector_key"])
            if not isinstance(vectors, list) or not vectors:
                raise ValueError("offline fixture has no validation vectors")
            if expected_reason := metadata.get("expected_reason"):
                vectors = [
                    vector
                    for vector in vectors
                    if vector.get("expected_reason") == expected_reason
                ]
            if not vectors:
                raise ValueError("offline fixture has no matching vectors")
            expected_ids = [vector[metadata["id_key"]] for vector in vectors]
            expected_target_role = metadata["target_role"]
        else:
            raise ValueError("unsupported conformance profile")
    except (ValueError, KeyError, json.JSONDecodeError) as error:
        raw = b""
        expected_version = None
        expected_ids = []
        expected_target_role = None
        errors = [str(error)]
    else:
        errors = []
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
    allowed = required | {"profile", "signature"}
    missing = sorted(required - result.keys())
    unknown = sorted(result.keys() - allowed)
    if missing:
        errors.append(f"missing fields: {','.join(missing)}")
    if unknown:
        errors.append(f"unknown fields: {','.join(unknown)}")
    if result.get("schema") != RESULT_SCHEMA:
        errors.append("unsupported result schema")
    if result.get("suite_version") != expected_version:
        errors.append("mixed or unsupported suite version")
    expected_digest = f"sha256:{hashlib.sha256(raw).hexdigest()}"
    if result.get("fixture_digest") != expected_digest:
        errors.append("fixture digest mismatch")
    if result.get("target_role") != expected_target_role:
        errors.append("unsupported target role")
    if result.get("evidence_class") not in EVIDENCE_CLASSES:
        errors.append("unsupported evidence class")
    if result.get("content_free") is not True:
        errors.append("content_free must be true")
    prohibited = sorted(_prohibited_keys(result))
    if prohibited:
        errors.append(f"prohibited fields: {','.join(prohibited)}")

    results = result.get("results")
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
        "profile": profile,
        "fixture_digest": result.get("fixture_digest"),
        "errors": errors,
        "content_free": True,
    }
