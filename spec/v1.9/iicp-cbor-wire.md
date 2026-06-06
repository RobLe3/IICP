# IICP CBOR Wire Format

**Version**: 0.1.1
**Date**: 2026-06-06
**Status**: draft
**Issue**: #35 (S.11 — CBOR wire format reference)
**Authority**: Protocol Steward
**Relation**: iicp-core.md, spec/schemas/task.json, spec/schemas/nodelist.json

---

## Purpose

This document specifies the CBOR (RFC 8949) binary wire format for IICP messages
as an alternative to the JSON encoding defined in `iicp-core.md`. CBOR encoding
is a Phase 3 feature — JSON remains the mandatory baseline encoding through Phase 2.

An implementation MAY offer CBOR encoding. If it does, it MUST conform to this
document. A client negotiates CBOR via the `Content-Type` and `Accept` headers
defined in §3.

---

## Normative Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in RFC 2119 / BCP 14.

---

## 1. Baseline

### 1.1 Encoding standard

All CBOR in this document is **Deterministic CBOR** as defined in RFC 8949 §4.2.1:

- Integer keys over string keys where both are valid
- Shortest encoding for each value (no indefinite-length items)
- Map keys lexicographically sorted by encoded byte representation
- No duplicate map keys

Implementations MUST reject CBOR that violates these rules at message boundaries.

### 1.2 JSON parity

Every IICP message that can be represented as JSON (as specified in `iicp-core.md`)
MUST have a semantically equivalent CBOR representation. The CBOR schema in §4 is
derived by mechanical transformation of the JSON Schema in `spec/schemas/`.

---

## 2. Transport

### 2.1 Content type

IICP CBOR messages use the media type:

```
application/iicp+cbor
```

This type MUST appear in `Content-Type` for request bodies and in `Content-Type`
for response bodies when the response is CBOR encoded.

### 2.2 Negotiation

A client that supports CBOR SHOULD include:

```
Accept: application/iicp+cbor, application/json;q=0.9
```

A server that supports CBOR and receives a CBOR request MUST respond in CBOR
unless the client's `Accept` header excludes it.

A server that does not support CBOR MUST return `415 Unsupported Media Type` if
a CBOR `Content-Type` is sent in a request, with body:

```json
{"error": {"code": "unsupported_media_type", "message": "CBOR encoding not supported"}}
```

### 2.3 Phase availability

| Endpoint | JSON (Phase 1+) | CBOR (Phase 3+) |
|----------|----------------|----------------|
| `POST /v1/task` | REQUIRED | OPTIONAL |
| `POST /v1/register` | REQUIRED | OPTIONAL |
| `POST /v1/heartbeat` | REQUIRED | OPTIONAL |
| `GET /v1/discover` | REQUIRED | OPTIONAL |
| `POST /v1/peers` | REQUIRED | OPTIONAL |

---

## 3. CBOR Tag Registry

IICP registers the following CBOR application tags (pending IANA allocation):

| Tag | Name | Applies to |
|-----|------|-----------|
| 65535 | `iicp-task` | IicpTask message root |
| 65534 | `iicp-response` | IicpTaskResponse message root |
| 65533 | `iicp-node` | NodeEntry in discovery list |
| 65532 | `iicp-nodelist` | NodeListResponse message root |

Until IANA numbers are allocated, implementations MUST treat these tags as
informational. Parsers MUST accept tagged and untagged versions of each message.

---

## 4. Schema

### 4.1 IicpTask

JSON Schema source: `spec/schemas/task.json`

CBOR field map (string keys, deterministic order):

| Field | CBOR type | Constraints |
|-------|-----------|------------|
| `task_id` | text string | UUID v4, 36 chars |
| `intent` | text string | `^urn:iicp:intent:[a-z0-9_-]+:[a-z0-9_-]+:v[0-9]+$` |
| `payload` | map | Arbitrary; content opaque to routing layer |
| `constraints` | map | See §4.1.1 |
| `auth` | map | See §4.1.2 |
| `trace_id` | text string | UUID v4, 36 chars; OPTIONAL |

#### 4.1.1 TaskConstraints

| Field | CBOR type | Constraints |
|-------|-----------|------------|
| `timeout_ms` | unsigned integer | 100–300 000 inclusive |
| `max_tokens` | unsigned integer | ≥ 1; OPTIONAL |
| `qos` | text string | `realtime` \| `interactive` \| `batch` \| `best-effort`; OPTIONAL (aligned with iicp-core §3.1 `constraints.qos`) |

#### 4.1.2 TaskAuth

| Field | CBOR type | Constraints |
|-------|-----------|------------|
| `node_token` | text string | ≥ 32 chars |

#### 4.1.3 Canonical example (hex)

The following IicpTask with minimal fields:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent": "urn:iicp:intent:llm:chat:v1",
  "payload": {},
  "constraints": {"timeout_ms": 5000},
  "auth": {"node_token": "tok"}
}
```

Encodes to deterministic CBOR (abbreviated; `65535(` = tag 65535):

```
65535({
  "auth":        {"node_token": "tok"},
  "constraints": {"timeout_ms": 5000},
  "intent":      "urn:iicp:intent:llm:chat:v1",
  "payload":     {},
  "task_id":     "550e8400-e29b-41d4-a716-446655440000"
})
```

Keys are sorted lexicographically by their UTF-8 byte encoding.

---

### 4.2 IicpTaskResponse

| Field | CBOR type | Constraints |
|-------|-----------|------------|
| `task_id` | text string | UUID v4 matching request |
| `status` | text string | `success` \| `error` \| `timeout` |
| `result` | map | Present when `status = success`; OPTIONAL |
| `error` | map | Present when `status = error`; OPTIONAL |
| `tokens_used` | unsigned integer | OPTIONAL |
| `duration_ms` | unsigned integer | OPTIONAL |

---

### 4.3 NodeListResponse

JSON Schema source: `spec/schemas/nodelist.json`

| Field | CBOR type | Constraints |
|-------|-----------|------------|
| `nodes` | array of NodeEntry | May be empty |
| `total` | unsigned integer | Total matching (may exceed `nodes` length) |
| `intent` | text string | Echo of request intent |

#### NodeEntry

| Field | CBOR type | Constraints |
|-------|-----------|------------|
| `node_id` | text string | UUID v4 |
| `endpoint` | text string | HTTPS URI |
| `score` | float (IEEE 754) | 0.0–1.0 |
| `region` | text string | OPTIONAL |
| `available` | bool | |
| `last_seen` | text string | RFC 3339 datetime |

---

## 5. Error Encoding

CBOR error responses use the same `error` envelope as JSON:

```cbor
{
  "error": {
    "code":    "validation_error",
    "message": "task_id must be UUID version 4"
  }
}
```

HTTP status codes are unchanged. The `Content-Type` on error responses when the
request was CBOR MUST be `application/iicp+cbor`.

---

## 6. Migration Path

| Phase | Requirement |
|-------|-------------|
| Phase 1–2 | JSON only. Servers MUST NOT accept CBOR requests. |
| Phase 3 | CBOR OPTIONAL on all endpoints. Servers that advertise `application/iicp+cbor` in `Accept-Post` MUST implement this spec. |
| Phase 4+ | Rust node (`iicp-node`) MUST support CBOR for peer-to-peer (`POST /v1/peers`) traffic. JSON support MUST be retained. |

---

## 7. Implementation Notes

1. **Do not use indefinite-length encoding** — all arrays and maps MUST be definite-length.
2. **Float precision** — scores and fractional values MUST be encoded as IEEE 754 double (CBOR major type 7, additional info 27).
3. **Datetime strings** — use RFC 3339 text strings (CBOR tag 1 is reserved for epoch integers; use tag 0 for text datetime or omit the tag).
4. **UUID representation** — text string, not binary. Binary UUID (tag 37) MAY be used in Phase 4 peer traffic as an optimization but MUST NOT be used in gateway-facing APIs.
5. **Unknown fields** — parsers MUST ignore unknown map keys (forward compatibility).

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.1 | 2026-06-06 | §4.1.1 TaskConstraints `qos`: added `realtime` to the enum to align with iicp-core §3.1 `constraints.qos` (`realtime`/`interactive`/`batch`/`best-effort`); the CBOR encoding was missing the realtime tier added to core in v1.2.0. |
| 0.1.0 | 2026-05-15 | Initial draft — S.11 Phase 3 CBOR reference |
