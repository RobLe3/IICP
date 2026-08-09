# RESPONSE streaming implementation audit

**Date:** 2026-08-09  
**Scope:** IICP #89 after the protocol decision in IICP #3  
**Classification:** implementation and parity gap; no new protocol decision

## Decision baseline

The protocol now distinguishes two behaviors:

- Base CALL is buffered and returns one terminal RESPONSE.
- A provider that negotiates
  `urn:iicp:profile:service-lifecycle:v1` may return ordered, incremental
  partial RESPONSE frames followed by exactly one terminal RESPONSE.

The profile requires a stable `call_id`, strictly increasing `sequence`,
`is_final=false` on partial events, and `is_final=true` on the terminal event.
Errors, timeouts and cancellation after partial output terminate the sequence;
partial token counts are cumulative and terminal accounting is authoritative.
Base HTTP `POST /v1/task` remains buffered. HTTP lifecycle streaming requires
an explicitly advertised event resource and must not be inferred from chunked
transfer or an `Accept` header.

This audit found no released SDK path that claims or implements that negotiated
native streaming profile.

## SDK and transport findings

| Behavior | Python | TypeScript | Rust |
|---|---|---|---|
| Native client reads multiple RESPONSE frames | No. `IicpTcpClient.call()` performs one `_read_frame()`. | No. `IicpTcpClient.call()` performs one `_readFrame()`. | No. `call_with_session()` performs one `read_frame()`. |
| Exposes partial chunks to callers | No. | No. | No. |
| Buffers native partials internally | No; a partial would be returned as if it were the complete response. | No; same behavior. | No; same behavior. |
| Terminates on `is_final=true` | No; key 12 and lifecycle envelope key 13 are not examined. | No. | No. |
| Handles error/timeout after partial output | No partial state exists. | No partial state exists. | No partial state exists. |
| Native cancellation coupled to the stream | No. The separate lifecycle research port is not connected to CALL. | No. | No. |
| Preserves `call_id` across streamed responses | Request emission supports key 15, but there is no response-sequence validation. | Same. | Same. |
| Native server emits multiple responses | No. `_on_call()` awaits one handler result and writes one RESPONSE. | No. `_onCall()` writes one RESPONSE. | No. The handler resolves once and the server writes one RESPONSE. |
| QUIC parity | No SDK contains a released QUIC CALL implementation. | No released QUIC CALL implementation. | No released QUIC CALL implementation. |

Relevant sources:

- Python: `src/iicp_client/iicp_tcp.py`, `relay_session.py`,
  `relay_worker_client.py`.
- TypeScript: `src/iicp_tcp.ts`, `relay_session.ts`,
  `relay_worker_client.ts`.
- Rust: `src/iicp_tcp.rs`, `relay_session.rs`,
  `relay_worker_client.rs`.

The opt-in lifecycle stores in all three SDKs already model ordered events,
terminality and cancellation. They are useful implementation components, but
their module-level boundaries explicitly avoid changing released CALL/RESPONSE
behavior. Passing lifecycle fixtures is therefore not evidence of native
streaming support.

## Relay findings

All TCP relay sessions and HTTP polling relay sessions use one pending future,
Promise or oneshot channel per `call_id`. The first RESPONSE resolves and removes
that pending entry. Relay workers await one handler result and write or post one
result. The relay paths cannot forward partial/final sequences today.

Before an SDK advertises the streaming profile, its relay path must preserve
each response envelope and must keep the pending call open until a valid
terminal event. It must reject a changed `call_id`, non-increasing sequence,
partial-after-final, multiple final events and transport close before final.

## Backend and compatibility-proxy findings

The supported inference adapters are buffered:

- Ollama, LM Studio, vLLM, llama.cpp and other OpenAI-compatible engines use
  each SDK's shared OpenAI-compatible backend and parse a complete JSON
  response.
- Anthropic adapters also parse a complete JSON response.
- MeshLLM is treated as a complete-response backend at the IICP boundary.

The Python Ollama compatibility proxy describes its behavior accurately as
fake streaming: it waits for the complete IICP result and returns one terminal
NDJSON line. TypeScript and Rust do the same for Ollama. Their Anthropic
compatibility endpoints construct a complete SSE event sequence only after the
IICP task has completed. These compatibility outputs are not upstream token
streaming and must not be advertised as native IICP streaming.

For Qwen served through llama.cpp, the current path is therefore:

```text
llama.cpp complete OpenAI-compatible JSON response
  -> SDK backend result
  -> one native IICP RESPONSE
  -> optional compatibility wrapper emits a terminal-only stream shape
```

## Directory responsibilities

The PHP and Rust directories do not execute task streams and need no stream
engine. Their responsibility is limited to carrying supported-profile evidence
honestly and refusing to imply native or HTTP streaming when the provider has
not demonstrated the profile. Directory conformance should test capability
projection only after an SDK implementation can pass the shared sequence
vectors.

## Implementation order

1. Add a transport-independent response-sequence evaluator to each SDK using
   the existing `service-lifecycle-v1.json` vectors. Do not connect it to the
   runtime yet.
2. Add a language-appropriate native streaming client API while preserving
   existing buffered `call()` behavior:
   Python async iterator, TypeScript async iterable, and Rust `Stream`.
3. Add native server handler interfaces that can emit validated events. Keep
   the current single-result handler as the default adapter.
4. Extend direct and HTTP-poll relay sessions to forward a sequence and resolve
   only on the terminal event.
5. Add one genuinely streaming OpenAI-compatible backend adapter per SDK with
   bounded provider-side aggregation. Do not synthesize token streaming for a
   buffered backend.
6. Only then advertise the profile and add directory projection fixtures.
7. Treat QUIC as a later transport binding; it must consume the same sequence
   evaluator rather than define different lifecycle semantics.

Each implementation slice must cover success, error after partial, timeout
after partial, cancellation, changed `call_id`, duplicate/non-increasing
sequence, partial after final, multiple finals, and close before final. Existing
`call()` and fake-stream compatibility behavior must remain backward compatible.

## Result

| Area | Result |
|---|---|
| Protocol lifecycle | PASS: the decision is recorded and transport semantics are unambiguous. |
| Native SDK clients | IMPLEMENTATION GAP: all read one RESPONSE. |
| Native SDK servers | IMPLEMENTATION GAP: all emit one RESPONSE. |
| Relay paths | PARITY GAP: all resolve one result and cannot relay a sequence. |
| Backend adapters | IMPLEMENTATION GAP: supported inference paths buffer complete output. |
| HTTP compatibility proxies | PASS for honest labeling; not streaming evidence. |
| Directories | PASS for current buffered behavior; future profile projection remains gated. |
| QUIC | NOT IMPLEMENTED; no current parity claim. |

No wire-version change is required for the optional profile. A version decision
would be required only if streaming became mandatory in the base profile or a
required field/HTTP response shape changed.
