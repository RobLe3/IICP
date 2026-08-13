import copy
import json
import unittest
from unittest.mock import patch

from check_public_evidence_access import (
    DEFAULT_MANIFEST,
    ROOT,
    validate,
    validate_live,
)


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

    def test_live_probe_covers_get_and_head(self) -> None:
        result = {
            "status": 200,
            "media_type": "application/json",
            "html_challenge": False,
            "error": None,
        }
        with patch("check_public_evidence_access.probe_url", return_value=result) as probe:
            errors, observations = validate_live(self.manifest, "https://example.test", 1)
        unique_paths = {
            self.manifest["discovery_path"],
            *(item["website_path"] for item in self.manifest["artifacts"] if item.get("website_path")),
        }
        self.assertEqual(errors, [])
        self.assertEqual(len(observations), len(unique_paths) * 2)
        self.assertEqual(probe.call_count, len(observations))

    def test_live_html_challenge_fails_closed(self) -> None:
        result = {
            "status": 200,
            "media_type": "text/html",
            "html_challenge": True,
            "error": None,
        }
        with patch("check_public_evidence_access.probe_url", return_value=result):
            errors, _ = validate_live(self.manifest, "https://example.test", 1)
        self.assertTrue(any("HTML challenge" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
