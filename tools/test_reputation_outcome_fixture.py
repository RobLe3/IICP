import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/reputation-outcome-v2.json"
MANIFEST = ROOT / "research/pre-normative-profiles/fixtures/profile-fixture-manifest-v0.json"


class ReputationOutcomeFixtureTest(unittest.TestCase):
    def test_manifest_digest_and_version(self):
        raw = FIXTURE.read_bytes()
        fixture = json.loads(raw)
        manifest = json.loads(MANIFEST.read_text())
        entry = next(x for x in manifest["fixtures"] if x["path"] == FIXTURE.name)
        self.assertEqual(entry["fixture_version"], fixture["fixture_version"])
        self.assertEqual(entry["sha256"], hashlib.sha256(raw).hexdigest())

    def test_required_regressions_are_present(self):
        fixture = json.loads(FIXTURE.read_text())
        cases = {case["name"]: case for case in fixture["cases"]}
        self.assertEqual(fixture["reputation_model"], "outcome-v2")
        self.assertEqual(cases["successful_slow_unknown_qos"]["expected"]["score"], 0.51)
        self.assertEqual(cases["failed"]["expected"]["score"], 0.45)
        self.assertEqual(cases["duplicate_batch"]["expected"]["applied_batches"], 1)
        self.assertFalse(cases["legacy_missing_model"]["expected"]["may_label_outcome_v2"])
        self.assertEqual(cases["cutover_epoch"]["expected"]["new_score"], 0.5)


if __name__ == "__main__":
    unittest.main()
