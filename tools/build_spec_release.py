#!/usr/bin/env python3
"""Build a deterministic, content-addressed IICP specification release archive."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "spec/v1.9/release-integrity-manifest.json"
ZIP_TIME = (2026, 7, 30, 0, 0, 0)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build/spec-release")
    args = parser.parse_args()

    subprocess.run(
        ["python3", str(ROOT / "tools/check_spec_release_integrity.py")],
        cwd=ROOT,
        check=True,
    )

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    version = manifest["protocol_suite_version"]
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"iicp-spec-v{version}.zip"

    members = sorted({*manifest["files"], "spec/v1.9/release-integrity-manifest.json"})
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for relative in members:
            info = zipfile.ZipInfo(f"iicp-spec-v{version}/{relative}", ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, (ROOT / relative).read_bytes(), compresslevel=9)

    digest = sha256(archive)
    checksum = archive.with_suffix(".zip.sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print(f"built {archive}")
    print(f"sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
