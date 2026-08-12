#!/usr/bin/env python3
"""Validate the informative IICP-selected A2A execution binding fixture."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/a2a-execution-binding-v0.json"
NOW = datetime.fromisoformat("2026-08-12T12:00:00+00:00")


def canonical_digest(document: dict) -> str:
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _origin(url: str) -> tuple[str, str, int | None]:
    parsed = urlparse(url)
    return parsed.scheme, parsed.hostname or "", parsed.port


def evaluate(document: dict, *, request_streaming: bool = False, now: datetime = NOW) -> str:
    provider = document["selected_provider"]
    binding = provider["binding"]
    card = document["agent_card"]
    authorization = document["authorization"]

    if authorization["iicp_ticket_forwarded"]:
        return "ticket_passthrough_forbidden"
    if authorization["a2a_credential_audience"] != authorization["expected_a2a_credential_audience"]:
        return "credential_audience_mismatch"
    if canonical_digest(card) != binding["agent_card_sha256"]:
        return "card_digest_mismatch"
    expires = datetime.fromisoformat(binding["card_expires_at"].replace("Z", "+00:00"))
    if expires <= now:
        return "card_binding_expired"
    if _origin(binding["agent_card_url"]) != _origin(binding["interface_url"]):
        return "interface_mismatch"

    interfaces = card.get("supportedInterfaces", [])
    selected = next(
        (
            item
            for item in interfaces
            if item.get("url") == binding["interface_url"]
            and item.get("protocolBinding") == binding["protocol_binding"]
            and item.get("protocolVersion") == binding["protocol_version"]
            and item.get("tenant") == binding.get("tenant")
        ),
        None,
    )
    if selected is None:
        return "interface_mismatch"

    extension_uris = {item.get("uri") for item in card.get("capabilities", {}).get("extensions", [])}
    if not set(binding["required_extensions"]).issubset(extension_uris):
        return "required_extension_missing"
    mapped_skill = binding["intent_skill_map"].get(provider["intent"])
    skill_ids = {item.get("id") for item in card.get("skills", [])}
    if not mapped_skill or mapped_skill not in skill_ids:
        return "skill_mismatch"
    if request_streaming and card.get("capabilities", {}).get("streaming") is not True:
        return "streaming_not_supported"
    return "accept"


def apply_mutation(base: dict, mutation: dict) -> dict:
    candidate = copy.deepcopy(base)
    binding = candidate["selected_provider"]["binding"]
    authorization = candidate["authorization"]
    for key, value in mutation.items():
        if key in authorization:
            authorization[key] = value
        elif key == "mapped_skill":
            intent = candidate["selected_provider"]["intent"]
            binding["intent_skill_map"][intent] = value
        else:
            binding[key] = value
    return candidate


def validate(document: dict) -> list[str]:
    errors: list[str] = []
    if document.get("profile") != "iicp-a2a-execution-binding-v0":
        errors.append("unexpected profile")
    provider = document.get("selected_provider", {})
    if not provider.get("node_id") or not provider.get("operator_ref") or not provider.get("intent"):
        errors.append("selected provider identity and intent are required")
    if provider.get("route_ticket_audience") != "iicp.directory.dispatch":
        errors.append("IICP route-ticket audience changed")
    if evaluate(document) != "accept":
        errors.append(f"base fixture rejected: {evaluate(document)}")

    seen: set[str] = set()
    for scenario in document.get("scenarios", []):
        scenario_id = scenario.get("id")
        if not scenario_id or scenario_id in seen:
            errors.append("scenario ids must be unique and non-empty")
            continue
        seen.add(scenario_id)
        candidate = apply_mutation(document, scenario.get("mutation", {}))
        actual = evaluate(candidate, request_streaming=scenario.get("request_streaming", False))
        if actual != scenario.get("expected"):
            errors.append(f"{scenario_id}: expected {scenario.get('expected')}, found {actual}")

    required_operations = {
        "send_CancelTask",
        "return_terminal_without_cancel",
        "cancel_local_request_only",
        "local_expired_remote_unknown",
        "do_not_automatic_fallback",
    }
    actual_operations = {item.get("expected") for item in document.get("operation_vectors", [])}
    if not required_operations.issubset(actual_operations):
        errors.append("cancellation, deadline, and partial-execution vectors are incomplete")

    required_errors = {
        "authentication",
        "VersionNotSupportedError",
        "UnsupportedOperationError",
        "TaskNotFoundError",
        "TaskNotCancelableError",
        "InvalidAgentResponseError",
        "transport_before_acknowledgement",
        "transport_after_acknowledgement",
    }
    if not required_errors.issubset(document.get("error_map", {})):
        errors.append("A2A error mapping is incomplete")

    receipt = document.get("receipt", {})
    if set(receipt.get("allowed_fields", [])) & set(receipt.get("forbidden_fields", [])):
        errors.append("receipt allowed and forbidden fields overlap")
    required_forbidden = {"authorization", "credential", "message", "history", "artifact", "prompt", "response", "payload"}
    if not required_forbidden.issubset(set(receipt.get("forbidden_fields", []))):
        errors.append("receipt privacy boundary is incomplete")
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
    print(f"A2A execution binding valid: {len(document['scenarios'])} scenarios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
