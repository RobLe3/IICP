import copy
import json
import unittest

from check_public_measurement_profile import DEFAULT_FIXTURE, validate


class PublicMeasurementProfileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(DEFAULT_FIXTURE.read_text(encoding="utf-8"))

    def test_reference_fixture_is_valid(self) -> None:
        self.assertEqual(validate(self.fixture), [])

    def test_negative_fixture_exposes_independence_diversity_and_accounting_failures(self) -> None:
        path = DEFAULT_FIXTURE.with_name("public-measurement-v1-invalid.json")
        errors = validate(json.loads(path.read_text(encoding="utf-8")))
        self.assertTrue(any("network-wide claim" in error for error in errors))
        self.assertTrue(any("target-controlled" in error for error in errors))
        self.assertTrue(any("failed observation cannot report latency" in error for error in errors))
        self.assertTrue(any("requested_samples" in error for error in errors))

    def test_missing_sample_cannot_be_hidden_in_summary(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["summary"]["requested_samples"] = 2
        self.assertTrue(any("requested_samples" in error for error in validate(candidate)))

    def test_payload_material_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["observations"][0]["payload"] = "private"
        self.assertTrue(any("forbidden public-evidence field" in error for error in validate(candidate)))

    def test_independent_evidence_excludes_target_controlled_vantage(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["vantages"][0]["target_controlled"] = True
        self.assertTrue(any("target-controlled" in error for error in validate(candidate)))

    def test_latency_percentiles_are_recomputed(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["summary"]["latency_ms"]["p95"] = 40
        self.assertTrue(any("latency_ms" in error for error in validate(candidate)))


if __name__ == "__main__":
    unittest.main()

