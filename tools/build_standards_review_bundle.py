#!/usr/bin/env python3
"""Build a deterministic, self-contained review bundle for the IICP peer draft.

The rendered XML, text and HTML must already have been produced by the pinned
Internet-Draft build. This tool packages them with the source, public evidence
and a digest manifest. It never uploads or submits the draft.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "standards/ietf/draft-roble-iicp-peer.md"
DEFAULT_RENDERED = ROOT / "build/ietf"
DEFAULT_OUTPUT = ROOT / "build/standards-review"
ZIP_TIME = (2026, 8, 15, 0, 0, 0)

PUBLIC_INPUTS = (
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CONTINUATION.md",
    "docs/governance/public-artifact-boundary.md",
    "docs/security/privacy-adversary-and-trust-model.md",
    "ecosystem/public-repositories.json",
    "ecosystem/CURRENT_VERSIONS.md",
    "pre1/README.md",
    "pre1/feature-baseline-v1.json",
    "standards/REVIEWING.md",
    "standards/IICP_PROTOCOL_POSITIONING.md",
    "standards/PROTOCOL_COMPARISON_2026-08-15.md",
    "standards/PROTOCOL_COMPARISON_2026-09-25.md",
    "standards/EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-08-21.md",
    "standards/EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-09-25.md",
    "standards/protocol-comparison-v1.json",
    "docs/architecture/directory-state-semantics-v1.json",
    "docs/architecture/directory-state-semantics.md",
    "docs/architecture/effective-service-capability-semantics.md",
    "docs/architecture/effective-service-capability-v1.json",
    "schemas/effective-capability-advertisement-v1.json",
    "schemas/capability-requirements-v1.json",
    "schemas/capability-refusal-v1.json",
    "docs/architecture/environmental-independence-and-extension-architecture.md",
    "docs/architecture/environmental-independence-v1.json",
    "docs/architecture/identifier-and-registry-architecture.md",
    "docs/architecture/identifier-registry-v1.json",
    "registry/fixtures/intent-payloads-v1.json",
    "research/pre-normative-profiles/fixtures/effective-capability-v1.json",
    "research/pre-normative-profiles/fixtures/restricted-trust-domain-v0.json",
    "research/pre-normative-profiles/restricted-trust-domain-v0.md",
    "spec/v1.9/conformance-test-suite.md",
    "spec/v1.9/iicp-core.md",
    "spec/v1.9/iicp-dir.md",
    "spec/v1.9/iicp-federated-directory.md",
    "spec/v1.9/iicp-semantics.md",
    "standards/STANDARDS_READINESS.md",
    "standards/SECURITY_PRIVACY_OPERATIONAL_CONSIDERATIONS_2026-08-13.md",
    "standards/ietf/README.md",
    "standards/ietf/evidence-matrix.md",
    # Local references needed to read the reviewed documents in isolation.
    "GOVERNANCE.md",
    "IMPLEMENTATIONS.md",
    "SPEC_RELEASE_PROCESS.md",
    "SPEC_STATUS.md",
    "VERSIONING.md",
    "docs/architecture/task-time-semantics-v1.json",
    "docs/architecture/task-time-semantics.md",
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
    "spec/v1.9/iicp-cbor-wire.md",
    "spec/v1.9/iicp-confidentiality.md",
    "spec/v1.9/iicp-framing.md",
    "spec/v1.9/iicp-service-lifecycle-profile.md",
    "spec/v1.9/replica-lifecycle-contract-v1.json",
    "standards/IETF_AGENT_PROTOCOL_LANDSCAPE_2026-08-08.md",
    "standards/SELECTION_CANDIDATE_ADVERSARIAL_REVIEW_2026-08-21.md",
    "standards/SELECTION_ELIGIBILITY_PROBLEM_STATEMENT.md",
    "standards/SELECTION_TRUST_AND_REVALIDATION.md",
    "standards/TRANSPORT_BINDING_AND_PORT_DECISION_2026-08-21.md",
    "tools/build_internet_draft.sh",
    "tools/check_native_framing_fixtures.py",
)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def zip_write(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(name, ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content, compresslevel=9)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--rendered-dir", type=Path, default=DEFAULT_RENDERED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    source = args.source.resolve()
    rendered = args.rendered_dir.resolve()
    output = args.output_dir.resolve()
    base = source.stem
    rendered_files = [rendered / f"{base}.{suffix}" for suffix in ("xml", "txt", "html")]

    missing = [str(path) for path in [source, *rendered_files] if not path.is_file()]
    missing.extend(relative for relative in PUBLIC_INPUTS if not (ROOT / relative).is_file())
    if missing:
        raise SystemExit("review bundle input missing:\n- " + "\n- ".join(missing))

    subprocess.run(
        ["python3", str(ROOT / "tools/check_public_artifact_closure.py")],
        cwd=ROOT,
        check=True,
    )

    members: dict[str, bytes] = {
        relative: (ROOT / relative).read_bytes() for relative in PUBLIC_INPUTS
    }
    source_name = f"standards/ietf/{source.name}"
    members[source_name] = source.read_bytes()
    for path in rendered_files:
        members[f"rendered/{path.name}"] = path.read_bytes()

    manifest = {
        "schema": "iicp.standards-review-bundle.v1",
        "status": "individual-draft-candidate; not submitted",
        "draft": base,
        "files": {
            name: sha256_bytes(content) for name, content in sorted(members.items())
        },
    }
    members["SHA256SUMS.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    output.mkdir(parents=True, exist_ok=True)
    bundle = output / f"{base}-review-bundle.zip"
    prefix = f"{base}-review-bundle/"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name, content in sorted(members.items()):
            zip_write(zf, prefix + name, content)

    digest = sha256_bytes(bundle.read_bytes())
    bundle.with_suffix(".zip.sha256").write_text(
        f"{digest}  {bundle.name}\n", encoding="ascii"
    )
    print(f"built {bundle}")
    print(f"sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
