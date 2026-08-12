from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "research/strategic/learned-routing-experiment"


class LearnedRoutingExperimentTests(unittest.TestCase):
    def test_candidate_ranker_fixture_is_bounded_and_self_consistent(self) -> None:
        fixture = json.loads((EXPERIMENT / "candidate-ranker-v0.json").read_text())
        self.assertEqual(fixture["schema"], "iicp.candidate-ranker-parity.v0")
        self.assertEqual(fixture["evidence_schema"], "iicp-candidate-evidence-v0")
        self.assertEqual(fixture["error_code"], "IICP-CANDIDATE-RANKER-REFUSED")
        eligible = set(fixture["eligible_node_ids"])
        self.assertNotIn("node-c-ineligible", eligible)
        self.assertEqual(len(fixture["cases"]), 6)
        for node in fixture["nodes"]:
            digest = hashlib.sha256(f"iicp:candidate:v0\n{node['node_id']}".encode()).hexdigest()
            self.assertEqual(node["candidate_ref"], digest)
        request_digest = hashlib.sha256(
            f"iicp:request:v0\n{fixture['request']['task_id']}".encode()
        ).hexdigest()
        self.assertEqual(fixture["request"]["request_ref"], request_digest)

    def test_candidate_projection_matches_research_schema(self) -> None:
        schema = json.loads((EXPERIMENT / "candidate-evidence-v0.schema.json").read_text())
        sample = json.loads((EXPERIMENT / "sample-candidate-evidence-v0.json").read_text())
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(sample)

    def test_projection_excludes_sensitive_or_dispatch_fields(self) -> None:
        sample = json.loads((EXPERIMENT / "sample-candidate-evidence-v0.json").read_text())
        keys: set[str] = set()

        def visit(value: object) -> None:
            if isinstance(value, dict):
                keys.update(str(key).lower() for key in value)
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(sample)
        self.assertTrue(sample["eligibility"]["filter_complete"])
        self.assertTrue(sample["eligibility"]["ticketed_dispatch_required"])
        self.assertTrue(
            {
                "endpoint",
                "node_id",
                "prompt",
                "response",
                "token",
                "public_key",
                "private_key",
            }.isdisjoint(keys)
        )

    def test_recorded_result_preserves_limitations(self) -> None:
        result = json.loads((EXPERIMENT / "result-draco-20-v0.json").read_text())
        self.assertEqual(result["method"]["rows"], 20)
        self.assertEqual(result["method"]["validation"], "leave-one-out")
        self.assertTrue(result["method"]["candidates_are_assumed_eligible"])
        self.assertGreaterEqual(len(result["limitations"]), 3)
        self.assertGreater(
            result["strategies"]["learned_best"]["mean_quality"],
            result["strategies"]["fixed_best_posthoc"]["mean_quality"],
        )


if __name__ == "__main__":
    unittest.main()
