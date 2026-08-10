#!/usr/bin/env python3
"""Validate the pre-normative local runtime-health parity fixture."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/runtime-supervision/fixtures/runtime-health-v1.json"
SCHEMA = ROOT / "research/runtime-supervision/fixtures/runtime-health-snapshot-v1.schema.json"
MANIFEST = ROOT / "research/runtime-supervision/fixtures/runtime-health-fixture-manifest-v1.json"

STATES = {"healthy", "degraded", "recovering", "unavailable", "not_applicable", "unknown"}
REASONS = {"STARTING", "STOPPING", "RUNTIME_PROGRESS_STALE", "SUPERVISOR_PROGRESS_STALE", "DIRECTORY_UNAVAILABLE", "DNS_UNAVAILABLE", "INTERNET_UNAVAILABLE", "TUNNEL_RECOVERING", "PROVIDER_UNAVAILABLE", "NO_CAPACITY", "ROUTING_UNAVAILABLE", "STATE_UNKNOWN"}

def classify(i: dict) -> tuple[str, str, list[str]]:
    if i["lifecycle"] == "starting": return "starting", "not_ready", ["STARTING"]
    if i["runtime_age_ms"] > i["runtime_stale_after_ms"]: return "not_live", "not_ready", ["RUNTIME_PROGRESS_STALE"]
    if i["supervisor_required"] and i["supervisor_age_ms"] > i["supervisor_stale_after_ms"]: return "not_live", "not_ready", ["SUPERVISOR_PROGRESS_STALE"]
    if i["lifecycle"] == "stopping": return "live", "not_ready", ["STOPPING"]
    reasons: list[str] = []
    if i["provider"] == "unavailable": reasons.append("PROVIDER_UNAVAILABLE")
    if not i["capacity_available"]: reasons.append("NO_CAPACITY")
    if i["routing"] == "unavailable": reasons.append("ROUTING_UNAVAILABLE")
    if i["tunnel"] == "recovering": reasons.append("TUNNEL_RECOVERING")
    if i["directory"] == "unavailable": reasons.append("DIRECTORY_UNAVAILABLE")
    if i["dns"] == "unavailable": reasons.append("DNS_UNAVAILABLE")
    if i["internet"] == "unavailable": reasons.append("INTERNET_UNAVAILABLE")
    if "PROVIDER_UNAVAILABLE" in reasons or "NO_CAPACITY" in reasons or "ROUTING_UNAVAILABLE" in reasons:
        readiness = "not_ready"
    elif reasons:
        readiness = "degraded"
    else:
        readiness = "ready"
    return "live", readiness, reasons

def main() -> None:
    fixture = json.loads(FIXTURE.read_text())
    schema = json.loads(SCHEMA.read_text())
    assert fixture["status"] == "pre-normative-operational"
    assert schema["properties"]["health_schema_version"]["const"] == 1
    seen: set[str] = set()
    for scenario in fixture["scenarios"]:
        assert scenario["id"] not in seen
        seen.add(scenario["id"])
        i, expected = scenario["input"], scenario["expected"]
        assert i["provider"] in STATES and i["routing"] in STATES and i["directory"] in STATES
        actual = classify(i)
        assert actual == (expected["liveness"], expected["readiness"], expected["reason_codes"]), (scenario["id"], actual, expected)
        assert set(expected["reason_codes"]) <= REASONS
    manifest = json.loads(MANIFEST.read_text())
    for entry in manifest["fixtures"]:
        path = MANIFEST.parent / entry["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], entry["path"]
    print(f"runtime-health fixture valid: {len(seen)} scenarios")

if __name__ == "__main__": main()
