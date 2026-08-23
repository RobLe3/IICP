import unittest

from model import ASSUMPTIONS, SCENARIOS, document, model


class ScalingModelTest(unittest.TestCase):
    def test_scenarios_are_deterministic_and_monotonic(self):
        rows = [model(n, d, share) for n, d, share in SCENARIOS]
        self.assertEqual(rows, [model(n, d, share) for n, d, share in SCENARIOS])
        self.assertEqual(sorted(r.full_state_bytes_per_directory for r in rows), [r.full_state_bytes_per_directory for r in rows])

    def test_summary_is_smaller_than_full_replication_at_research_scales(self):
        for n, d, share in SCENARIOS:
            self.assertLess(model(n, d, share).summary_bytes_per_directory, model(n, d, share).full_state_bytes_per_directory)

    def test_heartbeat_is_local_not_federated_event_traffic(self):
        row = model(100_000, 100, 100_000)
        self.assertEqual(row.local_heartbeats_per_hour, 12_000)
        self.assertEqual(row.global_state_change_events_per_hour, 500)

    def test_assumption_digest_is_stable(self):
        self.assertEqual(document()["assumptions_sha256"], "cf4960820db3f983add4a82b7033ee51de48024d99e3d0413c86cc51b9f12a35")

    def test_invalid_scenario_fails(self):
        for args in [(0, 1, 100_000), (1, 0, 100_000), (1, 2, 100_000), (10, 1, 0)]:
            with self.assertRaises(ValueError):
                model(*args)


if __name__ == "__main__":
    unittest.main()
