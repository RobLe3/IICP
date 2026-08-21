#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs/architecture/node-observability-v1.json").read_text())


class NodeObservabilityContractTests(unittest.TestCase):
    def test_unknown_event_is_neutral(self):
        event = next(item for item in DATA["events"] if item["name"] == "future_event")
        self.assertEqual(event["classification"], "unknown")

    def test_failures_never_classify_as_success(self):
        for event in DATA["events"]:
            if event["name"].endswith(("_fail", "_error")):
                self.assertEqual(event["classification"], "control_failure")

    def test_legacy_registration_alias_points_to_canonical_failure(self):
        alias = next(item for item in DATA["events"] if item["name"] == "register_error")
        canonical = next(item for item in DATA["events"] if item["name"] == "register_fail")
        self.assertEqual(alias["legacy_alias_for"], canonical["name"])
        self.assertTrue(canonical["canonical"])

    def test_explicit_health_precedes_inference(self):
        self.assertEqual(DATA["health_precedence"][0], "node_health_endpoint")
        self.assertEqual(DATA["health_precedence"][-1], "inferred_log_or_event_freshness")

    def test_private_local_never_falls_back_public(self):
        self.assertEqual(DATA["private_local_public_fallback"], "forbidden")

    def test_counter_delta_is_not_original_event(self):
        delta = DATA["task_counter_delta"]
        self.assertFalse(delta["original_node_event"])
        self.assertEqual(delta["timestamp_semantics"], "observation_time")

    def test_sensitive_content_is_excluded(self):
        forbidden = set(DATA["event_envelope"]["content_forbidden"])
        self.assertIn("task_prompt", forbidden)
        self.assertIn("credential", forbidden)
        self.assertIn("private_key", forbidden)


if __name__ == "__main__":
    unittest.main()
