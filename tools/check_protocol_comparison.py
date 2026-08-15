#!/usr/bin/env python3
"""Validate the dated, machine-readable protocol comparison."""
from __future__ import annotations

import json
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
    if len(entries) < 6:
        errors.append("comparison must include at least six subjects")
    ids: set[str] = set()
    for entry in entries:
        ident = entry.get("id", "<missing>")
        if ident in ids:
            errors.append(f"duplicate id: {ident}")
        ids.add(ident)
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

    forbidden = {"overall_score", "composite_score", "winner", "quality_rank", "rank"}
    if _contains_forbidden_key(data, forbidden):
        errors.append("composite ranking fields are forbidden")
    return errors


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
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        errors.append(f"{label} must use YYYY-MM-DD")
        return None


def _validate_date(
    errors: list[str], value: object, label: str, as_of: date | None
) -> None:
    parsed = _parse_date(errors, value, label)
    if parsed is not None and as_of is not None and parsed > as_of:
        errors.append(f"{label} cannot be later than the evidence date")


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
