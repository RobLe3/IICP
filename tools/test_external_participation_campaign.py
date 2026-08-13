import copy
import json
import unittest

from check_external_participation_campaign import DEFAULT, validate


class ExternalParticipationCampaignTest(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads(DEFAULT.read_text(encoding="utf-8"))

    def test_repository_campaign_is_valid(self) -> None:
        self.assertEqual(validate(self.record), [])

    def test_missing_lane_fails(self) -> None:
        record = copy.deepcopy(self.record)
        record["lanes"].pop()
        self.assertTrue(any("six unique" in error for error in validate(record)))

    def test_result_or_consent_claim_fails(self) -> None:
        record = copy.deepcopy(self.record)
        record["claim_boundary"]["contains_results"] = True
        self.assertTrue(any("claim boundary" in error for error in validate(record)))

    def test_campaign_cannot_infer_participant_acceptance(self) -> None:
        record = copy.deepcopy(self.record)
        record["lanes"][0]["state"] = "accepted"
        self.assertTrue(any("must not infer" in error for error in validate(record)))

    def test_tracker_must_be_repository_qualified(self) -> None:
        record = copy.deepcopy(self.record)
        record["lanes"][0]["tracker"] = "#31"
        self.assertTrue(any("repository-qualified" in error for error in validate(record)))


if __name__ == "__main__":
    unittest.main()
