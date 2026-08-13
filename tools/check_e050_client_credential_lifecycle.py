#!/usr/bin/env python3
"""Validate the implementation-only strict-E050 client lifecycle fixture."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/e050-client-credential-lifecycle-v1.json"
EXPECTED = {
    "fresh-registration",
    "tunnel-rotation",
    "supervised-restart",
    "stale-token-replay",
    "failed-current-token-rotation",
}


def validate(document: dict) -> list[str]:
    errors: list[str] = []
    if document.get("schema") != "iicp.e050_client_credential_lifecycle.v1":
        errors.append("unexpected schema")
    if document.get("status") != "implementation-evidence-only":
        errors.append("fixture must remain implementation evidence")
    if document.get("wire_change") is not False:
        errors.append("fixture cannot authorize a wire change")
    if document.get("production_activation_authorized") is not False:
        errors.append("fixture cannot authorize production activation")
    scenarios = document.get("scenarios", [])
    ids = [item.get("id") for item in scenarios]
    if set(ids) != EXPECTED or len(ids) != len(set(ids)):
        errors.append("fixture must contain every unique lifecycle scenario")
    for item in scenarios:
        status = item.get("directory_status")
        accepted = status == 201
        if status not in {201, 403}:
            errors.append(f"{item.get('id')}: unsupported directory status")
        if item.get("expected_endpoint_committed") is not accepted:
            errors.append(f"{item.get('id')}: route commit must follow acceptance")
        if accepted and not item.get("directory_token"):
            errors.append(f"{item.get('id')}: accepted registration needs a successor token")
        if not accepted and item.get("directory_token") is not None:
            errors.append(f"{item.get('id')}: rejected registration cannot issue a token")
    invariants = document.get("invariants", {})
    if not invariants or any(value is not True for value in invariants.values()):
        errors.append("every fail-closed lifecycle invariant must remain true")
    return errors


def main() -> int:
    errors = validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("strict-E050 client credential lifecycle fixture valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
