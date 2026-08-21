#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "iicp-selection-eligibility-review-candidate.zip"
PREFIX = "iicp-selection-eligibility-review-candidate/"


class SelectionReviewBundleTests(unittest.TestCase):
    def build(self, output: Path) -> Path:
        subprocess.run(
            ["python3", str(ROOT / "tools/build_selection_review_bundle.py"), "--output-dir", str(output)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return output / NAME

    def test_bundle_is_deterministic_and_claim_bounded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            left = self.build(root / "left")
            right = self.build(root / "right")
            self.assertEqual(hashlib.sha256(left.read_bytes()).digest(), hashlib.sha256(right.read_bytes()).digest())
            with zipfile.ZipFile(left) as archive:
                names = set(archive.namelist())
                for required in (
                    "standards/SELECTION_REVIEW_BUNDLE_README.md",
                    "standards/SELECTION_ELIGIBILITY_PROBLEM_STATEMENT.md",
                    "standards/SELECTION_TRUST_AND_REVALIDATION.md",
                    "docs/architecture/node-observability-interfaces.md",
                    "standards/PROTOCOL_COMPARISON_2026-08-15.md",
                    "IMPLEMENTATIONS.md",
                    "spec/v1.9/conformance-test-suite.md",
                    "SHA256SUMS.json",
                ):
                    self.assertIn(PREFIX + required, names)
                manifest = json.loads(archive.read(PREFIX + "SHA256SUMS.json"))
                self.assertIn("not submitted", manifest["status"])
                self.assertNotIn("standards/ietf/draft-roble-iicp-peer.md", manifest["files"])
                for relative, expected in manifest["files"].items():
                    self.assertEqual(expected, hashlib.sha256(archive.read(PREFIX + relative)).hexdigest())


if __name__ == "__main__":
    unittest.main()
