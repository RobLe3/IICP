#!/usr/bin/env python3
"""Regression checks for current-suite and editorial-version documentation."""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentationVersionTruthTest(unittest.TestCase):
    def test_current_suite_and_sdk_axes_agree(self) -> None:
        suite = (ROOT / "spec/v1.9/VERSION").read_text(encoding="utf-8").strip()
        projection = json.loads(
            (ROOT / "ecosystem/current-versions.json").read_text(encoding="utf-8")
        )
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        spec_index = (ROOT / "spec/v1.9/README.md").read_text(encoding="utf-8")
        sdk = projection["components"]["client-python"]["release"]

        self.assertEqual(projection["protocol_suite_release"], suite)
        self.assertEqual(projection["components"]["specification"]["release"], suite)
        self.assertIn(f"**Protocol-suite release**: v{suite}", root_readme)
        self.assertIn(f"**Current Protocol Suite version**: [`v{suite}`](./VERSION)", spec_index)
        self.assertIn(f"Published v{sdk}", root_readme)

    def test_spec_index_uses_authoritative_status_meanings(self) -> None:
        spec_index = (ROOT / "spec/v1.9/README.md").read_text(encoding="utf-8")
        self.assertIn("[`SPEC_STATUS.md`](../../SPEC_STATUS.md)", spec_index)
        self.assertNotIn("Active and normative within the project", spec_index)
        for status in (
            "Project-normative",
            "Stable",
            "Active draft",
            "Experimental",
            "Externally ratified",
        ):
            self.assertIn(f"`{status}`", spec_index)

    def test_editorial_versions_match_document_headers(self) -> None:
        framing = (ROOT / "spec/v1.9/iicp-framing.md").read_text(encoding="utf-8")
        versioning = (ROOT / "VERSIONING.md").read_text(encoding="utf-8")
        cip = (ROOT / "spec/v1.9/iicp-cooperative-inference.md").read_text(encoding="utf-8")
        framing_header = re.search(r"^\*\*Version\*\*: (\S+)$", framing, re.MULTILINE)
        framing_changes = re.findall(r"^\| (\S+) \|", framing, re.MULTILINE)
        cip_header = re.search(r"^\*\*Version\*\*: (\S+)$", cip, re.MULTILINE)

        self.assertIsNotNone(framing_header)
        self.assertEqual(framing_header.group(1), framing_changes[-1])
        self.assertIsNotNone(cip_header)
        self.assertIn(
            f"| S.12 `iicp-cooperative-inference.md` | {cip_header.group(1)} |",
            versioning,
        )


if __name__ == "__main__":
    unittest.main()
