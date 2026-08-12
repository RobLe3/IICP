#!/usr/bin/env python3
"""Validate public multi-vantage measurement evidence and derived claims."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "research/pre-normative-profiles/schemas/public-measurement-profile-v1.schema.json"
DEFAULT_FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/public-measurement-v1-valid.json"
OUTCOMES = {"success", "http_error", "transport_error", "timeout", "invalid_response", "not_run"}
MINIMUM_DIVERSITY = {
    "single-vantage": (1, 1, 1, 1, 1),
    "regional": (3, 3, 1, 3, 2),
    "multi-region": (3, 3, 3, 3, 2),
    "network-wide": (4, 3, 3, 3, 3),
}
FORBIDDEN_KEYS = {
    "payload",
    "prompt",
    "response",
    "credential",
    "credentials",
    "token",
    "ip",
    "ip_address",
    "url",
    "endpoint",
    "node_id",
    "operator_name",
}


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _nearest_rank(values: list[int], percentile: float) -> int:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


def _find_forbidden(value: object, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                errors.append(f"{path}.{key}: forbidden public-evidence field")
            errors.extend(_find_forbidden(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_find_forbidden(child, f"{path}[{index}]"))
    return errors


def validate(document: dict) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [f"schema {error.json_path}: {error.message}" for error in validator.iter_errors(document)]
    errors.extend(_find_forbidden(document))
    if errors:
        return sorted(errors)

    started = _timestamp(document["window"]["started_at"])
    ended = _timestamp(document["window"]["ended_at"])
    if started >= ended:
        errors.append("observation window must end after it starts")

    vantages = document["vantages"]
    vantage_ids = [item["vantage_id"] for item in vantages]
    if len(vantage_ids) != len(set(vantage_ids)):
        errors.append("vantage ids must be unique")

    observations = document["observations"]
    sample_ids = [item["sample_id"] for item in observations]
    if sorted(sample_ids) != list(range(1, len(observations) + 1)):
        errors.append("sample ids must be unique and contiguous from 1")

    known_vantages = set(vantage_ids)
    for observation in observations:
        sample = observation["sample_id"]
        if observation["vantage_id"] not in known_vantages:
            errors.append(f"sample {sample}: unknown vantage")
        observed_at = _timestamp(observation["observed_at"])
        if not started <= observed_at <= ended:
            errors.append(f"sample {sample}: timestamp outside observation window")
        outcome = observation["outcome"]
        if outcome == "success":
            if "latency_ms" not in observation:
                errors.append(f"sample {sample}: success requires latency")
            if not 200 <= observation.get("http_status", 0) < 300:
                errors.append(f"sample {sample}: success requires a 2xx status")
            if "reason_code" in observation:
                errors.append(f"sample {sample}: success cannot have a failure reason")
        else:
            if "latency_ms" in observation:
                errors.append(f"sample {sample}: failed observation cannot report latency")
            if "reason_code" not in observation:
                errors.append(f"sample {sample}: failed observation requires a bounded reason")
            if outcome == "http_error" and not 400 <= observation.get("http_status", 0) <= 599:
                errors.append(f"sample {sample}: HTTP error requires a 4xx or 5xx status")

    scope = document["claim"]["scope"]
    minimum_vantages, minimum_operators, minimum_regions, minimum_domains, minimum_networks = MINIMUM_DIVERSITY[scope]
    diversity = (
        len(vantage_ids),
        len({item["operator_id"] for item in vantages}),
        len({item["region"] for item in vantages}),
        len({item["failure_domain_id"] for item in vantages}),
        len({item["network_class"] for item in vantages}),
    )
    for actual, minimum, label in zip(
        diversity,
        (minimum_vantages, minimum_operators, minimum_regions, minimum_domains, minimum_networks),
        ("vantages", "operators", "regions", "failure domains", "network classes"),
        strict=True,
    ):
        if actual < minimum:
            errors.append(f"{scope} claim requires at least {minimum} {label}; found {actual}")

    if document["evidence_class"] == "independent" and any(item["target_controlled"] for item in vantages):
        errors.append("independent evidence cannot include a target-controlled vantage")

    summary = document["summary"]
    counts = Counter(item["outcome"] for item in observations)
    successful = counts["success"]
    failed = len(observations) - successful
    expected = {
        "requested_samples": len(observations),
        "successful_samples": successful,
        "failed_samples": failed,
        "latency_sample_count": successful,
    }
    for field, value in expected.items():
        if summary[field] != value:
            errors.append(f"summary {field} must be {value}")
    for outcome in OUTCOMES:
        if summary["outcomes"][outcome] != counts[outcome]:
            errors.append(f"summary outcome {outcome} must be {counts[outcome]}")
    availability = successful / len(observations)
    if not math.isclose(summary["availability"], availability, abs_tol=0.000001):
        errors.append(f"summary availability must be {availability:.6f}")

    latencies = [item["latency_ms"] for item in observations if item["outcome"] == "success"]
    if latencies:
        expected_latency = {
            "min": min(latencies),
            "p50": _nearest_rank(latencies, 0.50),
            "p95": _nearest_rank(latencies, 0.95),
            "max": max(latencies),
        }
        if summary.get("latency_ms") != expected_latency:
            errors.append(f"summary latency_ms must be {expected_latency}")
    elif "latency_ms" in summary:
        errors.append("summary latency_ms must be omitted when no observation succeeded")
    return sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", nargs="?", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    document = json.loads(args.evidence.read_text(encoding="utf-8"))
    errors = validate(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"public measurement evidence valid: {len(document['observations'])} observations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
