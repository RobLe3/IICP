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
    "standards/REVIEWING.md",
    "standards/STANDARDS_READINESS.md",
    "standards/SECURITY_PRIVACY_OPERATIONAL_CONSIDERATIONS_2026-08-13.md",
    "standards/ietf/README.md",
    "standards/ietf/evidence-matrix.md",
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
