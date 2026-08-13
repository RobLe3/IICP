#!/usr/bin/env python3
"""Validate the identity/evidence layering research decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT / "research/pre-normative-profiles/fixtures/identity-evidence-layering-v0.json"
)
REQUIRED_LAYERS = {
    "operator_identity",
    "portable_provenance",
    "workload_identity",
    "task_authority",
    "execution_evidence",
    "post_execution_evidence",
}
FORBIDDEN_AUTHORITY = {
    "operator_identity",
    "portable_provenance",
    "workload_identity",
    "execution_evidence",
    "post_execution_evidence",
}


def validate(document: dict) -> list[str]:
    errors: list[str] = []
    if (
        document.get("wire_change") is not False
        or document.get("trust_root_change") is not False
    ):
        errors.append("research decision cannot change the wire or trust roots")
    layers = document.get("layers", [])
    by_id = {layer.get("id"): layer for layer in layers}
    if set(by_id) != REQUIRED_LAYERS or len(layers) != len(by_id):
        errors.append("identity/evidence layers must be complete and unique")
    for layer_id in FORBIDDEN_AUTHORITY:
        if by_id.get(layer_id, {}).get("authority") is not False:
            errors.append(f"{layer_id} cannot grant task authority")
    if by_id.get("task_authority", {}).get("mechanism") != "iicp_dispatch_ticket":
        errors.append("IICP dispatch ticket must remain the task-authority mechanism")
    if by_id.get("execution_evidence", {}).get("stable_public") is not False:
        errors.append(
            "fresh execution evidence cannot become stable public directory data"
        )
    required_collapses = {
        frozenset(("operator_identity", "task_authority")),
        frozenset(("workload_identity", "task_authority")),
        frozenset(("execution_evidence", "operator_identity")),
        frozenset(("portable_provenance", "task_authority")),
    }
    actual_collapses = {
        frozenset(pair)
        for pair in document.get("forbidden_collapses", [])
        if len(pair) == 2
    }
    if actual_collapses != required_collapses:
        errors.append("forbidden identity/evidence collapses are incomplete")
    if any(document.get("privacy", {}).values()):
        errors.append(
            "privacy boundary must forbid composite identifiers, payloads, and implicit authority"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", type=Path, default=FIXTURE)
    args = parser.parse_args()
    document = json.loads(args.fixture.read_text(encoding="utf-8"))
    errors = validate(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"identity/evidence layering valid: {len(document['layers'])} layers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
