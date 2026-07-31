#!/usr/bin/env python3
"""Validate the pre-normative MCP era-negotiation fixture."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/mcp-era-negotiation-v0.json"
REQUIRED_IDS = {f"MCP-ERA-{number:02d}" for number in range(1, 12)}


def main() -> int:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert document["status"] == "pre-normative"
    assert document["supported_revisions"] == ["2025-11-25", "2026-07-28"]

    cases = document["cases"]
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids)), "duplicate MCP fixture case id"
    assert set(ids) == REQUIRED_IDS, "missing or unexpected MCP fixture case id"
    for case in cases:
        assert isinstance(case["expected"].get("accepted"), bool)

    rendered = json.dumps(document, sort_keys=True).lower()
    for forbidden in ("bearer ", "api_key", "private_key", "client_secret"):
        assert forbidden not in rendered, f"fixture contains forbidden secret material: {forbidden}"

    print(f"PASS {len(cases)} pre-normative MCP era-negotiation cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
