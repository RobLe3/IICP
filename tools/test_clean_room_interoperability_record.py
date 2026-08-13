import copy
import json
import unittest

from check_clean_room_interoperability_record import DEFAULT, validate


class CleanRoomRecordTest(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads(DEFAULT.read_text(encoding="utf-8"))

    def completed(self) -> dict:
        record = copy.deepcopy(self.record)
        record.update({"status": "external-result", "result_present": True})
        record["implementation"] = {
            "repository": "https://example.invalid/directory",
            "commit": "0123456789abcdef",
            "license": "Apache-2.0",
            "language_runtime": "example 1.0",
            "authors_independent_of_iicp": True,
            "operator_independent_of_iicp": True,
        }
        record["fixed_inputs"]["protocol_archive_sha256"] = "a" * 64
        record["fixed_inputs"]["openapi_sha256"] = "b" * 64
        for profile in record["profiles"]:
            profile.update({"positive_pass": True, "negative_pass": True, "signed_bundle_reference": "bundle.json"})
        record["compatibility_matrix"] = [
            {"case_type": "positive", "case_id": "accepted", "result": "pass"},
            {"case_type": "negative", "case_id": "refused", "result": "pass"},
        ]
        record["publication"] = {
            "published_by_external_implementer": True,
            "report_reference": "https://example.invalid/report",
            "evidence_class": "independent",
        }
        return record

    def test_blank_template_is_valid(self) -> None:
        self.assertEqual(validate(self.record), [])

    def test_completed_record_is_valid(self) -> None:
        self.assertEqual(validate(self.completed()), [])

    def test_reference_source_use_breaks_independence_boundary(self) -> None:
        record = self.completed()
        record["source_boundary"]["maintained_directory_source_consulted"] = True
        self.assertTrue(any("source_boundary" in error for error in validate(record)))

    def test_negative_cases_are_required(self) -> None:
        record = self.completed()
        record["profiles"][0]["negative_pass"] = False
        self.assertTrue(any("positive and negative" in error for error in validate(record)))

    def test_result_cannot_promote_a_profile(self) -> None:
        record = self.completed()
        record["claim_boundary"]["promotes_a_profile"] = True
        self.assertTrue(any("claim_boundary" in error for error in validate(record)))


if __name__ == "__main__":
    unittest.main()
