#!/usr/bin/env python3
"""Exercise MCP 2025-11-25 against a pinned official SDK fixture.

This is a local, project-verified compatibility probe. It starts a temporary
loopback MCP server using the published official TypeScript SDK, initializes a
stateful Streamable HTTP session, invokes one safe tool, and records only
content-free metadata. It neither publishes an artifact nor proves independent
interoperability.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

SDK_PACKAGE = "@modelcontextprotocol/sdk"
SDK_VERSION = "1.30.0"
MCP_REVISION = "2025-11-25"

ROOT = Path(__file__).resolve().parents[1]
CLIENT_GATEWAY_SOURCES = {
    "python": (
        ROOT.parent / "iicp-client-python/src/iicp_client/cli.py",
        ROOT.parent / "iicp-client-python/src/iicp_client/mcp_negotiation.py",
    ),
    "typescript": (
        ROOT.parent / "iicp-client-typescript/src/cli.ts",
        ROOT.parent / "iicp-client-typescript/src/mcp_negotiation.ts",
    ),
    "rust": (
        ROOT.parent / "iicp-client-rust/src/bin/iicp_node.rs",
        ROOT.parent / "iicp-client-rust/src/mcp_negotiation.rs",
    ),
}

SERVER_SOURCE = r'''
import { randomUUID } from 'node:crypto';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { createMcpExpressApp } from '@modelcontextprotocol/sdk/server/express.js';
import { isInitializeRequest } from '@modelcontextprotocol/sdk/types.js';
import * as z from 'zod/v4';

const app = createMcpExpressApp({host: '127.0.0.1'});
const transports = new Map();
function server() {
  const result = new McpServer({name: 'iicp-official-sdk-fixture', version: '1.0.0'});
  result.tool('format_json', {value: z.string()}, async ({value}) => ({
    content: [{type: 'text', text: JSON.stringify({length: value.length})}]
  }));
  return result;
}
app.post('/mcp', async (req, res) => {
  try {
    const sessionId = req.headers['mcp-session-id'];
    let transport = sessionId ? transports.get(sessionId) : undefined;
    if (!transport && !sessionId && isInitializeRequest(req.body)) {
      transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: () => randomUUID(),
        onsessioninitialized: id => transports.set(id, transport),
      });
      transport.onclose = () => { if (transport.sessionId) transports.delete(transport.sessionId); };
      await server().connect(transport);
    }
    if (!transport) {
      res.status(400).json({jsonrpc: '2.0', id: null, error: {code: -32000, message: 'session required'}});
      return;
    }
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    if (!res.headersSent) res.status(500).json({jsonrpc: '2.0', id: null, error: {code: -32603, message: 'fixture error'}});
  }
});
const listener = app.listen(0, '127.0.0.1', () => console.log(JSON.stringify({port: listener.address().port})));
'''


def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)


def post(url: str, body: dict[str, Any], headers: dict[str, str]) -> tuple[dict[str, Any], dict[str, str]]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        raw = response.read().decode("utf-8")
        headers_out = dict(response.headers.items())
        if "text/event-stream" in headers_out.get("Content-Type", headers_out.get("content-type", "")):
            messages = [line.removeprefix("data: ") for line in raw.splitlines() if line.startswith("data: ")]
            if not messages:
                raise RuntimeError("official MCP fixture returned an empty event stream")
            return json.loads(messages[-1]), headers_out
        try:
            return json.loads(raw), headers_out
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"official MCP fixture returned non-JSON: {raw[:200]!r} headers={headers_out!r}") from exc


def source_audit() -> dict[str, str]:
    outcomes: dict[str, str] = {}
    for language, paths in CLIENT_GATEWAY_SOURCES.items():
        if any(not path.is_file() for path in paths):
            raise RuntimeError(f"missing {language} MCP gateway source")
        source = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        if MCP_REVISION not in source or "tools/call" not in source or "mcp-gateway" not in source:
            raise RuntimeError(f"{language} gateway no longer declares the reviewed legacy MCP path")
        outcomes[language] = "legacy_gateway_path_declared"
    return outcomes


def main() -> int:
    if shutil.which("node") is None or shutil.which("npm") is None:
        raise SystemExit("node and npm are required for the official MCP SDK fixture")
    process: subprocess.Popen[str] | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="iicp-mcp-legacy-") as temporary:
            workdir = Path(temporary)
            run(["npm", "init", "--yes"], cwd=workdir)
            run(["npm", "install", "--no-save", f"{SDK_PACKAGE}@{SDK_VERSION}", "zod@3.25.76"], cwd=workdir)
            (workdir / "server.mjs").write_text(SERVER_SOURCE, encoding="utf-8")
            process = subprocess.Popen(
                ["node", "server.mjs"], cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            assert process.stdout is not None
            deadline = time.monotonic() + 10
            ready: dict[str, Any] | None = None
            while time.monotonic() < deadline:
                line = process.stdout.readline()
                if line:
                    ready = json.loads(line)
                    break
                if process.poll() is not None:
                    raise RuntimeError("official MCP fixture exited before readiness")
                time.sleep(0.05)
            if not ready or not isinstance(ready.get("port"), int):
                raise RuntimeError("official MCP fixture did not announce a loopback port")
            url = f"http://127.0.0.1:{ready['port']}/mcp"
            initialize, init_headers = post(
                url,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_REVISION,
                        "capabilities": {},
                        "clientInfo": {"name": "iicp-compatibility-fixture", "version": "1.0.0"},
                    },
                },
                {"MCP-Protocol-Version": MCP_REVISION},
            )
            session = init_headers.get("Mcp-Session-Id") or init_headers.get("mcp-session-id")
            if initialize.get("error") or not session:
                raise RuntimeError("official MCP fixture rejected legacy initialization")
            response, _ = post(
                url,
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "format_json", "arguments": {"value": "fixture"}},
                },
                {"MCP-Protocol-Version": MCP_REVISION, "MCP-Session-Id": session},
            )
            content = response.get("result", {}).get("content")
            if not isinstance(content, list) or not content or content[0].get("type") != "text":
                raise RuntimeError("official MCP fixture did not return a tool content response")
            print(json.dumps({
                "status": "passed",
                "evidence_class": "project_verified_official_sdk_endpoint",
                "official_sdk": {"package": SDK_PACKAGE, "version": SDK_VERSION},
                "revision": MCP_REVISION,
                "operation": "initialize_then_safe_tools_call",
                "iicp_gateway_source_audit": source_audit(),
                "content_free": True,
                "interpretation": "Local compatibility evidence only; not independent interoperability or authorization certification.",
            }, sort_keys=True))
    except (OSError, subprocess.CalledProcessError, RuntimeError, json.JSONDecodeError, urllib.error.URLError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
