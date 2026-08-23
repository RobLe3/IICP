from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from check_public_artifact_closure import validate


ROOT = Path(__file__).resolve().parents[1]


class PublicArtifactClosureTest(unittest.TestCase):
    def make_root(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "spec/v1.9").mkdir(parents=True)
        (root / "spec/v1.9/release-integrity-manifest.json").write_text(
            json.dumps({"files": {"doc.md": "unused"}}), encoding="utf-8"
        )
        return root

    def test_public_relative_and_external_links_pass(self) -> None:
        root = self.make_root()
        (root / "target.md").write_text("public\n", encoding="utf-8")
        (root / "doc.md").write_text(
            "[local](target.md) [RFC](https://www.rfc-editor.org/rfc/rfc8126.html)\n",
            encoding="utf-8",
        )
        self.assertEqual(validate(root, {"doc.md"}), [])

    def test_private_repository_is_rejected(self) -> None:
        root = self.make_root()
        (root / "doc.md").write_text(
            "See https://github.com/RobLe3/unavailable-component/issues/1\n", encoding="utf-8"
        )
        self.assertIn("unavailable repository", validate(root, {"doc.md"})[0].message)

    def test_internal_and_workstation_paths_are_rejected(self) -> None:
        root = self.make_root()
        (root / "doc.md").write_text(
            "Use `project/SECRET.md` from /Users/alice/work/iicp.\n", encoding="utf-8"
        )
        messages = [finding.message for finding in validate(root, {"doc.md"})]
        self.assertTrue(any("internal project path" in message for message in messages))
        self.assertTrue(any("workstation-local" in message for message in messages))

    def test_unresolved_local_link_is_rejected(self) -> None:
        root = self.make_root()
        (root / "doc.md").write_text("[missing](missing.md)\n", encoding="utf-8")
        self.assertIn("unresolved local link", validate(root, {"doc.md"})[0].message)

    def test_published_negative_path_vector_is_explicitly_exempt(self) -> None:
        root = self.make_root()
        relative = "fixtures/directory-implementation-metadata-v1.json"
        (root / "fixtures").mkdir()
        (root / relative).write_text(
            '{"implementation_name":"/Users/operator/private-build"}\n',
            encoding="utf-8",
        )
        self.assertEqual([], validate(root, {relative}))

    def test_research_index_rejects_private_method_marker(self) -> None:
        root = self.make_root()
        (root / "research").mkdir()
        (root / "research/RESEARCH.md").write_text("Maintained by FORGE\n", encoding="utf-8")
        self.assertIn(
            "private development-method provenance",
            validate(root, {"research/RESEARCH.md"})[0].message,
        )

    def test_all_public_option_cannot_be_combined_with_paths(self) -> None:
        result = subprocess.run(
            [
                "python3",
                str(ROOT / "tools/check_public_artifact_closure.py"),
                "--all-public",
                "README.md",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("mutually exclusive", result.stderr)


if __name__ == "__main__":
    unittest.main()
