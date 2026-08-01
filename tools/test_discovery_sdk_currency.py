#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


class DiscoverySdkCurrencyTest(unittest.TestCase):
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
