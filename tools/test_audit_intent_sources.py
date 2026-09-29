from __future__ import annotations
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import audit_intent_sources as audit
from audit_intent_sources import classify

class IntentSourceAuditTest(unittest.TestCase):
    def test_empty_namespace_segment_is_not_a_candidate(self) -> None:
        classification, _ = classify("urn:iicp:intent::chat:v1", set())
        self.assertEqual("negative-test", classification)

    def test_implementation_namespace_remains_a_candidate(self) -> None:
        classification, _ = classify("urn:iicp:intent:vendor:chat:v1", set())
        self.assertEqual("candidate-unregistered", classification)


class SourceInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "registry").mkdir()
        canonical = json.loads((audit.ROOT / "registry/intents.json").read_text())
        self.urn = next(row["urn"] for row in canonical["intents"]
                        if row["urn"].endswith(":llm:chat:v1"))
        (self.root / "registry/intents.json").write_text(json.dumps(canonical))
        self.sources = {self.urn: {"iicp-directory-php": {"scripts/known.py"}}}
        self.output = self.root / "registry/source-classification.json"
        for replacement in (patch.object(audit, "ROOT", self.root),
                            patch.object(audit, "OUTPUT", self.output),
                            patch.object(audit, "occurrences", lambda: self.sources),
                            patch.object(sys, "argv", ["audit_intent_sources.py", "--check"])):
            replacement.start()
            self.addCleanup(replacement.stop)
        self.output.write_text(json.dumps(audit.render()))

    def check(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return audit.main()

    def test_reviewed_source_passes_without_registry_promotion(self):
        self.assertEqual(self.check(), 0)
        row = audit.render()["records"][0]
        self.assertEqual(row["classification"], "canonical")
        self.assertEqual(row["disposition"], "present in registry/intents.json")

    def test_new_location_for_canonical_intent_still_fails(self):
        self.sources[self.urn]["iicp-directory-php"].add("scripts/new.py")
        with self.assertRaisesRegex(SystemExit, "unclassified intent source"):
            self.check()

    def test_new_repository_for_known_intent_still_fails(self):
        self.sources[self.urn]["iicp-directory-rust"] = {"scripts/known.py"}
        with self.assertRaisesRegex(SystemExit, "unclassified intent source"):
            self.check()

    def test_unknown_identifier_still_fails(self):
        self.sources[self.urn + "/unknown"] = {"iicp-directory-php": {"scripts/known.py"}}
        with self.assertRaisesRegex(SystemExit, "unclassified intent observation"):
            self.check()

    def test_classification_drift_still_fails(self):
        value = json.loads(self.output.read_text())
        value["records"][0]["classification"] = "candidate-unregistered"
        self.output.write_text(json.dumps(value))
        with self.assertRaisesRegex(SystemExit, "classification drift"):
            self.check()

    def test_missing_inventory_still_fails(self):
        self.output.unlink()
        with self.assertRaisesRegex(SystemExit, "classification is missing"):
            self.check()


if __name__ == "__main__":
    unittest.main()
