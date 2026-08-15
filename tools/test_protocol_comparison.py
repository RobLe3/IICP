#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from check_protocol_comparison import DATA, validate


class ProtocolComparisonTests(unittest.TestCase):
    def test_canonical_dataset_passes(self) -> None:
        self.assertEqual(validate(), [])

    def test_unknown_value_fails(self) -> None:
        data = json.loads(DATA.read_text(encoding="utf-8"))
        data["entries"][0]["dimensions"]["selection"] = "yes"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "comparison.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any("unknown comparison values" in item for item in validate(path)))

    def test_internet_draft_cannot_imply_endorsement(self) -> None:
        data = json.loads(DATA.read_text(encoding="utf-8"))
        data["entries"][1]["formal_status"] = "active_individual_internet_draft"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "comparison.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any("deny endorsement" in item for item in validate(path)))


if __name__ == "__main__":
    unittest.main()

