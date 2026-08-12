from __future__ import annotations

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "research/strategic/learned-routing-experiment"


class LearnedRoutingExperimentTests(unittest.TestCase):
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
