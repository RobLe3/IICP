#!/usr/bin/env python3
"""Fail when a pre-normative fixture diverges from its digest manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "research/pre-normative-profiles/fixtures"
MANIFEST = FIXTURES / "profile-fixture-manifest-v0.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    errors: list[str] = []
    for item in manifest["fixtures"]:
        path = FIXTURES / item["path"]
        if not path.is_file():
            errors.append(f"missing: {item['path']}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item["sha256"]:
            errors.append(
                f"digest mismatch: {item['path']} {digest} != {item['sha256']}"
            )
    if errors:
        raise SystemExit("fixture manifest check failed:\n" + "\n".join(errors))
    print(f"PASS {len(manifest['fixtures'])} pre-normative profile fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
