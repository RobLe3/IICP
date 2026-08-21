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
    "standards/REVIEWING.md",
    "standards/SELECTION_REVIEW_BUNDLE_README.md",
    "standards/SELECTION_ELIGIBILITY_PROBLEM_STATEMENT.md",
    "standards/SELECTION_TRUST_AND_REVALIDATION.md",
    "standards/IICP_PROTOCOL_POSITIONING.md",
    "standards/PROTOCOL_COMPARISON_2026-08-15.md",
    "standards/protocol-comparison-v1.json",
    "standards/EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-08-21.md",
    "standards/TRANSPORT_BINDING_AND_PORT_DECISION_2026-08-21.md",
    "docs/architecture/effective-service-capability-semantics.md",
    "docs/architecture/effective-service-capability-v1.json",
    "docs/architecture/directory-state-semantics.md",
    "docs/architecture/node-observability-interfaces.md",
    "docs/architecture/node-observability-v1.json",
    "docs/architecture/environmental-independence-and-extension-architecture.md",
    "docs/security/privacy-adversary-and-trust-model.md",
    "research/pre-normative-profiles/restricted-trust-domain-v0.md",
    "research/pre-normative-profiles/selection-profile-v1.md",
    "schemas/capability-requirements-v1.json",
    "schemas/capability-refusal-v1.json",
    "spec/v1.9/iicp-core.md",
    "spec/v1.9/iicp-semantics.md",
    "spec/v1.9/iicp-dir.md",
    "spec/v1.9/conformance-test-suite.md",
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
