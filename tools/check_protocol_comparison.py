#!/usr/bin/env python3
"""Validate the dated, machine-readable protocol comparison."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "standards/protocol-comparison-v1.json"


def validate(path: Path = DATA) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "iicp.protocol-comparison.v1":
        errors.append("unexpected schema")
    as_of = _parse_date(errors, data.get("as_of"), "as_of")
    warning = data.get("rating_warning", "")
    if "not a composite" not in warning:
        errors.append("rating warning must state that scores are not a composite")
    dimensions = data.get("dimensions", [])
    maturity_dimensions = data.get("maturity_dimensions", [])
    allowed_scores = {0, 1, 2, 3, 4, None}
    values = set(data.get("comparison_values", []))
    entries = data.get("entries", [])
    if data.get("legacy_assessment_as_of") != "2026-08-15":
        errors.append("legacy maturity assessments must retain their historical evidence date")
    if len(entries) < 6:
        errors.append("comparison must include at least six subjects")
    ids: set[str] = set()
    for entry in entries:
        ident = entry.get("id", "<missing>")
        if ident in ids:
            errors.append(f"duplicate id: {ident}")
        ids.add(ident)
        if entry.get("assessment_status") != "historical_2026-08-15_not_refreshed":
            errors.append(f"{ident}: old maturity assessments must remain explicitly historical")
        for field in (
            "name", "category", "version", "formal_status", "updated",
            "source", "role", "dimensions", "maturity",
            "first_public_evidence", "relative_to_iicp_first_public",
        ):
            if not entry.get(field):
                errors.append(f"{ident}: missing {field}")
        source = urlparse(entry.get("source", ""))
        if source.scheme != "https" or not source.netloc:
            errors.append(f"{ident}: source must be an absolute HTTPS URL")
        mapping = entry.get("dimensions", {})
        if set(mapping) != set(dimensions):
            errors.append(f"{ident}: dimension keys do not match contract")
        unknown = set(mapping.values()) - values
        if unknown:
            errors.append(f"{ident}: unknown comparison values {sorted(unknown)}")
        if "internet_draft" in entry.get("formal_status", "") and "not_ietf_endorsed" not in entry["formal_status"]:
            errors.append(f"{ident}: Internet-Draft status must deny endorsement")
        evidence = entry.get("first_public_evidence", {})
        for field in ("date", "kind", "artifact", "source", "confidence"):
            if not evidence.get(field):
                errors.append(f"{ident}: first public evidence missing {field}")
        _validate_date(errors, evidence.get("date"), f"{ident}: first public evidence", as_of)
        _validate_url(errors, evidence.get("source", ""), f"{ident}: first public evidence source")
        if entry.get("relative_to_iicp_first_public") not in {"predates", "same_day", "postdates"}:
            errors.append(f"{ident}: invalid chronology relation")
        maturity = entry.get("maturity", {})
        if set(maturity) != set(maturity_dimensions):
            errors.append(f"{ident}: maturity dimension keys do not match contract")
        for dimension, assessment in maturity.items():
            _validate_assessment(errors, assessment, allowed_scores, f"{ident}.{dimension}")

    overlap_subjects = data.get("overlap_evidence_subjects", [])
    overlap = data.get("overlap_evidence", {})
    if set(overlap) != set(overlap_subjects):
        errors.append("overlap evidence subjects do not match mapping")
    if not set(overlap_subjects).issubset(ids):
        errors.append("overlap evidence includes an unknown subject")
    for ident, mapping in overlap.items():
        if set(mapping) != set(dimensions):
            errors.append(f"{ident}: overlap evidence dimensions do not match contract")
        for dimension, assessment in mapping.items():
            _validate_assessment(errors, assessment, allowed_scores, f"{ident}.{dimension}")

    chronology = data.get("mechanism_chronology", [])
    chronology_dates: list[str] = []
    for index, event in enumerate(chronology):
        label = f"chronology[{index}]"
        for field in ("date", "subject", "mechanism", "artifact", "source", "confidence"):
            if not event.get(field):
                errors.append(f"{label}: missing {field}")
        _validate_date(errors, event.get("date"), label, as_of)
        _validate_url(errors, event.get("source", ""), f"{label}: source")
        if event.get("subject") not in ids:
            errors.append(f"{label}: unknown subject")
        chronology_dates.append(event.get("date", ""))
    if chronology_dates != sorted(chronology_dates):
        errors.append("mechanism chronology must be date sorted")

    inventory = data.get("source_inventory", [])
    source_ids: set[str] = set()
    for index, source in enumerate(inventory):
        label = f"source_inventory[{index}]"
        ident = source.get("id")
        if not ident or ident in source_ids:
            errors.append(f"{label}: missing or duplicate id")
        source_ids.add(ident)
        for field in ("document", "formal_status", "relevant_sections", "scope",
                      "evidence_class", "retrieval_limitations"):
            if not source.get(field):
                errors.append(f"{label}: missing {field}")
        revision = _validate_date(errors, source.get("revision_date"), f"{label}: revision date", as_of)
        verified = _validate_date(errors, source.get("verified_at"), f"{label}: verification date", as_of)
        if revision is not None and verified is not None and revision > verified:
            errors.append(f"{label}: revision date cannot be later than verification date")
        _validate_url(errors, source.get("source", ""), f"{label}: source")
        if source.get("formal_status") == "individual_internet_draft" and not str(source.get("document", "")).startswith("draft-"):
            errors.append(f"{label}: individual Internet-Draft must name its draft")
    required_sources = {
        "iaip", "aidip", "cirp", "intent-routing-requirements", "dawn",
        "dns-aid", "dmsc-architecture", "dmsc-information-architecture",
        "aipf", "iacp", "agent-routing-policy", "agent-session-requirements",
        "security-principal-binding", "scitt-agent-action-receipt",
    }
    if source_ids != required_sources:
        errors.append("current source inventory is incomplete or contains an unreviewed row")
    for source in inventory:
        if source.get("revision_source"):
            _validate_url(errors, source["revision_source"], f"{source['id']}: revision source")

    _validate_implementation_evidence(errors, data.get("implementation_evidence"), as_of)

    requirements = data.get("intent_routing_requirements", [])
    if [item.get("id") for item in requirements] != [f"REQ-{i}" for i in range(1, 18)]:
        errors.append("intent routing mapping must contain ordered REQ-1 through REQ-17 exactly once")
    dispositions = {"ALIGNED", "PARTIAL", "DIFFERENT_DESIGN", "OUT_OF_SCOPE", "NOT_ESTABLISHED"}
    for index, requirement in enumerate(requirements):
        label = f"intent_routing_requirements[{index}]"
        for field in ("title", "source_document", "source_section", "iicp_reference",
                      "scope", "implementation_evidence", "positive_negative_cases",
                      "limitation"):
            if not requirement.get(field):
                errors.append(f"{label}: missing {field}")
        if requirement.get("source_document") != "draft-feng-dmsc-intent-routing-requirements-00":
            errors.append(f"{label}: wrong source revision")
        if requirement.get("disposition") not in dispositions:
            errors.append(f"{label}: invalid disposition")
        _validate_date(errors, requirement.get("verified_at"), f"{label}: verification date", as_of)
        _validate_url(errors, requirement.get("source", ""), f"{label}: source")
        for field in ("iicp_reference", "fixture_reference"):
            relative = requirement.get(field)
            if relative and (Path(relative).is_absolute() or not (ROOT / relative).is_file()):
                errors.append(f"{label}: invalid {field}")

    forbidden = {"overall_score", "composite_score", "winner", "quality_rank", "rank"}
    if _contains_forbidden_key(data, forbidden):
        errors.append("composite ranking fields are forbidden")
    return errors


def _validate_implementation_evidence(errors: list[str], evidence: object, as_of: date | None) -> None:
    if not isinstance(evidence, dict) or evidence.get("schema") != "iicp.implementation-evidence.v1":
        errors.append("implementation evidence schema differs")
        return
    required_dimensions = {
        "versioned_contract", "machine_readable_contracts", "maintained_implementation",
        "implementation_diversity", "executable_conformance", "negative_security_vectors",
        "standalone_conformance_runner", "release_integrity", "operational_evidence",
        "independent_implementation", "policy_management_implementation",
    }
    if set(evidence.get("dimensions", [])) != required_dimensions:
        errors.append("implementation evidence dimensions differ")
    statuses = {
        "verified", "partial", "prototype", "not_identified", "not_applicable",
        "requirements_only", "charter_only", "not_independently_established",
    }
    rows = evidence.get("rows", [])
    if not isinstance(rows, list) or {row.get("id") for row in rows if isinstance(row, dict)} != {
        "iicp", "iaip", "aidip", "cirp", "intent-routing-requirements", "dawn"
    } or len(rows) != 6:
        errors.append("implementation evidence subjects differ")
        return
    for row in rows:
        ident = row["id"]
        label = f"implementation evidence {ident}"
        observed = _validate_date(errors, row.get("evidence_date"), f"{label} evidence date", as_of)
        verified = _validate_date(errors, row.get("verified_at"), f"{label} verification date", as_of)
        if observed and verified and observed > verified:
            errors.append(f"{label}: evidence date cannot follow verification")
        if not row.get("artifact_type") or not row.get("evidence_class") or not row.get("reviewed_scope"):
            errors.append(f"{label}: missing artifact type, evidence class or reviewed scope")
        dimensions = row.get("dimensions", {})
        if set(dimensions) != required_dimensions:
            errors.append(f"{label}: dimensions differ")
            continue
        languages = row.get("implementation_languages", [])
        if not isinstance(languages, list) or any(not isinstance(item, str) or not item for item in languages):
            errors.append(f"{label}: invalid implementation languages")
        elif languages and dimensions["implementation_diversity"].get("status") != "verified":
            errors.append(f"{label}: language claims require verified implementation diversity")
        for dimension, claim in dimensions.items():
            claim_label = f"{label}.{dimension}"
            if not isinstance(claim, dict):
                errors.append(f"{claim_label}: claim must be an object")
                continue
            status = claim.get("status")
            if status not in statuses:
                errors.append(f"{claim_label}: unsupported evidence status")
            if not claim.get("note"):
                errors.append(f"{claim_label}: evidence note required")
            sources = claim.get("sources")
            if not isinstance(sources, list) or not sources:
                errors.append(f"{claim_label}: public sources required")
            else:
                for source in sources:
                    _validate_url(errors, source, f"{claim_label} source")
            if status == "not_identified" and not row.get("reviewed_scope"):
                errors.append(f"{claim_label}: bounded search scope required")
            if dimension == "operational_evidence" and status == "verified" and not row.get("operational_scope"):
                errors.append(f"{claim_label}: operational scope required")
        if row.get("artifact_type") in {"requirements_draft", "proposed_charter"}:
            expected_contract = (
                "requirements_only" if row["artifact_type"] == "requirements_draft"
                else "charter_only"
            )
            if dimensions["versioned_contract"].get("status") != expected_contract:
                errors.append(f"{label}: contract status must be {expected_contract}")
            for dimension in required_dimensions - {"versioned_contract"}:
                if dimensions[dimension].get("status") != "not_applicable":
                    errors.append(f"{label}: requirements and charters are not implementation evidence")
        if ident == "iicp" and dimensions["independent_implementation"].get("status") == "verified":
            errors.append("iicp independent implementation cannot be inferred from same-project parity")


def _validate_assessment(
    errors: list[str], assessment: object, allowed_scores: set[object], label: str
) -> None:
    if not isinstance(assessment, dict):
        errors.append(f"{label}: assessment must be an object")
        return
    if assessment.get("score") not in allowed_scores:
        errors.append(f"{label}: score must be 0-4 or null")
    if not assessment.get("rationale"):
        errors.append(f"{label}: rationale is required")
    _validate_url(errors, assessment.get("source", ""), f"{label}: source")


def _validate_url(errors: list[str], value: str, label: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"{label} must be an absolute HTTPS URL")


def _parse_date(errors: list[str], value: object, label: str) -> date | None:
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        errors.append(f"{label} must use YYYY-MM-DD")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} must use YYYY-MM-DD")
        return None


def _validate_date(
    errors: list[str], value: object, label: str, as_of: date | None
) -> date | None:
    parsed = _parse_date(errors, value, label)
    if parsed is not None and as_of is not None and parsed > as_of:
        errors.append(f"{label} cannot be later than the evidence date")
    return parsed


def _contains_forbidden_key(value: object, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return bool(forbidden.intersection(value)) or any(
            _contains_forbidden_key(item, forbidden) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_key(item, forbidden) for item in value)
    return False


def main() -> int:
    errors = validate()
    if errors:
        print("protocol comparison invalid:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS protocol comparison dataset")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
