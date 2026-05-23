# IICP-DIR — Directory Sub-Protocol Specification

**Version**: 0.6.1  
**Date**: 2026-05-20  
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
{ "ok": true, "next_heartbeat_ms": 30000, "reputation_score": 0.82 }
```

`reputation_score` — the node's current reputation [0.0, 1.0] as stored in the directory. Allows operators to observe their reputation on every heartbeat cycle. Default 0.5 for nodes with no history.

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
| `min_reputation` | MAY | Float [0.0–1.0]; exclude nodes below threshold |
| `max_multiplier` | MAY | Float; exclude nodes whose `credit_cost_multiplier` exceeds value |
| `min_quality_score` | MAY | Float [0.0–1.0]; alias for minimum scoring threshold (ADR-019) |
| `cip_capable` | MAY | Boolean; if `true`, directory MUST return only nodes with `allow_remote_inference=true` (i.e. `cip_conformance_level` ≠ `CIP-None`). CIP coordinators SHOULD pass `cip_capable=true` to avoid client-side filtering (S.12 §5.2). |

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
      "latency_estimate_ms": 120,
      "probation": false,
      "completed_tasks_count": 1247,
      "cip_policy": {
        "allow_remote_inference": true,
        "allow_tool_execution": false,
        "allow_file_access": false,
        "pricing_credits_per_1000": 2.5000
      },
      "pricing": {
        "credit_cost_multiplier": 1.5,
        "pricing_model": "per_token",
        "currency": "credits",
        "effective_from": null,
        "effective_until": null,
        "attested": true
      },
      "cip_conformance_level": "CIP-Provider"
    }
  ],
  "count": 1,
  "query_ms": 8
}
```

**Field semantics:**

| Field | Type | Notes |
|-------|------|-------|
| `reputation_score` | float [0.0, 1.0] | Delta-based EMA per spec §11.2 (ADR-023). Default 0.5 for nodes with no heartbeat history. |
| `probation` | boolean | `true` when `completed_tasks_count < 100`. Nodes in probation are excluded from `?qos=interactive` and `?qos=realtime` queries. |
| `completed_tasks_count` | integer | Cumulative count of successfully completed tasks (heartbeat-reported). Used for probation tier gating (spec §11.3). |
| `cip_policy` | object | Provider CIP capability declaration (CIP-D1, spec §2.1.1). Present on all nodes; fields default to `false`/`null` if not declared at registration. |
| `cip_policy.allow_remote_inference` | boolean | Provider accepts CIP remote inference tasks. |
| `cip_policy.allow_tool_execution` | boolean | Provider allows tool-executing tasks. |
| `cip_policy.allow_file_access` | boolean | Provider allows file-access tasks. |
| `cip_policy.pricing_credits_per_1000` | decimal\|null | Price in credits per 1000 tokens. `null` = free/unset. DEPRECATED — use `pricing.credit_cost_multiplier` (ADR-019). |
| `pricing` | object\|null | ADR-019 declarative pricing block. `null` = node has no declared pricing. |
| `pricing.credit_cost_multiplier` | float | Applied to base rate: `credits = ceil(tokens/1000) × multiplier`. Default 1.0. |
| `pricing.pricing_model` | string | Only `"per_token"` defined in v1; others reserved. |
| `pricing.currency` | string | Always `"credits"` in v1. |
| `pricing.effective_from` | ISO-8601\|null | null = immediately effective. |
| `pricing.effective_until` | ISO-8601\|null | null = no expiry. |
| `pricing.attested` | bool | `true` if `declaration_signature` was verified at last registration (ADR-019 §5.1). |
| `cip_conformance_level` | string | One of `"CIP-None"`, `"CIP-Consumer"`, `"CIP-Provider"`, `"CIP-Full"`. `"CIP-None"` means the node has not opted into any CIP role (equivalent to not declared). Per spec §5.2. |

Only nodes with `available = true` AND `last_seen` within 90s are returned.
Score computed per ADR-008. Nodes with score < 0.1 are excluded.

**Consensus mode discovery** (Phase 5E — `constraints.consensus` ≠ `none`):  
When a proxy uses consensus mode (iicp-core.md §3.3), it MUST discover N workers
via N separate `/v1/discover` requests (or one request with `limit=N`). The proxy
MUST filter for `cip_policy.allow_remote_inference = true` on all N selected workers.
The directory is not aware of consensus mode; worker selection is proxy-side logic.

**QoS probation filter** (applied server-side when `?qos=` is specified):

| `?qos=` | Filter condition |
|---------|-----------------|
| `batch`, `best-effort` | No probation filter |
| `interactive` | `completed_tasks_count ≥ 100` |
| `realtime` | `completed_tasks_count ≥ 1000` AND `reputation_score ≥ 0.8` |

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
| 6 | REST/HTTPS + event stream | DID (directory operator), replica sync |

---

### 3.7 EVENT_LOG (Directory → Replica) — Phase 6

**Phase**: 6 (Federated Control Plane — ADR-013)  
**Status**: Spec draft — not implemented  
**Normative reference**: `spec/iicp-federated-directory.md` (S.13) — full protocol spec including trust model, DID document structure, replica sync lifecycle, redirect semantics, and 8 conformance requirements (DIR-FED-01–08). This section is the wire schema reference; S.13 is the authoritative normative text.

The event log enables a replica directory to maintain a consistent, cryptographically verifiable view of the Genesis Seed's state without a shared database. All state mutations in the directory emit a signed event; replicas consume events via `GET /v1/events` and replay them to reconstruct current state.

#### Event Envelope

All events share a common envelope:

```json
{
  "event_id": "uuid-v4",
  "event_type": "REGISTER | HEARTBEAT | SCORE_UPDATE | REPUTATION_UPDATE | CREDIT_AWARD | DEREGISTER",
  "seq": 1042,
  "ts_ms": 1715644800000,
  "payload": { ... },
  "sig": "base64url-ed25519-signature",
  "signer_did": "did:web:iicp.network"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `event_id` | UUID-v4 | MUST | Unique event identifier |
| `event_type` | enum | MUST | One of the six event types |
| `seq` | integer | MUST | Monotonically increasing per-directory sequence number |
| `ts_ms` | integer | MUST | Unix epoch milliseconds — wall clock at emission time |
| `payload` | object | MUST | Event-type-specific data (see below) |
| `sig` | base64url | MUST | Ed25519 signature over `event_id + event_type + seq + ts_ms + sha256(payload)` |
| `signer_did` | string | MUST | DID of the signing directory operator |

#### Event Types and Payloads

**REGISTER** — node joins the network:
```json
{
  "node_id": "uuid",
  "endpoint": "https://node.example.com",
  "region": "eu-central",
  "capabilities": [{ "intent": "urn:iicp:intent:llm:chat:v1", "models": ["llama3"] }],
  "limits": { "max_concurrent": 4 }
}
```

**HEARTBEAT** — node liveness update:
```json
{
  "node_id": "uuid",
  "load": 0.35,
  "active_jobs": 1,
  "available": true,
  "ts_ms": 1715644800000
}
```

**SCORE_UPDATE** — computed score changed (after each discover call):
```json
{
  "node_id": "uuid",
  "score": 0.87,
  "dimensions": { "avail": 0.35, "load": 0.24, "cap": 0.14, "region": 0.09, "rep": 0.05 }
}
```

**REPUTATION_UPDATE** — reputation score changed. Two source variants:

*Source: `heartbeat_metrics`* — adapter self-reported task outcomes (emitted by directory on HEARTBEAT when `tasks_success` or `tasks_failed` are non-zero):
```json
{
  "source": "heartbeat_metrics",
  "tasks_success": 5,
  "tasks_failed": 1,
  "avg_latency_ms": 120.0,
  "reputation_score": 0.82
}
```

*Source: `proxy_telemetry`* — externally observed latency from SCORE_UPDATE pipeline:
```json
{
  "source": "proxy_telemetry",
  "proxy_node_id": "uuid",
  "latency_ms_observed": 210.5,
  "observed_latency_ms": 198.3,
  "status": "success | failure | timeout",
  "quorum_met": true,
  "distinct_proxies": 4
}
```

**CREDIT_AWARD** — credits issued to a node after CIPWorkerReceipt validation:
```json
{
  "task_id": "task-uuid-or-string",
  "tokens_used": 500,
  "amount": 0.5,
  "new_balance": 12.75,
  "cip_parent_task_id": "optional-string-or-null",
  "cip_session_key": "optional-string-or-null"
}
```

**DEREGISTER** — node explicitly deregistered or expired:
```json
{
  "node_id": "uuid",
  "reason": "explicit | expired | liveness_failure"
}
```

#### Event Stream API

```
GET /v1/events?since_seq=<N>&limit=100
Authorization: Bearer <replica_token>
```

| Parameter | Required | Notes |
|-----------|---------|-------|
| `since_seq` | MAY | Return events with `seq > since_seq`. Omit to start from genesis (seq=0). |
| `limit` | MAY | Max events per response. Default 100, max 1000. |

Response:
```json
{
  "events": [ { ...event_envelope... }, ... ],
  "next_seq": 1043,
  "genesis_hash": "sha256-of-seq-0-event"
}
```

`genesis_hash` is constant — any replica can verify it against the Genesis Seed's DID document.

#### Replica MUST requirements

- Replicas MUST verify `sig` for every event before applying to local state. [→ DIR-FED-01]
- Replicas MUST reject events with non-monotonic `seq`. [→ DIR-FED-02]
- Replicas MUST verify `signer_did` resolves to the Genesis Seed's DID document. [→ DIR-FED-03]
- Replicas MUST NOT trust events from peers unless those events carry a valid `sig` from the Genesis Seed. [→ DIR-FED-04]

#### 307 Redirect — Federated Redirection

When a Genesis Seed or replica is under load, it MAY redirect clients:

```http
HTTP/1.1 307 Temporary Redirect
Location: https://dir2.example.com/v1/discover?intent=...
X-IICP-Seed-Redirect: true
X-IICP-Replica-Trust: high | medium | low
Retry-After: 5
```

Clients and proxies MUST follow `307` transparently and update their directory cache TTL for the redirected host. [→ DIR-FED-05]

---

### 3.8 METRICS (iicp-node → Scraper) — Phase 4

**Phase**: 4 (Rust Node Runtime)  
**Status**: Implemented in `iicp-node/src/telemetry/mod.rs`

The iicp-node exposes Prometheus-compatible metrics at `GET /metrics` in text exposition format (MIME: `text/plain; version=0.0.4`). This endpoint is public (no auth required) to allow Prometheus scraping.

**ADR-014 mandatory metrics**:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `iicp_tasks_total` | counter | `status`, `intent`, `qos` | Total tasks processed |
| `iicp_task_latency_ms` | histogram | `intent`, `qos` | End-to-end task latency (ms) |
| `iicp_tokens_used_total` | counter | `intent` | Inference tokens consumed |
| `iicp_peers_active` | gauge | — | Current count of known live peers |
| `iicp_heartbeat_failures_total` | counter | `reason` | Cumulative heartbeat failures |

**Histogram buckets** (ms): 10, 50, 100, 250, 500, 1000, 2500, 5000, 30000

**Conformance**: `test_rust_node_metrics_endpoint` (PH4-M6) verifies 200 response with mandatory metrics present.

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

## 7. Optional Extensions

Optional extensions are directory-layer additions that conformant directories MAY implement.
A directory that omits these extensions is fully IICP-DIR conformant (ADR-031).

### IICP-DIR-EXT-CREDITS: S-Credit Economy

Allows directory operators to run a peer credit economy where nodes earn credits by serving
tasks and spend credits to route. Implementing this extension is NOT required for core
IICP conformance.

**Endpoints (all require `Authorization: Bearer <node_token>`):**

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/credits/earn` | Award credits after validated CIPWorkerReceipt |
| `POST` | `/v1/credits/spend` | Deduct credits before routing (consumer-side) |
| `GET`  | `/v1/credits/supply` | Mint telemetry — total supply, burn rate, TTL expiry rate |

**Advertise support**: A directory that implements this extension SHOULD return
`"credits_extension": true` in `GET /api/v1/stats`. Nodes SHOULD check this field before
calling credit endpoints.

Full design: `research/credit-economy/09-scalability-safety-implementation-plan.md`  
Governing ADR: ADR-031  
Tracking: #302

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.0 | 2026-05-14 | Initial draft — fills SPEC_ANALYSIS.md GAP-1; REGISTER, HEARTBEAT, QUERY, NODELIST, BOOTSTRAP, PEER_EXCHANGE message types |
| 0.1.1 | 2026-05-15 | Added Changelog section (A6 spec cleanup) |
| 0.2.0 | 2026-05-17 | §3.4 NODELIST: added `probation`, `completed_tasks_count`, `cip_policy` fields + QoS probation filter table (ADR-023, CIP-D1, spec §11.3) |
| 0.3.0 | 2026-05-17 | §3.4 Consensus mode discovery note: proxy discovers N workers for consensus; directory unaware of consensus mode; cip_policy.allow_remote_inference filter requirement. |
| 0.6.1 | 2026-05-20 | §3.3 DISCOVER: `cip_capable` query parameter added — boolean, server-side filter for CIP-Provider nodes (`allow_remote_inference=true`). Existing params `min_reputation`, `max_multiplier`, `min_quality_score` documented in table. CIP coordinators SHOULD pass `cip_capable=true` to avoid client-side filtering (S.12 §5.2). |
| 0.6.0 | 2026-05-20 | §3.4 NODELIST: `cip_conformance_level` type changed from `string\|null` to `string`; `"CIP-None"` added as explicit non-CIP value (consistent with implementation in RegisterController + NodeScorer). S.12 §5.2 updated to include `CIP-None` in profile table. |
| 0.5.0 | 2026-05-19 | §3.2 HEARTBEAT PONG: added `reputation_score` field (operator feedback on current standing). §3.7 REPUTATION_UPDATE event: dual-source schemas (`heartbeat_metrics` from HEARTBEAT pipeline, `proxy_telemetry` from SCORE_UPDATE pipeline). §3.7 CREDIT_AWARD event: corrected to actual CIPWorkerReceipt fields (`task_id`, `tokens_used`, `amount`, `new_balance`, `cip_parent_task_id`, `cip_session_key`). |
| 0.4.0 | 2026-05-17 | §3.4 NODELIST: added ADR-019 `pricing` block (credit_cost_multiplier, pricing_model, currency, effective_from, effective_until, attested); `cip_conformance_level` field (CIP-Consumer/Provider/Full per S.12 §5.2); `cip_policy.pricing_credits_per_1000` DEPRECATED in favor of pricing.credit_cost_multiplier. |

---

## Sign-off

**Protocol Steward**: IICP-DIR fills GAP-1 from SPEC_ANALYSIS.md. SUB_PROTOCOL binding
keeps core opcode table stable per ADR-009. Phase 1 REST form is a valid stepping stone.
Closes GitHub issue #14 (draft). ✓
