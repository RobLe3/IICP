# IICP-DIR — Directory Sub-Protocol Specification

**Version**: 0.1.0  
**Date**: 2026-05-14  
**Status**: draft  
**Issue**: #14  
**Authority**: Protocol Steward  
**Relation**: ADR-009, SPEC_ANALYSIS.md GAP-1

---

## 1. Purpose

IICP v1.4.2 defines a peer-to-peer protocol. It contains no specification for how a node
registers with a central directory, how clients query it, or how liveness is maintained.
This document fills that gap.

IICP-DIR is defined as an **IICP SUB_PROTOCOL binding** (per ADR-009), not as new base opcodes.
In Phase 1 the protocol is carried over REST/HTTPS. Phase 2 wraps the same semantics inside
IICP `SUB_PROTOCOL` payloads over an established IICP session.

---

## 2. Protocol Roles

| Role | Description |
|------|-------------|
| **Directory** | Central authority. Accepts REGISTER and HEARTBEAT; answers QUERY with NODELIST. |
| **Provider Node** | Sends REGISTER on startup, periodic HEARTBEAT during operation. |
| **Client** | Sends QUERY; receives NODELIST; selects a node; sends CALL directly to the node. |

---

## 3. Message Types

### 3.1 REGISTER (Node → Directory)

Registers a node's identity, capabilities, and resource limits.

```json
{
  "message_type": "REGISTER",
  "node_id": "uuid-v4",
  "endpoint": "https://node.example.com",
  "region": "eu-central",
  "capabilities": [
    {
      "intent": "urn:iicp:intent:llm:chat:v1",
      "models": ["llama3", "mistral"],
      "max_tokens": 8192
    }
  ],
  "limits": {
    "max_concurrent": 4,
    "tokens_per_min": 20000
  },
  "availability": [
    { "start": "00:00", "end": "08:00", "share": 0.8 }
  ]
}
```

**Required fields**: `endpoint`, `region`, `capabilities[].intent`, `limits.max_concurrent`  
**Optional**: `node_id` (directory assigns if absent), `availability`, `limits.tokens_per_min`

**Response (ACK)**:

```json
{
  "message_type": "ACK",
  "node_id": "uuid-v4",
  "node_token": "opaque-32-byte-hex",
  "expires_at": null,
  "directory": "https://iicp.network"
}
```

`node_token` is returned once in plaintext; stored hashed (bcrypt) by the directory.

**Invariants**:
- Directory MUST perform a liveness check (`GET {endpoint}/iicp/health`) before issuing a token. [→ DIR-REG-04]
- Directory MUST rate-limit: 10 REGISTER requests per minute per source IP. [→ DIR-RL-01]

---

### 3.2 HEARTBEAT (Node → Directory)

Periodic liveness signal. Absence for > 90 seconds marks the node inactive.

```json
{
  "message_type": "HEARTBEAT",
  "node_id": "uuid-v4",
  "load": 0.35,
  "active_jobs": 1,
  "available": true,
  "metrics": {
    "tasks_success": 42,
    "tasks_failed": 1,
    "avg_latency_ms": 320.0
  }
}
```

Authorization: `Bearer <node_token>` header REQUIRED.

**Response (PONG)**:

```json
{ "ok": true, "next_heartbeat_ms": 30000 }
```

**Timing rules**:
- Node SHOULD send every 30 seconds.
- Directory marks inactive after 90 seconds without a valid HEARTBEAT.

---

### 3.3 QUERY (Client → Directory)

Requests a scored list of nodes matching an intent.

```
GET /v1/discover
  ?intent=urn:iicp:intent:llm:chat:v1
  &qos=interactive
  &region=eu-central
  &limit=10
```

| Parameter | Required | Notes |
|-----------|---------|-------|
| `intent` | MUST | Full intent URN |
| `qos` | SHOULD | `interactive` \| `batch` \| `best-effort` |
| `region` | MAY | Preference, not exclusion |
| `limit` | MAY | Default 10, max 50 |

---

### 3.4 NODELIST (Directory → Client)

```json
{
  "nodes": [
    {
      "node_id": "uuid",
      "endpoint": "https://node1.example.com",
      "region": "eu-central",
      "score": 0.91,
      "available": true,
      "load": 0.2,
      "active_jobs": 1,
      "max_concurrent": 4,
      "reputation_score": 0.87,
      "latency_estimate_ms": 120
    }
  ],
  "count": 1,
  "query_ms": 8
}
```

Only nodes with `available = true` AND `last_seen` within 90s are returned.
Score computed per ADR-008. Nodes with score < 0.1 are excluded.

---

### 3.5 BOOTSTRAP (Node → Directory)

Returns a seed peer list for mesh bootstrapping (Phase 2).

```
GET /v1/bootstrap?limit=5
```

Response: same structure as NODELIST, limited to `limit` healthy nodes.

---

### 3.6 PEER_EXCHANGE (Node → Node)

**Phase**: 2+ (not required for Phase 1 conformance — see `@phase2` mark in conformance suite)

Peer gossip — exchange known peer lists between nodes to bootstrap mesh connectivity without directory dependency. Each node maintains a local peer cache and periodically synchronises it with a random selection of known peers.

#### Request

```
POST /v1/peers
Authorization: Bearer <node_token>
X-IICP-Signature: <hmac-sha256-hex>
Content-Type: application/json
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `sender_id` | UUID-v4 | MUST | `node_id` of the sending node |
| `known_peers` | string[] | MUST | List of `node_id` UUIDs the sender already knows |
| `timestamp_ms` | integer | MUST | Unix epoch milliseconds — used for replay detection |
| `ttl_s` | integer | SHOULD | Sender's suggested peer cache TTL; receiver MAY ignore |

#### Response (200 OK)

Returns peer entries the receiver knows that the sender did not list in `known_peers`:

```json
{
  "new_peers": [
    {
      "node_id": "uuid",
      "endpoint": "https://node.example.com",
      "region": "eu-central",
      "last_seen_ms": 1715644800000
    }
  ],
  "receiver_id": "uuid"
}
```

Returns an empty `new_peers` array when the receiver has no peers unknown to the sender.

#### MUST requirements [→ DIR-HB-05]

- Receiver MUST validate `Authorization: Bearer <node_token>` on every PEER_EXCHANGE request. Invalid or absent token → 401.
- Receiver MUST verify `X-IICP-Signature` (HMAC-SHA256 of request body keyed with node_token). Invalid signature → 403.
- Receiver MUST reject replayed signatures: if the same HMAC has been seen within the last 5 minutes → 409. [→ SEC-NONCE-01]
- `timestamp_ms` MUST be within ±60 seconds of receiver's wall clock. Stale request → 422.

#### SHOULD requirements

- Senders SHOULD NOT gossip to the same peer more than once per 30 seconds.
- Receivers SHOULD limit the response list to 20 peers (prioritise highest-scored peers).
- Receivers SHOULD exclude nodes with `last_seen_ms` older than 90 seconds from their response.

#### Merge semantics

Upon receiving `new_peers`, the receiver SHOULD:
1. Add all returned entries to its local peer cache.
2. Not remove existing cache entries based on this response alone.
3. Expire entries whose `last_seen_ms` exceeds the liveness window (90s default).

#### Error codes

| Code | HTTP | Meaning |
|------|------|---------|
| `unauthorized` | 401 | Missing or invalid `node_token` |
| `forbidden` | 403 | Invalid HMAC signature |
| `conflict` | 409 | Replayed HMAC nonce |
| `validation_error` | 422 | Missing required field or stale `timestamp_ms` |
| `rate_limited` | 429 | Gossip rate exceeded (> 1 per 30s to this peer) |

---

## 4. Phase Mapping

| Phase | Transport | Auth |
|-------|-----------|------|
| 1 | REST/HTTPS | Bearer node_token |
| 2 | IICP SUB_PROTOCOL session | JWT (HS256, 1h TTL) |
| 3 | IICP SUB_PROTOCOL + DID session | W3C DID, signed requests |

---

## 5. Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `unauthorized` | 401 | Missing or invalid node_token |
| `not_found` | 404 | node_id not registered |
| `rate_limited` | 429 | Registration rate limit exceeded |
| `liveness_failed` | 422 | Endpoint did not respond to health check |
| `validation_error` | 422 | Required field missing or invalid |

---

## 6. Security Requirements

- TLS 1.3 MUST be enforced on all IICP-DIR endpoints. [→ SEC-TLS-01]
- REGISTER MUST be rate-limited (10/min/IP). [→ DIR-RL-01]
- node_token MUST be 32+ bytes cryptographically random. [→ DIR-REG-05]
- node_token MUST be stored hashed (bcrypt) by the directory. [→ DIR-REG-07]
- HEARTBEAT MUST validate node_token on every request. [→ DIR-HB-02]
- PEER_EXCHANGE MUST validate node_token on every request. [→ DIR-HB-05, Phase 2]
- PEER_EXCHANGE SHOULD include `X-IICP-Signature` (HMAC-SHA256) for replay protection.

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.0 | 2026-05-14 | Initial draft — fills SPEC_ANALYSIS.md GAP-1; REGISTER, HEARTBEAT, QUERY, NODELIST, BOOTSTRAP, PEER_EXCHANGE message types |
| 0.1.1 | 2026-05-15 | Added Changelog section (A6 spec cleanup) |

---

## Sign-off

**Protocol Steward**: IICP-DIR fills GAP-1 from SPEC_ANALYSIS.md. SUB_PROTOCOL binding
keeps core opcode table stable per ADR-009. Phase 1 REST form is a valid stepping stone.
Closes GitHub issue #14 (draft). ✓
