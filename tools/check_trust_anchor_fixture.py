#!/usr/bin/env python3
"""Check the shared pre-normative rollback-anchor fixture."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/trust-bundle-rollback-anchor-v0.json"
SIMULATOR = ROOT / "tools/rollback_anchor_simulation.py"
SPEC = importlib.util.spec_from_file_location("rollback_anchor_simulation", SIMULATOR)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def main() -> int:
    fixture = json.loads(FIXTURE.read_text())
    required = {
        "anchor_ok",
        "rollback_detected",
        "anchor_unavailable",
        "anchor_mismatch",
        "recovery_required",
        "recovery_authorized",
    }
    if set(fixture["reason_codes"]) != required:
        raise SystemExit("rollback-anchor reason-code set drifted")
    if fixture["status"] != "pre-normative":
        raise SystemExit("rollback-anchor fixture must remain pre-normative")
    result = MODULE.run(FIXTURE)
    if result["failed"]:
        raise SystemExit(f"{result['failed']} rollback-anchor vectors failed")
    print(f"Rollback-anchor fixture passed: {result['passed']} vectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
