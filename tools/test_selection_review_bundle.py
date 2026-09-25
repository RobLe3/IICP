#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import posixpath
import re
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
                    "standards/PROTOCOL_COMPARISON_2026-09-25.md",
                    "standards/EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-09-25.md",
                    "IMPLEMENTATIONS.md",
                    "ecosystem/CURRENT_VERSIONS.md",
                    "pre1/README.md",
                    "pre1/feature-baseline-v1.json",
                    "docs/architecture/identifier-registry-v1.json",
                    "spec/v1.9/conformance-test-suite.md",
                    "SHA256SUMS.json",
                ):
                    self.assertIn(PREFIX + required, names)
                manifest = json.loads(archive.read(PREFIX + "SHA256SUMS.json"))
                comparison = json.loads(archive.read(PREFIX + "standards/protocol-comparison-v1.json"))
                references = {
                    row[field]
                    for row in comparison["intent_routing_requirements"]
                    for field in ("iicp_reference", "fixture_reference")
                    if row.get(field)
                }
                self.assertTrue(references.issubset(manifest["files"]))
                for relative in manifest["files"]:
                    if not relative.endswith(".md"):
                        continue
                    markdown = archive.read(PREFIX + relative).decode("utf-8")
                    for target in re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", markdown):
                        target = target.split("#")[0].split(" ")[0]
                        if not target or target.startswith(("http:", "https:", "mailto:", "/")):
                            continue
                        linked = posixpath.normpath((Path(relative).parent / target).as_posix())
                        if (ROOT / linked).is_file():
                            self.assertIn(linked, manifest["files"], relative)
                self.assertIn("not submitted", manifest["status"])
                self.assertNotIn("standards/ietf/draft-roble-iicp-peer.md", manifest["files"])
                for relative, expected in manifest["files"].items():
                    self.assertEqual(expected, hashlib.sha256(archive.read(PREFIX + relative)).hexdigest())


if __name__ == "__main__":
    unittest.main()
