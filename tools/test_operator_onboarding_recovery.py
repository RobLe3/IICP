import copy
import json
import unittest

from check_operator_onboarding_recovery import FIXTURE, validate


class OperatorOnboardingRecoveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_reference_fixture_is_valid(self) -> None:
        self.assertEqual(validate(self.fixture), [])

    def test_all_official_sdk_families_are_required(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["packages"].pop()
        self.assertTrue(any("must be covered" in error for error in validate(candidate)))

    def test_install_and_rollback_versions_are_pinned(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["packages"][0]["install"] = "python3 -m pip install iicp-client"
        self.assertTrue(any("not version-pinned" in error for error in validate(candidate)))

    def test_automatic_update_follows_rollback_proof(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["update_policy"]["initial_validation_enabled"] = True
        self.assertTrue(any("initial validation" in error for error in validate(candidate)))

    def test_operator_run_cannot_claim_independent_conformance(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["evidence"]["supports_claims"]["independent_conformance"] = True
        self.assertTrue(any("independent_conformance" in error for error in validate(candidate)))

    def test_package_removal_preserves_shared_operator_state(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["boundaries"]["package_removal_deletes_operator_state"] = True
        self.assertTrue(any("operator state" in error for error in validate(candidate)))


if __name__ == "__main__":
    unittest.main()
