from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tomllib

from iicp_conformance.runner import (
    bundled_manifest_bytes,
    canonical_json,
    load_manifest,
    run,
    sign_result,
    verify_result,
)


class Handler(BaseHTTPRequestHandler):
    node_id = "fixture-node-id"
    current_token: str | None = None

    def do_GET(self) -> None:
        if self.headers.get("User-Agent") != "iicp-conformance/0.3.0":
            self.reply(403, {})
            return
        if self.path.startswith("/api/v1/discover?"):
            if "min_reputation=2.0" in self.path:
                self.reply(422, {"error": {"code": "validation_error"}})
            else:
                self.reply(200, {"nodes": [{"score": 0.8}], "count": 1})
        elif self.path == "/api/v1/discover":
            self.reply(422, {"error": {"code": "validation_error"}})
        elif self.path.startswith("/api/v1/probe"):
            self.reply(422, {"error": "private_address"})
        elif self.path.startswith("/api/v1/credits/"):
            self.reply(401, {"error": {"code": "unauthorized"}})
        else:
            self.reply(404, {})

    def do_POST(self) -> None:
        if self.headers.get("User-Agent") != "iicp-conformance/0.3.0":
            self.reply(403, {})
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/api/v1/register":
            if "node_id" not in body:
                Handler.current_token = "fixture-stale-token"
            elif (
                body.get("node_id") == Handler.node_id
                and body.get("current_node_token") == Handler.current_token
            ):
                Handler.current_token = "fixture-current-token"
            else:
                self.reply(401, {"error": {"code": "unauthorized"}})
                return
            self.reply(
                201,
                {"node_id": Handler.node_id, "node_token": Handler.current_token},
            )
            return
        if self.path == "/api/v1/heartbeat":
            token = self.headers.get("Authorization", "").removeprefix("Bearer ")
            if body.get("node_id") != Handler.node_id or token != Handler.current_token:
                self.reply(401, {"error": {"code": "unauthorized"}})
            else:
                self.reply(200, {"ok": True, "next_heartbeat_ms": 30000})
            return
        if self.path == "/api/v1/dispatch/ticket":
            if set(body) == {"intent"} and body["intent"] == "urn:iicp:intent:llm:chat:v1":
                self.reply(
                    201,
                    {
                        "ticket": "fixture-ticket",
                        "route": {"endpoint": "https://fixture.invalid"},
                        "data_class": "ticketed_route_dispatch",
                        "route_fields_present": True,
                        "prompt_payload_accepted": False,
                    },
                )
            else:
                self.reply(422, {"error": {"code": "validation_error"}})
            return
        self.reply(401, {"error": {"code": "unauthorized"}})

    def do_DELETE(self) -> None:
        if self.headers.get("User-Agent") != "iicp-conformance/0.3.0":
            self.reply(403, {})
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        token = self.headers.get("Authorization", "").removeprefix("Bearer ")
        if (
            self.path == "/api/v1/register"
            and body.get("node_id") == Handler.node_id
            and token == Handler.current_token
        ):
            Handler.current_token = None
            self.reply(200, {"deregistered": True})
        else:
            self.reply(401, {"error": {"code": "unauthorized"}})

    def reply(self, status: int, value: dict) -> None:
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


class RunnerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_loopback_run_is_content_free_and_passes(self) -> None:
        target = f"http://127.0.0.1:{self.server.server_port}"
        result = run(target)
        self.assertEqual(result["summary"], {"total": 10, "passed": 10, "failed": 0})
        encoded = json.dumps(result)
        self.assertNotIn(target, encoded)
        self.assertNotIn("urn:iicp", encoded)
        self.assertTrue(result["content_free"])

    def test_standalone_package_uses_canonical_apache_metadata(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        package_root = repository_root / "conformance-runner"
        metadata = tomllib.loads((package_root / "pyproject.toml").read_text())
        self.assertEqual(metadata["project"]["license"], "Apache-2.0")
        self.assertEqual(metadata["project"]["license-files"], ["LICENSE"])
        self.assertEqual(
            (package_root / "LICENSE").read_bytes(),
            (repository_root / "LICENSE").read_bytes(),
        )

    def test_mixed_suite_is_rejected(self) -> None:
        manifest = json.loads(bundled_manifest_bytes())
        manifest["suite_version"] = "different"
        with self.assertRaisesRegex(ValueError, "mixed or unsupported"):
            load_manifest(json.dumps(manifest).encode())
        manifest = json.loads(bundled_manifest_bytes())
        manifest["profile"] = "unknown"
        with self.assertRaisesRegex(ValueError, "unsupported conformance profile"):
            load_manifest(json.dumps(manifest).encode())

    def test_dispatch_profile_is_loopback_only_content_free_and_verifiable(self) -> None:
        target = f"http://127.0.0.1:{self.server.server_port}"
        result = run(target, profile="directory-dispatch-v1")
        self.assertEqual(result["profile"], "directory-dispatch-v1")
        self.assertEqual(result["summary"], {"total": 5, "passed": 5, "failed": 0})
        encoded = json.dumps(result)
        self.assertNotIn(target, encoded)
        self.assertNotIn("fixture-ticket", encoded)
        self.assertNotIn("fixture-only", encoded)
        self.assertTrue(verify_result(result)["valid"])
        with self.assertRaisesRegex(ValueError, "restricted to loopback"):
            run("https://directory.example", profile="directory-dispatch-v1")

    def test_lifecycle_profile_rotates_credentials_without_retaining_them(self) -> None:
        Handler.current_token = None
        target = f"http://127.0.0.1:{self.server.server_port}"
        result = run(target, profile="directory-lifecycle-v1")
        self.assertEqual(result["runner_version"], "0.3.0")
        self.assertEqual(result["suite_version"], "4.50.0")
        self.assertEqual(result["summary"], {"total": 6, "passed": 6, "failed": 0})
        encoded = json.dumps(result)
        for prohibited in (
            target,
            Handler.node_id,
            "fixture-stale-token",
            "fixture-current-token",
            "node.example.com",
            "urn:iicp",
        ):
            self.assertNotIn(prohibited, encoded)
        self.assertTrue(verify_result(result)["valid"])
        with self.assertRaisesRegex(ValueError, "restricted to loopback"):
            run("https://directory.example", profile="directory-lifecycle-v1")

    def test_manifest_rejects_unresolved_state_and_invalid_capture(self) -> None:
        manifest = json.loads(bundled_manifest_bytes("directory-lifecycle-v1"))
        manifest["tests"][0]["headers"] = {"Authorization": "Bearer ${missing}"}
        with self.assertRaisesRegex(ValueError, "unresolved state variable"):
            load_manifest(json.dumps(manifest).encode())

        manifest = json.loads(bundled_manifest_bytes("directory-lifecycle-v1"))
        manifest["tests"][0]["capture"] = {"Invalid-Name": "node_token"}
        with self.assertRaisesRegex(ValueError, "invalid capture name"):
            load_manifest(json.dumps(manifest).encode())

        manifest = json.loads(bundled_manifest_bytes("directory-lifecycle-v1"))
        manifest["tests"][0]["capture"] = {"node_token": "node-token"}
        with self.assertRaisesRegex(ValueError, "invalid capture path"):
            load_manifest(json.dumps(manifest).encode())

        manifest = json.loads(bundled_manifest_bytes("directory-lifecycle-v1"))
        manifest["tests"][1]["headers"]["Host"] = "fixture.invalid"
        with self.assertRaisesRegex(ValueError, "unsupported request header"):
            load_manifest(json.dumps(manifest).encode())

        manifest = json.loads(bundled_manifest_bytes("directory-lifecycle-v1"))
        manifest["tests"][2]["capture"] = {"node_id": "node_id"}
        with self.assertRaisesRegex(ValueError, "must not be reused"):
            load_manifest(json.dumps(manifest).encode())

    def test_legacy_public_result_without_profile_still_verifies(self) -> None:
        target = f"http://127.0.0.1:{self.server.server_port}"
        result = run(target)
        result.pop("profile")
        self.assertTrue(verify_result(result)["valid"])
        try:
            import rfc8785  # noqa: F401
        except ImportError:
            return
        signed = sign_result(result, "22" * 32)
        self.assertTrue(verify_result(signed, require_signature=True)["valid"])

    def test_unsigned_result_verifies_and_signature_can_be_required(self) -> None:
        target = f"http://127.0.0.1:{self.server.server_port}"
        result = run(target)
        self.assertTrue(verify_result(result)["valid"])
        required = verify_result(result, require_signature=True)
        self.assertFalse(required["valid"])
        self.assertIn("signature is required", required["errors"])

    def test_tampering_and_prohibited_fields_fail_verification(self) -> None:
        target = f"http://127.0.0.1:{self.server.server_port}"
        result = run(target)
        result["summary"]["passed"] = 9
        result["target_url"] = target
        verification = verify_result(result)
        self.assertFalse(verification["valid"])
        self.assertIn("summary does not match result outcomes", verification["errors"])
        self.assertIn("prohibited fields: target_url", verification["errors"])

    def test_rfc8785_ed25519_signature_round_trip_and_tamper_rejection(self) -> None:
        try:
            import rfc8785  # noqa: F401
        except ImportError:
            self.skipTest("signing extra not installed")
        target = f"http://127.0.0.1:{self.server.server_port}"
        signed = sign_result(run(target), "11" * 32)
        verification = verify_result(signed, require_signature=True)
        self.assertTrue(verification["valid"])
        self.assertTrue(verification["signed"])
        self.assertRegex(verification["signer_key_fingerprint"], r"^sha256:[0-9a-f]{64}$")
        signed["results"][0]["outcome"] = "fail"
        self.assertFalse(verify_result(signed, require_signature=True)["valid"])

    def test_rfc8785_vectors_cover_utf16_order_and_negative_zero(self) -> None:
        try:
            import rfc8785  # noqa: F401
        except ImportError:
            self.skipTest("signing extra not installed")
        self.assertEqual(
            canonical_json({"\ue000": 2, "😀": 1}),
            '{"😀":1,"\ue000":2}'.encode(),
        )
        self.assertEqual(
            canonical_json({"z": -0.0, "a": {"β": "café", "a": None}}),
            '{"a":{"a":null,"β":"café"},"z":0}'.encode(),
        )


if __name__ == "__main__":
    unittest.main()
