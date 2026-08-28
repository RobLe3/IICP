#!/usr/bin/env python3
"""Protect the single, always-present Protocol pull-request quality context."""

from __future__ import annotations

import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RequiredCheckContractTest(unittest.TestCase):
    def test_ecosystem_validate_is_the_only_automatic_quality_workflow(self) -> None:
        workflow = (ROOT / ".github/workflows/ecosystem.yml").read_text()
        self.assertIn("  pull_request:\n", workflow)
        self.assertNotIn("  push:\n", workflow)
        self.assertIn("  validate:\n", workflow)
        self.assertIn("tools/run_profile_fixture_contract.sh", workflow)
        self.assertIn("tools/generate_implementations.py --check", workflow)

    def test_profile_fixture_workflow_is_manual_diagnostic_only(self) -> None:
        workflow = (ROOT / ".github/workflows/profile-fixtures.yml").read_text()
        self.assertIn("  workflow_dispatch:\n", workflow)
        self.assertNotIn("  pull_request:\n", workflow)
        self.assertNotIn("  push:\n", workflow)
        self.assertIn("fixture-contract-diagnostic", workflow)

    def test_shared_gate_is_executable_and_contains_closure_checks(self) -> None:
        gate = ROOT / "tools/run_profile_fixture_contract.sh"
        self.assertTrue(os.access(gate, os.X_OK))
        text = gate.read_text()
        self.assertIn("set -euo pipefail", text)
        self.assertIn("tools/manage_release_closure.py --check", text)
        self.assertIn("test_directory_state_semantics.py", text)
        self.assertIn("test_compatibility_environment.py", text)


if __name__ == "__main__":
    unittest.main()
