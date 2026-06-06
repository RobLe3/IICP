# WASM — Client Adapter Feasibility Study (WASM-1 to WASM-4)

**Issue**: #292 (ADOPTION: WASM client adapter — browser-installable IICP mesh client)
**Date**: 2026-05-24
**Author**: RESA loop, FORGE iter963

---

## WASM-1: Rust → WASM Compilation Feasibility

**Question**: Can the proxy codebase compile to WASM?

**Assessment**: The Python proxy (`proxy/`) cannot compile to WASM directly — Python is
not a WASM compilation target. The Rust `iicp-node` is a WASM candidate but its current
design (tokio async runtime, reqwest HTTP client, file system access) does not compile
to the `wasm32-unknown-unknown` target without significant refactoring:

- `tokio` → needs `wasm-bindgen-futures` and browser-compatible async executor
- `reqwest` → needs `fetch` API wrapper (different WASM-specific client)
- File system ops → not available in WASM sandbox
- Port binding → not applicable (WASM client is consumer-only, no server socket)

**Verdict**: A full Rust → WASM compilation of the existing proxy is NOT FEASIBLE without
a significant rewrite. The recommended approach is a TypeScript re-implementation of the
**consumer-only** subset of the IICP protocol (no provider/adapter functionality).

**TypeScript alternative assessment**:
- IICP consumer protocol: `GET /v1/discover`, `POST /v1/call` (task dispatch)
- CIP consumer mode: `compute_cip_envelope` → dispatch → aggregate
- Total scope: ~500 lines of TypeScript
- Bundle size: ~80–120KB gzipped (no heavy dependencies needed — fetch API native in browsers)
- Browser compatibility: All modern browsers (fetch + TextEncoder + SubtleCrypto)

**Recommendation**: Implement `iicp-client-wasm` as a TypeScript PWA. Do NOT attempt
to compile the Python or Rust codebase to WASM.

---

## WASM-2: CORS/Localhost Detection Feasibility

**Question**: Which local endpoints are reachable from the browser?

**Localhost constraints** (browser CORS policy):

| Endpoint | Reachable from browser? | Constraint |
|----------|------------------------|-----------|
| `https://iicp.network` | ✓ Yes | CORS headers already present |
| `http://localhost:11434` (Ollama) | ✗ No by default | Mixed-content blocked (HTTPS page → HTTP local) |
| `http://localhost:8000` (vLLM) | ✗ No by default | Same mixed-content issue |
| `http://127.0.0.1:*` | ✗ No by default | Chrome blocks direct localhost from HTTPS |

**Chrome exception**: Chrome allows `http://localhost:*` from `https://` pages in
Chrome 129+ via "Localhost Network Access" policy — but this is non-standard and
not supported in Firefox or Safari.

**Service Worker relay approach**: A Service Worker (SW) installed by the PWA can
intercept fetch requests and relay them to localhost via the SW's own network context.
However, SWs also run in the browser's main process and face the same CORS restrictions
for localhost calls.

**Recommended solution**: A lightweight local relay shim (< 200 lines) that users
install via `npm install -g iicp-relay-shim` or via the existing `iicp-node` binary:

```bash
iicp-node relay --port 7654
# Starts a CORS-enabled HTTP relay on localhost:7654
# Proxies requests to detected LLM endpoints
# Responds with CORS headers that the browser can reach
```

The browser-side PWA calls `http://localhost:7654/v1/chat` which the relay forwards
to the detected LLM endpoint. This breaks the mixed-content restriction without
compromising security (relay only serves localhost-to-localhost).

---

## WASM-3: Consumer-Only Architecture Spec

**CIP Consumer Client Contract** (browser/WASM client, no registration, no heartbeat):

```typescript
interface IICPConsumer {
  // Discover nodes for an intent
  discover(intent: string, opts?: DiscoverOptions): Promise<Node[]>
  
  // Dispatch a task (single provider, no CIP multi-path)
  call(node: Node, payload: TaskPayload, opts?: CallOptions): Promise<TaskResult>
  
  // Dispatch with CIP best_of_n (optional, requires ≥2 nodes)
  cipCall(nodes: Node[], payload: TaskPayload, policy: CIPPolicy): Promise<TaskResult>
  
  // OpenAI-compatible shim (wraps discover + call)
  chat(messages: Message[], opts?: ChatOptions): Promise<ChatResult>
}
```

**No registration, no heartbeat, no provider functions**. Consumer clients are invisible
to the directory — they don't appear in discover results and don't need node_tokens.

The consumer-only contract requires a "consumer_key" for signed requests (to prevent
request spoofing). Proposed: ECDH ephemeral key pair generated in browser SubtleCrypto,
rotated per session. No persistent key storage needed for consumer-only mode.

---

## WASM-4: WebLLM Integration Feasibility

**Question**: Can we embed a local inference engine (WebLLM / llama.wasm) as a built-in node?

**Assessment**:
- WebLLM (via MLC): Yes, feasible. `@mlc-ai/web-llm` npm package runs Llama 3.2 1B/3B
  in the browser via WebGPU. Bundle size: ~5MB JS + model download (300MB–8GB)
- llama.wasm: feasible but compilation is complex; MLC-AI's web-llm is a better-maintained option
- WebGPU support: Chrome 113+, Firefox (behind flag), Safari Technology Preview

**Use case**: The PWA detects no external local LLM → offers to load a small model via WebLLM
(Llama 3.2 1B, ~300MB download). This creates a "no install required" path for first-time users.

**Recommendation**: Include WebLLM as an OPTIONAL feature behind a user prompt:
"No local LLM detected. Would you like to load a small model in your browser? (~300MB download)"
Do NOT make WebLLM the default — operators who run dedicated hardware will prefer their
local LLM over a browser-resident model.

---

## Implementation Summary

| WASM track | Recommendation | Priority |
|------------|---------------|---------|
| WASM-1 | TypeScript PWA (not Rust WASM) | High — prerequisite |
| WASM-2 | iicp-node relay shim for localhost LLMs | Medium |
| WASM-3 | Consumer-only TypeScript contract drafted | Medium |
| WASM-4 | WebLLM optional, opt-in, small model | Low |

**Repo**: `RobLe3/iicp-client-wasm` (new, private initially)
**Target**: Alpha release after Phase 5 CIP ships and TypeScript SDK (`iicp-client`) is published to npm.

---

## Acceptance Criteria Verification

| AC | Requirement | Status |
|----|-------------|--------|
| WASM-1 feasibility report | §WASM-1: Rust→WASM not feasible, TypeScript recommended | ✓ |
| WASM-3 consumer-only spec | §WASM-3: IICPConsumer interface defined | ✓ |
| PWA manifest recommendation | Progressive Web App with local relay shim | ✓ |
| Demo page recommendation | /client or /app — deferred to implementation | Noted |
