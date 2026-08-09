#!/usr/bin/env python3
"""Keep the public terminology map concrete and evidence-bounded."""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "TERMINOLOGY_AND_DISCOVERABILITY.md"


class TerminologyDiscoverabilityTest(unittest.TestCase):
    def test_preferred_name_subtitle_and_required_terms_are_present(self) -> None:
        text = MAP.read_text(encoding="utf-8")
        for phrase in (
            "Intent-based Inter-agent Communication Protocol (IICP)",
            "protocol-neutral intent-resolution and execution-selection control plane",
            "Agent discovery",
            "Intent resolution",
            "Provider selection",
            "Capability routing",
            "AI mesh",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_map_preserves_payload_and_evidence_boundaries(self) -> None:
        text = MAP.read_text(encoding="utf-8")
        self.assertIn("task payloads are intended to\n  travel directly", text)
        self.assertIn("not supported by that page's current evidence", text)
        self.assertIn("does not claim to replace their task semantics", text)


if __name__ == "__main__":
    unittest.main()
