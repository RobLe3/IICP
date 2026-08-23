#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "research/pre-normative-profiles/fixtures/security-mechanism-lifecycle-v0.json").read_text())
assert data["decision_steps"] == ["understand", "verify", "trust", "authorize"]
assert set(data["lifecycle_states"]) == {"active", "deprecated", "prohibited", "replaced"}
cases = {case["id"]: case for case in data["cases"]}
required = {"unknown-required-mechanism", "prohibited-valid-signature", "downgrade-attempt", "gateway-misleading-claim", "verified-not-authorized"}
assert required <= cases.keys()
assert all(cases[item]["expected"].startswith("refuse") for item in required)
relation = data["replacement_relations"][0]
assert relation["preserves_historical_meaning"] is True
assert relation["implies_equal_properties"] is False
print(f"PASS {len(cases)} security-mechanism lifecycle cases")
