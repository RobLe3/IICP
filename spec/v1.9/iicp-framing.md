# IICP Binary Framing Layer

**Document**: `spec/iicp-framing.md`  
**Version**: 0.1.0-draft  
**Date**: 2026-05-20  
**Status**: Draft — NOT YET RATIFIED (see §12)  
**Authority**: Protocol Steward  
**Issue**: #231  
**Supersedes**: (none — new document)  
**Relation**: `iicp-core.md`, `iicp-cbor-wire.md`, `spec/IICP_draft_1.4.2.txt`, ADR-002

---

## Normative Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in RFC 2119 / BCP 14.

---

## Abstract

This document defines the binary framing layer for the Intent-based Inter-agent
Communication Protocol (IICP). It specifies the wire format for IICP frames
transmitted over TCP and QUIC, the CBOR payload encoding rules for all 14 core
message types (ported from IICP v1.4.2), a formal HTTP fallback mode for Phase 1-3
interoperability, a custom/proprietary extension range, version negotiation, and
error-handling behavior.

The framing layer is a Phase 4 MUST requirement. It does NOT replace the HTTP/JSON
transport (Phase 1-3) — both are first-class IICP transport tiers. See §5 for the
HTTP fallback mode specification.

---

## 1. Binary Frame Format

### 1.1 Frame structure

Every IICP native-transport frame consists of an 11-byte fixed header followed by a
variable-length CBOR payload:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   Magic  (4 bytes):  0x49494350               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   Version (1) |    Type (1)   |   Flags (1)   | Reserved (1) |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      Length  (4 bytes, big-endian)            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   CBOR Payload  (Length bytes)                |
 ...
```

Total header size: **11 bytes**. Length field does NOT include the header.

### 1.2 Header fields

#### Magic (4 bytes)

Fixed value `0x49 0x49 0x43 0x50` (ASCII "IICP"). A receiver MUST verify the magic
bytes as the first action upon receiving a new connection or reconnect. A connection
that does not begin with the IICP magic bytes MUST be closed immediately with no
reply. The magic bytes provide fast peer-identity guarding — they do NOT constitute
authentication (see §9).

#### Version (1 byte)

The framing layer version negotiated for this connection. Current value: `0x01`.
Upper 4 bits are reserved and MUST be zero on send; MUST be ignored on receive.
Receivers MUST NOT accept frames with a Version lower than their minimum supported
version (see §6).

#### Type (1 byte)

The message type. See §3 for the type table and §7 for the custom extension range.
Receivers that receive an unknown Type in the range 0x0F–0xEF MUST send a
`CLOSE` frame with error code `unknown_type` and close the connection. Receivers that
receive a Type in the CUSTOM range (0xF0–0xFE) and have not negotiated that type
via INIT MUST send a `CLOSE` frame with error code `unsupported_extension`.

#### Flags (1 byte)

```
Bit 0 (LSB):  COMPRESSED — payload is gzip-compressed
Bit 1:        FRAGMENTED — this frame is a fragment; see §10
Bits 2–7:     Reserved; MUST be zero on send; MUST be ignored on receive
```

#### Reserved (1 byte)

MUST be `0x00` on send. MUST be ignored on receive. Reserved for future use.

#### Length (4 bytes, big-endian)

Unsigned 32-bit integer in network byte order (big-endian). Specifies the byte count
of the CBOR payload following the header. Does NOT include the 11-byte header itself.
A receiver MUST NOT allocate a buffer for the payload until after validating the magic
bytes and confirming Length is within its configured maximum (see §2).

---

## 2. Length Constraints

| Limit | Value | Rationale |
|-------|-------|-----------|
| Minimum payload | 0 bytes | Valid for PING / PONG frames |
| Maximum single frame | 16,777,216 bytes (16 MiB) | Prevents memory amplification |
| Recommended segment | 65,536 bytes (64 KiB) | Fits within a single QUIC datagram after overhead |
| Maximum CALL payload (compressed) | 1,048,576 bytes (1 MiB) | Hard limit for task invocations |
| Maximum CALL payload (uncompressed) | 33,554,432 bytes (32 MiB) | Reject inflate beyond this |
| Fragmentation threshold | 65,536 bytes | Frames exceeding this SHOULD use fragmentation |

A receiver MUST close the connection with error code `frame_too_large` if the
Length field exceeds 16,777,216 bytes. The check MUST be performed before allocating
any buffer — a receiver MUST NOT speculatively allocate memory proportional to the
Length field before this check.

A receiver MUST close the connection with error code `payload_too_large` if a CALL
frame's decompressed payload exceeds 33,554,432 bytes.

---

## 3. Message Type Table

The 256-value type byte is partitioned as follows:

| Range | Allocation |
|-------|-----------|
| 0x00 | RESERVED — must not be sent |
| 0x01–0x0E | IICP core protocol (14 types, this section) |
| 0x0F–0xEF | RESERVED for future IICP protocol use |
| 0xF0–0xFE | CUSTOM — proprietary and application-specific (§7) |
| 0xFF | RESERVED — must not be sent |

### Core message types

| Byte | Name | Direction | Purpose |
|------|------|-----------|---------|
| `0x01` | INIT | client → server | Session handshake and version negotiation |
| `0x02` | ACK | server → client | Handshake acknowledgement; echoes negotiated parameters |
| `0x03` | DISCOVER | client → server | Node discovery query by intent URN |
| `0x04` | SUB_PROTOCOL | bidirectional | Sub-protocol extension negotiation |
| `0x05` | CALL | client → server | Task invocation (the primary protocol message) |
| `0x06` | RESPONSE | server → client | Task result or streaming update |
| `0x07` | CLOSE | bidirectional | Graceful session teardown with optional error |
| `0x08` | FEEDBACK | client → server | Quality signal and outcome report |
| `0x09` | PING | bidirectional | Keepalive request |
| `0x0A` | PONG | bidirectional | Keepalive reply |
| `0x0B` | CONTROL | bidirectional | Flow control and credit allocation |
| `0x0C` | ADVERTISE | server → client | Capability advertisement |
| `0x0D` | OBSERVE | bidirectional | Stream telemetry subscription or event |
| `0x0E` | TELEMETRY | bidirectional | Diagnostic telemetry report |

---

## 4. CBOR Payload Encoding

### 4.1 Encoding baseline

All CBOR payloads in IICP MUST use **Deterministic CBOR** as defined in RFC 8949 §4.2.1:

- Integer keys over string keys where both options exist (numbered field maps)
- Shortest encoding for each value
- Map keys sorted lexicographically by their encoded byte representation
- No indefinite-length items (arrays and maps MUST be definite-length)
- No duplicate map keys

Receivers MUST reject frames whose CBOR payload violates deterministic encoding
rules. This requirement enables signature verification (ADR-024) without normalization.

### 4.2 Integer-keyed field maps

All IICP native-transport CBOR messages use **integer-keyed maps** (CBOR major type 5
with integer keys). String-keyed maps are the HTTP fallback encoding (§5) and MUST NOT
be used in native-transport frames.

### 4.3 CALL message schema (0x05)

The CALL message carries a task invocation. All integer keys from IICP v1.4.2 are
preserved; three keys are deprecated (marked †).

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | protocol_version | uint | MUST | Framing version, current `1` |
| 2 | session_id | tstr | MUST | UUID v4, 36 chars |
| 3 | intent | tstr | MUST | Standard: `urn:iicp:intent:<domain>:<action>:v<N>`; Custom: `urn:iicp:intent:x.<vendor>:<action>:v<N>` |
| 4 | provider_id | tstr | SHOULD | UUID v4 of target node; omit for directory routing |
| 5 | payload | bstr | MUST | Task content; gzip-compressed when Flags bit 0 set |
| 6 | timeout | uint | MUST | Seconds; 1–3600 |
| 7 | priority | uint | SHOULD | 0 = best-effort, 1 = normal, 2 = high, 3 = critical |
| 8 | credits | uint | MAY | Credit units consumed by this call |
| 9 | routing_hint | tstr | MAY | Opaque routing directive for the directory |
| 10 | scheduling_hint | tstr | MAY | Scheduler directive (e.g., `batch`, `interactive`) |
| 11 | auth_token | tstr | MUST | Bearer token; ≥ 32 chars; **LOG-FORBIDDEN** |
| 12 | retry_policy | map | MAY | `{1: max_retries(uint), 2: backoff_ms(uint)}` |
| 13 | trace_id | bstr | SHOULD | Exactly 16 bytes (W3C trace ID) |
| 14 | parent_span | bstr | MAY | Exactly 8 bytes (W3C parent span ID) |
| 15 | call_id | tstr | SHOULD | UUID v4 uniquely identifying this call attempt |
| 16 | idempotency_key | tstr | MAY | Client-chosen idempotency token |
| 17 | max_tokens | uint | MAY | Maximum output tokens requested |
| 18 | qos | tstr | MAY | `interactive` \| `batch` \| `best-effort` |
| 19 | transport_hint† | tstr | deprecated | Use framing version negotiation instead |
| 20 | region | tstr | MAY | Target region code (`us-east-1`, etc.) |
| 21 | capabilities | array | MAY | Required node capabilities; array of tstr |
| 22 | ttl | uint | MAY | Time-to-live in seconds; 0 = no limit |
| 23 | metadata | map | MAY | Opaque key/value pairs; keys and values MUST be tstr |

**LOG-FORBIDDEN**: Implementations MUST NOT log the value of key 11 (`auth_token`)
in any log, trace, metric label, error message, or debug output. This prohibition
applies to all log levels including DEBUG and TRACE.

**Note — v1.4.2 payload_hash field (A-001)**: IICP v1.4.2 defined an `X-IICP-Hash` field
(SHA-256 of the raw payload) for integrity verification. In v1.5 this field is intentionally
superseded by ADR-024 (Signed Message Envelope), which signs the full CBOR-encoded message
including the payload. Implementations that need payload integrity verification MUST use
ADR-024 envelope signing rather than a standalone hash field.

### 4.4 RESPONSE message schema (0x06)

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | protocol_version | uint | MUST | |
| 2 | session_id | tstr | MUST | Echo of CALL session_id |
| 3 | call_id | tstr | MUST | Echo of CALL call_id |
| 4 | status | tstr | MUST | `success` \| `error` \| `timeout` \| `partial` |
| 5 | result | bstr or map | COND | Present when status = `success` or `partial` |
| 6 | error | map | COND | Present when status = `error`; `{1: code(tstr), 2: message(tstr)}` |
| 7 | tokens_used | uint | SHOULD | Output tokens consumed |
| 8 | duration_ms | uint | SHOULD | Wall-clock time at server in ms |
| 9 | trace_id | bstr | SHOULD | 16 bytes; echo of CALL trace_id |
| 10 | credits_charged | uint | MAY | Credits deducted for this call |
| 11 | node_id | tstr | SHOULD | Responding node UUID |
| 12 | is_final | bool | SHOULD | `true` when streaming is complete |

### 4.5 INIT message schema (0x01)

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | protocol_version | uint | MUST | Framing version; current `1` |
| 2 | min_version | uint | MUST | Minimum framing version sender supports |
| 3 | node_id | tstr | SHOULD | Sender's registered node UUID |
| 4 | node_token | tstr | COND | Required when node_id present; **LOG-FORBIDDEN** |
| 5 | capabilities | array | SHOULD | Supported custom type URNs (for 0xF0–0xFE negotiation) |
| 6 | compression | array | MAY | Supported compression algorithms; e.g., `["gzip"]` |
| 7 | max_frame_size | uint | MAY | Sender's maximum accepted frame size in bytes |

### 4.6 ACK message schema (0x02)

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | protocol_version | uint | MUST | Negotiated framing version (§6) |
| 2 | node_id | tstr | SHOULD | Responder's registered node UUID |
| 3 | capabilities | array | SHOULD | Accepted custom type URNs from INIT |
| 4 | compression | tstr | MAY | Selected compression algorithm |
| 5 | max_frame_size | uint | MAY | Responder's maximum accepted frame size |
| 6 | server_time | uint | MAY | Epoch seconds; aids clock synchronisation |

### 4.7 DISCOVER message schema (0x03)

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | intent | tstr | MUST | Intent URN to discover |
| 2 | limit | uint | MAY | Maximum nodes to return; default 10 |
| 3 | region | tstr | MAY | Preferred region |
| 4 | exclude | array | MAY | Array of node_id tstr to exclude |
| 5 | min_score | float | MAY | Minimum NodeScorer score 0.0–1.0 |

### 4.8 CLOSE message schema (0x07)

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | reason | tstr | SHOULD | Error code or `graceful` |
| 2 | message | tstr | MAY | Human-readable description |
| 3 | session_id | tstr | MAY | Session being closed |

Standard close reason codes: `graceful`, `unknown_type`, `unsupported_extension`,
`frame_too_large`, `payload_too_large`, `version_mismatch`, `auth_failed`,
`idle_timeout`, `protocol_error`.

### 4.9 PING and PONG (0x09, 0x0A)

PING and PONG MAY have a zero-byte payload (Length = 0) or a CBOR map with key 1
(`echo_data`: bstr, ≤ 64 bytes) which MUST be echoed verbatim in the PONG. A
receiver MUST reply to PING with PONG within 30 seconds or the sender MAY close
the connection with reason `idle_timeout`.

### 4.10 FEEDBACK message schema (0x08)

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | call_id | tstr | MUST | UUID v4 of the CALL being rated |
| 2 | score | float | MUST | 0.0 (worst) – 1.0 (best) |
| 3 | latency_ms | uint | SHOULD | Observed end-to-end latency |
| 4 | error_code | tstr | MAY | Error code if task failed |
| 5 | comment | tstr | MAY | Free-text; ≤ 512 chars |

### 4.11 CONTROL message schema (0x0B)

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | action | tstr | MUST | `credit_grant` \| `credit_revoke` \| `rate_limit` \| `pause` \| `resume` |
| 2 | credits | uint | COND | Required for credit actions |
| 3 | rate_limit_rps | uint | COND | Required for `rate_limit` action |
| 4 | session_id | tstr | MAY | Targets a specific session |

### 4.12 ADVERTISE message schema (0x0C)

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | node_id | tstr | MUST | Advertising node UUID |
| 2 | intents | array | MUST | Array of intent URN tstr this node supports |
| 3 | score | float | SHOULD | Current NodeScorer score 0.0–1.0 |
| 4 | region | tstr | SHOULD | Node's region code |
| 5 | endpoint | tstr | SHOULD | Node's public endpoint URI |
| 6 | load | float | MAY | Current load 0.0 (idle) – 1.0 (full) |

### 4.13 OBSERVE message schema (0x0D)

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | subject | tstr | MUST | `session` \| `node` \| `call` |
| 2 | subject_id | tstr | MUST | UUID of the subject |
| 3 | event_type | tstr | MUST | `start` \| `update` \| `end` \| `error` |
| 4 | data | map | SHOULD | Event payload; opaque |
| 5 | sequence | uint | SHOULD | Monotonically increasing per-subject sequence number |

**Note — v1.4.2 routing_metrics field (A-002)**: IICP v1.4.2 OBSERVE had an additional
`routing_metrics` field (array) for topology-based routing optimization via QuDAG. In v1.5,
OBSERVE serves the streaming subscription purpose exclusively. Topology-aware routing is
performed by the directory's discovery and scoring mechanism (ADR-008), not by peer-to-peer
OBSERVE messages. The `routing_metrics` field is intentionally omitted.

### 4.14 TELEMETRY message schema (0x0E)

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | node_id | tstr | MUST | Reporting node UUID |
| 2 | timestamp | uint | MUST | Epoch seconds |
| 3 | metrics | map | MUST | Key/value pairs; keys MUST be tstr |
| 4 | trace_id | bstr | MAY | 16 bytes; W3C trace context |
| 5 | span_id | bstr | MAY | 8 bytes; W3C parent span |

### 4.15 SUB_PROTOCOL message schema (0x04)

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | sub_protocol | tstr | MUST | Sub-protocol URN; e.g., `urn:iicp:sp:cip:v1` |
| 2 | action | tstr | MUST | `propose` \| `accept` \| `reject` |
| 3 | parameters | map | MAY | Sub-protocol-specific parameters |
| 4 | reason | tstr | COND | Required when action = `reject` |

### 4.16 Field validation rules

1. **Exact-length binary fields**: `trace_id` (key 13 in CALL, key 4 in OBSERVE/TELEMETRY)
   MUST be exactly 16 bytes. `parent_span` (key 14 in CALL, key 5 in TELEMETRY) MUST be
   exactly 8 bytes. Receivers MUST reject frames where these fields have incorrect lengths
   with reason `protocol_error`.

2. **Unknown fields**: receivers MUST ignore unknown integer keys (open schema, forward
   compatibility). This rule is symmetric — senders MAY add fields in future versions
   without breaking older receivers.

3. **String character sets**: all `tstr` fields MUST be valid UTF-8. Receivers MUST
   reject frames with invalid UTF-8 strings with reason `protocol_error`.

4. **LOG-FORBIDDEN fields**: keys carrying credentials or tokens MUST NOT appear in
   logs, traces, metric labels, or debug output at any log level. Affected keys:
   CALL key 11 (`auth_token`), INIT key 4 (`node_token`).

---

## 5. HTTP Fallback Mode

### 5.1 Status

HTTP fallback mode is a **first-class IICP transport tier**. It is the mandatory
transport for Phase 1–3 conformance. Nodes that implement HTTP fallback and satisfy
all REACH conformance probes are fully conformant IICP implementations.

Native binary framing (§1) is the mandatory transport for Phase 4 conformance.
Both modes MUST coexist; Phase 4 nodes MUST support HTTP fallback for
directory-facing calls where the directory is Phase 1–3 only.

### 5.2 Message mapping

| Native type | HTTP method | Endpoint | Body format |
|-------------|-------------|----------|-------------|
| INIT (0x01) | POST | `/api/v1/register` | JSON or `application/iicp+cbor` |
| ACK (0x02) | 200 response to INIT | — | JSON or `application/iicp+cbor` |
| DISCOVER (0x03) | GET | `/api/v1/discover?intent=<urn>` | — |
| CALL (0x05) | POST | `/v1/task` | JSON or `application/iicp+cbor` |
| RESPONSE (0x06) | 200 response to CALL | — | JSON or `application/iicp+cbor` |
| CLOSE (0x07) | Implicit on 4xx/5xx or connection close | — | JSON error body |
| FEEDBACK (0x08) | POST | `/api/v1/heartbeat` | JSON |
| PING (0x09) | GET | `/iicp/health` | — |
| PONG (0x0A) | 200 response to PING | — | JSON |
| CONTROL (0x0B) | POST | `/v1/control` | JSON |
| ADVERTISE (0x0C) | GET | `/api/v1/node/{node_id}` | — |
| OBSERVE (0x0D) | GET | `/v1/stream` (SSE) | `text/event-stream` |
| TELEMETRY (0x0E) | POST | `/v1/telemetry` | JSON |
| CUSTOM (0xF0–0xFE) | POST | `/v1/custom/{type-urn}` | `application/iicp+cbor` RECOMMENDED |

### 5.3 Version advertisement in HTTP mode

A node implementing HTTP fallback MUST include the following header in all
outbound requests:

```
X-IICP-Version: 1.5
```

A node that also supports native binary framing MUST include:

```
X-IICP-Framing: native/1
```

This signals to the peer that native framing is available for future connections.
The peer MAY switch to native framing on the next connection attempt.

### 5.4 CBOR-over-HTTP

An HTTP-mode node MAY negotiate CBOR body encoding using standard content
negotiation:

```
Accept: application/iicp+cbor, application/json;q=0.9
```

CBOR-over-HTTP uses **string-keyed maps** (as specified in `iicp-cbor-wire.md`).
Native-transport frames use **integer-keyed maps** (§4). The two CBOR encodings
are semantically equivalent but structurally distinct.

### 5.5 Semantic gaps in HTTP fallback

| Gap | HTTP behavior | Native behavior | Mitigation |
|-----|---------------|----------------|-----------|
| Session state | Stateless; each request independent | Stateful connection | Use `session_id` field for correlation |
| Ordering | HTTP/1.1 head-of-line; HTTP/2 streams | QUIC streams; ordered per-stream | Not a concern for request/response pairs |
| Streaming OBSERVE | Server-Sent Events (SSE) | Native OBSERVE frames | SSE is the HTTP fallback for streaming |
| CLOSE | Implicit (4xx, connection close, timeout) | Explicit CLOSE frame | Servers MUST return meaningful 4xx codes |
| Fragmentation | Handled by HTTP chunked transfer | IICP fragmentation protocol (§10) | No action needed; HTTP handles it |
| Custom frames 0xF0–0xFE | POST /v1/custom/{urn} | Custom type byte | Endpoint MUST return 404 for unsupported URNs |

### 5.6 Conformance tiers

| Tier | Transport | Conformance requirement |
|------|-----------|------------------------|
| Phase 1–3 | HTTP/JSON (+ optional CBOR-over-HTTP) | MUST implement §5 HTTP mapping |
| Phase 4 | Native binary framing over TCP or QUIC | MUST implement §1–§4 |
| Phase 4 (directory calls) | HTTP fallback for directory API | MUST retain HTTP fallback |

---

## 6. Version Negotiation

### 6.1 Algorithm

1. The client sends an INIT frame with `protocol_version = N` (its preferred version)
   and `min_version = M` (its minimum acceptable version).

2. The server receives INIT. If `N` exceeds the server's maximum supported version,
   the server selects its own maximum. If the resulting version is below `M`, the
   server sends a CLOSE frame with reason `version_mismatch` and closes the connection.
   Otherwise, the server sends an ACK with `protocol_version = min(N, server_max)`.

3. All subsequent frames in the connection MUST use the negotiated version.

### 6.2 Version table

| Version | Status | Features |
|---------|--------|---------|
| 0x01 | Current | Binary framing, 14 core types, custom range 0xF0–0xFE |
| 0x00 | Reserved | Must not be sent |

### 6.3 Forward compatibility

A receiver that encounters a Version byte higher than its maximum supported version
MUST send CLOSE with reason `version_mismatch`. It MUST NOT attempt to parse the
CBOR payload.

### 6.4 Rollback defense

Version selection is protected by the IICP Signed Message Envelope (ADR-024) when
that extension is active. A MITM that downgrades the version field in an INIT frame
will produce a signature mismatch on the INIT payload, which the receiver MUST treat
as an `auth_failed` close.

---

## 7. Custom / Proprietary Extension Range

### 7.1 Range allocation

Type bytes 0xF0–0xFE (15 values) are reserved for **CUSTOM** use. IICP commits
to never assigning these bytes to core protocol types. This commitment is permanent
and applies to all future versions of the IICP standard.

### 7.2 Motivation

IICP is designed for deployment by vertical AI platforms, enterprise clusters, and
research networks that may require proprietary message semantics not suitable for
the public protocol. The CUSTOM range enables these operators to embed IICP as their
transport while adding application-specific message types without IETF process friction.

Examples of legitimate uses:
- A medical AI network adding HIPAA-provenance audit frames
- An enterprise cluster adding proprietary billing and audit messages
- A research deployment experimenting with new routing protocols before IETF proposal

### 7.3 Design: capability-negotiated custom types

IICP uses a **capability-negotiated** model for custom types:

1. In the INIT message (§4.5), the sender includes `capabilities` (key 5): an array
   of custom type URNs the sender supports. Each URN MUST have the form
   `urn:iicp:custom:<vendor>:<type>:<version>`.
   Example: `urn:iicp:custom:acme:audit:v1` → uses type byte 0xF0.

2. The ACK message (§4.6) echoes the `capabilities` array with the subset the server
   accepts. Only types present in the ACK are valid for use on this connection.

3. The mapping from URN to type byte is VENDOR-DEFINED and established out-of-band.
   Vendors SHOULD publish their URN↔byte mappings at `iicp.network/extensions`.

4. A receiver that receives a CUSTOM type byte that was NOT negotiated in INIT/ACK
   MUST send CLOSE with reason `unsupported_extension`. It MUST NOT silently discard
   the frame.

### 7.4 Behavior of standard-only peers

A node that does not support any CUSTOM types MUST:
- Send an empty `capabilities` array in INIT.
- Upon receiving a frame with type byte in 0xF0–0xFE, send CLOSE with reason
  `unsupported_extension` and close the connection.

Standard relay nodes MUST NOT forward CUSTOM frames to peers that did not negotiate
them in INIT/ACK. A relay that cannot determine whether a CUSTOM type was negotiated
MUST drop the frame and send CLOSE with reason `unsupported_extension` to the sender.

### 7.5 Upgrade path to standard protocol

A CUSTOM type with demonstrated broad adoption (≥ 3 independent implementations and
≥ 1 production deployment) MAY be proposed for the IICP standard type range
(0x0F–0xEF) via the IICP governance process. The proposer MUST submit a protocol
extension document following the `iicp-extensions.md` template, demonstrating:
- Functional necessity (what the core 14 types cannot express)
- Implementation evidence
- Backward compatibility with standard-only receivers

### 7.6 Collision avoidance

Since the type byte alone is insufficient for collision avoidance (15 values for
all vendors), implementors MUST use URN negotiation (§7.3) as the canonical identity.
The type byte is a session-scoped shorthand. Vendors SHOULD register their URNs at
`iicp.network/extensions` to avoid cross-vendor URN collisions.

---

## 8. Connection Lifecycle

### 8.1 Handshake

```
Client                              Server
  |                                   |
  |-- TCP/QUIC connect -------------> |
  |-- INIT (0x01) -----------------> |
  |                                   | (validate magic, version, auth)
  |<-- ACK (0x02) ------------------- |
  |                                   |
  |  (session established)           |
```

The server MUST respond to INIT within 5 seconds. If no response arrives, the
client MUST close the connection and MAY retry with exponential backoff.

### 8.2 Active session

After the handshake, both peers MAY send any negotiated message type. The server
MUST NOT send CALL frames; the client MUST NOT send RESPONSE frames (direction
constraints from §3).

### 8.3 Graceful close

Either peer MAY initiate close by sending CLOSE (0x07) with `reason = graceful`.
The receiving peer MUST acknowledge by sending its own CLOSE frame and then closing
the underlying transport. Both peers MUST send any in-flight RESPONSE frames before
sending CLOSE.

### 8.4 Error close

When a protocol error is detected, the detecting peer MUST:
1. Send a CLOSE frame with the appropriate reason code (§4.8).
2. Close the underlying TCP/QUIC connection without further reads.

The remote peer that receives an unexpected close MUST NOT retry on the same
connection. It MAY open a new connection after a backoff period.

---

## 9. Security Considerations

### 9.1 Transport security

All IICP native-transport connections MUST use TLS 1.3 or higher over TCP, or
QUIC 1 (which mandates TLS 1.3 internally) over UDP. Plaintext IICP connections
MUST NOT be used in production. Development environments MAY use plaintext with
explicit configuration; implementations MUST require explicit opt-in and MUST log
a warning when plaintext mode is active.

### 9.2 Magic bytes are not authentication

The IICP magic bytes (§1.2) provide fast peer-identity guarding against accidental
connections from non-IICP software. They do NOT authenticate the connecting peer.
Authentication is performed by the `auth_token` / `node_token` fields in INIT and
CALL messages. See ADR-024 (Signed Message Envelope) for frame-level authentication.

### 9.3 Credential handling

Implementations MUST:
- Never log INIT key 4 (`node_token`) or CALL key 11 (`auth_token`) at any level.
- Zero memory regions holding credential values before freeing.
- Not include credential values in error messages, stack traces, or core dumps.

### 9.4 Custom frame relay security

A standard relay that receives an unrecognized CUSTOM frame (§7) MUST NOT forward
it silently. Blind relay of unknown frame types is a potential covert channel.
The relay MUST either reject with `unsupported_extension` or have explicit
forwarding authorization negotiated in INIT/ACK.

### 9.5 Length field amplification

A receiver MUST validate that the Length field (§1.2) does not exceed its configured
maximum before allocating any memory. A Length value of `0xFFFFFFFF` on a PING frame
from a malicious peer MUST be rejected immediately. See §2 for the maximum length table.

### 9.6 Malformed frame handling — disposition table

The following table specifies the normative disposition for each malformed-frame
case. Implementations MUST comply. The dispositions are derived from the
security principle: fail closed, fail cheap, fail loudly (log at warn level).

| Case | Detection point | Disposition | Error code |
|------|----------------|-------------|------------|
| Magic bytes wrong or absent | First 4 bytes | Close TCP/QUIC connection immediately; no reply | — (no CLOSE frame sent — peer may not speak IICP) |
| Length > 16 MiB | After magic OK | Send CLOSE(frame_too_large); close connection; DO NOT allocate | `frame_too_large` |
| Length = 0 on CALL/RESPONSE | Header parse | Send CLOSE(invalid_frame); reject | `invalid_frame` |
| Length = 0 on PING/PONG | Header parse | VALID — 0-byte payload is permitted for PING/PONG | — (no error) |
| Partial payload (stream delivers fewer bytes than Length within 30s) | Read loop | Send CLOSE(read_timeout); close connection | `read_timeout` |
| Version = 0x00 | Header parse | Send CLOSE(invalid_version); reject | `invalid_version` |
| Version unknown and peer rejected downgrade | Version negotiation §6 | Send CLOSE(version_mismatch); close connection | `version_mismatch` |
| Type = 0x00 (RESERVED) | Header parse | Send CLOSE(invalid_type); reject | `invalid_type` |
| Type = 0xFF (RESERVED) | Header parse | Send CLOSE(invalid_type); reject | `invalid_type` |
| Type in 0x0F–0xEF (future IICP reserved) | Header parse | Send CLOSE(unknown_type) if not forward-compat; MUST NOT process payload | `unknown_type` |
| Type in 0xF0–0xFE and no capability negotiated | Header parse | Send CLOSE(unsupported_extension); reject | `unsupported_extension` |
| Flags: unknown bits set | Header parse | MUST ignore unknown flag bits; process frame normally | — (extensibility rule) |
| Reserved byte non-zero | Header parse | MUST ignore; process frame normally | — (forward compat) |
| CBOR decode failure in payload | Payload parse | Send CLOSE(cbor_decode_error); close connection | `cbor_decode_error` |
| CBOR payload violates field type constraints (§4.16) | Payload parse | Send CLOSE(invalid_payload); close connection | `invalid_payload` |
| Fragment out-of-order (see §10.3) | Reassembly | Buffer up to 256 fragments; discard after 30s timeout; send CLOSE(fragment_timeout) | `fragment_timeout` |
| Fragment storm (> 256 pending fragments total) | Reassembly | Send CLOSE(fragment_limit_exceeded); close connection | `fragment_limit_exceeded` |
| CALL payload inflates beyond 32 MiB (§2) | Decompression | Abort decompression; send CLOSE(payload_too_large) | `payload_too_large` |

**Notes:**
- All CLOSE frames sent in response to malformed input MUST be sent before closing the
  connection (one CLOSE frame, then close). Except when magic bytes are wrong — in
  that case, silently close without sending a CLOSE frame (peer likely is not IICP).
- Implementations MUST log all malformed-frame events at `warn` level, including the
  peer address, frame type (if parseable), and error code. This enables operational
  monitoring of scanning/probe traffic.
- Memory MUST NOT be allocated proportional to the Length field before the
  `frame_too_large` check is performed. A two-pass strategy (check → allocate) is REQUIRED.
- All error codes in this table are IICP error codes carried in the CLOSE frame payload
  (key 2 of the CLOSE schema, §4.8). They MUST be ASCII strings ≤ 64 bytes.

### 9.7 Version negotiation failure paths

Version negotiation failure cases and their normative dispositions (extends §6):

| Case | Initiator action | Responder action | Error code |
|------|-----------------|-----------------|------------|
| Client offers version higher than server supports | Client sends INIT with `version = N` | Server sends CLOSE(`version_mismatch`, `server_max = M`); client MAY retry with `version ≤ M` | `version_mismatch` |
| Client offers version lower than server's minimum floor | Client sends INIT with `version = N` | Server sends CLOSE(`version_too_old`, `server_min = K`); client MUST NOT retry with same version | `version_too_old` |
| Both sides agree on version but feature flag conflict | Per §6.3 forward compat | Unknown flag bits MUST be ignored; feature negotiation is separate from version negotiation | — (no error; ignore unknown flags) |
| Version byte is 0x00 (invalid) | Client sends 0x00 | Server sends CLOSE(`invalid_version`); close | `invalid_version` |
| Rollback attack (MITM replaces INIT version) | INIT arrives with downgraded version | If TLS used (REQUIRED in production), MITM is impossible — connection already authenticated. In plaintext dev mode, server logs warn and applies §6.4 anti-downgrade check. | `version_mismatch` |
| Client does not send INIT within 10 seconds | Server waits | Server sends CLOSE(`init_timeout`); close | `init_timeout` |
| Server does not send ACK within 10 seconds | Client waits | Client MUST close the connection; log warn; do not retry the same endpoint within 60 seconds | `ack_timeout` (client-side) |
| ACK version differs from negotiated version | Client receives ACK | Client MUST close immediately: server violated negotiation contract | `version_mismatch` |

**Rollback defense detail (§6.4 extended):**

A downgrade-resistant implementation MUST:
1. Record the version offered in INIT in a tamper-evident session record (e.g., TLS exported keying material or a session-level HMAC).
2. On ACK receipt, verify the acknowledged version matches the INIT offer.
3. If the version was lowered without the client's explicit retry, send CLOSE(`version_mismatch`) and treat the connection as potentially compromised.

The TLS 1.3 handshake already prevents MITM version tampering for native-transport connections in production (§9.1 REQUIRED). This rollback defense is a defense-in-depth measure for future non-TLS transport profiles.

---

## 10. Fragmentation Protocol

### 10.1 When to fragment

Implementations SHOULD fragment frames whose payload exceeds 65,536 bytes. Over
QUIC, fragmentation at the IICP layer is OPTIONAL — QUIC handles segmentation
transparently. Over TCP, IICP-layer fragmentation is the application's responsibility.

### 10.2 Fragment frame format

A fragment frame sets Flags bit 1 (FRAGMENTED). Its CBOR payload is a map with:

| Key | Name | CBOR type | Required | Constraints |
|-----|------|-----------|----------|-------------|
| 1 | fragment_id | tstr | MUST | UUID v4 identifying the original complete message |
| 2 | fragment_seq | uint | MUST | 0-based fragment index |
| 3 | fragment_total | uint | MUST | Total number of fragments |
| 4 | fragment_data | bstr | MUST | This fragment's data slice |

The Type byte in the fragment frame MUST match the type of the original message being
fragmented. Receivers MUST reassemble fragments in order before processing.

### 10.3 Reassembly constraints

- Maximum fragments per message: 256.
- Reassembly timeout: 30 seconds from first fragment received. Partial messages that
  exceed this timeout MUST be discarded and a CLOSE sent with reason `protocol_error`.
- Maximum reassembly buffer: 16 MiB (enforces the frame size limit from §2).

### 10.4 QUIC transport profile

IICP-over-QUIC uses QUIC streams for multiplexing concurrent requests without
head-of-line blocking.

**Stream mapping:**

- One QUIC connection per peer pair (as for TCP).
- Session control (INIT, ACK, CLOSE): carried on **stream 0** (bidirectional,
  client-initiated).
- Request/response pairs: each CALL/RESPONSE pair occupies a dedicated
  **client-initiated bidirectional stream**. The client opens a stream, sends one
  CALL frame, and waits for one RESPONSE frame; both endpoints close the stream
  after RESPONSE delivery.
- Push messages (OBSERVE, TELEMETRY, ADVERTISE): carried on **server-initiated
  unidirectional streams**.

This stream-per-request model eliminates head-of-line blocking inherent in a single
TCP stream. It mirrors QUIC's native multiplexing design (comparable to HTTP/2 stream
IDs over QUIC in HTTP/3).

**Why not a single session-level stream?**

A single stream preserves ordering but reintroduces head-of-line blocking — a large
CALL payload will delay subsequent control frames. Stream-per-request is preferred for
IICP workloads where concurrent inference tasks are common.

**Length field over QUIC:**

The IICP 11-byte frame header (§1.1) including the 4-byte Length field is **required
over QUIC**. QUIC STREAM frames partition the byte stream arbitrarily at the network
layer; IICP frames may span multiple QUIC STREAM frames. The Length field is the
authoritative frame boundary marker regardless of transport.

### 10.5 Fragmentation over QUIC

QUIC handles network-layer segmentation transparently. IICP-layer fragmentation
(§10.1–10.3) is therefore **OPTIONAL** over QUIC:

- If a CALL payload exceeds the peer's advertised `max_frame_size` (negotiated via
  §7.3 capability map, default 16 MiB), IICP-layer fragmentation MUST be used.
- If no `max_frame_size` constraint applies, implementations SHOULD let QUIC handle
  segmentation and SHOULD NOT set the FRAGMENTED flag.
- Over TCP, where no transport-level message segmentation occurs, IICP-layer
  fragmentation (§10.1–10.3) is the application's responsibility for payloads
  exceeding 65,536 bytes.

| Property | TCP | QUIC |
|----------|-----|------|
| Frame boundary | Length field (§1.2) | Length field (§1.2) — same requirement |
| Head-of-line blocking | Yes (single stream) | No (stream-per-request) |
| Application-layer fragmentation | Required for payload > 65 KiB | Optional — QUIC segments natively |
| Concurrent CALL/RESPONSE pairs | No | Yes (independent streams) |
| 0-RTT connection resumption | No | Available; IICP INIT replay is replay-protected by `session_id` nonce |

### 10.6 CBOR encoding constraints

**Deterministic encoding (RFC 8949 §4.2.1):**

IICP messages that carry ADR-024 signature fields MUST use deterministic CBOR
encoding. Deterministic CBOR requires:
- Integers encoded in minimal form (no leading zero bytes).
- Map keys sorted by length then lexicographic order.
- Indefinite-length items MUST NOT be used.

The following message types carry ADR-024 signature fields and therefore MUST use
deterministic CBOR: CALL (0x05), RESPONSE (0x06), INIT (0x01), FEEDBACK (0x08),
TELEMETRY (0x0E).

**Indefinite-length CBOR:**

- MUST NOT be used in CALL, RESPONSE, INIT, FEEDBACK, or TELEMETRY messages.
- SHOULD NOT be used in any other IICP message (OBSERVE, ADVERTISE, etc.) — prefer
  IICP-layer fragmentation (§10.1–10.3) for streaming large payloads.
- Implementations that receive a message with indefinite-length CBOR where
  deterministic encoding is required MUST respond with `invalid_payload` and close.

---

## 11. IANA Considerations

### 11.1 Port assignment

IICP uses port **9484** (TCP and UDP) as its canonical port.

**IANA status**: Port 9484 is **confirmed IANA-unassigned** (direct verification 2026-05-20:
queried `https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.csv`
for ports 9480–9490; zero rows returned — no service registered on any port in this range).
No conflicts found. This closes issue #239.

**Registration path** (RFC 6335):

Port 9484 is in the registered user ports range (1024–49151), which requires
"IETF Review" or "IESG Approval" for standards-track registration. The path:

1. Produce a stable IICP Internet-Draft (individual submission or WG adoption)
2. Include this IANA Considerations section in the draft
3. Request IANA early allocation via the IETF process once the draft is WG-adopted
4. Registration granted at or before RFC publication

This mirrors the process used by MQTT (RFC 9431, port 1883) and CoAP (RFC 7252, port 5683).

**Until registration is granted**: implementations SHOULD listen on port 9484 by
default and MUST advertise it in registered `endpoint` URLs when no other port is
specified.

**Design rationale**: Port 9484 is in the registered range (not ephemeral, not dynamic),
appears unassigned, and is not known to appear in ISP or enterprise firewall block lists.
Port 443 (QUIC/HTTPS piggyback via ALPN) was explicitly rejected — IICP requires a
distinct port for clean firewall identity, IANA registration, and protocol visibility
without ALPN negotiation overhead. This aligns with MQTT and CoAP precedent over the
QUIC-sharing approach.

**Alternatives considered**: 9800 (clean but arbitrary), 8494 (IICP reversed — novelty not
a strong rationale), 4994, 7878. All rejected in favor of 9484 which was already in use
in the reference implementation at the time of this decision.

### 11.2 Media types

IICP registers the following media types (registration pending):

| Media type | Use |
|-----------|-----|
| `application/iicp+cbor` | CBOR-encoded IICP message over HTTP |
| `application/iicp+json` | JSON-encoded IICP message over HTTP |

### 11.3 CBOR tags

IICP has pending CBOR tag registrations (issue #35):

| Tag | Name |
|-----|------|
| 65535 | `iicp-task` |
| 65534 | `iicp-response` |
| 65533 | `iicp-node` |
| 65532 | `iicp-nodelist` |

Until IANA numbers are allocated, implementations MUST accept both tagged and
untagged versions of each message type.

---

## 12. Status and Ratification Process

This document is at **DRAFT** status. The following gates must be cleared before
ratification:

- [x] Research issues #232 (FRAME1), #233 (FRAME2), #234 (FRAME3), #235 (FRAME4),
  #236 (FRAME5), #237 (FRAME6), #238 (FRAME7) resolved; no open blocking findings
  — FRAME5 closed: §10.4-10.6 (QUIC profile, CBOR constraints) 2026-05-20
  — FRAME7 closed: §13 (interoperability, dual-mode design) 2026-05-20
- [ ] Port 9484 IANA research (#239) complete; port confirmed or changed
- [ ] Adversarial review (#242) complete; all persona findings resolved
- [ ] ADR-024 (Signed Message Envelope) ratified; §9.2 and §6.4 verified
- [ ] CBOR deterministic encoding requirement (§4.1) validated by test suite
- [ ] HTTP fallback mapping table (§5.2) validated against REACH conformance probes
- [ ] Protocol Steward approval

**Quality target**: A cold-read by an IETF reviewer or CCIE-level network engineer
should produce the response: "This is solid. Not over-engineered, not too simple.
It solves a real problem and the design is defensible."

---

## 13. Interoperability — HTTP Fallback and Native Framing Boundary

### 13.1 Design selection

In mixed deployments (Phase 1–3 HTTP-mode nodes coexisting with Phase 4 native-framing
nodes), IICP adopts **Option 2 — Dual-mode nodes**: each Phase 4 node implements HTTP
fallback natively for control-plane calls to the directory. No separate gateway daemon
is required.

Rationale for selecting Option 2:

- **Option 1 (dedicated gateway proxy)**: adds operational complexity — a separate
  daemon must be deployed and supervised alongside every Phase 4 node. Rejected.
- **Option 2 (dual-mode, selected)**: the Phase 4 `iicp-node` speaks HTTP/JSON to
  the directory (register, heartbeat, discover) and native framing to peer nodes.
  Clean separation — control plane stays HTTP, data plane uses native framing when
  both peers support it.
- **Option 3 (first-byte detection)**: fragile — HTTP method bytes (`G`, `P`, `D`)
  could overlap with future IICP magic-byte extensions; introduces ambiguity at the
  connection layer. Rejected.

### 13.2 HTTP ↔ native framing translation table

For gateways that must translate between modes, the authoritative field mapping is:

| Semantic field | HTTP transport | Native CBOR key |
|----------------|---------------|-----------------|
| Authentication token | `Authorization: Bearer <token>` | CALL key 11: `node_token` (tstr) |
| Trace identifier | `X-Trace-Id: <16-byte hex>` | CALL key 13: `trace_id` (bstr, 16 bytes) |
| Routing hint | `X-IICP-Routing-Hint: <opaque>` | CALL key 9: `routing_hint` (tstr) |
| Scheduling hint | `X-IICP-Scheduling-Hint: <val>` | CALL key 10: `scheduling_hint` (tstr) |
| Retry policy | `X-IICP-Retry: {"max":N,"backoff_ms":M}` | CALL key 12: `retry_policy` (map) |
| Intent URN | Query param `intent=<urn>` (DISCOVER only) | CALL key 3: `intent` (tstr) |
| TTL | `X-IICP-TTL: <seconds>` | CALL key 22: `ttl` (uint) |

**Security constraint**: a gateway MUST NOT log translated credential fields. The
`node_token` value in particular MUST be treated as a secret at all translation points.

### 13.3 CUSTOM frame gateway behavior

CUSTOM message types (0xF0–0xFE, §7) have no HTTP equivalent.

A gateway receiving a CUSTOM frame from a native-mode peer:
- MUST send `CLOSE(reason: "unsupported_extension", type: <frame_type>)` to the native peer.
- MUST NOT silently drop the frame or forward partial data to the HTTP-mode peer.
- MUST NOT attempt to serialize the CUSTOM payload as a JSON body.

Peers that require CUSTOM frame support MUST negotiate native framing mode via INIT
capability exchange (§7.3). HTTP fallback mode cannot carry CUSTOM frames; this
constraint is intentional and non-negotiable.

### 13.4 Streaming (OBSERVE) at mode boundary

OBSERVE semantics differ across modes:

| Mode | Transport mechanism | Push model |
|------|--------------------|----|
| Native | Persistent TCP/QUIC stream; server-initiated OBSERVE frames | Server-push |
| HTTP fallback | `GET /api/v1/observe` with `text/event-stream` (SSE) | SSE long-poll |

A gateway translating native OBSERVE to HTTP fallback:
1. Establishes an SSE stream (`Content-Type: text/event-stream`) toward the HTTP peer.
2. Re-emits each received OBSERVE frame as one SSE `data:` event, with the CBOR
   payload base64-encoded in the `data:` field.
3. If the native stream closes, the gateway MUST emit `event: close\ndata: connection_closed\n\n`
   and then close the SSE stream.

### 13.5 Directory control-plane constraint

The directory service (`iicp.network/api/v1/`) is **HTTP-only**. Native IICP framing
MUST NOT be used for control-plane calls (register, heartbeat, discover, stats).

Phase 4 `iicp-node` implementations MUST therefore maintain an HTTP client for
control-plane calls, even when native framing is the primary peer protocol. The control
plane stays HTTP; the data plane negotiates transport in INIT. See #230 for the
`iicp-node` implementation checklist.

---

## Appendix A — Design Decisions

### A.1 Why 11-byte header (not 8)?

8 bytes: `[magic:4][version:1][type:1][length:2]` — only 64 KiB max payload, forces
fragmentation for any non-trivial CALL. 12 bytes with a 4-byte length allows 4 GiB
which is too large. 11 bytes: `[magic:4][version:1][type:1][flags:1][reserved:1][length:4]`
gives 4 GiB theoretical max but enforced at 16 MiB by §2. The single reserved byte
costs nothing and provides a clean alignment point for future extension.

### A.2 Why big-endian length?

Network byte order (big-endian) is the IETF standard for protocol header fields
(RFC 1700). All existing IETF binary protocols (TCP, QUIC, HTTP/2) use big-endian.
IICP follows this convention to be structurally familiar to network engineers.

### A.3 Why CBOR and not protobuf or msgpack?

CBOR (RFC 8949) is an IETF standard with deterministic encoding rules (RFC 8949
§4.2.1) required for signature verification. It supports self-describing types
(no schema file required for debugging), is compact, and has strong library support
in all target languages (Rust: `ciborium`; Python: `cbor2`; PHP: `cbor-php`).
Protobuf requires schema distribution; msgpack lacks a deterministic encoding standard.

### A.4 Why a custom extension range and not a sub-protocol mechanism?

The SUB_PROTOCOL message (0x04) handles sub-protocol negotiation at the application
layer. The CUSTOM type range handles transport-layer message types that don't fit the
request/response model. An enterprise audit frame that must be delivered regardless
of application state cannot use SUB_PROTOCOL — it needs its own type byte. The two
mechanisms are complementary.

---

## Changelog

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 0.1.0-draft | 2026-05-20 | PS | Initial draft — 14 CBOR schemas from v1.4.2, HTTP fallback formal spec, custom range 0xF0–0xFE, IANA considerations. Issue #231. |
| 0.1.1-draft | 2026-05-20 | PS | §9.6 malformed frame disposition table (18 cases, normative) — #232. §9.7 version negotiation failure paths (8 cases, normative) — #233. |
| 0.1.2-draft | 2026-05-20 | PS | v1.4.2 port audit amendments: §4.3 note A-001 (payload_hash superseded by ADR-024 envelope signing); §4.13 note A-002 (routing_metrics intentionally dropped, OBSERVE purpose changed from topology to streaming). Audit report: reports/v142-port-audit.md. Issue #243. |
| 0.1.3-draft | 2026-05-20 | PS | §11.1 IANA status upgraded from "appears unassigned" to "confirmed IANA-unassigned" — direct IANA CSV query verified zero assignments for ports 9480–9490. Issue #239 closed. |
| 0.1.4-draft | 2026-05-20 | PS | §10.4-10.6 QUIC transport profile — stream mapping (stream-per-request), fragmentation over QUIC (OPTIONAL, QUIC segments natively), CBOR encoding constraints (deterministic encoding for signed messages, no indefinite-length). §13 Interoperability — dual-mode design selected, HTTP↔native translation table, CUSTOM frame gateway behavior, OBSERVE SSE bridge, directory control-plane constraint. Issues #236 #238 closed. |
