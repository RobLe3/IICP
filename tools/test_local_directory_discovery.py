#!/usr/bin/env python3
"""Validate verified local-directory discovery semantics and fixtures."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
PROFILE_ROOT = ROOT / "research/pre-normative-profiles"
PROFILE = PROFILE_ROOT / "local-directory-discovery-v0.md"
FIXTURE = PROFILE_ROOT / "fixtures/local-directory-discovery-v0.json"
SCHEMA = PROFILE_ROOT / "schemas/local-directory-discovery-v0.schema.json"
GENESIS = "https://iicp.network/api"

REQUIRED_TXT = {"pv": "0", "path": "/.well-known/iicp-directory.json", "transport": "https"}
FORBIDDEN_TXT = {"credential", "token", "secret", "membership", "nodes", "models", "intents", "capabilities", "topology", "federation"}


def valid_candidate(candidate: dict, mode: str, now: int, maximum_txt_bytes: int) -> bool:
    txt = candidate["txt"]
    if candidate["txt_bytes"] > maximum_txt_bytes:
        return False
    if any(txt.get(key) != value for key, value in REQUIRED_TXT.items()):
        return False
    if FORBIDDEN_TXT.intersection(key.lower() for key in txt):
        return False
    if urlparse(txt["path"]).scheme or not txt["path"].startswith("/"):
        return False
    if txt.get("did") and txt["did"] != candidate["descriptor_did"]:
        return False
    if not candidate["descriptor_signature_valid"]:
        return False
    if min(candidate["descriptor_expires_at"], candidate["cache_expires_at"]) < now:
        return False
    allowed_trust = {
        "public": {"pinned"},
        "private": {"domain"},
        "federated_private": {"domain", "federation"},
        "custom": {"pinned", "domain", "federation"},
    }
    return candidate["trust"] in allowed_trust.get(mode, set())


def resolve(vector: dict, maximum_txt_bytes: int) -> dict:
    item = vector["input"]
    if item["explicit_directory"]:
        return {"source": "explicit", "selected": item["explicit_directory"], "reason": "explicit_configuration", "mdns_query": False}
    if item["mode"] == "local_only":
        return {"source": "none", "selected": None, "reason": "local_only_external_forbidden", "mdns_query": False}
    if item["client_kind"] == "browser":
        return {"source": "genesis", "selected": GENESIS, "reason": "browser_local_discovery_unsupported", "mdns_query": False}
    if not item["profile_enabled"]:
        selected = GENESIS if item["genesis_fallback_allowed"] else None
        return {"source": "genesis" if selected else "none", "selected": selected, "reason": "profile_disabled", "mdns_query": False}

    candidates = [candidate for candidate in item["candidates"] if valid_candidate(candidate, item["mode"], item["now"], maximum_txt_bytes)]
    if candidates:
        selected = min(candidates, key=lambda candidate: (candidate["descriptor_did"], candidate["endpoint"]))
        return {"source": "mdns", "selected": selected["endpoint"], "reason": "verified_local_candidate", "mdns_query": True}

    if not item["genesis_fallback_allowed"]:
        return {"source": "none", "selected": None, "reason": "no_verified_directory", "mdns_query": True}
    if item["mdns"] == "ssdp_only":
        reason = "ssdp_not_supported"
    elif item["mdns"] in {"timeout", "unavailable"}:
        reason = "local_discovery_unavailable"
    else:
        reason = "local_candidates_rejected" if item["candidates"] else "no_local_candidate"
    return {"source": "genesis", "selected": GENESIS, "reason": reason, "mdns_query": True}


class LocalDirectoryDiscoveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.schema = json.loads(SCHEMA.read_text())

    def test_schema_and_vectors(self) -> None:
        jsonschema.Draft202012Validator.check_schema(self.schema)
        jsonschema.validate(self.fixture, self.schema)
        for vector in self.fixture["cases"]:
            with self.subTest(vector=vector["id"]):
                self.assertEqual(vector["expected"], resolve(vector, self.fixture["defaults"]["maximum_txt_bytes"]))

    def test_profile_records_discovery_trust_and_fallback_boundaries(self) -> None:
        profile = PROFILE.read_text()
        normalized = " ".join(profile.split())
        for required in [
            "_iicp-dir._tcp.local.",
            "Finding a candidate never changes that order",
            "silent TOFU is forbidden",
            "Public fallback is forbidden",
            "SSDP remains part of UPnP/IGD reachability discovery",
            "No released Intent, Capability, Core frame, directory API or provider record is changed",
        ]:
            self.assertIn(required, normalized)

    def test_multicast_data_contains_no_sensitive_fixture_fields(self) -> None:
        for vector in self.fixture["cases"]:
            for candidate in vector["input"]["candidates"]:
                if vector["id"] == "secret_bearing_txt_rejected":
                    continue
                self.assertFalse(FORBIDDEN_TXT.intersection(key.lower() for key in candidate["txt"]))


if __name__ == "__main__":
    unittest.main()
