# IICP-MCP Binding Specification

**Version**: 0.2.1
**Date**: 2026-08-09
**Status**: draft  
**Issue**: #15 (historical), #35 (current alignment)
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

## 4. Protocol-Era Binding (Phase 2)

An implementation MUST declare the MCP revisions it supports and MUST NOT silently
reinterpret one revision as another. This binding defines two eras:

| Era | MCP revision | Bootstrap and state |
|---|---|---|
| legacy | `2025-11-25` | `initialize` / `initialized`; HTTP adapters retain the negotiated session |
| modern | `2026-07-28` | stateless, self-contained requests; `server/discover` MAY be used before invocation |

Support for either era is optional. Advertising MCP capability without advertising a
supported revision does not authorize tool execution.

### 4.1 Legacy session binding

For IICP-compliant sessions (Phase 2+), an MCP-capable node signals this in INIT:

```json
{
  "sub_protocol": "mcp",
  "sub_protocol_version": "2025-11-25"
}
```

MCP tool calls ride inside `SUB_PROTOCOL` payloads:

```
[Client] → INIT(sub_protocol="mcp") → [Node]
[Client] → SUB_PROTOCOL(payload=<JSON-RPC tools/call>) → [Node]
[Node]   → RESPONSE(payload=<JSON-RPC result>) → [Client]
```

The `SUB_PROTOCOL` payload is a JSON-RPC 2.0 object as defined by the MCP specification.

#### 4.1.1 Legacy Streamable HTTP gateway lifecycle

This subsection applies only when an IICP gateway invokes an MCP server over
legacy Streamable HTTP. It does not redefine native IICP framing.

1. Before the first `tools/call`, the gateway **MUST** send `initialize` with
   `MCP-Protocol-Version: 2025-11-25` and then send the MCP `initialized`
   notification required by the selected MCP server.
2. The gateway **MUST** retain the session identifier returned by a successful
   initialization and **MUST** include it on every later request in that
   session. A missing, malformed, or changed session identifier is a
   fail-closed transport error; it is not an authorization fallback.
3. A gateway **MUST NOT** forward an IICP node token, dispatch ticket, caller
   credential, or tool arguments as a session identifier or downstream MCP
   credential.
4. If a session expires before a call is accepted, the gateway may
   reinitialize once. It may retry the original `tools/call` only when the
   caller has explicitly marked the IICP task payload with
   `mcp_replay_safe: true`. Absent or non-boolean values are false. Otherwise
   it returns a retryable session-expired failure without reissuing the tool
   call.
5. Session identifiers, downstream credentials, and raw tool arguments
   **MUST NOT** appear in IICP receipts, audit records, telemetry, or public
   health responses.

The gateway keeps this session state locally, scoped to the selected MCP
endpoint and negotiated revision. It does not make the session an IICP route
credential and does not change the default MCP revision.

### 4.2 Modern stateless binding

For MCP `2026-07-28`, each request is independently versioned and authorized. An HTTP
adapter MUST validate `MCP-Protocol-Version`, `Mcp-Method`, and, when the method names a
specific object such as a tool, `Mcp-Name`. Header values and the JSON-RPC body MUST agree.
Equivalent metadata carried inside native IICP `SUB_PROTOCOL` messages MUST be represented
in the request `_meta` object.

The request `_meta` MUST identify the negotiated protocol revision and MAY carry client
identity, capabilities, W3C Trace Context, and extension negotiation data defined by MCP.
IICP routing metadata, dispatch tickets, node tokens, provider credentials, and private
policy evidence MUST NOT be copied into `_meta` unless a separately versioned binding
defines a specific, audience-bound field.

The modern era has no implicit MCP connection session. Stateful application workflows MUST
use explicit MCP request state, a modern MCP Task handle, or an application argument. IICP
`task_id` remains the IICP idempotency and receipt correlation identifier; it MUST NOT be
treated as an MCP bearer credential.

### 4.3 Negotiation and downgrade

- Explicit operator or caller configuration wins over automatic negotiation.
- An `auto` client MAY offer modern and legacy support, but MUST select only a revision the
  peer explicitly supports.
- Failure of a modern request MUST NOT trigger an unauthenticated legacy retry.
- A downgrade MUST preserve audience, issuer, resource, consent, tool-risk, and sandbox
  requirements. If that is impossible, the call fails closed.
- Unknown `_meta` members are ignored only where the selected MCP revision permits them;
  malformed reserved members are rejected.

### 4.4 Optional extensions

Tasks, Skills over MCP, and MCP Apps are separate opt-in extensions in the modern era.
IICP discovery MAY report their availability through a versioned capability profile, but
an extension is usable only after both endpoints explicitly negotiate it. Extension
advertisement does not bypass IICP intent-risk, tool-risk, policy, authorization, or
confidentiality gates.

---

## 5. Discovery

An MCP-capable node includes its MCP tool list in the REGISTER `capabilities` array:

```json
{
  "intent": "urn:iicp:intent:mcp:tools/call:v1",
  "mcp_tools": ["bash", "read_file", "web_search"],
  "mcp_version": "2026-07-28",
  "mcp_versions": ["2025-11-25", "2026-07-28"]
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

Adapters MUST distinguish at least unsupported protocol revision, header/body mismatch,
malformed reserved metadata, unsupported extension, authentication failure, authorization
failure, policy refusal, cancellation, and backend failure. A legacy retry MUST not replace
or hide the original modern-era failure.

---

## 7. Authorization and Trust Boundary

MCP authorization and IICP dispatch authorization are separate. Implementations MUST:

- validate OAuth issuer, resource and audience binding for the selected MCP endpoint;
- use protected-resource metadata and PKCE where the selected MCP profile requires them;
- prohibit token passthrough: an IICP token or caller token is never forwarded as the MCP
  server's downstream credential;
- store downstream credentials outside model, tool, IICP task, receipt, and audit payloads;
- retain explicit user/operator consent and the IICP dangerous-tool policy;
- bind any server identity returned in MCP response metadata to the selected endpoint and
  fail on an unexpected identity change;
- use HTTPS for remote MCP HTTP endpoints.

MCP capability or tool annotations are untrusted input unless separately authenticated.
Tool-name risk classification is a conservative baseline, not sufficient authorization.

---

## 8. Phase Mapping

| Feature | Phase |
|---------|-------|
| `urn:iicp:intent:mcp:tools/call:v1` in registry | Phase 1 (reserved) |
| MCP→IICP proxy translation | Phase 2 |
| IICP SUB_PROTOCOL MCP session | Phase 2 |
| MCP 2026-07-28 stateless request binding | Phase 2 draft |
| Tasks / Skills / Apps extension profiles | Phase 3 draft |
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
| 0.1.2 | 2026-06-06 | Added reserved-status note — the MCP intent URN is registry-reserved in Phase 1; directories MUST accept it in capability arrays without implementing translation, MUST NOT reject on it; clients MUST NOT assume tool execution until the Phase-2 binding ships. Header reconciled to 0.1.2 (it trailed the changelog at 0.1.1). |
| 0.2.0 | 2026-07-31 | Added explicit MCP 2025-11-25 legacy and 2026-07-28 modern eras, stateless request metadata, downgrade rules, optional extension negotiation, authorization boundaries, server identity binding, and shared conformance requirements. Remains draft; no SDK default or production behavior changed. |
| 0.2.1 | 2026-08-09 | Clarified the legacy Streamable HTTP gateway lifecycle: initialize and retain the MCP session, fail closed on invalid session state, prohibit credential/session reuse, and constrain expired-session retry to explicitly replay-safe calls. Remains draft; this records an implementation requirement and does not change an SDK default. |

---

## Sign-off

**Protocol Steward**: Binding fills SPEC_ANALYSIS.md GAP-3. SUB_PROTOCOL approach
consistent with ADR-009 pattern. Intent URN format per ADR-007.
Closes GitHub issue #15 (draft). ✓
