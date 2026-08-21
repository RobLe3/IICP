import copy
import json
import unittest
from check_ecosystem_version_truth import SAMPLES, validate

class EcosystemVersionTruthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.release_ahead = json.loads((SAMPLES / "ecosystem-version-truth-release-ahead.json").read_text(encoding="utf-8"))

    def test_all_reference_fixtures_are_valid(self) -> None:
        for path in sorted(SAMPLES.glob("ecosystem-version-truth-*.json")):
            with self.subTest(path=path.name):
                self.assertEqual(validate(json.loads(path.read_text(encoding="utf-8"))), [])

    def test_unavailable_axis_cannot_copy_published_version(self) -> None:
        candidate = copy.deepcopy(self.release_ahead)
        candidate["deployed_release"].update(status="unavailable", observed_at=None, evidence=None)
        self.assertTrue(any("unavailable observations must have null data" in error for error in validate(candidate)))

    def test_adoption_counts_must_match_sample(self) -> None:
        candidate = copy.deepcopy(self.release_ahead)
        candidate["observed_adoption"]["data"]["sample_size"] = 5
        self.assertTrue(any("group counts must equal sample_size" in error for error in validate(candidate)))

    def test_stale_status_requires_limitation(self) -> None:
        candidate = copy.deepcopy(self.release_ahead)
        candidate["deployed_release"]["status"] = "stale"
        candidate["deployed_release"]["limitations"] = []
        self.assertTrue(any("stale observations require a limitation" in error for error in validate(candidate)))

    def test_private_topology_fields_are_not_part_of_contract(self) -> None:
        candidate = copy.deepcopy(self.release_ahead)
        candidate["deployed_release"]["data"]["node_ids"] = ["private-node"]
        self.assertTrue(validate(candidate))

if __name__ == "__main__":
    unittest.main()
