from __future__ import annotations
import unittest
from audit_intent_sources import classify

class IntentSourceAuditTest(unittest.TestCase):
    def test_empty_namespace_segment_is_not_a_candidate(self) -> None:
        classification, _ = classify("urn:iicp:intent::chat:v1", set())
        self.assertEqual("negative-test", classification)

    def test_implementation_namespace_remains_a_candidate(self) -> None:
        classification, _ = classify("urn:iicp:intent:vendor:chat:v1", set())
        self.assertEqual("candidate-unregistered", classification)

if __name__ == "__main__":
    unittest.main()
