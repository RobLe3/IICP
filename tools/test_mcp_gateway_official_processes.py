#!/usr/bin/env python3
"""Run each official IICP gateway against pinned official MCP SDK 1.30.0."""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from test_mcp_legacy_official_endpoint import SDK_PACKAGE, SDK_VERSION, SERVER_SOURCE, run

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
TOKEN = "gateway-process-fixture-token"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class DirectoryHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("content-length", "0"))
        self.rfile.read(length)
        body = {"node_token": TOKEN} if self.path.endswith("/register") else {}
        encoded = json.dumps(body).encode()
        self.send_response(201 if self.path.endswith("/register") else 200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *_args: object) -> None:
        return


def request_json(url: str, *, body: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    headers = {"accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body, separators=(",", ":")).encode()
        headers["content-type"] = "application/json"
    if token:
        headers["authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def wait_gateway(port: int, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(f"gateway exited before readiness: stdout={stdout[-500:]!r} stderr={stderr[-500:]!r}")
        try:
            status, _ = request_json(f"http://127.0.0.1:{port}/iicp/health")
            if status == 200:
                return
        except (OSError, ValueError):
            pass
        time.sleep(0.1)
    raise RuntimeError("gateway did not become ready")


def gateway_commands() -> dict[str, tuple[list[str], dict[str, str]]]:
    python = WORKSPACE / "iicp-client-python"
    typescript = WORKSPACE / "iicp-client-typescript"
    rust = WORKSPACE / "iicp-client-rust"
    for path in (python, typescript, rust):
        if not path.is_dir():
            raise RuntimeError(f"missing sibling repository: {path.name}")
    run(["npm", "run", "build"], cwd=typescript)
    run(["cargo", "build", "--locked", "--bin", "iicp-node"], cwd=rust)
    python_runtime = python / ".venv/bin/python"
    if not python_runtime.is_file():
        raise RuntimeError("Python SDK .venv is required for the local process harness")
    python_env = os.environ.copy()
    python_env["PYTHONPATH"] = str(python / "src")
    return {
        "rust": ([str(rust / "target/debug/iicp-node")], os.environ.copy()),
        "python": ([str(python_runtime), "-m", "iicp_client.cli"], python_env),
        "typescript": (["node", str(typescript / "dist/cli.js")], os.environ.copy()),
    }


def main() -> int:
    if shutil.which("node") is None or shutil.which("npm") is None or shutil.which("cargo") is None:
        raise SystemExit("node, npm and cargo are required")
    directory = ThreadingHTTPServer(("127.0.0.1", 0), DirectoryHandler)
    directory_thread = threading.Thread(target=directory.serve_forever, daemon=True)
    directory_thread.start()
    server_process: subprocess.Popen[str] | None = None
    gateway: subprocess.Popen[str] | None = None
    outcomes: dict[str, str] = {}
    try:
        with tempfile.TemporaryDirectory(prefix="iicp-mcp-gateway-process-") as temporary:
            workdir = Path(temporary)
            run(["npm", "init", "--yes"], cwd=workdir)
            run(["npm", "install", "--no-save", f"{SDK_PACKAGE}@{SDK_VERSION}", "zod@3.25.76"], cwd=workdir)
            (workdir / "server.mjs").write_text(SERVER_SOURCE, encoding="utf-8")
            server_process = subprocess.Popen(
                ["node", "server.mjs"], cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            assert server_process.stdout is not None
            ready = json.loads(server_process.stdout.readline())
            mcp_port = int(ready["port"])
            directory_port = int(directory.server_address[1])
            for language, (command, environment) in gateway_commands().items():
                gateway_port = free_port()
                args = [
                    *command,
                    "mcp-gateway",
                    "--tools", "format_json",
                    "--node-id", f"gateway-{language}-fixture",
                    "--mcp-url", f"http://127.0.0.1:{mcp_port}",
                    "--directory-url", f"http://127.0.0.1:{directory_port}",
                    "--host", "127.0.0.1",
                    "--port", str(gateway_port),
                    "--public-endpoint", f"http://127.0.0.1:{gateway_port}",
                    "--region", "test",
                ]
                gateway = subprocess.Popen(args, env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                wait_gateway(gateway_port, gateway)
                status, response = request_json(
                    f"http://127.0.0.1:{gateway_port}/v1/task",
                    token=TOKEN,
                    body={
                        "task_id": f"official-{language}-001",
                        "intent": "urn:iicp:intent:mcp:format_json:v1",
                        "payload": {"tool_name": "format_json", "arguments": {"value": "fixture"}},
                    },
                )
                if status != 200 or response.get("status") not in {"completed", "success"}:
                    raise RuntimeError(
                        f"{language} gateway tool call failed: status={status} "
                        f"error={response.get('error', 'unknown')}"
                    )
                serialized = json.dumps(response)
                if "mcp-session" in serialized.lower() or TOKEN in serialized:
                    raise RuntimeError(f"{language} gateway exposed session or directory credentials")
                outcomes[language] = "actual_gateway_initialize_session_tools_call_passed"
                gateway.terminate()
                gateway.wait(timeout=5)
                gateway = None
            print(json.dumps({
                "status": "passed",
                "evidence_class": "project_verified_actual_gateway_processes",
                "official_sdk": {"package": SDK_PACKAGE, "version": SDK_VERSION},
                "revision": "2025-11-25",
                "gateways": outcomes,
                "content_free": True,
                "interpretation": "Local project verification; not independent interoperability or modern-profile support.",
            }, sort_keys=True))
    finally:
        if gateway and gateway.poll() is None:
            gateway.terminate()
        if server_process and server_process.poll() is None:
            server_process.terminate()
        directory.shutdown()
        directory.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
