from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/http-task-resource-boundary-v1.json"


class HttpTaskResourceBoundaryFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(FIXTURE.read_text())
        cls.vectors = {vector["id"]: vector for vector in cls.data["vectors"]}

    def test_finite_symmetric_limit(self) -> None:
        self.assertEqual(self.data["max_encoded_request_bytes"], 1_048_576)
        self.assertEqual(self.data["max_encoded_response_bytes"], 1_048_576)
        self.assertEqual(self.data["supported_content_encodings"], ["identity"])

    def test_required_boundary_vectors_are_present(self) -> None:
        required = {
            "request_exact_limit",
            "request_limit_plus_one",
            "declared_request_over_limit",
            "conflicting_content_length",
            "chunked_exact_limit",
            "chunked_limit_plus_one",
            "unsupported_request_encoding",
            "malformed_json",
            "disconnect_before_declared_length",
            "response_exact_limit",
            "response_limit_plus_one",
            "generated_response_over_limit",
        }
        self.assertEqual(set(self.vectors), required)

    def test_oversize_is_non_retryable_and_cannot_fallback(self) -> None:
        for vector_id in ("request_limit_plus_one", "response_limit_plus_one"):
            vector = self.vectors[vector_id]
            self.assertFalse(vector["retryable"])
            self.assertFalse(vector["fallback"])

    def test_spec_registers_fixture_and_errors(self) -> None:
        spec = (ROOT / "spec/v1.9/iicp-core.md").read_text()
        self.assertIn("fixtures/http-task-resource-boundary-v1.json", spec)
        for code in (
            "invalid_http_body",
            "request_too_large",
            "unsupported_content_encoding",
            "response_too_large",
        ):
            self.assertIn(f"`{code}`", spec)


if __name__ == "__main__":
    unittest.main()
