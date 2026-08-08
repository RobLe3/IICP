from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from check_intent_registry import validate

ROOT = Path(__file__).resolve().parents[1]


class IntentRegistryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads((ROOT / "registry/intents.json").read_text())

    def test_current_registry_passes(self) -> None:
        self.assertEqual([], validate(self.document))

    def test_duplicate_urn_fails(self) -> None:
        document = copy.deepcopy(self.document)
        document["intents"].append(copy.deepcopy(document["intents"][0]))
        self.assertTrue(any("duplicate intent URN" in error for error in validate(document)))

    def test_deprecated_successor_must_exist(self) -> None:
        document = copy.deepcopy(self.document)
        deprecated = next(item for item in document["intents"] if item["status"] == "deprecated")
        deprecated["deprecated_by"] = "urn:iicp:intent:missing:v1"
        self.assertTrue(any("deprecated_by successor" in error for error in validate(document)))


if __name__ == "__main__":
    unittest.main()
