#!/usr/bin/env python3
"""Tests for the conformance-suite version-truth gate."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).with_name("check_conformance_version_truth.py")
SPEC = importlib.util.spec_from_file_location("check_conformance_version_truth", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ConformanceVersionTruthTest(unittest.TestCase):
    def test_repository_state_is_consistent(self) -> None:
        self.assertEqual(MODULE.check(), [])


if __name__ == "__main__":
    unittest.main()
