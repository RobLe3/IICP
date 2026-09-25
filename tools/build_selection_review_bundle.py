#!/usr/bin/env python3
"""Build the deterministic public IICP selection/eligibility review bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "build/selection-review"
ZIP_TIME = (2026, 8, 21, 0, 0, 0)
BUNDLE_NAME = "iicp-selection-eligibility-review-candidate"

PUBLIC_INPUTS = (
    "LICENSE",
    "SPEC_STATUS.md",
    "IMPLEMENTATIONS.md",
    "VERSIONING.md",
    "SECURITY.md",
    "CONTINUATION.md",
    "TERMINOLOGY_AND_DISCOVERABILITY.md",
    "ecosystem/public-repositories.json",
    "ecosystem/CURRENT_VERSIONS.md",
    "pre1/README.md",
    "pre1/feature-baseline-v1.json",
    "standards/REVIEWING.md",
    "standards/SELECTION_REVIEW_BUNDLE_README.md",
    "standards/SELECTION_ELIGIBILITY_PROBLEM_STATEMENT.md",
    "standards/SELECTION_TRUST_AND_REVALIDATION.md",
    "standards/SELECTION_CANDIDATE_ADVERSARIAL_REVIEW_2026-08-21.md",
    "standards/IICP_PROTOCOL_POSITIONING.md",
    "standards/PROTOCOL_COMPARISON_2026-08-15.md",
    "standards/PROTOCOL_COMPARISON_2026-09-25.md",
    "standards/protocol-comparison-v1.json",
    "standards/EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-08-21.md",
    "standards/EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-09-25.md",
    "standards/TRANSPORT_BINDING_AND_PORT_DECISION_2026-08-21.md",
    "docs/architecture/effective-service-capability-semantics.md",
    "docs/architecture/effective-service-capability-v1.json",
    "docs/architecture/directory-state-semantics.md",
    "docs/architecture/directory-state-semantics-v1.json",
    "docs/architecture/environmental-independence-v1.json",
    "docs/architecture/identifier-and-registry-architecture.md",
    "docs/architecture/identifier-registry-v1.json",
    "docs/architecture/node-observability-interfaces.md",
    "docs/architecture/node-observability-v1.json",
    "docs/architecture/environmental-independence-and-extension-architecture.md",
    "docs/security/privacy-adversary-and-trust-model.md",
    "research/pre-normative-profiles/restricted-trust-domain-v0.md",
    "research/pre-normative-profiles/fixtures/effective-capability-v1.json",
    "research/pre-normative-profiles/fixtures/restricted-trust-domain-v0.json",
    "research/pre-normative-profiles/selection-profile-v1.md",
    "schemas/capability-requirements-v1.json",
    "schemas/capability-refusal-v1.json",
    "registry/fixtures/intent-payloads-v1.json",
    "spec/v1.9/iicp-core.md",
    "spec/v1.9/iicp-semantics.md",
    "spec/v1.9/iicp-dir.md",
    "spec/v1.9/iicp-federated-directory.md",
    "spec/v1.9/conformance-test-suite.md",
    # Local references needed to read the reviewed documents in isolation.
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "SPEC_RELEASE_PROCESS.md",
    "docs/architecture/task-time-semantics-v1.json",
    "docs/architecture/task-time-semantics.md",
    "docs/governance/public-artifact-boundary.md",
    "ecosystem/repositories.json",
    "research/RESEARCH.md",
    "research/native-ai-infrastructure/fixtures/native-framing-fixture-manifest-v1.json",
    "research/native-ai-infrastructure/fixtures/native-framing-v1.json",
    "research/pre-normative-profiles/dispatch-ticket-trust-profile-v2.md",
    "research/pre-normative-profiles/endpoint-security-profile-v1.md",
    "research/pre-normative-profiles/fixtures/reputation-outcome-v2.json",
    "research/pre-normative-profiles/restricted-trust-domain-membership-v0.md",
    "research/strategic/2026-07-11-layered-intent-capability-research.md",
    "research/strategic/2026-08-12-execution-privacy-and-attested-confidential-execution.md",
    "research/strategic/2026-08-12-heterogeneous-model-quality-and-learned-routing.md",
    "research/strategic/2026-08-21-outcome-v2-implementation-experience.md",
    "research/strategic/2026-08-21-weekly-intelligence-disposition.md",
    "research/strategic/execution-privacy-feasibility/README.md",
    "research/strategic/execution-privacy-feasibility/profile-v0.md",
    "research/strategic/execution-privacy-feasibility/software_prototype.py",
    "research/strategic/learned-routing-experiment/README.md",
    "schemas/effective-capability-advertisement-v1.json",
    "spec/v1.9/iicp-cbor-wire.md",
    "spec/v1.9/iicp-confidentiality.md",
    "spec/v1.9/iicp-framing.md",
    "spec/v1.9/iicp-service-lifecycle-profile.md",
    "spec/v1.9/replica-lifecycle-contract-v1.json",
    "standards/IETF_AGENT_PROTOCOL_LANDSCAPE_2026-08-08.md",
    "standards/SECURITY_PRIVACY_OPERATIONAL_CONSIDERATIONS_2026-08-13.md",
    "standards/STANDARDS_READINESS.md",
    "standards/ietf/evidence-matrix.md",
    "tools/build_internet_draft.sh",
    "tools/check_native_framing_fixtures.py",
)


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def write_member(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(name, ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content, compresslevel=9)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    missing = [relative for relative in PUBLIC_INPUTS if not (ROOT / relative).is_file()]
    if missing:
        raise SystemExit("selection review input missing:\n- " + "\n- ".join(missing))

    subprocess.run(
        ["python3", str(ROOT / "tools/check_public_artifact_closure.py")],
        cwd=ROOT,
        check=True,
    )

    members = {relative: (ROOT / relative).read_bytes() for relative in PUBLIC_INPUTS}
    manifest = {
        "schema": "iicp.selection-review-bundle.v1",
        "status": "project review candidate; not submitted or externally ratified",
        "scope": "selection and eligibility before endpoint authentication and execution binding",
        "files": {name: digest(content) for name, content in sorted(members.items())},
    }
    members["SHA256SUMS.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    bundle = output / f"{BUNDLE_NAME}.zip"
    prefix = f"{BUNDLE_NAME}/"
    with zipfile.ZipFile(bundle, "w") as archive:
        for name, content in sorted(members.items()):
            write_member(archive, prefix + name, content)

    checksum = digest(bundle.read_bytes())
    bundle.with_suffix(".zip.sha256").write_text(
        f"{checksum}  {bundle.name}\n", encoding="ascii"
    )
    print(f"built {bundle}")
    print(f"sha256 {checksum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
