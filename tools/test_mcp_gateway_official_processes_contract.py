#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("test_mcp_gateway_official_processes.py")
spec = importlib.util.spec_from_file_location("mcp_gateway_processes", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GatewayProcessContractTests(unittest.TestCase):
    def test_pinned_official_sdk_and_all_gateways(self) -> None:
        self.assertEqual(module.SDK_VERSION, "1.30.0")
        source = SCRIPT.read_text(encoding="utf-8")
        for language in ("python", "typescript", "rust"):
            self.assertIn(f'"{language}"', source)
        self.assertIn("mcp-gateway", source)
        self.assertIn("format_json", source)
        self.assertIn("content_free", source)
        self.assertIn("not independent interoperability", source)


if __name__ == "__main__":
    unittest.main()
