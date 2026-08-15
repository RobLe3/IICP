#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "standards/ietf/draft-roble-iicp-peer.md"


class StandardsReviewBundleTest(unittest.TestCase):
    def test_bundle_is_deterministic_and_self_describing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rendered = root / "rendered"
            rendered.mkdir()
            for suffix in ("xml", "txt", "html"):
                (rendered / f"{SOURCE.stem}.{suffix}").write_text(
                    f"test {suffix}\n", encoding="utf-8"
                )
            outputs = [root / "first", root / "second"]
            for output in outputs:
                subprocess.run(
                    [
                        "python3",
                        str(ROOT / "tools/build_standards_review_bundle.py"),
                        "--rendered-dir",
                        str(rendered),
                        "--output-dir",
                        str(output),
                    ],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            name = f"{SOURCE.stem}-review-bundle.zip"
            left = outputs[0] / name
            right = outputs[1] / name
            self.assertEqual(
                hashlib.sha256(left.read_bytes()).digest(),
                hashlib.sha256(right.read_bytes()).digest(),
            )

            prefix = f"{SOURCE.stem}-review-bundle/"
            with zipfile.ZipFile(left) as archive:
                names = set(archive.namelist())
                for required in (
                    "LICENSE",
                    "SECURITY.md",
                    "CONTINUATION.md",
                    "docs/governance/public-artifact-boundary.md",
                    "ecosystem/public-repositories.json",
                    "standards/REVIEWING.md",
                    "standards/ietf/evidence-matrix.md",
                    f"standards/ietf/{SOURCE.name}",
                    f"rendered/{SOURCE.stem}.xml",
                    f"rendered/{SOURCE.stem}.txt",
                    f"rendered/{SOURCE.stem}.html",
                    "SHA256SUMS.json",
                ):
                    self.assertIn(prefix + required, names)
                manifest = json.loads(archive.read(prefix + "SHA256SUMS.json"))
                for relative, expected in manifest["files"].items():
                    actual = hashlib.sha256(archive.read(prefix + relative)).hexdigest()
                    self.assertEqual(expected, actual, relative)


if __name__ == "__main__":
    unittest.main()
