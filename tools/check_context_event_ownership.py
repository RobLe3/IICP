#!/usr/bin/env python3
"""Validate the implementation-neutral context and event ownership contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_CONTRACT = Path(__file__).resolve().parents[1] / "docs/architecture/context-event-ownership-v1.json"
FEDERATED_EVENTS = {
    "REGISTER",
    "DEREGISTER",
    "CREDIT_AWARD",
    "REPLICA_REGISTERED",
    "REPLICA_DEREGISTERED",
    "REPUTATION_DECAY",
    "OPERATOR_OBSERVED",
}
SCOPES = {"federated", "local", "retired", "dedicated"}
REPLICATION_ACTIONS = {"apply_state", "record_only", "none"}


def validate(contract: dict) -> list[str]:
    errors: list[str] = []
    contexts = contract.get("contexts", [])
    context_ids = [entry.get("id") for entry in contexts]
    if not context_ids or None in context_ids or len(context_ids) != len(set(context_ids)):
        errors.append("contexts must have unique non-empty ids")

    rules = contract.get("rules", {})
    if rules.get("event_owner_source") != "event_type":
        errors.append("event ownership must derive from event_type")
    if rules.get("service_id_is_authorization") is not False:
        errors.append("service_id must not be authorization")

    service = contract.get("service_identity", {})
    try:
        pattern = re.compile(service.get("identifier_pattern", ""))
    except re.error:
        pattern = None
        errors.append("service identifier pattern is invalid")
    if pattern is not None and not pattern.fullmatch(service.get("current_process_label", "")):
        errors.append("current process label does not match the service identifier pattern")

    events = contract.get("events", [])
    event_types = [entry.get("type") for entry in events]
    if not event_types or None in event_types or len(event_types) != len(set(event_types)):
        errors.append("events must have unique non-empty types")

    for event in events:
        event_type = event.get("type", "<missing>")
        if event.get("owner") not in context_ids:
            errors.append(f"{event_type}: unknown owner {event.get('owner')!r}")
        if event.get("scope") not in SCOPES:
            errors.append(f"{event_type}: invalid scope {event.get('scope')!r}")
        if event.get("replication_action") not in REPLICATION_ACTIONS:
            errors.append(f"{event_type}: invalid replication_action")
        if event.get("scope") != "federated" and event.get("replication_action") != "none":
            errors.append(f"{event_type}: non-federated events cannot mutate replica state")

    actual_federated = {entry["type"] for entry in events if entry.get("scope") == "federated"}
    if actual_federated != FEDERATED_EVENTS:
        errors.append(
            "federated event set differs: "
            f"missing={sorted(FEDERATED_EVENTS - actual_federated)} "
            f"extra={sorted(actual_federated - FEDERATED_EVENTS)}"
        )

    transitions = contract.get("public_state_transitions", [])
    transition_ids = [entry.get("id") for entry in transitions]
    if not transition_ids or None in transition_ids or len(transition_ids) != len(set(transition_ids)):
        errors.append("public state transitions must have unique non-empty ids")
    for transition in transitions:
        if transition.get("owner") not in context_ids:
            errors.append(f"transition {transition.get('id')}: unknown owner")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", nargs="?", type=Path, default=DEFAULT_CONTRACT)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    errors = validate(contract)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        f"context/event ownership valid: {len(contract['contexts'])} contexts, "
        f"{len(contract['public_state_transitions'])} transitions, {len(contract['events'])} events"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
