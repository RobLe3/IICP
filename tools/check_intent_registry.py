#!/usr/bin/env python3
"""Validate the additive IICP intent registry without external dependencies."""
from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/intents.json"
URN = re.compile(r"^urn:iicp:intent:[a-z0-9_.-]+(?::[a-z0-9_./-]+)*:v[1-9][0-9]*$")
SEMVER = re.compile(r"^[1-9][0-9]*\.[0-9]+\.[0-9]+$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
STATUSES = {"active", "experimental", "reserved", "deprecated", "withdrawn"}
KINDS = {
    "analysis",
    "generation",
    "inference",
    "interactive",
    "ranking",
    "representation",
    "tool",
    "transformation",
}
ENTRY_KEYS = {
    "urn", "name", "description", "payload_schema", "result_schema", "phase", "status", "kind",
    "declaration_version", "owner", "created", "updated", "review_by", "schemas", "compatibility",
    "references", "fixtures", "implementation_evidence", "status_history", "deprecated_by",
    "deprecated_since", "withdrawn_reason",
}
ALLOWED_TRANSITIONS = {
    "reserved": {"reserved", "experimental", "active", "withdrawn"},
    "experimental": {"experimental", "reserved", "active", "withdrawn"},
    "active": {"active", "experimental", "deprecated", "withdrawn"},
    "deprecated": {"deprecated", "withdrawn"},
    "withdrawn": {"withdrawn"},
}


def parse_date(value: object, field: str, errors: list[str]) -> date | None:
    if not isinstance(value, str):
        errors.append(f"{field} must be an ISO 8601 date")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{field} must be an ISO 8601 date")
        return None


def resolve_json_pointer(document: object, pointer: str) -> object:
    if not pointer.startswith("/"):
        raise ValueError("fragment must be a JSON Pointer")
    current = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            if not token.isdigit():
                raise ValueError("array token must be an index")
            current = current[int(token)]
        elif isinstance(current, dict):
            current = current[token]
        else:
            raise ValueError("pointer traverses a scalar")
    return current


def validate_fixture_refs(entry: dict[str, Any], prefix: str, errors: list[str]) -> None:
    seen_validity: set[bool] = set()
    for index, value in enumerate(entry.get("fixtures", [])):
        field = f"{prefix}.fixtures[{index}]"
        if not isinstance(value, str) or "#" not in value:
            errors.append(f"{field} must be a fixture JSON Pointer URI")
            continue
        relative, fragment = value.split("#", 1)
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"{field} does not exist: {relative}")
            continue
        try:
            case = resolve_json_pointer(json.loads(path.read_text()), fragment)
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, IndexError, ValueError):
            errors.append(f"{field} does not resolve to a JSON resource")
            continue
        if not isinstance(case, dict) or case.get("intent") != entry.get("urn"):
            errors.append(f"{field} does not identify a case for {entry.get('urn')}")
            continue
        if not isinstance(case.get("valid"), bool):
            errors.append(f"{field} must identify a case with boolean valid")
            continue
        seen_validity.add(case["valid"])
    if entry.get("status") == "active" and seen_validity != {True, False}:
        errors.append(f"active intent {entry.get('urn')} must cite one positive and one negative fixture case")


def validate_schema_ref(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return
    schema_id, relative, digest = value.get("id"), value.get("path"), value.get("sha256")
    if not isinstance(schema_id, str) or not schema_id.startswith("https://iicp.network/"):
        errors.append(f"{field}.id must be an iicp.network HTTPS identifier")
    if not isinstance(relative, str) or not relative.startswith("registry/schemas/"):
        errors.append(f"{field}.path must identify a registry schema")
        return
    path = ROOT / relative
    if not path.is_file():
        errors.append(f"{field}.path does not exist: {relative}")
        return
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if not isinstance(digest, str) or not SHA256.fullmatch(digest) or digest != actual:
        errors.append(f"{field}.sha256 does not match {relative}")
    try:
        schema = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append(f"{field}.path is not valid JSON")
        return
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append(f"{field}.path must declare JSON Schema 2020-12")
    if schema.get("$id") != schema_id:
        errors.append(f"{field}.id does not match the schema $id")


def validate_history(entry: dict[str, Any], prefix: str, errors: list[str]) -> None:
    history = entry.get("status_history")
    if not isinstance(history, list) or not history:
        errors.append(f"{prefix}.status_history must be a non-empty array")
        return
    prior_status: str | None = None
    prior_date: date | None = None
    for index, event in enumerate(history):
        field = f"{prefix}.status_history[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{field} must be an object")
            continue
        status = event.get("status")
        if status not in STATUSES:
            errors.append(f"{field}.status must be one of {sorted(STATUSES)}")
        event_date = parse_date(event.get("date"), f"{field}.date", errors)
        if not isinstance(event.get("reason"), str) or not event["reason"].strip():
            errors.append(f"{field}.reason must be a non-empty string")
        if prior_status and status in STATUSES and status not in ALLOWED_TRANSITIONS[prior_status]:
            errors.append(f"invalid lifecycle transition {prior_status} -> {status} for {entry.get('urn', prefix)}")
        if prior_date and event_date and event_date < prior_date:
            errors.append(f"{field}.date precedes the previous lifecycle event")
        if status in STATUSES:
            prior_status = status
        if event_date:
            prior_date = event_date
    if prior_status != entry.get("status"):
        errors.append(f"{prefix}.status must match the final status_history event")


def validate(document: object, *, today: date | None = None) -> list[str]:
    if not isinstance(document, dict):
        return ["registry root must be an object"]
    errors: list[str] = []
    root_schema = ROOT / "registry/schemas/intent-registry-v1.4.json"
    try:
        root_schema_id = json.loads(root_schema.read_text(encoding="utf-8"))["$id"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError):
        errors.append("registry root schema must exist and declare $id")
        root_schema_id = None
    if document.get("schema") != root_schema_id:
        errors.append("registry schema must identify the canonical 1.4 root schema")
    if document.get("version") != "1.4.0":
        errors.append("registry version must be 1.4.0")
    entries = document.get("intents")
    if not isinstance(entries, list) or not entries:
        return [*errors, "intents must be a non-empty array"]

    now = today or date.today()
    urns: set[str] = set()
    deprecated: list[tuple[str, str | None]] = []
    for index, entry in enumerate(entries):
        prefix = f"intents[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        unexpected = sorted(set(entry) - ENTRY_KEYS)
        if unexpected:
            errors.append(f"{prefix} has unknown properties: {', '.join(unexpected)}")
        if not isinstance(entry.get("phase"), int) or isinstance(entry.get("phase"), bool) or entry["phase"] < 1:
            errors.append(f"{prefix}.phase must be a positive integer")
        urn = entry.get("urn")
        if not isinstance(urn, str) or not URN.fullmatch(urn):
            errors.append(f"{prefix}.urn is not a canonical versioned intent URN")
        elif urn in urns:
            errors.append(f"duplicate intent URN: {urn}")
        else:
            urns.add(urn)
        for field in ("name", "description", "owner"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if entry.get("kind") not in KINDS:
            errors.append(f"{prefix}.kind must be one of {sorted(KINDS)}")
        if not isinstance(entry.get("declaration_version"), str) or not SEMVER.fullmatch(entry["declaration_version"]):
            errors.append(f"{prefix}.declaration_version must be semantic version text")
        created = parse_date(entry.get("created"), f"{prefix}.created", errors)
        updated = parse_date(entry.get("updated"), f"{prefix}.updated", errors)
        review_by = parse_date(entry.get("review_by"), f"{prefix}.review_by", errors)
        if created and updated and updated < created:
            errors.append(f"{prefix}.updated precedes created")
        if review_by and review_by < now:
            errors.append(f"{prefix}.review_by is expired")
        if not isinstance(entry.get("payload_schema"), dict) or not entry["payload_schema"]:
            errors.append(f"{prefix}.payload_schema must preserve the non-empty legacy object")
        status = entry.get("status")
        if status not in STATUSES:
            errors.append(f"{prefix}.status must be one of {sorted(STATUSES)}")
        validate_history(entry, prefix, errors)
        schemas = entry.get("schemas")
        if not isinstance(schemas, dict):
            errors.append(f"{prefix}.schemas must be an object")
        else:
            validate_schema_ref(schemas.get("input"), f"{prefix}.schemas.input", errors)
            validate_schema_ref(schemas.get("output"), f"{prefix}.schemas.output", errors)
        compatibility = entry.get("compatibility")
        if not isinstance(compatibility, dict) or compatibility.get("legacy_payload_schema") is not True or compatibility.get("existing_urn_preserved") is not True:
            errors.append(f"{prefix}.compatibility must preserve the URN and legacy payload_schema")
        for field in ("references", "fixtures", "implementation_evidence"):
            if not isinstance(entry.get(field), list):
                errors.append(f"{prefix}.{field} must be an array")
        validate_fixture_refs(entry, prefix, errors)
        if status == "active":
            if not entry.get("implementation_evidence"):
                errors.append(f"active intent {urn} must cite a released implementation")
        if status == "deprecated":
            deprecated.append((urn if isinstance(urn, str) else prefix, entry.get("deprecated_by")))
        if status == "withdrawn" and not isinstance(entry.get("withdrawn_reason"), str):
            errors.append(f"withdrawn intent {urn} must provide withdrawn_reason")

    for urn, successor in deprecated:
        if not isinstance(successor, str) or successor not in urns:
            errors.append(f"deprecated intent {urn} must name an existing deprecated_by successor")
    return errors


def main() -> int:
    errors = validate(json.loads(REGISTRY.read_text()))
    if errors:
        print("intent registry validation failed:", *errors, sep="\n- ", file=sys.stderr)
        return 1
    print("intent registry validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
