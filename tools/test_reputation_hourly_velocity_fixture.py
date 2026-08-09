#!/usr/bin/env python3
"""Validate the pre-normative RT-01b hourly-velocity fixture."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/reputation-hourly-velocity-v0.json"


def main() -> int:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert document["fixture_version"] == "0.1.0-draft"
    assert document["status"] == "pre-normative"
    assert document["profile_id"] == "iicp.directory.reputation-hourly-velocity.v0"

    scope = document["scope"]
    assert scope["implementation_flavors"] == ["php", "rust"]
    assert scope["database_mode"] == "disposable_mysql"
    assert len(scope["required_behaviors"]) == 5

    inputs = document["inputs"]
    expected = document["expected"]
    assert inputs["initial_reputation"] == 0.5
    assert inputs["positive_delta_per_heartbeat"] == 0.1
    assert inputs["maximum_hourly_positive_gain"] == 0.2
    assert inputs["workers"] == 4
    assert inputs["tasks_success_per_worker"] == 10
    assert inputs["workers"] * inputs["tasks_success_per_worker"] == expected["concurrent_tasks_total"]
    assert expected["concurrent_score"] == 0.7
    assert expected["concurrent_hourly_gain"] == inputs["maximum_hourly_positive_gain"]
    assert expected["same_window_age_seconds"] == 3599
    assert expected["same_window_score"] == expected["concurrent_score"]
    assert expected["next_window_age_seconds"] == 3600
    assert expected["next_window_score_after_first_positive"] == 0.8
    assert expected["next_window_hourly_gain_after_first_positive"] == 0.1
    assert expected["final_score_after_reload_and_negative"] == 0.85
    assert expected["final_hourly_gain"] == inputs["maximum_hourly_positive_gain"]

    required = document["result_contract"]["required_fields"]
    assert len(required) == len(set(required)), "duplicate result-contract field"
    rendered = json.dumps(document, sort_keys=True).lower()
    for forbidden in ("bearer ", "api_key", "private_key", "client_secret"):
        assert forbidden not in rendered, f"fixture contains forbidden secret material: {forbidden}"

    print("PASS RT-01b hourly-velocity fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
