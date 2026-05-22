# S.13 — IICP Federated Directory Protocol

**Version**: 0.1.0 (Draft)  
**Date**: 2026-05-15  
**Status**: draft  
**Authority**: Federation Coordinator + Protocol Steward  
**Linked ADR**: ADR-013 (Federated Control Plane — Vision)  
**Prerequisite**: Phase 5 complete; ADR-013 advanced to Proposed  
**Relation to**: iicp-dir.md §3.7 (event log wire schema); BOUNDED_CONTEXTS.md BC-8

---

## 1. Purpose

IICP-DIR (iicp-dir.md) defines a single authoritative directory. This spec defines how multiple directory instances federate — how a **Genesis Seed** emits signed state events, how **Replica Directories** consume and verify them, and how **clients** are redirected between healthy instances.

The protocol preserves the core IICP rules: task payloads never touch any directory, and scores are computed server-side independently by each directory instance. Federation adds resilience and sovereignty without compromising these invariants.

---

## 2. Roles

| Role | Description |
|------|-------------|
| **Genesis Seed** | `iicp.network` — the root trust anchor. Emits signed events. Manages the Genesis DID. |
| **Replica Directory** | Operator-run instance that subscribes to the Genesis Seed event stream and maintains a locally consistent state. |
| **Light Client** | A proxy or SDK that caches a local discovery view and handles `307` redirects transparently. |

---

## 3. Trust Model

Trust is established through a DID document chain rooted at the Genesis Seed:

```
did:web:iicp.network  →  Genesis Seed signing key (Ed25519)
                      →  All events signed by this key
did:web:replica.example.com  →  Replica DID (operator-controlled)
                              →  Replica trust level declared in Genesis Seed's trusted-replicas registry
```

**Trust tiers**:

| Tier | Criteria | Discovery weight adjustment |
|------|----------|-----------------------------|
| `high` | Replica operated by Genesis Seed team or formally audited | None — full score parity |
| `medium` | Operator has ≥ 30-day uptime history; event lag < 60s median | Score × 0.95 |
| `low` | New or unaudited replica | Score × 0.85; client SHOULD prefer Genesis Seed when available |

---

## 4. Genesis Seed DID Document

The Genesis Seed publishes a W3C DID document at:
```
GET https://iicp.network/.well-known/did.json
```

```json
{
  "@context": ["https://www.w3.org/ns/did/v1"],
  "id": "did:web:iicp.network",
  "verificationMethod": [{
    "id": "did:web:iicp.network#key-1",
    "type": "JsonWebKey2020",
    "controller": "did:web:iicp.network",
    "publicKeyJwk": {
      "kty": "OKP",
      "crv": "Ed25519",
      "x": "<base64url-encoded-public-key>"
    }
  }],
  "assertionMethod": ["did:web:iicp.network#key-1"],
  "service": [{
    "id": "did:web:iicp.network#event-log",
    "type": "IicpEventLog",
    "serviceEndpoint": "https://iicp.network/v1/events"
  }, {
    "id": "did:web:iicp.network#trusted-replicas",
    "type": "IicpTrustedReplicas",
    "serviceEndpoint": "https://iicp.network/.well-known/iicp-replicas.json"
  }]
}
```

**Key rotation**: Genesis Seed key rotation requires publishing a new DID document version with `previousKey` reference. Replicas MUST re-verify their event history on key rotation.

---

## 5. Event Log Protocol

### 5.1 Event Envelope

(Normative text — see also iicp-dir.md §3.7 for the original draft)

```json
{
  "event_id": "uuid-v4",
  "event_type": "REGISTER | HEARTBEAT | SCORE_UPDATE | REPUTATION_UPDATE | CREDIT_AWARD | DEREGISTER",
  "seq": 1042,
  "ts_ms": 1715644800000,
  "payload": { "...event-specific fields..." },
  "sig": "base64url-ed25519-signature",
  "signer_did": "did:web:iicp.network"
}
```

**Signature input**: `Ed25519Sign(key, SHA256(event_id + ":" + event_type + ":" + seq + ":" + ts_ms + ":" + SHA256_hex(canonical_json(payload))))`

`canonical_json` = RFC 8785 (JSON Canonicalization Scheme) — deterministic, no whitespace variation.

### 5.2 Event Stream API

```
GET /v1/events?since_seq=<N>&limit=<M>
Authorization: Bearer <replica_token>
```

| Parameter | Required | Default | Notes |
|-----------|---------|---------|-------|
| `since_seq` | MAY | 0 | Return events with `seq > since_seq` |
| `limit` | MAY | 100 | Max events per page. Hard cap: 1000 |
| `event_types` | MAY | all | Comma-separated filter: `REGISTER,HEARTBEAT` |

**Response**:
```json
{
  "events": [ { "...event_envelope..." } ],
  "next_seq": 1043,
  "genesis_hash": "sha256-hex-of-seq-0-event-payload",
  "replica_lag_ms": 0
}
```

`genesis_hash` is immutable — any replica can verify it against its own seq-0 event.  
`replica_lag_ms` is the milliseconds between the latest event's `ts_ms` and the server's wall clock.

### 5.3 Replica Sync Lifecycle

```
1. Bootstrap:   GET /v1/events?since_seq=0           (full replay from genesis)
2. Incremental: GET /v1/events?since_seq=<last_known> (poll every 30s or on push notification)
3. Verify:      For each event: verify sig, verify seq monotonicity, verify signer_did
4. Apply:       Update local state: upsert Node, update score/reputation/credits, delete on DEREGISTER
```

**Error handling**:
- `seq` gap (non-monotonic): emit `IICP-E014`, halt sync, re-fetch from `since_seq = last_valid_seq`
- Signature invalid: emit `IICP-E013`, discard event, alert operator
- Replica lag > 5 minutes: replica MUST NOT serve discovery results; return `503` with `Retry-After`

### 5.4 Event Payload Schemas (Normative)

Replicas MUST consume these payloads to maintain locally consistent node state.

**REGISTER** — emitted on node registration or identity recovery:
```json
{
  "endpoint": "https://node.example.com",
  "region": "eu-central",
  "cip_conformance_level": "CIP-None | CIP-Provider | CIP-Full",
  "cip_policy": {
    "allow_remote_inference": false,
    "allow_tool_execution": false,
    "allow_file_access": false
  },
  "pricing": {
    "credit_cost_multiplier": 1.0,
    "pricing_model": "per_token",
    "attested": false
  }
}
```

**HEARTBEAT** — emitted on every heartbeat; includes reputation for CIP-Full routing:
```json
{
  "load": 0.42,
  "active_jobs": 2,
  "available": true,
  "reputation_score": 0.85
}
```

**REPUTATION_UPDATE** — two sources; replicas MUST process both:
- `source = "heartbeat_metrics"` — adapter self-reported task outcomes:
```json
{
  "source": "heartbeat_metrics",
  "tasks_success": 5,
  "tasks_failed": 1,
  "avg_latency_ms": 120.0,
  "reputation_score": 0.82
}
```
- `source = "proxy_telemetry"` — externally observed (from `SCORE_UPDATE` events):
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

**CREDIT_AWARD** — emitted on successful CIPWorkerReceipt credit award:
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

**DEREGISTER** — emitted before node deletion:
```json
{
  "endpoint": "https://node.example.com",
  "region": "eu-central"
}
```

---

## 6. Federated Redirect Protocol

When a Genesis Seed or replica is under load, it redirects clients:

### 6.1 Redirect Response

```http
HTTP/1.1 307 Temporary Redirect
Location: https://dir2.example.com/v1/discover?intent=urn:iicp:intent:llm:chat:v1&region=eu
X-IICP-Seed-Redirect: true
X-IICP-Replica-Trust: high | medium | low
X-IICP-Redirect-Reason: load | maintenance | geographic
Retry-After: 5
```

### 6.2 Client Handling (MUST requirements)

- Clients MUST follow `307` transparently and repeat the original request at `Location`. [→ DIR-FED-05]
- Clients MUST cache the redirected host for the duration of `Retry-After` (default: 5 seconds if header absent).
- Clients MUST NOT follow more than 3 consecutive redirects (prevents redirect loops). [→ DIR-FED-06]
- Clients SHOULD prefer the Genesis Seed when `X-IICP-Replica-Trust` is `low`.
- Clients MUST NOT cache `307` responses beyond `Retry-After`; the Genesis Seed is always the preferred endpoint.

### 6.3 Load Shedding Trigger

The Genesis Seed SHOULD redirect when:
- P95 request latency for `GET /v1/discover` exceeds 200ms (2× target SLO)
- Active request queue depth > 50

Configuration: `IICP_REDIRECT_LATENCY_MS_THRESHOLD=200` + `IICP_REDIRECT_QUEUE_DEPTH=50` in directory config.

---

## 7. Replica Onboarding

A new replica operator:

1. **Register**: POST to Genesis Seed's `GET /.well-known/iicp-replicas.json` governance process (off-protocol — currently manual; Phase 6 will define a structured process)
2. **Obtain replica_token**: Genesis Seed issues a `replica_token` (scoped JWT with `role: replica`) for `GET /v1/events` access
3. **Bootstrap**: Replay all events from `since_seq=0`
4. **Declare**: Publish own DID document at `https://<replica-domain>/.well-known/did.json`
5. **Advertise**: Request inclusion in `trusted-replicas.json` at trust tier `low`; trust tier upgrades over time via uptime + audit

---

## 8. Conformance Requirements

| ID | Requirement | Who |
|----|------------|-----|
| DIR-FED-01 | Replicas MUST verify Ed25519 sig for every event before applying | Replica |
| DIR-FED-02 | Replicas MUST reject events with non-monotonic `seq` | Replica |
| DIR-FED-03 | Replicas MUST verify `signer_did` resolves to Genesis Seed DID | Replica |
| DIR-FED-04 | Replicas MUST NOT trust events without valid Genesis Seed signature | Replica |
| DIR-FED-05 | Clients MUST follow `307` transparently | Client/Proxy |
| DIR-FED-06 | Clients MUST NOT follow > 3 consecutive redirects | Client/Proxy |
| DIR-FED-07 | Genesis Seed MUST include `genesis_hash` in every `/v1/events` response | Genesis Seed |
| DIR-FED-08 | Replicas with lag > 5 min MUST NOT serve discovery results | Replica |

---

## 9. Phase Readiness

| Component | Change required |
|-----------|----------------|
| Directory (PHP) | Add EventLogEmitter service; emit signed events on every state mutation; expose `GET /v1/events`; publish `/.well-known/did.json` |
| Proxy | Handle `307` redirect transparently; cache redirected host for `Retry-After` duration |
| Rust node | Event log signature verification on bootstrap |
| SDK | `IicpClient` follows `307`; tracks replica trust tier for scoring hints |

**CIP-Full prerequisite**: Replica directories that serve CIP-enabled nodes MUST propagate `pricing`, `cip_conformance_level`, and `cip_policy` fields in every emitted `NODE_REGISTERED` and `HEARTBEAT` event. Replicas that omit these fields MUST NOT be used by `CIP-Full` consumers for cooperative worker discovery — clients SHOULD prefer Genesis Seed discovery for CIP routing until replica event schema compliance is verified.

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.2.0 | 2026-05-17 | §9 Phase Readiness: added CIP-Full prerequisite — replicas MUST propagate pricing, cip_conformance_level, and cip_policy fields in events for CIP-Full consumer compatibility. |
| 0.1.0 | 2026-05-15 | Initial draft — event log wire format, DID document, replica sync lifecycle, redirect protocol, 8 conformance requirements (DIR-FED-01–08) |
