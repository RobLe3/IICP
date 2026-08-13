import copy
import json
import unittest

from check_newcomer_validation_record import DEFAULT, validate


class NewcomerValidationRecordTest(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads(DEFAULT.read_text(encoding="utf-8"))

    def completed(self) -> dict:
        record = copy.deepcopy(self.record)
        record.update(
            {
                "status": "participant-result",
                "result_present": True,
                "consent_confirmed": True,
                "participant_role": "node_operator",
                "failure_scenario": "live_not_ready",
                "first_blocking_step_code": "RECOVERY_ACTION_NOT_FOUND",
                "hint_count": 1,
                "retained_note": "The recovery action was not visible near health output.",
                "participant_reviewed_summary": True,
            }
        )
        record["observation"].update(
            {
                "observed_at_utc": "2026-08-13T00:00:00Z",
                "device_class": "laptop",
                "input_methods": ["keyboard"],
            }
        )
        record["outcomes"] = {
            "first_minute_comprehension": "pass",
            "quickest_path": "hint",
            "keyboard_navigation": "pass",
            "failure_recovery": "hint",
        }
        return record

    def test_blank_template_is_valid_but_not_a_result(self) -> None:
        self.assertEqual(validate(self.record), [])
        self.assertFalse(self.record["result_present"])

    def test_completed_content_free_record_is_valid(self) -> None:
        self.assertEqual(validate(self.completed()), [])

    def test_completed_record_requires_consent(self) -> None:
        record = self.completed()
        record["consent_confirmed"] = False
        self.assertTrue(any("consent" in error for error in validate(record)))

    def test_full_transcript_is_forbidden(self) -> None:
        record = self.completed()
        record["privacy"]["full_transcript"] = True
        self.assertTrue(any("forbidden data" in error for error in validate(record)))

    def test_self_review_cannot_become_independent_evidence(self) -> None:
        record = self.completed()
        record["claim_boundary"]["independent_conformance"] = True
        self.assertTrue(any("independence" in error for error in validate(record)))


if __name__ == "__main__":
    unittest.main()

