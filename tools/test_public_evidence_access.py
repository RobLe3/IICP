import copy
import json
import unittest

from check_public_evidence_access import DEFAULT_MANIFEST, ROOT, validate


class PublicEvidenceAccessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))

    def test_current_manifest_is_valid(self) -> None:
        self.assertEqual(validate(self.manifest, ROOT), [])

    def test_html_challenge_cannot_be_success(self) -> None:
        candidate = copy.deepcopy(self.manifest)
        candidate["http_contract"]["html_challenge_is_success"] = True
        self.assertTrue(any("HTML challenges" in error for error in validate(candidate, ROOT)))

    def test_source_artifact_requires_existing_fallback(self) -> None:
        candidate = copy.deepcopy(self.manifest)
        candidate["artifacts"][0]["repository_path"] = "missing.json"
        self.assertTrue(any("fallback is missing" in error for error in validate(candidate, ROOT)))

    def test_live_state_cannot_be_inferred_from_static_source(self) -> None:
        candidate = copy.deepcopy(self.manifest)
        live = next(item for item in candidate["artifacts"] if item["class"] == "live-runtime")
        live["fallback_equivalent"] = True
        self.assertTrue(any("cannot claim equivalence" in error for error in validate(candidate, ROOT)))

    def test_sensitive_material_is_forbidden(self) -> None:
        candidate = copy.deepcopy(self.manifest)
        candidate["privacy"]["credentials_allowed"] = True
        self.assertTrue(any("credentials_allowed" in error for error in validate(candidate, ROOT)))


if __name__ == "__main__":
    unittest.main()
