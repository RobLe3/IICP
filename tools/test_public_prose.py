#!/usr/bin/env python3

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("check_public_prose.py")
SPEC = importlib.util.spec_from_file_location("check_public_prose", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PublicProseTests(unittest.TestCase):
    def findings(self, text):
        return MODULE.lint_text(text, "sample.md")

    def test_leaked_marker_is_objective_error(self):
        findings = self.findings("The result is supported by turn12search4.")
        self.assertEqual([(item.code, item.severity) for item in findings], [("leaked-citation-marker", "error")])

    def test_promotional_claim_is_advisory_not_authorship_claim(self):
        findings = self.findings("This revolutionary protocol changes routing.")
        self.assertEqual(findings[0].code, "promotional-tone")
        self.assertEqual(findings[0].severity, "advisory")

    def test_direct_quote_and_code_fence_are_excluded(self):
        text = '> A source says "revolutionary".\n\n```text\nturn1search2\n```\n'
        self.assertEqual(self.findings(text), [])

    def test_concrete_technical_paragraph_is_not_anchorless(self):
        text = (
            "The IICP Rust directory 0.1.8 verifies the signed snapshot before event replay. "
            "It rejects a missing verification key, reports the failure through the API, and "
            "retains the PHP directory as Genesis authority. The local test uses MySQL 8 and "
            "checks restart behavior, duplicate events, signature failure, stale state and "
            "rollback. These results describe the tested operator preview; they do not authorize "
            "a production cutover or establish independent federation."
        )
        self.assertNotIn("concrete-anchor-missing", [item.code for item in self.findings(text)])

    def test_long_abstract_stock_passage_is_advisory(self):
        text = (
            "This robust and pivotal landscape highlights a vibrant interplay of valuable ideas "
            "that foster an intricate and enduring approach to the future. The broader framework "
            "continues to evolve through meticulous alignment and enhanced collaboration while "
            "showcasing a tapestry of possibilities. Its crucial role underscores the importance "
            "of this work and reflects a commitment to innovation, shared progress, meaningful "
            "development, broad opportunity and a lasting vision for everyone involved."
        )
        codes = [item.code for item in self.findings(text)]
        self.assertIn("concrete-anchor-missing", codes)
        self.assertIn("stock-vocabulary-density", codes)

    def test_duplicate_long_paragraph_is_reported_across_files(self):
        paragraph = " ".join(["Concrete public explanation with a deliberately repeated sentence"] * 8)
        findings = MODULE.duplicate_findings([("a.md", paragraph), ("b.md", paragraph)])
        self.assertEqual(findings[0].code, "duplicate-public-prose")
        self.assertEqual(findings[0].severity, "advisory")


if __name__ == "__main__":
    unittest.main()
