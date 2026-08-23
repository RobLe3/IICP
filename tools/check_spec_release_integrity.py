#!/usr/bin/env python3
"""Fail-closed integrity gate for a reviewed spec-only release candidate."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "spec/v1.9/release-integrity-manifest.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    errors: list[str] = []
    if (ROOT / "spec/v1.9/VERSION").read_text().strip() != manifest["protocol_suite_version"]:
        errors.append("suite version differs from release manifest")
    registry = json.loads((ROOT / "registry/intents.json").read_text())
    if registry.get("version") != manifest["registry_version"]:
        errors.append("registry version differs from release manifest")
    from check_intent_registry import validate as validate_intent_registry
    errors.extend(f"intent registry: {error}" for error in validate_intent_registry(registry))
    ecosystem = json.loads((ROOT / "ecosystem/repositories.json").read_text())
    specification = next(
        (item for item in ecosystem["repositories"] if item["id"] == "specification"),
        None,
    )
    if specification is None or specification.get("release") != manifest["protocol_suite_version"]:
        errors.append("ecosystem specification release differs from suite version")
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
        elif digest(path) != expected:
            errors.append(f"digest mismatch: {relative}")
    from check_public_artifact_closure import validate as validate_public_artifacts
    errors.extend(
        f"public artifact closure: {finding.path}:{finding.line}: {finding.message}"
        for finding in validate_public_artifacts(ROOT)
    )
    required = {
        "LICENSE",
        "GOVERNANCE.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CONTINUATION.md",
        "CHANGELOG.md",
        "ecosystem/repositories.json",
        "ecosystem/public-repositories.json",
        "SPEC_STATUS.md",
        "VERSIONING.md",
        "registry/intents.json",
        "registry/README.md",
        "spec/v1.9/VERSION",
        "spec/v1.9/iicp-core.md",
        "spec/v1.9/iicp-framing.md",
        "spec/v1.9/conformance-test-suite.md",
        "tools/check_intent_registry.py",
        "tools/test_intent_registry.py",
        "registry/schemas/intent-registry-v1.4.json",
        "tools/requirements.txt",
        "tools/check_intent_registry_schema.py",
        "spec/v1.9/iicp-service-lifecycle-profile.md",
        "research/native-ai-infrastructure/fixtures/service-profiles-v1.json",
        "tools/test_service_lifecycle_fixture.py",
        "docs/operator-onboarding-recovery.md",
        "docs/governance/public-artifact-boundary.md",
        "docs/security/privacy-adversary-and-trust-model.md",
        "docs/architecture/environmental-independence-and-extension-architecture.md",
        "docs/architecture/environmental-independence-v1.json",
        "tools/test_environmental_independence_decision.py",
        "docs/architecture/identifier-and-registry-architecture.md",
        "docs/architecture/identifier-registry-v1.json",
        "tools/test_identifier_registry_architecture.py",
        "docs/architecture/task-time-semantics.md",
        "docs/architecture/task-time-semantics-v1.json",
        "tools/test_task_time_semantics.py",
        "docs/architecture/directory-state-semantics.md",
        "docs/architecture/directory-state-semantics-v1.json",
        "docs/architecture/node-observability-interfaces.md",
        "docs/architecture/node-observability-v1.json",
        "tools/test_node_observability_contract.py",
        "tools/test_directory_state_semantics.py",
        "docs/architecture/effective-service-capability-semantics.md",
        "docs/architecture/effective-service-capability-v1.json",
        "tools/test_effective_service_capability_semantics.py",
        "schemas/effective-capability-advertisement-v1.json",
        "schemas/capability-requirements-v1.json",
        "schemas/capability-refusal-v1.json",
        "schemas/ecosystem-version-truth-v1.json",
        "schemas/samples/ecosystem-version-truth-release-ahead.json",
        "schemas/samples/ecosystem-version-truth-stale.json",
        "schemas/samples/ecosystem-version-truth-unavailable.json",
        "docs/ECOSYSTEM_VERSION_TRUTH.md",
        "tools/check_ecosystem_version_truth.py",
        "tools/test_ecosystem_version_truth.py",
        "research/pre-normative-profiles/fixtures/effective-capability-v1.json",
        "tools/test_effective_capability_wire_contract.py",
        "research/pre-normative-profiles/fixtures/runtime-identity-context-v0.json",
        "research/pre-normative-profiles/restricted-trust-domain-v0.md",
        "research/pre-normative-profiles/schemas/restricted-trust-domain-v0.schema.json",
        "research/pre-normative-profiles/fixtures/restricted-trust-domain-v0.json",
        "tools/test_restricted_trust_domain_fixture.py",
        "research/pre-normative-profiles/schemas/restricted-trust-domain-directory-decision-v0.schema.json",
        "research/pre-normative-profiles/fixtures/restricted-trust-domain-directory-decision-v0.json",
        "tools/test_restricted_directory_decision_fixture.py",
        "research/pre-normative-profiles/restricted-trust-domain-membership-v0.md",
        "research/pre-normative-profiles/schemas/restricted-trust-domain-membership-v0.schema.json",
        "research/pre-normative-profiles/fixtures/restricted-trust-domain-membership-v0.json",
        "tools/test_restricted_trust_domain_membership.py",
        "research/pre-normative-profiles/schemas/restricted-trust-domain-bootstrap-v0.schema.json",
        "research/pre-normative-profiles/fixtures/restricted-trust-domain-bootstrap-v0.json",
        "tools/test_restricted_trust_domain_bootstrap.py",
        "research/pre-normative-profiles/local-directory-discovery-v0.md",
        "research/pre-normative-profiles/schemas/local-directory-discovery-v0.schema.json",
        "research/pre-normative-profiles/fixtures/local-directory-discovery-v0.json",
        "tools/test_local_directory_discovery.py",
        "research/strategic/2026-08-14-runtime-identity-and-self-description-decision.md",
        "research/strategic/2026-08-21-outcome-v2-implementation-experience.md",
        "tools/test_runtime_identity_context.py",
        "research/pre-normative-profiles/fixtures/operator-onboarding-recovery-v1.json",
        "research/pre-normative-profiles/fixtures/e050-client-credential-lifecycle-v1.json",
        "tools/check_e050_client_credential_lifecycle.py",
        "tools/test_e050_client_credential_lifecycle.py",
        "tools/check_operator_onboarding_recovery.py",
        "tools/test_operator_onboarding_recovery.py",
        "docs/external-evidence-participation.md",
        "docs/oia-application-matrix.md",
        "evidence/external-participation-campaign-v1.json",
        "evidence/newcomer-validation-record-v1.json",
        "evidence/clean-room-interoperability-record-v1.json",
        "evidence/public-evidence-access-v1.json",
        "tools/check_newcomer_validation_record.py",
        "tools/test_newcomer_validation_record.py",
        "tools/check_clean_room_interoperability_record.py",
        "tools/test_clean_room_interoperability_record.py",
        "tools/check_external_participation_campaign.py",
        "tools/test_external_participation_campaign.py",
        "standards/SUBMISSION_GOVERNANCE_DECISION.md",
        "standards/submission-governance-decision-v1.json",
        "standards/IICP_PROTOCOL_POSITIONING.md",
        "standards/SELECTION_ELIGIBILITY_PROBLEM_STATEMENT.md",
        "standards/SELECTION_TRUST_AND_REVALIDATION.md",
        "standards/SELECTION_CANDIDATE_ADVERSARIAL_REVIEW_2026-08-21.md",
        "standards/SELECTION_REVIEW_BUNDLE_README.md",
        "standards/TRANSPORT_BINDING_AND_PORT_DECISION_2026-08-21.md",
        "standards/REVIEWING.md",
        "standards/PROTOCOL_COMPARISON_2026-08-15.md",
        "standards/EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-08-21.md",
        "standards/protocol-comparison-v1.json",
        "tools/check_protocol_comparison.py",
        "tools/test_protocol_comparison.py",
        "tools/check_submission_governance_decision.py",
        "tools/test_submission_governance_decision.py",
        "research/strategic/2026-08-13-signed-message-envelope-boundary.md",
        "research/pre-normative-profiles/fixtures/signed-message-envelope-boundary-v0.json",
        "tools/check_signed_message_envelope_boundary.py",
        "tools/test_signed_message_envelope_boundary.py",
        "tools/check_public_evidence_access.py",
        "tools/test_public_evidence_access.py",
        "tools/check_public_artifact_closure.py",
        "tools/test_public_artifact_closure.py",
        "tools/build_selection_review_bundle.py",
        "tools/test_selection_review_bundle.py",
    }
    missing_pins = sorted(required - set(manifest["files"]))
    if missing_pins:
        errors.append("required release artifacts are not pinned: " + ", ".join(missing_pins))
    if errors:
        print("spec release integrity check failed:", *errors, sep="\n- ", file=sys.stderr)
        return 1
    print(
        "spec release integrity check passed: "
        f"suite v{manifest['protocol_suite_version']}, registry v{manifest['registry_version']}, "
        f"{len(manifest['files'])} pinned artifacts"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
