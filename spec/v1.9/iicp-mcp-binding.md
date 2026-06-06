# IICP-MCP Binding Specification

**Version**: 0.1.2  
**Date**: 2026-06-06  
**Status**: draft  
**Issue**: #15  
**Authority**: Protocol Steward  
**Relation**: SPEC_ANALYSIS.md GAP-3, ADR-007

---

## 1. Purpose

This document specifies how Model Context Protocol (MCP) tool calls map to IICP tasks,
and how IICP inference nodes expose MCP-compatible capability advertisements.

The IICP v1.4.2 spec contains `sub_protocol: "mcp"` in INIT and the `SUB_PROTOCOL`
opcode (0x04) for encapsulated payloads. This document makes that binding concrete.

---

## 2. Two Binding Directions

### 2.1 MCP → IICP (Claude calling an IICP node as an MCP tool)

An MCP client (e.g. Claude Code) invokes an IICP node via a tool call:

```json
{
  "tool": "iicp_task",
  "arguments": {
    "intent": "urn:iicp:intent:llm:chat:v1",
    "messages": [{ "role": "user", "content": "Summarise this paper..." }],
    "qos": "interactive"
  }
}
```

The IICP proxy translates this into a CALL message:

```json
{
  "task_id": "uuid-v4",
  "intent": "urn:iicp:intent:llm:chat:v1",
  "payload": {
    "messages": [{ "role": "user", "content": "Summarise this paper..." }]
  },
  "constraints": { "qos": "interactive", "timeout_ms": 30000 },
  "auth": { "node_token": "..." }
}
```

The proxy returns the RESPONSE result as the MCP tool result.

### 2.2 IICP → MCP (an IICP node exposing MCP tool execution)

A node that executes MCP tool calls advertises:

```json
{
  "intent": "urn:iicp:intent:mcp:tools/call:v1",
  "models": [],
  "max_tokens": 0,
  "mcp_tools": ["bash", "read_file", "web_search"]
}
```

The CALL message payload for this intent:

```json
{
  "tool_name": "bash",
  "arguments": { "command": "ls -la" }
}
```

The RESPONSE payload mirrors the MCP tool result:

```json
{
  "content": [{ "type": "text", "text": "total 48\n..." }],
  "isError": false
}
```

---

## 3. Intent URN Naming for MCP Tools

MCP tool names map to intent URNs under the `mcp` domain (ADR-007):

```
urn:iicp:intent:mcp:<tool_name_slug>:v1
```

Examples:
```
urn:iicp:intent:mcp:tools/call:v1        ← generic MCP tool dispatch
urn:iicp:intent:mcp:bash:v1             ← Bash tool
urn:iicp:intent:mcp:read_file:v1        ← File read tool
urn:iicp:intent:mcp:web_search:v1       ← Web search tool
```

Slashes in tool names are permitted per ADR-007 (action field allows `/`).

---

## 4. SUB_PROTOCOL Session Binding (Phase 2)

For IICP-compliant sessions (Phase 2+), an MCP-capable node signals this in INIT:

```json
{
  "sub_protocol": "mcp",
  "sub_protocol_version": "2025-03-26"
}
```

MCP tool calls ride inside `SUB_PROTOCOL` payloads:

```
[Client] → INIT(sub_protocol="mcp") → [Node]
[Client] → SUB_PROTOCOL(payload=<JSON-RPC tools/call>) → [Node]
[Node]   → RESPONSE(payload=<JSON-RPC result>) → [Client]
```

The `SUB_PROTOCOL` payload is a JSON-RPC 2.0 object as defined by the MCP specification.

---

## 5. Discovery

An MCP-capable node includes its MCP tool list in the REGISTER `capabilities` array:

```json
{
  "intent": "urn:iicp:intent:mcp:tools/call:v1",
  "mcp_tools": ["bash", "read_file", "web_search"],
  "mcp_version": "2025-03-26"
}
```

The directory includes this in NODELIST responses. Clients can filter by intent to find
nodes that support specific MCP tools.

---

## 6. Error Handling

MCP tool errors are wrapped in the IICP RESPONSE error structure:

```json
{
  "status": "error",
  "error": {
    "code": "backend_error",
    "message": "MCP tool execution failed",
    "mcp_error": { "code": -32603, "message": "Internal error" }
  }
}
```

The raw MCP error is preserved in `error.mcp_error` for debugging, but internal
details MUST NOT be exposed to untrusted callers.

---

## 7. Phase Mapping

| Feature | Phase |
|---------|-------|
| `urn:iicp:intent:mcp:tools/call:v1` in registry | Phase 1 (reserved) |
| MCP→IICP proxy translation | Phase 2 |
| IICP SUB_PROTOCOL MCP session | Phase 2 |
| Bidirectional MCP↔IICP node | Phase 3 |
| MCP server discovery via IICP-DIR | Phase 3 |

> **Reserved-status note (v0.1.2).** In Phase 1 the `urn:iicp:intent:mcp:tools/call:v1`
> URN is **registry-reserved only** — no MCP↔IICP translation is active yet (it begins in
> Phase 2). A Phase-1 directory MUST accept the reserved URN appearing in a node's
> `capabilities` array (and index it for discovery per node-capability-format §7) **without**
> implementing any translation, and MUST NOT reject a registration solely because it carries
> the MCP intent. Clients MUST NOT assume an MCP-advertising node performs tool execution
> until the Phase-2 binding ships. This mirrors the node-capability-format §4 MCP Tool
> Execution Capability, which is likewise additive and ignored by non-MCP nodes.

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.0 | 2026-05-14 | Initial draft — MCP tool-call to IICP CALL translation, SUB_PROTOCOL binding, Phase 1 REST form; closes issue #15 |
| 0.1.1 | 2026-05-15 | Added Changelog section (A6 spec cleanup) |
| 0.1.2 | 2026-06-06 | §7: added reserved-status note — the MCP intent URN is registry-reserved in Phase 1; directories MUST accept it in capability arrays without implementing translation, MUST NOT reject on it; clients MUST NOT assume tool execution until the Phase-2 binding ships. Header reconciled to 0.1.2 (it trailed the changelog at 0.1.1). |

---

## Sign-off

**Protocol Steward**: Binding fills SPEC_ANALYSIS.md GAP-3. SUB_PROTOCOL approach
consistent with ADR-009 pattern. Intent URN format per ADR-007.
Closes GitHub issue #15 (draft). ✓
