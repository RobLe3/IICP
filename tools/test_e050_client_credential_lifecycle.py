import copy
import json
import unittest

from check_e050_client_credential_lifecycle import FIXTURE, validate


class E050ClientCredentialLifecycleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_is_valid(self) -> None:
        self.assertEqual(validate(self.fixture), [])

    def test_missing_replay_case_fails(self) -> None:
        changed = copy.deepcopy(self.fixture)
        changed["scenarios"] = [
            item for item in changed["scenarios"] if item["id"] != "stale-token-replay"
        ]
        self.assertTrue(validate(changed))

    def test_rejection_cannot_commit_route(self) -> None:
        changed = copy.deepcopy(self.fixture)
        replay = next(item for item in changed["scenarios"] if item["id"] == "stale-token-replay")
        replay["expected_endpoint_committed"] = True
        self.assertTrue(any("route commit" in error for error in validate(changed)))

    def test_fixture_cannot_authorize_activation(self) -> None:
        changed = copy.deepcopy(self.fixture)
        changed["production_activation_authorized"] = True
        self.assertTrue(any("production activation" in error for error in validate(changed)))


if __name__ == "__main__":
    unittest.main()
