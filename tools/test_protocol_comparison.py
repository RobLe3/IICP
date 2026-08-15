#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from check_protocol_comparison import DATA, validate


class ProtocolComparisonTests(unittest.TestCase):
    def _validate_mutation(self, mutate) -> list[str]:
        data = json.loads(DATA.read_text(encoding="utf-8"))
        mutate(data)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "comparison.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return validate(path)

    def test_canonical_dataset_passes(self) -> None:
        self.assertEqual(validate(), [])

    def test_unknown_value_fails(self) -> None:
        errors = self._validate_mutation(
            lambda data: data["entries"][0]["dimensions"].__setitem__("selection", "yes")
        )
        self.assertTrue(any("unknown comparison values" in item for item in errors))

    def test_internet_draft_cannot_imply_endorsement(self) -> None:
        errors = self._validate_mutation(
            lambda data: data["entries"][1].__setitem__(
                "formal_status", "active_individual_internet_draft"
            )
        )
        self.assertTrue(any("deny endorsement" in item for item in errors))

    def test_score_outside_rubric_fails(self) -> None:
        errors = self._validate_mutation(
            lambda data: data["entries"][0]["maturity"]["specification_precision"].__setitem__(
                "score", 5
            )
        )
        self.assertTrue(any("score must be 0-4" in item for item in errors))

    def test_assessment_requires_source_and_rationale(self) -> None:
        def mutate(data: dict) -> None:
            assessment = data["overlap_evidence"]["iicp"]["selection"]
            assessment["rationale"] = ""
            assessment["source"] = ""

        errors = self._validate_mutation(mutate)
        self.assertTrue(any("rationale is required" in item for item in errors))
        self.assertTrue(any("source must be" in item for item in errors))

    def test_future_evidence_date_fails(self) -> None:
        errors = self._validate_mutation(
            lambda data: data["entries"][0]["first_public_evidence"].__setitem__(
                "date", "2026-08-16"
            )
        )
        self.assertTrue(any("later than the evidence date" in item for item in errors))

    def test_unsorted_mechanism_chronology_fails(self) -> None:
        def mutate(data: dict) -> None:
            data["mechanism_chronology"][0], data["mechanism_chronology"][1] = (
                data["mechanism_chronology"][1],
                data["mechanism_chronology"][0],
            )

        errors = self._validate_mutation(mutate)
        self.assertIn("mechanism chronology must be date sorted", errors)

    def test_unknown_chronology_subject_fails(self) -> None:
        errors = self._validate_mutation(
            lambda data: data["mechanism_chronology"][0].__setitem__("subject", "unknown")
        )
        self.assertTrue(any("unknown subject" in item for item in errors))

    def test_composite_ranking_is_forbidden_at_any_depth(self) -> None:
        errors = self._validate_mutation(
            lambda data: data["entries"][0].__setitem__("overall_score", 99)
        )
        self.assertIn("composite ranking fields are forbidden", errors)

    def test_key_chronology_is_explicit(self) -> None:
        data = json.loads(DATA.read_text(encoding="utf-8"))
        first_public = {
            entry["id"]: entry["first_public_evidence"]["date"]
            for entry in data["entries"]
        }
        self.assertEqual(first_public["iicp"], "2025-10-27")
        self.assertEqual(first_public["aidip"], "2025-10-15")
        aidip_events = [
            event["date"]
            for event in data["mechanism_chronology"]
            if event["subject"] == "aidip"
        ]
        self.assertEqual(aidip_events, ["2025-10-15", "2026-02-12", "2026-07-06"])


if __name__ == "__main__":
    unittest.main()
