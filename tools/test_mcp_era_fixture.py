#!/usr/bin/env python3
"""Validate the pre-normative MCP era-negotiation fixture."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/mcp-era-negotiation-v0.json"
REQUIRED_IDS = {f"MCP-ERA-{number:02d}" for number in range(1, 24)}


def main() -> int:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert document["status"] == "pre-normative"
    assert document["fixture_version"] == "0.1.2-draft"
    assert document["supported_revisions"] == ["2025-11-25", "2026-07-28"]

    cases = document["cases"]
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids)), "duplicate MCP fixture case id"
    assert set(ids) == REQUIRED_IDS, "missing or unexpected MCP fixture case id"
    for case in cases:
        assert isinstance(case["expected"].get("accepted"), bool)

    case_by_id = {case["id"]: case for case in cases}
    assert case_by_id["MCP-ERA-19"]["expected"]["reason"] == "initialize_required"
    assert case_by_id["MCP-ERA-20"]["expected"]["session_mode"] == "retained"
    assert case_by_id["MCP-ERA-21"]["expected"]["reason"] == "missing_session_identifier"
    assert case_by_id["MCP-ERA-22"]["expected"]["reason"] == "session_expired_caller_retry_required"
    assert case_by_id["MCP-ERA-23"]["expected"]["reason"] == "reinitialized_once"

    rendered = json.dumps(document, sort_keys=True).lower()
    for forbidden in ("bearer ", "api_key", "private_key", "client_secret"):
        assert forbidden not in rendered, f"fixture contains forbidden secret material: {forbidden}"

    print(f"PASS {len(cases)} pre-normative MCP era-negotiation cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
