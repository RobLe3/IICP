import copy
import json
import unittest

from check_identity_evidence_layering import FIXTURE, validate


class IdentityEvidenceLayeringTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_reference_fixture_is_valid(self) -> None:
        self.assertEqual(validate(self.fixture), [])

    def test_vc_cannot_become_task_authority(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        layer = next(
            item for item in candidate["layers"] if item["id"] == "portable_provenance"
        )
        layer["authority"] = True
        self.assertTrue(
            any("portable_provenance" in error for error in validate(candidate))
        )

    def test_spiffe_cannot_replace_dispatch_ticket(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        layer = next(
            item for item in candidate["layers"] if item["id"] == "task_authority"
        )
        layer["mechanism"] = "spiffe_x509_svid"
        self.assertTrue(
            any("dispatch ticket" in error for error in validate(candidate))
        )

    def test_hardware_identity_stays_out_of_directory(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        layer = next(
            item for item in candidate["layers"] if item["id"] == "execution_evidence"
        )
        layer["stable_public"] = True
        self.assertTrue(any("directory data" in error for error in validate(candidate)))

    def test_research_cannot_change_wire_or_trust_root(self) -> None:
        for field in ("wire_change", "trust_root_change"):
            candidate = copy.deepcopy(self.fixture)
            candidate[field] = True
            self.assertTrue(
                any("wire or trust" in error for error in validate(candidate))
            )


if __name__ == "__main__":
    unittest.main()
