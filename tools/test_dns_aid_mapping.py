import copy
import json
import unittest

from check_dns_aid_mapping import FIXTURE, evaluate, validate


class DnsAidMappingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_reference_fixture_is_valid(self) -> None:
        self.assertEqual(validate(self.fixture), [])

    def test_all_import_vectors_reach_declared_disposition(self) -> None:
        for vector in self.fixture["import_vectors"]:
            self.assertEqual(evaluate(vector), vector["expected"], vector["id"])

    def test_dns_candidate_never_establishes_iicp_authority(self) -> None:
        self.assertFalse(any(self.fixture["boundaries"].values()))

    def test_bogus_dnssec_rejects_even_when_dnssec_not_required(self) -> None:
        vector = copy.deepcopy(self.fixture["import_vectors"][0])
        vector.update({"dnssec": "bogus", "require_dnssec": False})
        self.assertEqual(evaluate(vector), "reject_dnssec_bogus")

    def test_runtime_or_publication_enablement_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["decision"]["runtime_default"] = True
        self.assertTrue(any("offline" in error for error in validate(candidate)))


if __name__ == "__main__":
    unittest.main()

