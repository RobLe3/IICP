#!/usr/bin/env python3
"""Regression tests for the synthetic execution-privacy binding fixture."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

try:
    import cryptography  # noqa: F401
except ModuleNotFoundError:
    HAS_CRYPTOGRAPHY = False
else:
    HAS_CRYPTOGRAPHY = True

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "research"
    / "strategic"
    / "execution-privacy-feasibility"
    / "verify_vectors.py"
)
FIXTURE_PATH = MODULE_PATH.with_name("vectors-v1.json")
PROTOTYPE_PATH = MODULE_PATH.with_name("software_prototype.py")
if HAS_CRYPTOGRAPHY:
    SPEC = importlib.util.spec_from_file_location(
        "execution_privacy_vectors", MODULE_PATH
    )
    assert SPEC and SPEC.loader
    MODULE = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(MODULE)
    sys.path.insert(0, str(MODULE_PATH.parent))
    PROTOTYPE_SPEC = importlib.util.spec_from_file_location(
        "execution_privacy_software_prototype", PROTOTYPE_PATH
    )
    assert PROTOTYPE_SPEC and PROTOTYPE_SPEC.loader
    PROTOTYPE = importlib.util.module_from_spec(PROTOTYPE_SPEC)
    sys.modules[PROTOTYPE_SPEC.name] = PROTOTYPE
    PROTOTYPE_SPEC.loader.exec_module(PROTOTYPE)
else:
    MODULE = None
    PROTOTYPE = None


@unittest.skipUnless(
    HAS_CRYPTOGRAPHY, "optional cryptography dependency is unavailable"
)
class ExecutionPrivacyFixtureTests(unittest.TestCase):
    def test_all_vectors_match_expected_outcomes(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        results = MODULE.verify_fixture(fixture)
        self.assertEqual(len(results), 17)
        self.assertTrue(all(expected == actual for _, expected, actual in results))

    def test_fixture_is_deterministic(self) -> None:
        generated = json.dumps(MODULE.make_fixture(), indent=2, sort_keys=True) + "\n"
        self.assertEqual(FIXTURE_PATH.read_text(encoding="utf-8"), generated)

    def test_fixture_is_content_free_and_contains_no_private_key(self) -> None:
        fixture_text = FIXTURE_PATH.read_text(encoding="utf-8")
        lowered = fixture_text.lower()
        for forbidden in (
            "prompt",
            "response content",
            '"route_ticket":',
            "endpoint",
            "hardware_serial",
            "raw_vendor_quote",
        ):
            self.assertNotIn(forbidden, lowered)
        fixture = json.loads(fixture_text)

        def keys(value: object) -> set[str]:
            if isinstance(value, dict):
                return set(value) | set().union(
                    *(keys(item) for item in value.values())
                )
            if isinstance(value, list):
                return set().union(*(keys(item) for item in value))
            return set()

        self.assertNotIn("private_key", keys(fixture))
        self.assertEqual(fixture["evidence_class"], "synthetic-research-only")
        self.assertIn("not_hardware_attestation", fixture["non_claims"])

    def test_software_prototype_reuses_existing_cx_envelope(self) -> None:
        result = PROTOTYPE.run_demo()
        self.assertEqual(result["verification"], "PASS")
        self.assertEqual(result["proof_of_possession"], "PASS")
        self.assertEqual(result["response_context"], "execution-privacy-task-v0")
        self.assertEqual(
            result["existing_cx_envelope_keys"],
            sorted(
                {
                    "version",
                    "recipient_key_id",
                    "kem_ciphertext",
                    "encrypted_body",
                    "nonce",
                    "aad",
                    "plaintext_size",
                }
            ),
        )
        self.assertIn("not_hardware_attestation", result["non_claims"])

    def test_retired_execution_key_cannot_be_reused(self) -> None:
        worker = PROTOTYPE.SoftwareConfidentialWorker()
        worker.retire()
        with self.assertRaisesRegex(ValueError, "execution key retired"):
            worker.public_key_claim()

    def test_proof_of_possession_rejects_unrelated_worker(self) -> None:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
        )

        signer = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
        attested_worker = PROTOTYPE.SoftwareConfidentialWorker()
        unrelated_worker = PROTOTYPE.SoftwareConfidentialWorker()
        now = 1_800_000_000
        policy = {
            "now": now,
            "expected_nonce": "consumer-challenge-v0",
            "expected_audience": "iicp-consumer-session-v0",
            "expected_candidate_ref": "sha256:" + "c" * 64,
            "expected_route_ticket_digest_sha256": "d" * 64,
            "accepted_eat_profiles": [MODULE.EAT_PROFILE],
            "accepted_measurements": ["a" * 64],
            "accepted_tcb_status": ["up_to_date"],
            "required_protected_components": ["cpu", "memory", "runtime"],
        }
        evidence = attested_worker.evidence(
            nonce=policy["expected_nonce"],
            audience=policy["expected_audience"],
            candidate_ref=policy["expected_candidate_ref"],
            route_ticket_digest_sha256=policy["expected_route_ticket_digest_sha256"],
            issued_at=now - 1,
            expires_at=now + 60,
        )
        result = PROTOTYPE.SyntheticVerifier(signer).appraise(evidence)
        with self.assertRaises(ValueError):
            PROTOTYPE.verify_and_prove_possession(
                result=result,
                policy=policy,
                verifier_public_key=signer.public_key(),
                worker=unrelated_worker,
                seen_evidence_refs=set(),
            )

    def test_response_context_substitution_fails(self) -> None:
        result = PROTOTYPE.run_demo()
        self.assertEqual(result["response_context"], "execution-privacy-task-v0")
        # The primitive is covered in the successful demo. This direct negative
        # uses a fresh flow so changing the task context invalidates response AEAD.
        from cryptography.exceptions import InvalidTag
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
        )

        signer = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
        worker = PROTOTYPE.SoftwareConfidentialWorker()
        now = 1_800_000_000
        evidence = worker.evidence(
            nonce="consumer-challenge-v0",
            audience="iicp-consumer-session-v0",
            candidate_ref="sha256:" + "c" * 64,
            route_ticket_digest_sha256="d" * 64,
            issued_at=now - 1,
            expires_at=now + 60,
        )
        signed = PROTOTYPE.SyntheticVerifier(signer).appraise(evidence)
        envelope, context = PROTOTYPE.encrypt_existing_cx_envelope(
            {"synthetic": "payload"},
            signed,
            task_id="task-a",
            intent="urn:iicp:intent:llm:chat:v1",
        )
        _, shared_secret = worker.open_envelope(envelope)
        response = worker.seal_response({"task_id": "task-a"}, shared_secret, "task-a")
        wrong_context = PROTOTYPE.ConsumerContext(
            task_id="task-b", shared_secret=context.shared_secret
        )
        with self.assertRaises(InvalidTag):
            PROTOTYPE.decrypt_existing_cx_response(response, wrong_context)


if __name__ == "__main__":
    unittest.main()
