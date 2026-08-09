import copy
import json
import unittest
from pathlib import Path

from check_context_event_ownership import DEFAULT_CONTRACT, validate


class ContextEventOwnershipTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(Path(DEFAULT_CONTRACT).read_text(encoding="utf-8"))

    def test_current_contract_is_valid(self) -> None:
        self.assertEqual(validate(self.contract), [])

    def test_duplicate_event_owner_entry_fails(self) -> None:
        candidate = copy.deepcopy(self.contract)
        candidate["events"].append(copy.deepcopy(candidate["events"][0]))
        self.assertTrue(any("unique" in error for error in validate(candidate)))

    def test_service_id_cannot_become_authorization(self) -> None:
        candidate = copy.deepcopy(self.contract)
        candidate["rules"]["service_id_is_authorization"] = True
        self.assertIn("service_id must not be authorization", validate(candidate))

    def test_federated_set_is_closed(self) -> None:
        candidate = copy.deepcopy(self.contract)
        candidate["events"][0]["scope"] = "local"
        errors = validate(candidate)
        self.assertTrue(any("federated event set differs" in error for error in errors))

    def test_local_event_cannot_mutate_replica_state(self) -> None:
        candidate = copy.deepcopy(self.contract)
        local = next(event for event in candidate["events"] if event["scope"] == "local")
        local["replication_action"] = "apply_state"
        self.assertTrue(any("cannot mutate" in error for error in validate(candidate)))


if __name__ == "__main__":
    unittest.main()
