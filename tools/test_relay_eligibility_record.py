import copy
import json
import unittest

from check_relay_eligibility_record import DEFAULT, validate


class RelayEligibilityRecordTest(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads(DEFAULT.read_text(encoding="utf-8"))

    def completed(self) -> dict:
        record = copy.deepcopy(self.record)
        record.update({"status": "external-result", "result_present": True})
        record["operator"] = {
            "independent_of_iicp": True,
            "report_reference": "https://example.invalid/relay-report",
            "environment_class": "external-two-network-topology",
        }
        record["fixed_inputs"]["implementation_release"] = "example-relay-1.0"
        for case in record["cases"]:
            case["passed"] = True
        record["measurements"] = {
            field: True for field in record["measurements"]
        }
        record["publication"] = {
            "published_by_external_operator": True,
            "evidence_class": "independent",
            "signed_bundle_reference": "https://example.invalid/bundle.json",
        }
        return record

    def test_blank_template_is_valid(self) -> None:
        self.assertEqual(validate(self.record), [])

    def test_completed_record_is_valid(self) -> None:
        self.assertEqual(validate(self.completed()), [])

    def test_negative_case_cannot_be_omitted(self) -> None:
        record = self.completed()
        record["cases"] = record["cases"][:-1]
        self.assertTrue(any("every unique" in error for error in validate(record)))

    def test_failed_measurement_rejects_completed_record(self) -> None:
        record = self.completed()
        record["measurements"]["payload_confidentiality_preserved"] = False
        self.assertTrue(any("payload_confidentiality" in error for error in validate(record)))

    def test_claim_expansion_rejects_record(self) -> None:
        record = self.completed()
        record["claim_boundary"]["authorizes_default_routing"] = True
        self.assertTrue(any("claim_boundary" in error for error in validate(record)))


if __name__ == "__main__":
    unittest.main()
