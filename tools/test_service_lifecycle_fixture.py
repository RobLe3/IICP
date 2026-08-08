#!/usr/bin/env python3
"""Structural and semantic checks for the draft service-lifecycle vectors."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/native-ai-infrastructure/fixtures/service-profiles-v1.json"
TERMINAL = {"completed", "failed", "cancelled", "timed_out", "rejected"}


class ServiceLifecycleFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(FIXTURE.read_text())
        cls.vectors = {item["id"]: item for item in cls.data["lifecycle_vectors"]}

    def test_identifiers_are_unique_and_complete(self) -> None:
        ids = [item["id"] for item in self.data["lifecycle_vectors"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(
            {f"SERVICE-LIFECYCLE-{number:02d}" for number in range(1, 14)},
            set(ids),
        )

    def test_basic_stream_uses_incremental_chunks_and_terminal_accounting(self) -> None:
        events = self.vectors["SERVICE-LIFECYCLE-02"]["events"]
        chunks = [event.get("result", "") for event in events if event["event"] in {"partial", "completed"}]
        self.assertEqual("hello!", "".join(chunks))
        self.assertEqual([1, 2, 3], [event["tokens_used"] for event in events if "tokens_used" in event])
        self.assertTrue(events[-1]["is_final"])

    def test_valid_histories_have_increasing_sequence_and_one_terminal(self) -> None:
        for vector_id in [
            "SERVICE-LIFECYCLE-01",
            "SERVICE-LIFECYCLE-02",
            "SERVICE-LIFECYCLE-04",
            "SERVICE-LIFECYCLE-05",
            "SERVICE-LIFECYCLE-06",
            "SERVICE-LIFECYCLE-09",
        ]:
            with self.subTest(vector_id=vector_id):
                events = self.vectors[vector_id]["events"]
                self.assertEqual(
                    list(range(len(events))),
                    [event["sequence"] for event in events],
                )
                terminals = [event for event in events if event["event"] in TERMINAL]
                self.assertEqual(1, len(terminals))
                self.assertTrue(terminals[0]["is_final"])
                for event in events:
                    if event["event"] == "partial":
                        self.assertFalse(event["is_final"])

    def test_negative_vectors_capture_terminal_and_finality_failures(self) -> None:
        after_final = self.vectors["SERVICE-LIFECYCLE-10"]["events"]
        duplicate_terminal = self.vectors["SERVICE-LIFECYCLE-11"]["events"]
        missing_terminal = self.vectors["SERVICE-LIFECYCLE-12"]["events"]
        partial_final = self.vectors["SERVICE-LIFECYCLE-13"]["events"]

        self.assertTrue(after_final[1]["is_final"])
        self.assertGreater(len(after_final), 2)
        self.assertEqual(2, sum(event["event"] in TERMINAL for event in duplicate_terminal))
        self.assertFalse(any(event["event"] in TERMINAL for event in missing_terminal))
        self.assertEqual("partial", partial_final[-1]["event"])
        self.assertTrue(partial_final[-1]["is_final"])


if __name__ == "__main__":
    unittest.main()
