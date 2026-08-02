from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from iicp_conformance.runner import bundled_manifest_bytes, load_manifest, run


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.headers.get("User-Agent") != "iicp-conformance/0.1.0":
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
        if self.headers.get("User-Agent") != "iicp-conformance/0.1.0":
            self.reply(403, {})
            return
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

    def test_mixed_suite_is_rejected(self) -> None:
        manifest = json.loads(bundled_manifest_bytes())
        manifest["suite_version"] = "different"
        with self.assertRaisesRegex(ValueError, "mixed or unsupported"):
            load_manifest(json.dumps(manifest).encode())


if __name__ == "__main__":
    unittest.main()
