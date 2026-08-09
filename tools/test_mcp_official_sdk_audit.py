#!/usr/bin/env python3
from __future__ import annotations

import unittest

from audit_mcp_official_sdk import IICP_LEGACY, IICP_MODERN, report, supported_versions


class OfficialMcpSdkAuditTests(unittest.TestCase):
    def test_extracts_declared_versions(self) -> None:
        source = "export const LATEST_PROTOCOL_VERSION = '2025-11-25'; export const SUPPORTED_PROTOCOL_VERSIONS = [LATEST_PROTOCOL_VERSION, '2025-06-18', '2025-03-26'];"
        self.assertEqual(supported_versions(source), ["2025-11-25", "2025-06-18", "2025-03-26"])

    def test_report_labels_only_observed_sdk_support(self) -> None:
        result = report("example", "1.0.0", [IICP_LEGACY])
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["iicp_revision_support"][IICP_LEGACY], "supported")
        self.assertEqual(result["iicp_revision_support"][IICP_MODERN], "not_supported_by_sdk")
        self.assertIn("does not prove endpoint interoperability", result["interpretation"])


if __name__ == "__main__":
    unittest.main()
