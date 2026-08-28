#!/usr/bin/env python3
"""Validate the bounded pre-1.0 feature and specification crosswalk."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "pre1/feature-baseline-v1.json"
CLASSIFICATIONS = {
    "REQUIRED_STABLE",
    "COMPATIBILITY_ANCHOR",
    "OPTIONAL_STABLE",
    "EXPERIMENTAL",
    "RESEARCH",
    "UNSUPPORTED",
}


def capability_digest(ids: list[str]) -> str:
    payload = json.dumps(sorted(ids), separators=(",", ":"), ensure_ascii=True).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def local_ref_exists(value: str, root: Path = ROOT) -> bool:
    return value.startswith(("http://", "https://", "RobLe3/")) or (root / value).is_file()


def validate(value: dict, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if value.get("schema") != "iicp.pre1-feature-baseline.v1":
        errors.append("unexpected feature-baseline schema")
    if value.get("non_authorizing") is not True:
        errors.append("feature baseline must remain non-authorizing")
    if value.get("stable_designation_authorized") is not False:
        errors.append("pre-qualification baseline cannot authorize a stable designation")

    reviews = value.get("component_reviews", [])
    review_components = [row.get("component") for row in reviews]
    if len(reviews) != 6 or len(review_components) != len(set(review_components)):
        errors.append("component reviews must contain six unique components")
    for row in reviews:
        if row.get("status") not in {"OPEN", "PASS"}:
            errors.append(f"invalid component review status: {row.get('component')}")

    capabilities = value.get("capabilities", [])
    ids = [row.get("id") for row in capabilities]
    if not capabilities or any(not isinstance(row, str) or not row for row in ids):
        errors.append("capability ids must be non-empty strings")
    elif len(ids) != len(set(ids)):
        errors.append("capability ids must be unique")
    if capabilities and value.get("capability_ids_sha256") != capability_digest(ids):
        errors.append("capability_ids_sha256 does not match the declared capability ids")

    for row in capabilities:
        row_id = row.get("id", "<missing>")
        classification = row.get("classification")
        if classification not in CLASSIFICATIONS:
            errors.append(f"invalid classification: {row_id}")
        authority_refs = row.get("authority_refs", [])
        fixture_refs = row.get("fixture_refs", [])
        implementations = row.get("implementations", [])
        if not authority_refs:
            errors.append(f"missing authority reference: {row_id}")
        for ref in authority_refs + fixture_refs:
            if not isinstance(ref, str) or not local_ref_exists(ref, root):
                errors.append(f"missing referenced artifact: {row_id}: {ref}")
        if classification in {"REQUIRED_STABLE", "COMPATIBILITY_ANCHOR"}:
            if not fixture_refs:
                errors.append(f"required capability has no fixture: {row_id}")
            if not implementations:
                errors.append(f"required capability has no implementation: {row_id}")
        if classification == "UNSUPPORTED" and implementations:
            errors.append(f"unsupported capability must not claim a stable implementation: {row_id}")
        if row.get("contradiction_status") not in {
            "CLEAR",
            "CLEAR_WITH_EXPLICIT_BOUNDARY",
            "OPEN",
        }:
            errors.append(f"invalid contradiction status: {row_id}")

    native = next(
        (row for row in capabilities if row.get("id") == "native-binary-framing"),
        None,
    )
    if native is None:
        errors.append("native binary framing capability is missing")
    elif native.get("classification") != "EXPERIMENTAL":
        errors.append(
            "native binary framing must remain experimental while native TCP is excluded"
        )
    return errors


def evaluate(value: dict) -> dict:
    capabilities = value.get("capabilities", [])
    blocking = sorted(
        row["id"]
        for row in capabilities
        if row.get("classification") in {"REQUIRED_STABLE", "COMPATIBILITY_ANCHOR"}
        and row.get("contradiction_status") == "OPEN"
    )
    open_reviews = sorted(
        row["component"]
        for row in value.get("component_reviews", [])
        if row.get("status") != "PASS"
    )
    return {
        "capabilities": len(capabilities),
        "blocking_contradictions": blocking,
        "open_component_reviews": open_reviews,
        "strict_ready": (
            value.get("status") in {"CANDIDATE_BOUNDARY_FROZEN", "QUALIFIED"}
            and not blocking
            and not open_reviews
            and value.get("stable_designation_authorized") is False
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    value = json.loads(args.baseline.read_text())
    errors = validate(value, args.baseline.resolve().parents[1])
    evaluation = evaluate(value) if not errors else {}
    result = {
        "schema": "iicp.pre1-feature-baseline-check.v1",
        "valid": not errors,
        "strict_ready": not errors and evaluation.get("strict_ready", False),
        "errors": errors,
        "evaluation": evaluation,
        "non_authorizing": True,
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"pre-1.0 feature baseline: {'valid' if not errors else 'invalid'}")
        if evaluation:
            print(f"capabilities: {evaluation['capabilities']}")
            print(f"open component reviews: {len(evaluation['open_component_reviews'])}")
            print(f"strict freeze: {'PASS' if result['strict_ready'] else 'OPEN'}")
        for error in errors:
            print(f"- {error}")
    if errors:
        return 2
    if args.strict and not result["strict_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
