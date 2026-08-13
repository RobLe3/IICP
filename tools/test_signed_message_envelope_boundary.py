import copy
import json
import unittest

from check_signed_message_envelope_boundary import FIXTURE, validate


class SignedMessageEnvelopeBoundaryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_reference_decision_is_valid(self) -> None:
        self.assertEqual(validate(self.fixture), [])

    def test_research_cannot_enable_a_universal_envelope(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["universal_envelope"] = "required"
        self.assertTrue(any("universal envelope" in error for error in validate(candidate)))

    def test_identity_signature_cannot_grant_task_authority(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["forbidden_claims"]["identity_signature_grants_task_authority"] = True
        self.assertTrue(any("forbidden" in error for error in validate(candidate)))

    def test_future_profile_requires_independent_implementations(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["required_future_profile_properties"].remove("two_independent_implementations")
        self.assertTrue(any("admission" in error for error in validate(candidate)))

    def test_decision_cannot_change_wire_or_deploy(self) -> None:
        for field in ("wire_change", "authentication_default_change", "deployment_authorized"):
            candidate = copy.deepcopy(self.fixture)
            candidate[field] = True
            self.assertTrue(any(field in error for error in validate(candidate)))


if __name__ == "__main__":
    unittest.main()
