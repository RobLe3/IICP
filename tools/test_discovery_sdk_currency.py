#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class DiscoverySdkCurrencyTest(unittest.TestCase):
    def test_language_specific_patch_keeps_common_baseline(self) -> None:
        from tools.check_discovery_sdk_currency import coordinated_baseline

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ecosystem").mkdir()
            (root / "ecosystem/releases.json").write_text(json.dumps({"releases": [
                {"id": "client-python", "version": "0.7.102"},
                {"id": "client-typescript", "version": "0.7.102"},
                {"id": "client-rust", "version": "0.7.103"},
            ]}))
            self.assertEqual(coordinated_baseline(root), "0.7.102")

    def test_current_catalog_and_fixture_agree(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["python3", str(root / "tools/check_discovery_sdk_currency.py")],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
