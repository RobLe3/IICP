#!/usr/bin/env python3
"""Validate the bounded #56/#58 pre-normative candidate manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "research/pre-normative-profiles/fixtures"
MANIFEST = FIXTURES / "profile-security-candidate-manifest-v0.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    if manifest["status"] != "pre-normative":
        raise SystemExit("candidate manifest must remain pre-normative")
    expected = {
        "policy-data-handling-v0.json",
        "policy-detail-disclosure-v0.json",
        "policy-detail-disclosure-authority-v0.json",
        "policy-operational-evidence-v0.json",
        "dispatch-route-ticket-v1.json",
        "dispatch-ticket-trust-v2.json",
        "dispatch-ticket-trust-v2-crypto.json",
        "dispatch-ticket-trust-store-v1.json",
        "trust-bundle-rollback-anchor-v0.json",
    }
    paths = {item["path"] for item in manifest["fixtures"]}
    if paths != expected:
        raise SystemExit(f"candidate fixture set mismatch: {sorted(paths ^ expected)}")
    for item in manifest["fixtures"]:
        digest = hashlib.sha256((FIXTURES / item["path"]).read_bytes()).hexdigest()
        if digest != item["sha256"]:
            raise SystemExit(f"candidate digest mismatch: {item['path']}")
    print(f"PASS {len(paths)} profile security candidate fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
