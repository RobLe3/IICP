#!/usr/bin/env python3
"""Evaluate pre-normative trust-bundle rollback-anchor fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def evaluate(vector: dict[str, Any]) -> dict[str, str]:
    local = vector["local"]
    anchor = vector["anchor"]
    recovery = bool(vector["authorization"].get("recovery"))

    if not anchor["available"]:
        if recovery:
            return {"decision": "recover", "reason": "recovery_authorized"}
        return {"decision": "reject", "reason": "anchor_unavailable"}
    if anchor["machine_binding_matches"] is not True:
        if recovery:
            return {"decision": "recover", "reason": "recovery_authorized"}
        return {"decision": "reject", "reason": "recovery_required"}
    if local["bundle_version"] < anchor["bundle_version"]:
        return {"decision": "reject", "reason": "rollback_detected"}
    if local["bundle_version"] != anchor["bundle_version"]:
        return {"decision": "reject", "reason": "anchor_mismatch"}
    if local["bundle_digest"] != anchor["bundle_digest"]:
        return {"decision": "reject", "reason": "anchor_mismatch"}
    return {"decision": "accept", "reason": "anchor_ok"}


def run(fixture_path: Path) -> dict[str, Any]:
    fixture = json.loads(fixture_path.read_text())
    results = []
    for vector in fixture["vectors"]:
        actual = evaluate(vector)
        results.append(
            {
                "id": vector["id"],
                "actual": actual,
                "passed": actual == vector["expected"],
            }
        )
    return {
        "schema_version": fixture["schema_version"],
        "profile": fixture["profile"],
        "passed": sum(result["passed"] for result in results),
        "failed": sum(not result["passed"] for result in results),
        "results": results,
        "limitations": [
            "models anchor semantics, not native OS secure-store APIs",
            "does not enable strict trust or change the wire protocol",
            "authorized recovery requires an external authenticated ceremony",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.fixture)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
