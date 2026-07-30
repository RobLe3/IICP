#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SpecReleaseTest(unittest.TestCase):
    def test_two_clean_archive_builds_are_identical(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for output in (first, second):
                subprocess.run(
                    [
                        "python3",
                        str(ROOT / "tools/build_spec_release.py"),
                        "--output-dir",
                        output,
                    ],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            version = (ROOT / "spec/v1.9/VERSION").read_text().strip()
            left = Path(first) / f"iicp-spec-v{version}.zip"
            right = Path(second) / f"iicp-spec-v{version}.zip"
            self.assertEqual(
                hashlib.sha256(left.read_bytes()).digest(),
                hashlib.sha256(right.read_bytes()).digest(),
            )


if __name__ == "__main__":
    unittest.main()
