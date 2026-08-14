from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/architecture/task-time-semantics-v1.json"
CORE = ROOT / "spec/v1.9/iicp-core.md"
LIFECYCLE = ROOT / "spec/v1.9/iicp-service-lifecycle-profile.md"
PATTERN = re.compile(r"\b(timeout_ms|timeout|deadline|TTL|ttl|expiry|expires|lifetime)\b")


class TaskTimeSemanticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text())
        cls.core = CORE.read_text()
        cls.lifecycle = LIFECYCLE.read_text()
        cls.scenarios = {case["name"]: case["expected"] for case in cls.contract["scenarios"]}

    def test_five_axes_are_distinct(self) -> None:
        self.assertEqual(
            {"execution_timeout", "delivery_lifetime", "task_deadline", "result_validity", "caller_wait_timeout"},
            set(self.contract["axes"]),
        )
        self.assertIsNone(self.contract["axes"]["delivery_lifetime"]["current_mapping"])
        self.assertIsNone(self.contract["axes"]["task_deadline"]["current_mapping"])

    def test_current_timeout_mapping_is_compatible(self) -> None:
        execution = self.contract["axes"]["execution_timeout"]
        self.assertEqual("provider_receipt", execution["origin"])
        self.assertIn("provider attempt budget", self.core)
        self.assertIn("provider attempt budget", self.lifecycle)

    def test_local_wait_does_not_confirm_cancellation(self) -> None:
        expected = self.scenarios["caller_wait_expires_without_cancel_ack"]
        self.assertEqual("unknown", expected["provider_state"])
        self.assertFalse(expected["confirmed_cancelled"])
        self.assertIn("does not confirm cancellation", self.lifecycle)

    def test_retry_preserves_logical_task(self) -> None:
        expected = self.scenarios["retry_after_ambiguous_disconnect"]
        self.assertEqual("same", expected["task_id"])
        self.assertEqual("same", expected["idempotency_key"])
        self.assertEqual("new", expected["call_id"])

    def test_native_ttl_is_not_logical_deadline(self) -> None:
        ttl = self.contract["native_ttl_key_22"]
        self.assertFalse(ttl["logical_task_deadline"])
        self.assertFalse(ttl["general_delivery_lifetime"])

    def test_inventory_counts_are_current(self) -> None:
        for record in self.contract["source_inventory"]:
            text = (ROOT / record["path"]).read_text()
            self.assertEqual(record["matches"], len(PATTERN.findall(text)), record["path"])

    def test_no_phase_8_or_storage_claim(self) -> None:
        claims = set(self.contract["explicit_non_claims"])
        self.assertIn("no_dtn_or_bpv7_support", claims)
        self.assertIn("no_persistent_queue", claims)
        self.assertFalse(self.contract["wire_change"])


if __name__ == "__main__":
    unittest.main()
