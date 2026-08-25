import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manage_release_closure as closure


class ReleaseClosureTests(unittest.TestCase):
    def test_artifact_entries_finds_nested_digest_records(self):
        value = {"a": [{"reference": "x", "sha256": "old"}], "b": {"ignored": True}}
        self.assertEqual(list(closure.artifact_entries(value)), [value["a"][0]])

    def test_sync_campaign_replaces_only_rust_fixed_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ecosystem").mkdir()
            (root / "evidence").mkdir()
            (root / "ecosystem/current-versions.json").write_text(json.dumps({
                "components": {"client-rust": {"release": "0.7.108"}}
            }))
            campaign = {"lanes": [{"id": "linux-systemd-operator", "fixed_inputs": [
                "iicp-client-rust 0.7.107", "opt-in native watchdog"
            ]}]}
            (root / "evidence/external-participation-campaign-v1.json").write_text(json.dumps(campaign))
            closure.sync_campaign(root)
            updated = json.loads((root / "evidence/external-participation-campaign-v1.json").read_text())
            self.assertEqual(updated["lanes"][0]["fixed_inputs"], [
                "iicp-client-rust 0.7.108", "opt-in native watchdog"
            ])

    def test_repository_promotion_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ecosystem").mkdir()
            (root / "ecosystem/releases.json").write_text(json.dumps({
                "releases": [{"id": "client-rust", "version": "0.7.108"}]
            }))
            path = root / "ecosystem/repositories.json"
            path.write_text(json.dumps({
                "repositories": [{"id": "client-rust", "release": "0.7.107"}]
            }))

            # Ordinary closure refreshes must not turn a prepared release into
            # a published release. Promotion is a separate, explicit step.
            self.assertEqual(json.loads(path.read_text())["repositories"][0]["release"], "0.7.107")
            closure.sync_repository_versions(root)
            self.assertEqual(json.loads(path.read_text())["repositories"][0]["release"], "0.7.108")

    def test_compatibility_catalog_follows_suite_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "spec/v1.9").mkdir(parents=True)
            (root / "evidence").mkdir()
            (root / "artifact.json").write_text("candidate\n")
            (root / "spec/v1.9/VERSION").write_text("9.8.7\n")
            path = root / "evidence/compatibility-environment-v9.8.7.json"
            path.write_text(json.dumps({
                "artifact": {"reference": "artifact.json", "sha256": "stale"}
            }))

            closure.sync_compatibility_catalog(root)

            updated = json.loads(path.read_text())
            self.assertEqual(
                updated["artifact"]["sha256"],
                closure.sha256(root / "artifact.json"),
            )

    def test_check_reports_every_failure_without_fail_fast(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "first.py").write_text("raise SystemExit('first failure')\n")
            (root / "second.py").write_text("raise SystemExit('second failure')\n")
            previous = closure.CHECKS
            closure.CHECKS = (("first", "first.py"), ("second", "second.py"))
            try:
                results = closure.check(root)
            finally:
                closure.CHECKS = previous
            self.assertEqual([result["status"] for result in results], ["fail", "fail"])
            self.assertIn("first failure", results[0]["output"])
            self.assertIn("second failure", results[1]["output"])


if __name__ == "__main__":
    unittest.main()
