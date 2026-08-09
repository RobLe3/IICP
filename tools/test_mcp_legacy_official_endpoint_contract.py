#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("test_mcp_legacy_official_endpoint.py")
spec = importlib.util.spec_from_file_location("mcp_legacy_endpoint", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LegacyOfficialMcpEndpointContractTests(unittest.TestCase):
    def test_fixture_is_pinned_to_the_reviewed_legacy_revision(self) -> None:
        self.assertEqual(module.SDK_PACKAGE, "@modelcontextprotocol/sdk")
        self.assertEqual(module.SDK_VERSION, "1.30.0")
        self.assertEqual(module.MCP_REVISION, "2025-11-25")
        self.assertIn("StreamableHTTPServerTransport", module.SERVER_SOURCE)
        self.assertIn("format_json", module.SERVER_SOURCE)

    def test_all_released_gateway_sources_declare_the_legacy_path(self) -> None:
        self.assertEqual(
            module.source_audit(),
            {
                "python": "legacy_gateway_path_declared",
                "typescript": "legacy_gateway_path_declared",
                "rust": "legacy_gateway_path_declared",
            },
        )


if __name__ == "__main__":
    unittest.main()
