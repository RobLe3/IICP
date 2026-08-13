import copy
import json
import unittest

from check_submission_governance_decision import DEFAULT, validate


class SubmissionGovernanceDecisionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads(DEFAULT.read_text(encoding="utf-8"))

    def completed(self) -> dict:
        record = copy.deepcopy(self.record)
        record.update({"status": "maintainer-decision", "decision_present": True, "decided_at": "2026-08-20"})
        record["lead_editor"] = {"public_name": "Lead", "public_contact": "lead@example.invalid", "publication_consent": True}
        record["backup_editor"] = {
            "public_name": "Backup",
            "public_contact": "backup@example.invalid",
            "publication_consent": True,
            "maintenance_consent": True,
        }
        record["change_control"].update({"controller": "Lead", "public_issue_process": "public issues", "errata_process": "public errata"})
        record["contributions"] = {
            "copyright_treatment": "documented treatment",
            "ipr_treatment": "documented IPR process",
            "contributor_consent_record": "public consent record",
        }
        record["succession"].update(
            {
                "temporary_unavailability_process": "backup handles correspondence",
                "permanent_succession_process": "public maintainer decision",
            }
        )
        return record

    def test_blank_template_is_valid(self) -> None:
        self.assertEqual(validate(self.record), [])

    def test_completed_record_is_valid(self) -> None:
        self.assertEqual(validate(self.completed()), [])

    def test_real_backup_is_required(self) -> None:
        record = self.completed()
        record["backup_editor"]["maintenance_consent"] = False
        self.assertTrue(any("maintenance responsibility" in error for error in validate(record)))

    def test_governance_record_cannot_authorize_submission(self) -> None:
        record = self.completed()
        record["submission"]["authorized_now"] = True
        self.assertTrue(any("cannot authorize" in error for error in validate(record)))

    def test_implementation_cannot_become_normative(self) -> None:
        record = self.completed()
        record["change_control"]["implementation_behavior_is_normative"] = True
        self.assertTrue(any("normative authority" in error for error in validate(record)))


if __name__ == "__main__":
    unittest.main()
