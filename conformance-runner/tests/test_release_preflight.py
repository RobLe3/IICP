from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


class ReleasePreflightContractTest(unittest.TestCase):
    def test_preflight_covers_each_packaging_form_and_offline_profile(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "release_preflight.py"
        spec = importlib.util.spec_from_file_location("release_preflight", script)
        self.assertIsNotNone(spec)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.ARTIFACT_KINDS, ("source", "wheel", "sdist"))
        self.assertEqual(
            module.OFFLINE_COMMANDS,
            (
                "verify-dispatch-ticket-fixture",
                "verify-dispatch-ticket-trust-v2-fixture",
                "verify-dispatch-ticket-trust-v2-semantics-fixture",
                "verify-policy-refusal-fixture",
                "verify-federation-chain-fixture",
            ),
        )


if __name__ == "__main__":
    unittest.main()
