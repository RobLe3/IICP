#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/discovery-evidence-v1.json"
MANIFEST = ROOT / "research/pre-normative-profiles/fixtures/profile-fixture-manifest-v0.json"

def main() -> int:
    fixture = json.loads(FIXTURE.read_text())
    manifest = json.loads(MANIFEST.read_text())
    assert fixture["content_free"] is True
    assert [case["id"] for case in fixture["cases"]] == [f"DIR-EVIDENCE-{n:02d}" for n in range(1, 6)]
    entry = next(item for item in manifest["fixtures"] if item["path"] == FIXTURE.name)
    assert entry["sha256"] == hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    assert fixture["invariants"]["identity_material_exposed"] is False
    assert fixture["invariants"]["failure_domain_basis"] == "not_attested"
    rendered = FIXTURE.read_text()
    for forbidden in ["operator_pubkey", "endpoint", "node_id", "credential", "payload"]:
        assert forbidden not in rendered
    print("PASS 5 content-free discovery-evidence cases")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
