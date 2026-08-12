#!/usr/bin/env python3
"""Non-production software proof of attestation-bound IICP-CX key reuse.

This executable model proves protocol composition only. It provides no process,
VM, hardware, operator, or private-key containment guarantee.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from verify_vectors import (
    EAT_PROFILE,
    b64url,
    b64url_decode,
    binding_digest,
    sign,
    verify_result,
)

REQUEST_INFO_PREFIX = b"IICP-CX-v1"
RESPONSE_INFO_PREFIX = b"IICP-CX-RESP-v1"
PROOF_INTENT = "urn:iicp:intent:execution-privacy:proof:v0"


def execution_key_id(public_key: bytes) -> str:
    return "cx-" + hashlib.sha256(public_key).hexdigest()[:16]


def route_ticket_digest(ticket: str) -> str:
    return hashlib.sha256(ticket.encode("utf-8")).hexdigest()


def derive_key(shared_secret: bytes, nonce: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=nonce, info=info).derive(
        shared_secret
    )


@dataclass(frozen=True)
class ConsumerContext:
    task_id: str
    shared_secret: bytes


class SoftwareConfidentialWorker:
    """Software-only stand-in for the future measured confidential worker."""

    def __init__(self) -> None:
        self._execution_key: X25519PrivateKey | None = X25519PrivateKey.generate()
        self._accepted_task_ids: set[str] = set()
        self._retired = False

    def public_key_claim(self) -> dict[str, str]:
        if self._execution_key is None:
            raise ValueError("execution key retired")
        public = self._execution_key.public_key().public_bytes(
            Encoding.Raw, PublicFormat.Raw
        )
        return {
            "kty": "OKP",
            "crv": "X25519",
            "x": b64url(public),
            "kid": execution_key_id(public),
        }

    def evidence(
        self,
        *,
        nonce: str,
        audience: str,
        candidate_ref: str,
        route_ticket_digest_sha256: str,
        issued_at: int,
        expires_at: int,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": "iicp-research-attestation-result-v0",
            "eat_profile": EAT_PROFILE,
            "intuse": 5,
            "iss": "https://verifier.invalid/software-prototype",
            "iat": issued_at,
            "exp": expires_at,
            "eat_nonce": nonce,
            "aud": audience,
            "candidate_ref": candidate_ref,
            "route_ticket_digest_sha256": route_ticket_digest_sha256,
            "cnf": {"COSE_Key": self.public_key_claim()},
            "runtime": {
                "measurement_sha256": "a" * 64,
                "profile_id": "iicp-confidential-worker-software-only-v0",
                "debug": False,
                "tcb_status": "up_to_date",
                "protected_components": ["cpu", "memory", "runtime"],
            },
        }
        result["binding_digest_sha256"] = binding_digest(result)
        return result

    def open_envelope(self, envelope: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
        if self._retired:
            raise ValueError("execution key retired")
        assert self._execution_key is not None
        required = {
            "version",
            "recipient_key_id",
            "kem_ciphertext",
            "encrypted_body",
            "nonce",
            "aad",
            "plaintext_size",
        }
        if set(envelope) != required or envelope["version"] != 1:
            raise ValueError("unsupported IICP-CX envelope")
        expected_key_id = self.public_key_claim()["kid"]
        if envelope["recipient_key_id"] != expected_key_id:
            raise ValueError("recipient key mismatch")
        aad = b64url_decode(envelope["aad"])
        task_id, separator, intent = aad.decode("utf-8").partition("|")
        if not separator or not task_id or not intent:
            raise ValueError("invalid IICP-CX AAD")
        if task_id in self._accepted_task_ids:
            raise ValueError("task replay")
        peer_public = X25519PublicKey.from_public_bytes(
            b64url_decode(envelope["kem_ciphertext"])
        )
        shared_secret = self._execution_key.exchange(peer_public)
        nonce = b64url_decode(envelope["nonce"])
        key = derive_key(
            shared_secret,
            nonce,
            REQUEST_INFO_PREFIX + task_id.encode() + intent.encode(),
        )
        plaintext = AESGCM(key).decrypt(
            nonce, b64url_decode(envelope["encrypted_body"]), aad
        )
        if len(plaintext) != envelope["plaintext_size"]:
            raise ValueError("plaintext size mismatch")
        self._accepted_task_ids.add(task_id)
        return json.loads(plaintext), shared_secret

    def seal_response(
        self, response: dict[str, Any], shared_secret: bytes, task_id: str
    ) -> dict[str, Any]:
        nonce = os.urandom(12)
        key = derive_key(shared_secret, nonce, RESPONSE_INFO_PREFIX + task_id.encode())
        aad = f"{task_id}|resp".encode()
        body = json.dumps(response, sort_keys=True, separators=(",", ":")).encode()
        return {
            "version": 1,
            "nonce": b64url(nonce),
            "encrypted_body": b64url(AESGCM(key).encrypt(nonce, body, aad)),
        }

    def retire(self) -> None:
        self._retired = True
        self._execution_key = None


class SyntheticVerifier:
    """Stand-in for vendor-evidence appraisal and COSE_Sign1 issuance."""

    def __init__(self, signing_key: Ed25519PrivateKey) -> None:
        self._signing_key = signing_key

    def appraise(self, evidence: dict[str, Any]) -> dict[str, Any]:
        return sign(evidence, self._signing_key)


def encrypt_existing_cx_envelope(
    payload: dict[str, Any],
    result: dict[str, Any],
    *,
    task_id: str,
    intent: str,
) -> tuple[dict[str, Any], ConsumerContext]:
    key_claim = result["cnf"]["COSE_Key"]
    recipient = X25519PublicKey.from_public_bytes(b64url_decode(key_claim["x"]))
    client_private = X25519PrivateKey.generate()
    client_public = client_private.public_key().public_bytes(
        Encoding.Raw, PublicFormat.Raw
    )
    shared_secret = client_private.exchange(recipient)
    nonce = os.urandom(12)
    aad = f"{task_id}|{intent}".encode()
    plaintext = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    key = derive_key(
        shared_secret,
        nonce,
        REQUEST_INFO_PREFIX + task_id.encode() + intent.encode(),
    )
    envelope = {
        "version": 1,
        "recipient_key_id": key_claim["kid"],
        "kem_ciphertext": b64url(client_public),
        "encrypted_body": b64url(AESGCM(key).encrypt(nonce, plaintext, aad)),
        "nonce": b64url(nonce),
        "aad": b64url(aad),
        "plaintext_size": len(plaintext),
    }
    return envelope, ConsumerContext(task_id=task_id, shared_secret=shared_secret)


def decrypt_existing_cx_response(
    envelope: dict[str, Any], context: ConsumerContext
) -> dict[str, Any]:
    nonce = b64url_decode(envelope["nonce"])
    key = derive_key(
        context.shared_secret,
        nonce,
        RESPONSE_INFO_PREFIX + context.task_id.encode(),
    )
    aad = f"{context.task_id}|resp".encode()
    plaintext = AESGCM(key).decrypt(
        nonce, b64url_decode(envelope["encrypted_body"]), aad
    )
    return json.loads(plaintext)


def verify_and_prove_possession(
    *,
    result: dict[str, Any],
    policy: dict[str, Any],
    verifier_public_key: Any,
    worker: SoftwareConfidentialWorker,
    seen_evidence_refs: set[str],
) -> None:
    outcome = verify_result(result, policy, verifier_public_key, seen_evidence_refs)
    if outcome != "PASS":
        raise ValueError(f"attestation rejected: {outcome}")
    challenge = {"challenge": b64url(os.urandom(32))}
    envelope, context = encrypt_existing_cx_envelope(
        challenge,
        result,
        task_id="execution-privacy-pop-v0",
        intent=PROOF_INTENT,
    )
    opened, shared_secret = worker.open_envelope(envelope)
    acknowledgement = worker.seal_response(
        {"challenge_sha256": hashlib.sha256(opened["challenge"].encode()).hexdigest()},
        shared_secret,
        context.task_id,
    )
    confirmed = decrypt_existing_cx_response(acknowledgement, context)
    expected = hashlib.sha256(challenge["challenge"].encode()).hexdigest()
    if confirmed.get("challenge_sha256") != expected:
        raise ValueError("execution-key proof of possession failed")


def run_demo() -> dict[str, Any]:
    verifier_private = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
    verifier_public = verifier_private.public_key()
    worker = SoftwareConfidentialWorker()
    verifier = SyntheticVerifier(verifier_private)
    now = int(time.time())
    policy = {
        "now": now,
        "expected_nonce": b64url(os.urandom(32)),
        "expected_audience": "iicp-consumer-session-software-v0",
        "expected_candidate_ref": "sha256:" + "c" * 64,
        "expected_route_ticket_digest_sha256": route_ticket_digest(
            "synthetic-route-ticket"
        ),
        "accepted_eat_profiles": [EAT_PROFILE],
        "accepted_measurements": ["a" * 64],
        "accepted_tcb_status": ["up_to_date"],
        "required_protected_components": ["cpu", "memory", "runtime"],
    }
    evidence = worker.evidence(
        nonce=policy["expected_nonce"],
        audience=policy["expected_audience"],
        candidate_ref=policy["expected_candidate_ref"],
        route_ticket_digest_sha256=policy["expected_route_ticket_digest_sha256"],
        issued_at=now - 1,
        expires_at=now + 60,
    )
    result = verifier.appraise(evidence)
    verify_and_prove_possession(
        result=result,
        policy=policy,
        verifier_public_key=verifier_public,
        worker=worker,
        seen_evidence_refs=set(),
    )
    task_id = "execution-privacy-task-v0"
    task, consumer_context = encrypt_existing_cx_envelope(
        {"synthetic": "payload"},
        result,
        task_id=task_id,
        intent="urn:iicp:intent:llm:chat:v1",
    )
    opened, shared_secret = worker.open_envelope(task)
    response = worker.seal_response(
        {"task_id": task_id, "status": "success", "result": opened},
        shared_secret,
        task_id,
    )
    recovered = decrypt_existing_cx_response(response, consumer_context)
    worker.retire()
    public_result = copy.deepcopy(result)
    return {
        "evidence_class": "software-simulation-only",
        "verification": "PASS",
        "proof_of_possession": "PASS",
        "existing_cx_envelope_keys": sorted(task),
        "response_context": recovered["task_id"],
        "key_retired": True,
        "attestation_result": public_result,
        "non_claims": [
            "not_hardware_attestation",
            "not_operator_isolation",
            "not_private_key_containment_evidence",
            "not_cose_sign1_encoding",
        ],
    }


def main() -> int:
    result = run_demo()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
