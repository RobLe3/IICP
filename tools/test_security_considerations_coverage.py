import copy
import json
import unittest

from check_security_considerations_coverage import MATRIX, validate


class SecurityConsiderationsCoverageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_reference_matrix_is_valid(self) -> None:
        self.assertEqual(validate(self.matrix), [])

    def test_missing_security_topic_fails(self) -> None:
        candidate = copy.deepcopy(self.matrix)
        candidate["topics"].pop()
        self.assertTrue(any("topic coverage" in error for error in validate(candidate)))

    def test_independent_evidence_profiles_cannot_be_promoted(self) -> None:
        for issue in ("55", "56", "58"):
            candidate = copy.deepcopy(self.matrix)
            candidate["profile_dispositions"][issue] = "normative"
            self.assertTrue(any(f"#{issue}" in error for error in validate(candidate)))

    def test_research_cannot_authorize_submission_or_promotion(self) -> None:
        for field in ("submission_authorized", "profile_promotion_authorized"):
            candidate = copy.deepcopy(self.matrix)
            candidate[field] = True
            self.assertTrue(any("cannot" in error for error in validate(candidate)))

    def test_execution_privacy_retains_hardware_gate(self) -> None:
        candidate = copy.deepcopy(self.matrix)
        candidate["profile_dispositions"]["136"] = "complete"
        self.assertTrue(any("hardware gate" in error for error in validate(candidate)))


if __name__ == "__main__":
    unittest.main()
