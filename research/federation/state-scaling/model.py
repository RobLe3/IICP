#!/usr/bin/env python3
"""Deterministic IICP federation current-state scaling model.

This is a capacity and semantics model, not a network simulator or a claim of
Internet-scale support. All assumptions are explicit in ASSUMPTIONS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

ASSUMPTIONS: dict[str, Any] = {
    "model_version": "iicp-federation-state-scaling-v1",
    "provider_record_bytes": 4096,
    "local_index_overhead_ratio_ppm": 250_000,
    "domain_descriptor_bytes": 4096,
    "capability_prefixes_per_domain": 64,
    "summary_entry_bytes": 256,
    "state_change_events_per_provider_hour_ppm": 5_000,
    "federated_event_bytes": 1024,
    "heartbeat_interval_seconds": 300,
    "summary_refresh_seconds": [60, 300],
    "event_tail_hours": 24,
}

SCENARIOS = [
    # providers, domains, share of providers in the largest domain (ppm)
    (1_000, 10, 250_000),
    (100_000, 100, 100_000),
    (1_000_000, 1_000, 50_000),
    (100_000_000, 10_000, 10_000),
]

@dataclass(frozen=True)
class Result:
    providers: int
    domains: int
    providers_per_domain: int
    largest_domain_providers: int
    full_state_bytes_per_directory: int
    full_state_bytes_ecosystem: int
    sharded_bytes_per_directory: int
    largest_shard_bytes: int
    summary_bytes_per_directory: int
    global_state_change_events_per_hour: int
    full_state_event_bytes_per_directory_hour: int
    full_state_event_bytes_ecosystem_hour: int
    local_heartbeats_per_hour: int
    max_changed_providers_per_60s: int
    max_changed_providers_per_300s: int


def ceil_div(value: int, divisor: int) -> int:
    return (value + divisor - 1) // divisor


def model(providers: int, domains: int, largest_domain_share_ppm: int) -> Result:
    if providers <= 0 or domains <= 0 or domains > providers:
        raise ValueError("providers and domains must be positive, with domains <= providers")
    if not 1 <= largest_domain_share_ppm <= 1_000_000:
        raise ValueError("largest domain share must be between 1 and 1,000,000 ppm")
    a = ASSUMPTIONS
    per_domain = ceil_div(providers, domains)
    overhead_ppm = 1_000_000 + a["local_index_overhead_ratio_ppm"]
    full = ceil_div(providers * a["provider_record_bytes"] * overhead_ppm, 1_000_000)
    local = ceil_div(per_domain * a["provider_record_bytes"] * overhead_ppm, 1_000_000)
    largest_domain = ceil_div(providers * largest_domain_share_ppm, 1_000_000)
    largest_local = ceil_div(largest_domain * a["provider_record_bytes"] * overhead_ppm, 1_000_000)
    descriptors = domains * a["domain_descriptor_bytes"]
    summaries = domains * a["capability_prefixes_per_domain"] * a["summary_entry_bytes"]
    changes = ceil_div(providers * a["state_change_events_per_provider_hour_ppm"], 1_000_000)
    event_bytes = changes * a["federated_event_bytes"]
    heartbeats = ceil_div(per_domain * 3600, a["heartbeat_interval_seconds"])

    def changed(refresh_seconds: int) -> int:
        return ceil_div(changes * refresh_seconds, 3600)

    return Result(
        providers=providers,
        domains=domains,
        providers_per_domain=per_domain,
        largest_domain_providers=largest_domain,
        full_state_bytes_per_directory=full,
        full_state_bytes_ecosystem=full * domains,
        sharded_bytes_per_directory=local + descriptors,
        largest_shard_bytes=largest_local + descriptors,
        summary_bytes_per_directory=local + descriptors + summaries,
        global_state_change_events_per_hour=changes,
        full_state_event_bytes_per_directory_hour=event_bytes,
        full_state_event_bytes_ecosystem_hour=event_bytes * domains,
        local_heartbeats_per_hour=heartbeats,
        max_changed_providers_per_60s=changed(60),
        max_changed_providers_per_300s=changed(300),
    )


def document() -> dict[str, Any]:
    assumptions_json = json.dumps(ASSUMPTIONS, sort_keys=True, separators=(",", ":"))
    return {
        "schema": ASSUMPTIONS["model_version"],
        "assumptions_sha256": hashlib.sha256(assumptions_json.encode()).hexdigest(),
        "assumptions": ASSUMPTIONS,
        "results": [asdict(model(n, d, share)) for n, d, share in SCENARIOS],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit the canonical JSON document")
    args = parser.parse_args()
    doc = document()
    if args.json:
        print(json.dumps(doc, indent=2, sort_keys=True))
        return
    for row in doc["results"]:
        print(json.dumps(row, sort_keys=True))


if __name__ == "__main__":
    main()
