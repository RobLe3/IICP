#!/usr/bin/env python3
"""Validate the operator onboarding, recovery and removal contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "research/pre-normative-profiles/fixtures/operator-onboarding-recovery-v1.json"
)

SDK_IDS = {"python", "typescript", "rust"}
REQUIRED_STAGES = [
    "install_published_package",
    "verify_exact_version",
    "initialize_identity_and_node",
    "foreground_registration_check",
    "install_user_service",
    "verify_service_state",
    "verify_local_liveness",
    "classify_readiness",
    "exercise_recovery",
    "verify_rollback",
    "remove_service",
    "remove_package",
]
REQUIRED_COMMANDS = {
    "version",
    "update_check",
    "initialize",
    "foreground",
    "service_install",
    "service_status",
    "service_restart",
    "service_remove",
    "doctor",
    "liveness",
    "readiness",
}
FORBIDDEN_EVIDENCE = {
    "credentials",
    "node_identifiers",
    "backend_urls",
    "private_addresses",
    "prompts",
    "responses",
    "raw_logs",
}
FORBIDDEN_CLAIMS = {
    "independent_implementation",
    "independent_conformance",
    "execution_privacy",
    "credit_eligibility",
    "production_availability",
}


def validate(document: dict) -> list[str]:
    errors: list[str] = []
    if document.get("wire_change") is not False:
        errors.append("operator onboarding cannot change the wire contract")
    if document.get("sdk_release") != "0.7.102":
        errors.append("operator path must pin the current 0.7.102 package line")
    if document.get("rollback_release") != "0.7.101":
        errors.append("operator path must pin the immutable 0.7.101 rollback line")

    packages = document.get("packages", [])
    ids = {package.get("id") for package in packages}
    if ids != SDK_IDS or len(packages) != len(ids):
        errors.append("Python, TypeScript and Rust packages must be covered once")
    for package in packages:
        command_text = " ".join(
            str(package.get(field, "")) for field in ("install", "rollback", "remove")
        )
        if "curl" in command_text or "| sh" in command_text:
            errors.append(f"{package.get('id')} uses an unreviewed pipe-to-shell path")
        if document.get("sdk_release", "") not in package.get("install", ""):
            errors.append(f"{package.get('id')} install is not version-pinned")
        if document.get("rollback_release", "") not in package.get("rollback", ""):
            errors.append(f"{package.get('id')} rollback is not version-pinned")

    if document.get("ordered_stages") != REQUIRED_STAGES:
        errors.append("operator stages are incomplete or out of dependency order")
    commands = document.get("commands", {})
    if set(commands) != REQUIRED_COMMANDS:
        errors.append("shared operator command surface is incomplete")
    if any("--json" not in commands[name] for name in ("doctor", "liveness")):
        errors.append("doctor and liveness evidence must be machine-readable")

    update = document.get("update_policy", {})
    if update.get("initial_validation_enabled") is not False:
        errors.append("initial validation must keep automatic package changes disabled")
    if update.get("enable_after_rollback_verified") is not True:
        errors.append("automatic update cannot precede rollback verification")

    evidence = document.get("evidence", {})
    privacy = evidence.get("privacy", {})
    if set(privacy) != FORBIDDEN_EVIDENCE or any(privacy.values()):
        errors.append("content-free evidence privacy boundary is incomplete")
    claims = evidence.get("supports_claims", {})
    for claim in FORBIDDEN_CLAIMS:
        if claims.get(claim) is not False:
            errors.append(f"operator evidence cannot support {claim}")

    boundaries = document.get("boundaries", {})
    if boundaries.get("relay_required") or boundaries.get("tunnel_required"):
        errors.append("experimental relay or tunnel paths cannot be onboarding requirements")
    if boundaries.get("package_removal_deletes_operator_state") is not False:
        errors.append("package removal cannot silently delete shared operator state")
    if boundaries.get("normal_shutdown_deregistration") != "best_effort":
        errors.append("shutdown deregistration must be described as best effort")
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
    print(f"operator onboarding contract valid: {len(document['packages'])} SDKs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

