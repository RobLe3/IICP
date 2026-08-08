from __future__ import annotations

import copy
from datetime import date
import json
from pathlib import Path
import unittest

from check_intent_registry import validate

ROOT = Path(__file__).resolve().parents[1]


class IntentRegistryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads((ROOT / "registry/intents.json").read_text())

    def test_current_registry_passes(self) -> None:
        self.assertEqual([], validate(self.document, today=date(2026, 8, 8)))

    def test_root_schema_identifier_is_required(self) -> None:
        document = copy.deepcopy(self.document)
        document["schema"] = "https://example.invalid/registry.json"
        self.assertIn(
            "registry schema must identify the canonical 1.4 root schema",
            validate(document),
        )

    def test_duplicate_urn_fails(self) -> None:
        document = copy.deepcopy(self.document)
        document["intents"].append(copy.deepcopy(document["intents"][0]))
        self.assertTrue(any("duplicate intent URN" in error for error in validate(document)))

    def test_deprecated_successor_must_exist(self) -> None:
        document = copy.deepcopy(self.document)
        deprecated = next(item for item in document["intents"] if item["status"] == "deprecated")
        deprecated["deprecated_by"] = "urn:iicp:intent:missing:v1"
        self.assertTrue(any("deprecated_by successor" in error for error in validate(document)))

    def test_schema_digest_mismatch_fails(self) -> None:
        document = copy.deepcopy(self.document)
        document["intents"][0]["schemas"]["input"]["sha256"] = "0" * 64
        self.assertTrue(any("sha256 does not match" in error for error in validate(document)))

    def test_expired_review_date_fails(self) -> None:
        document = copy.deepcopy(self.document)
        document["intents"][0]["review_by"] = "2026-08-07"
        self.assertTrue(any("review_by is expired" in error for error in validate(document, today=date(2026, 8, 8))))

    def test_invalid_lifecycle_transition_fails(self) -> None:
        document = copy.deepcopy(self.document)
        entry = next(item for item in document["intents"] if item["status"] == "deprecated")
        entry["status_history"].append(
            {"status": "active", "date": "2026-08-08", "reason": "invalid reactivation"}
        )
        entry["status"] = "active"
        self.assertTrue(any("invalid lifecycle transition" in error for error in validate(document)))

    def test_active_intent_requires_evidence(self) -> None:
        document = copy.deepcopy(self.document)
        active = next(item for item in document["intents"] if item["status"] == "active")
        active["implementation_evidence"] = []
        self.assertTrue(any("released implementation" in error for error in validate(document)))


if __name__ == "__main__":
    unittest.main()
