import copy
import json
import unittest

from check_a2a_execution_binding import FIXTURE, apply_mutation, evaluate, validate


class A2AExecutionBindingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_reference_fixture_and_scenarios(self) -> None:
        self.assertEqual(validate(self.fixture), [])

    def test_each_negative_scenario_fails_for_declared_reason(self) -> None:
        for scenario in self.fixture["scenarios"]:
            candidate = apply_mutation(self.fixture, scenario["mutation"])
            actual = evaluate(candidate, request_streaming=scenario["request_streaming"])
            self.assertEqual(actual, scenario["expected"], scenario["id"])

    def test_unknown_task_state_has_no_projection(self) -> None:
        self.assertNotIn("TASK_STATE_UNSPECIFIED", self.fixture["state_map"])
        self.assertNotIn("TASK_STATE_NEWER_FUTURE_STATE", self.fixture["state_map"])

    def test_ticket_audience_is_not_a2a_credential_audience(self) -> None:
        self.assertNotEqual(
            self.fixture["selected_provider"]["route_ticket_audience"],
            self.fixture["authorization"]["a2a_credential_audience"],
        )

    def test_cancellation_and_partial_execution_are_explicit(self) -> None:
        outcomes = {item["expected"] for item in self.fixture["operation_vectors"]}
        self.assertIn("send_CancelTask", outcomes)
        self.assertIn("local_expired_remote_unknown", outcomes)
        self.assertIn("do_not_automatic_fallback", outcomes)

    def test_error_mapping_distinguishes_pre_and_post_acknowledgement_failure(self) -> None:
        errors = self.fixture["error_map"]
        self.assertEqual(errors["transport_before_acknowledgement"], "candidate_transport_failure")
        self.assertEqual(errors["transport_after_acknowledgement"], "execution_state_unknown_no_automatic_replay")

    def test_missing_extension_fails_closed(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["agent_card"]["capabilities"]["extensions"] = []
        candidate["selected_provider"]["binding"]["agent_card_sha256"] = __import__(
            "check_a2a_execution_binding"
        ).canonical_digest(candidate["agent_card"])
        self.assertEqual(evaluate(candidate), "required_extension_missing")


if __name__ == "__main__":
    unittest.main()
