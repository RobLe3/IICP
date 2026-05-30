# S.13 — IICP Federated Directory Protocol

**Version**: 0.3.6 (Draft)  
**Date**: 2026-05-25  
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

### 3.2 Conflict resolution (v0.3.0 — Normative)

When a proxy or SDK receives node state from multiple sources within the
same query window, it MUST resolve conflicts in this strict precedence
order:

1. **Genesis Seed beats all replicas.** If the Genesis Seed reports node
   `N` as `available: false` and a replica reports `available: true`,
   the proxy MUST treat `N` as unavailable. The Seed is the canonical
   source for any field it returns.

2. **Among replicas: newer `seq` beats older.** If two replicas disagree
   on a field, the proxy MUST take the value from the replica whose
   latest event `seq` (returned in the `/v1/snapshot` response or
   `/v1/events` cursor) is higher. Trust tier (§3 table above) is a
   tie-breaker only when both replicas have identical `seq` — in that
   case, higher trust tier wins.

3. **Gossip-derived data is suggestion-only.** Any state learned via
   Phase 2 peer-exchange gossip MAY inform discovery heuristics but
   MUST NOT override a Seed or replica `/v1/snapshot` value for the
   same field on the same node. Gossip is conventionally annotated
   with `gossip_origin: <peer_id>` in proxy logs; receivers SHOULD
   discard gossip values older than 90 s (one heartbeat window).

4. **Field-level resolution, not row-level.** Conflicts MUST resolve
   per-field. If the Seed has fresher `load` data for node `N` but a
   replica has fresher `credit_balance`, the proxy MUST combine
   (Seed.load, Replica.credit_balance) — not pick one row wholesale.

**Why this ordering**: the Seed is the audit anchor (ADR-013); replicas
exist to absorb load + reduce latency, not to introduce trust drift.
Newer-seq-wins among replicas reflects the snapshot+event-tail model
(§5.5) — the replica with the highest seq has the most-recent state.
Trust tier as tie-breaker preserves the v0.1.0 trust-tier weighting
without overriding the more-fundamental seq-recency signal.

**Spec conformance**: a proxy that violates §3.2 ordering MAY produce
inconsistent discovery results across queries — caught by the
DIR-FED-TRUST-01 conformance probe (Phase 6 charter P6-4.3).

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
  "event_type": "REGISTER | DEREGISTER | CREDIT_AWARD | REPLICA_REGISTERED | REPUTATION_DECAY",
  "seq": 1042,
  "ts_ms": 1715644800000,
  "payload": { "...event-specific fields..." },
  "sig": "base64url-ed25519-signature",
  "signer_did": "did:web:iicp.network"
}
```

**Federated event type list (v0.3.0, Normative)**: the federated event log MUST carry
only **state-change** events whose information content is not derivable from the
canonical `nodes` row:

| Event type | Trigger | Rationale |
|---|---|---|
| `REGISTER` | node registers or re-identifies | new state, must federate |
| `DEREGISTER` | node leaves cleanly | state removal, must federate |
| `CREDIT_AWARD` | CIP receipt processed | audit-load-bearing (HMAC-signed); must federate |
| `REPLICA_REGISTERED` | replica registers via §7.1 handshake | trust-chain event; must federate |
| `REPUTATION_DECAY` | automated hourly decay cron | distinguishable from task-driven updates; audit-load-bearing |
| `OPERATOR_OBSERVED` | seed observes a discrepancy between a node's self-reported claim and externally-observable signal (region vs IP geolocation, model declaration vs `/iicp/health` response, etc.) | audit-trail extension per W-033; replicas record but do not act |

**Event types removed in v0.3.0** (no longer federated): `HEARTBEAT`,
`SCORE_UPDATE`, `REPUTATION_UPDATE`. These were *state*, not state-change —
their information content is already on the canonical `nodes` row
(`last_seen`, `load`, `active_jobs`, `reputation_score`, `credit_balance`).
Replicas derive these signals from §5.5 snapshots, not from the event
stream. Removing them eliminates ~99% of event-log growth at any node
count (HEARTBEAT alone was 126k of 126k rows at 8 nodes during the
v0.2.0 era).

Implementations that previously consumed HEARTBEAT/SCORE_UPDATE/REPUTATION_UPDATE
events MUST switch to reading the canonical row via §5.5 snapshot. See
ADR-033 for the design rationale (ephemeral storage horizon ≤ 3×
heartbeat window; long-term observability moves to external telemetry).

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

### 5.3 Replica Sync Lifecycle (v0.3.0 — snapshot+event-tail)

```
1. Bootstrap:    GET /v1/snapshot                          (canonical state, one RTT)
2. Catch-up:     GET /v1/events?since_seq=<snapshot.seq>   (events that landed during bootstrap)
3. Verify:       For each event: verify sig, seq monotonicity, signer_did
4. Apply:        Update local state — for the event types in §5.1
5. Incremental:  Poll GET /v1/events?since_seq=<last_known> every 30s
```

The Genesis Seed MAY prune events older than 60 minutes (the federation
rolling window). Replicas that fall behind by more than the window
MUST re-bootstrap from §5.5 snapshot — they cannot replay from
`since_seq=0`. This is the "git clone + git pull" model: bounded
storage on the seed, fast bootstrap for new replicas, no genesis-replay
data accumulation.

**Error handling**:
- `seq` gap (non-monotonic): emit `IICP-E014`, halt sync, re-fetch from `since_seq = last_valid_seq`
- Signature invalid: emit `IICP-E013`, discard event, alert operator
- Replica lag > 5 minutes: replica MUST NOT serve discovery results; return `503` with `Retry-After`
- `since_seq` older than the seed's rolling window: server returns
  `IICP-E045` (snapshot_required) with hint to call `GET /v1/snapshot`

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

**OPERATOR_OBSERVED** — emitted when the genesis seed observes a
discrepancy between a node's self-reported claim and an externally-
verifiable signal. Replicas MUST record this event for the audit log
but MUST NOT mutate node state on its basis — the trust auditor on
the seed is the sole authority on score/tier impact. Added v0.3.5
per Phase 6 charter P6-2.2 + W-033 (null/self-reported field
manipulation).

```json
{
  "observation_type": "region_geolocation_mismatch | model_declaration_drift | private_ip_public_region | tls_downgrade | <other>",
  "observed_at": "2026-05-26T12:00:00Z",
  "evidence": {
    "claimed":  "eu-central",
    "observed": "private (RFC1918)",
    "source":   "NodeAddressObserver",
    "rule_id":  "IICP-SEC-GEO-01"
  },
  "severity": "info | low | medium | high",
  "note": "free-form human-readable summary, optional"
}
```

Field requirements: `observation_type` MUST be a stable string identifier
(future enumeration in §X); `observed_at` MUST be ISO 8601 UTC;
`evidence.source` MUST identify the in-directory subsystem that produced
the observation; `severity` defaults to `info`. The `node_id` field on
the outer event row identifies which node the observation pertains to.

### 5.5 Snapshot Endpoint (Normative, v0.3.0)

`GET /v1/snapshot` returns the canonical current state of all registered
nodes — a one-RTT bootstrap that replaces genesis-to-now event replay.
Combined with §5.3 catch-up, this is the "git clone + git pull" model
that lets replica storage stay bounded forever (independent of node-count
× time).

**Endpoint**: `GET /v1/snapshot` (Genesis Seed only)

**Authentication**: Bearer `replica_token` (issued by §7.1 handshake)

**Response** (200, JSON):
```json
{
  "schema_version": "v0.3.0",
  "snapshot_seq": 42891,
  "snapshot_ts_ms": 1715644800000,
  "genesis_hash": "<hex>",
  "nodes": [
    {
      "node_id": "uuid",
      "endpoint": "https://...",
      "region": "eu-central",
      "load": 0.3,
      "active_jobs": 0,
      "available": true,
      "last_seen": "2026-05-25T19:30:24Z",
      "reputation_score": 0.51,
      "reputation_tier": "silver",
      "credit_balance": 0.0000,
      "cip_policy": { "...as in /v1/discover..." },
      "pricing": { "...as in /v1/discover..." }
    }
  ],
  "capabilities": [
    { "node_id": "uuid", "intent": "urn:...", "models": [...], "max_tokens": 4096 }
  ]
}
```

**Normative requirements**:

- `snapshot_seq` is the highest `seq` value that has been emitted to the
  event log at the moment the snapshot was generated. Replicas MUST
  call `GET /v1/events?since_seq=<snapshot_seq>` immediately afterwards
  to catch events that landed during snapshot generation. The seed
  MUST NOT delete events with `seq > snapshot_seq` before serving the
  snapshot.
- `genesis_hash` MUST match the value surfaced by `GET /v1/events`
  (DIR-FED-07 parity) — pin-on-first-use to detect chain forks.
- The snapshot MUST be a consistent point-in-time view (single
  read transaction or equivalent).
- Response size at 1000 nodes is bounded ~2-5 MB; replicas MAY accept
  `Accept-Encoding: gzip`.
- The snapshot MUST be served over HTTPS with TLS ≥ 1.3 (replica_token
  is bearer auth).

**Rate limit**: 5 snapshot requests per replica per hour (bootstrap is
infrequent; abuse prevention).

**Errors** (422):

| Code | Meaning |
|---|---|
| `IICP-E045` | snapshot_required (returned by /v1/events when since_seq is older than the seed's rolling window) |
| `IICP-E046` | snapshot generation timed out (transient; retry after 30s) |
| `IICP-E047` | replica_mode_misconfigured (returned by a replica directory when `IICP_REPLICA_MODE=true` but `IICP_SEED_URL` is missing or non-https — replica cannot 307-redirect writes without a target). 503 status. |
| `IICP-E048` | replica_signing_misconfigured (returned by a replica directory when `IICP_REPLICA_MODE=true` but `IICP_REPLICA_ED25519_SECRET_KEY` is missing or wrong length — replica cannot sign discovery responses per §6.5). 503 status. |

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

### 6.2a Replica Write-Gate (Normative — DIR-FED-18)

A directory operating in replica mode MUST 307-redirect every unsafe HTTP
method (`POST`, `PUT`, `PATCH`, `DELETE`) back to the Genesis Seed. This
is the reciprocal of §6.1 (seed → replica for reads); together they
enforce the read/write split: replicas serve discovery, the seed owns
state. Token issuance, heartbeat ingestion, credit accounting, and event
emission MUST happen only on the seed.

```http
HTTP/1.1 307 Temporary Redirect
Location: https://iicp.network/v1/register
X-IICP-Replica-Redirect: true
X-IICP-Redirect-Reason: replica_mode
Retry-After: 0
```

A replica that has `IICP_REPLICA_MODE=true` but cannot determine its
seed URL (`IICP_SEED_URL` missing or non-https) MUST refuse writes with
`503 IICP-E047 replica_mode_misconfigured` — it must not silently apply
writes locally (would diverge from seed) and must not redirect to an
unverified target (would be an open-redirect vector).

### 6.3 Load Shedding Trigger

The Genesis Seed SHOULD redirect when:
- P95 request latency for `GET /v1/discover` exceeds 200ms (2× target SLO)
- Active request queue depth > 50

Configuration: `IICP_REDIRECT_LATENCY_MS_THRESHOLD=200` + `IICP_REDIRECT_QUEUE_DEPTH=50` in directory config.

### 6.4 Trusted-Replicas Registry (Normative — DIR-FED-19)

The genesis seed publishes the canonical list of trusted replicas at
`https://<seed>/.well-known/iicp-replicas.json`. Discovery clients SHOULD
fetch this list to obtain a bootstrap set of replicas they can use when
the seed is unreachable, and to rank replicas they receive in `307`
redirects.

**Schema** (v2 — added 2026-05-26 per P6-3.2):

```json
{
  "@context": "https://iicp.network/ns/replicas/v1",
  "schema_version": "2",
  "genesis_seed": "did:web:iicp.network",
  "version": "2",
  "updated_at": "YYYY-MM-DD",
  "replicas": [
    {
      "replica_id":     "rep-<32-hex>",
      "did":            "did:web:replica.example.com",
      "endpoint":       "https://replica.example.com",
      "trust_tier":     "low | medium | high",
      "registered_at":  "2026-05-26T12:00:00Z",
      "region_hint":    "eu-central",
      "tls_min_version": "1.3",
      "availability_window": "30d",
      "schema_compat":  ["v0.3.0", "v0.3.3"]
    }
  ]
}
```

**Field requirements**:

| Field | Required | Meaning |
|-------|----------|---------|
| `replica_id`        | MUST  | UUID issued by §7.1 handshake; persistent across re-registrations |
| `did`               | MUST  | Replica's did:web identifier (matches its `/.well-known/did.json`) |
| `endpoint`          | MUST  | https:// base URL (TLS ≥ 1.3) |
| `trust_tier`        | MUST  | One of `low`, `medium`, `high`; clients SHOULD prefer higher tiers |
| `registered_at`     | MUST  | ISO 8601 UTC timestamp of original §7.1 handshake |
| `region_hint`       | SHOULD| Geographic hint for client locality (e.g. `eu-central`, `us-west`) |
| `tls_min_version`   | SHOULD| Minimum TLS version the replica accepts |
| `availability_window` | MAY | Time window over which `trust_tier` was assessed (e.g. `30d`) |
| `schema_compat`     | MAY   | List of S.13 schema versions the replica's event-log understands |

**What this registry is NOT**: dynamic state (current `last_seen_at`,
`event_log_lag_ms`, current load) is NOT carried here. Clients that
need dynamic freshness MUST query `GET /api/v1/stats` on each candidate
replica. The registry carries pin-on-first-use static metadata only;
otherwise it would become a hot endpoint that defeats the
"clients-can-route-around-the-seed" design goal.

**Update cadence**: the seed operator updates this file when:
- A replica registers via §7.1 (new entry, `trust_tier: low`)
- A replica's trust tier changes (uptime audit / SA review)
- A replica is decommissioned (entry removed)

This is operator-driven, not automatic — automatic publication would
require the seed to expose write access to its public static files,
which is out of scope on shared hosting.

**Conformance**: DIR-FED-19 — Genesis Seed MUST serve a valid v2
schema document at `/.well-known/iicp-replicas.json`. Discovery clients
MAY use this registry for bootstrap-without-seed; if used, they MUST
validate every field against the schema before acting on entries.

### 6.5 Replica Response Signing (Normative — DIR-FED-20)

When a replica directory serves a discovery response (`GET /v1/discover`,
`GET /v1/node/{id}`, `GET /v1/bootstrap`), it MUST sign the response with
its own Ed25519 key and include the signature in the `X-IICP-Replica-Sig`
header. The Genesis Seed itself is NOT required to sign responses — clients
trust the seed's TLS certificate + DNS. Replicas are intermediaries; the
signature lets clients verify the response came from a registered, trusted
replica and was not tampered with by a transparent proxy.

**Header format**:

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-IICP-Replica-DID: did:web:replica.example.com
X-IICP-Replica-Sig: <hex-encoded Ed25519 sig of canonical signing input>
X-IICP-Snapshot-Seq: 42891
```

**Canonical signing input** (matches the seed-side event log signing pattern
in §3.4 for consistency):

```
SHA256_bin( method + ":" + path + ":" + query_canonical + ":" + snapshot_seq + ":" + SHA256_hex(response_body) )
```

Where:
- `method` is the HTTP method (uppercase)
- `path` is the request path (e.g. `/v1/discover`)
- `query_canonical` is the request query string with parameters sorted by
  name (URL-encoded, no leading `?`); empty string if no query
- `snapshot_seq` is the replica's current synced event-log seq (matches
  X-IICP-Snapshot-Seq); decimal integer as string
- `response_body` is the exact bytes the server sent in the response body

The signature is hex-encoded (128 chars) Ed25519 detached signature using
the replica's secret key. The corresponding public key is published in
the replica's DID document (`/.well-known/did.json`) and referenced from
the trusted-replicas registry (§6.4 `did` field).

**Client verification** (MUST):

1. Look up the redirect target's `did` in the trusted-replicas registry
   (§6.4). If absent, reject the response.
2. Fetch the replica's DID document; extract the first Ed25519 verification
   method's `publicKeyJwk.x` (base64url, 32 bytes raw).
3. Recompute the canonical signing input from request method/path/query +
   `X-IICP-Snapshot-Seq` header + the received response body.
4. Verify the hex-decoded signature against the input using the replica's
   public key. On verification failure, REJECT the response (do not use the
   nodes returned) and log `IICP-SEC-REPLICA-01`.

**Why client-side verification matters**: a replica with TLS misconfig, a
transparent corporate proxy on the client side, or a compromised CDN edge
could substitute response bytes. The replica sig is end-to-end (signed at
replica, verified at proxy) and bypasses all intermediaries.

**Backwards compatibility**: a discover response without `X-IICP-Replica-Sig`
or `X-IICP-Replica-DID` is treated as coming from a non-signing source
(typically the seed itself, or a pre-DIR-FED-20 replica). Proxies MAY
accept unsigned responses from sources NOT listed in the registry as
replicas (the seed), but MUST reject unsigned responses from any endpoint
that IS listed as a replica — registered replicas have a public key and
no reason to skip signing.

**Snapshot freshness check**: the `X-IICP-Snapshot-Seq` value MUST be
within `replica_lag_ms < 5min` of the seed's current seq (per DIR-FED-08).
Proxies SHOULD periodically check freshness by comparing against the seed's
`/v1/events` `next_seq`; replicas more than 5 minutes behind MUST be
treated as untrusted regardless of signature validity.

---

## 7. Replica Onboarding

A new replica operator follows the **registration handshake** in §7.1 (introduced
v0.2.0, iter-1347 per Phase 6 charter P6-1.1), then the bootstrap + advertise steps:

1. **Declare**: Publish own DID document at `https://<replica-domain>/.well-known/did.json` (W3C DID v1; Ed25519 verification method)
2. **Register** (§7.1): `POST /v1/replicas/register` — handshake; receive `replica_id` + `replica_token` + initial `since_seq` + `genesis_hash`
3. **Bootstrap**: Replay all events from `since_seq=0` (use the issued `replica_token` for `GET /v1/events`)
4. **Verify**: For each event: verify sig per DIR-FED-01..04
5. **Advertise**: Listed in `/.well-known/iicp-replicas.json` at trust tier `low` (default on first registration); trust tier upgrades over time via uptime + audit

### 7.1 Replica Registration Handshake (Normative, v0.2.0)

**Endpoint**: `POST /v1/replicas/register` (Genesis Seed only; replicas do NOT serve this endpoint)

**Authentication**: unauthenticated for the handshake itself — the Genesis Seed validates the replica's DID resolves and that its endpoint is reachable. Subsequent `/v1/events` access uses the `replica_token` returned by this handshake.

**Request body** (JSON):
```json
{
  "did":      "did:web:replica.example.com",
  "endpoint": "https://replica.example.com",
  "trust_tier_request": "low"
}
```

| Field | Type | Required | Constraint |
|---|---|---|---|
| `did` | string | MUST | Valid W3C DID; MUST resolve to a DID document at `https://<did-domain>/.well-known/did.json` containing an Ed25519 verification method |
| `endpoint` | string | MUST | HTTPS URL (TLS ≥ 1.3); MUST NOT use `http://` or private/loopback addresses (SSRF guard, IICP-E034 family) |
| `trust_tier_request` | string | SHOULD | One of `low` (default), `medium`, `high`; the Genesis Seed always issues `low` on first registration regardless of request |

**Genesis Seed validation sequence** (Normative MUST):

1. **DID resolution**: HTTP GET `https://<did-domain>/.well-known/did.json` over TLS ≥ 1.3 with timeout ≤ 5s. The response MUST be a valid DID document per W3C DID v1 with at least one `Ed25519VerificationKey2020` (or equivalent) verification method.
2. **Endpoint reachability**: HTTP GET `https://<endpoint>/iicp/health` over TLS ≥ 1.3 with timeout ≤ 5s. MUST return 200.
3. **Scheme + address guard**: `endpoint` MUST be `https://`; MUST NOT resolve to RFC-1918 / loopback / link-local (existing SSRF guard from /v1/probe).
4. **Idempotency**: if a replica with this `did` is already registered, return the existing `replica_id` + a freshly-rotated `replica_token` (200 OK); do not create a duplicate row.
5. **Event log emission**: on first-time registration, emit a `REPLICA_REGISTERED` event with payload `{did, endpoint, trust_tier}` so subsequent replicas mirror the registration.

**Response body** (200 on success; 422 on validation failure):
```json
{
  "replica_id":   "uuid-v4",
  "replica_token": "<JWT, role: replica, scoped to GET /v1/events>",
  "since_seq":    0,
  "genesis_hash": "<hex>",
  "did_acknowledged": true,
  "trust_tier":   "low",
  "expires_at":   "2026-08-23T00:00:00Z"
}
```

| Field | Notes |
|---|---|
| `replica_id` | UUIDv4 assigned by Genesis Seed; persisted; used as `signer_did` for replica-side event annotations in future federation |
| `replica_token` | Scoped JWT for `GET /v1/events`; expires after 90 days; rotated on re-registration |
| `since_seq` | Always `0` for first-time registration (full bootstrap); on re-registration may be the replica's last-acknowledged seq if the replica supplied a `last_seen_seq` query param |
| `genesis_hash` | Same `genesis_hash` field surfaced by `GET /v1/events` (DIR-FED-07) — pin-on-first-use to detect chain forks |
| `expires_at` | Issued `replica_token` expiry; replica MUST re-register before this date to maintain access |

**Error responses** (422 with `error.code`):

| Error code | Meaning |
|---|---|
| `IICP-E040` | `did` does not resolve to a valid DID document |
| `IICP-E041` | DID document has no Ed25519 verification method |
| `IICP-E042` | `endpoint` `/iicp/health` did not return 200 |
| `IICP-E043` | `endpoint` is non-https or resolves to a private address (SSRF guard) |
| `IICP-E044` | `trust_tier_request` is not one of the allowed values |

**Rate limit**: 5 registration attempts per IP per hour (throttle:5,60). Prevents enumeration / abuse of the DID-resolution probe path.

**Off-protocol governance** (preserved from v0.1.0): the Genesis Seed operator MAY still curate the `iicp-replicas.json` advertisement list; the handshake creates the protocol-level relationship, but inclusion in the trusted-replicas roster remains a governance act for non-`low` trust tiers.

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
| DIR-FED-11 | Genesis Seed MUST validate `did` resolves to a DID document with an Ed25519 verification method (IICP-E040/E041 on failure) | Genesis Seed |
| DIR-FED-12 | Genesis Seed MUST reject `endpoint` that is non-https or resolves to a private/loopback address (IICP-E043; SSRF guard parity with /v1/probe) | Genesis Seed |
| DIR-FED-13 | `POST /v1/replicas/register` MUST be idempotent on `did`: re-registration returns the same `replica_id` with a freshly rotated `replica_token` | Genesis Seed |
| DIR-FED-14 | Response MUST include `genesis_hash` matching the value surfaced by `GET /v1/events` (DIR-FED-07 parity) so replicas can pin-on-first-use | Genesis Seed |
| DIR-FED-15 | `GET /v1/snapshot` MUST return current state with `snapshot_seq` = highest emitted event `seq` at generation time | Genesis Seed |
| DIR-FED-16 | Federated event log MUST emit ONLY {REGISTER, DEREGISTER, CREDIT_AWARD, REPLICA_REGISTERED, REPUTATION_DECAY, OPERATOR_OBSERVED} (v0.3.5 closed federation type list; OPERATOR_OBSERVED added per P6-2.2 / W-033) | Genesis Seed |
| DIR-FED-17 | Snapshot response `genesis_hash` MUST match the value returned by `GET /v1/events` (parity with DIR-FED-07) | Genesis Seed |
| DIR-FED-19 | Genesis Seed MUST serve a valid v2-schema document at `/.well-known/iicp-replicas.json` (per §6.4 trusted-replicas registry). Required entry fields: `replica_id`, `did`, `endpoint`, `trust_tier`, `registered_at`. Discovery clients MAY use this for bootstrap-without-seed; MUST validate every field against the schema before acting on entries. | Genesis Seed |
| DIR-FED-20 | Replica directories MUST sign every discovery response (`GET /v1/discover`, `/v1/node/{id}`, `/v1/bootstrap`) with their own Ed25519 key and include `X-IICP-Replica-Sig` + `X-IICP-Replica-DID` + `X-IICP-Snapshot-Seq` headers per §6.5. Clients MUST verify the signature against the replica's published DID key before using returned nodes; failure → log IICP-SEC-REPLICA-01 + reject response. Genesis Seed responses are exempt (TLS+DNS trust). | Replica / Client |
| DIR-FED-18 | Replicas (`IICP_REPLICA_MODE=true`) MUST 307-redirect every unsafe HTTP method (POST/PUT/PATCH/DELETE) to the configured seed at `IICP_SEED_URL`, preserving path + query. Replicas with missing or non-https `IICP_SEED_URL` MUST refuse writes with `503 IICP-E047 replica_mode_misconfigured`. Reads (GET/HEAD/OPTIONS) and the replica-mirror apply path are unaffected. | Replica |
| DIR-FED-EVENTCHAIN-01 | Federated event log MUST be append-only — past events MUST NOT mutate: for any (`seq`, `event_id`) pair observed in two successive `GET /v1/events` responses, every field (`event_type`, `ts_ms`, `signer_did`, `payload`, `sig`) MUST be byte-identical, and `genesis_hash` MUST match across calls. Tampering, re-ordering, or tombstoning a past event causes undetectable replica divergence. | Genesis Seed |

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
| 0.3.6 | 2026-05-26 | §6.5 Replica Response Signing (Normative) + §8 DIR-FED-20 added per Phase 6 charter P6-4.2b. Replicas MUST sign discovery responses with Ed25519 (`X-IICP-Replica-Sig` + `X-IICP-Replica-DID` + `X-IICP-Snapshot-Seq` headers); signing input matches §3.4 event log pattern (method:path:query:snapshot_seq:body_hash). Clients MUST verify against replica's published DID key; failure logs IICP-SEC-REPLICA-01. Genesis Seed exempt (TLS+DNS trust). Replicas more than 5min behind seed (`replica_lag_ms`) MUST be treated as untrusted regardless of sig validity. |
| 0.3.5 | 2026-05-26 | §5.1 + §5.4 + §8 DIR-FED-16: `OPERATOR_OBSERVED` event type added per Phase 6 charter P6-2.2 + W-033 (null/self-reported field manipulation audit trail). Replicas MUST record but MUST NOT mutate state — trust auditor on seed is sole authority. Closed federation type list expands from 5 → 6 types. |
| 0.3.4 | 2026-05-26 | §6.4 Trusted-Replicas Registry (Normative) + §8 DIR-FED-19 added per Phase 6 charter P6-3.2. Schema v2 for `/.well-known/iicp-replicas.json`: required fields (replica_id, did, endpoint, trust_tier, registered_at) + optional health hints (region_hint, tls_min_version, availability_window, schema_compat). Dynamic state (last_seen_at, event_log_lag_ms) explicitly NOT in registry — clients query `/api/v1/stats` on each replica for freshness. Static metadata only — keeps the file CDN-cacheable so clients can route around the seed during outages. |
| 0.3.3 | 2026-05-26 | §6.2a Replica Write-Gate (Normative) + §8 DIR-FED-18 added per Phase 6 charter P6-1.3b-ii. Reciprocal of §6.1: replicas 307-redirect unsafe HTTP methods to the seed (Read-from-replica, Write-to-seed split). New error code IICP-E047 (replica_mode_misconfigured) for replicas with missing/non-https seed URL. Implemented as `App\Http\Middleware\ReplicaModeRedirect` toggled by `IICP_REPLICA_MODE` env flag. |
| 0.3.2 | 2026-05-25 | §8 DIR-FED-EVENTCHAIN-01 (chain-of-custody) added per Phase 6 charter P6-2.1. Makes explicit the implicit append-only invariant of the event log: past events MUST NOT mutate across successive `GET /v1/events` calls. Verified at runtime by the eponymous REACH probe (4 unit tests). Closes a quiet gap — DIR-FED-01..04 covered replica verification, but the seed itself had no externally-observable integrity probe. |
| 0.3.1 | 2026-05-25 | §3.2 Conflict resolution (Normative) added per Phase 6 charter P6-4.1. Strict precedence: Seed > Replica-by-newer-seq > Trust-tier-tiebreaker > Gossip-suggestion-only. Field-level resolution (not row-level). DIR-FED-TRUST-01 probe (P6-4.3) verifies. |
| 0.3.0 | 2026-05-25 | **Ephemeral-by-design** federation per W-042 + ADR-033. §5.1: federated event-type list reduced to {REGISTER, DEREGISTER, CREDIT_AWARD, REPLICA_REGISTERED, REPUTATION_DECAY}; HEARTBEAT/SCORE_UPDATE/REPUTATION_UPDATE removed (state-not-state-change; derivable from canonical row). §5.3: replica sync now snapshot+event-tail model (was: genesis-replay). §5.5: new `GET /v1/snapshot` endpoint contract (one-RTT bootstrap). §8: conformance DIR-FED-15/16/17 added. New error codes IICP-E045/E046. Closes the storage-scale gap: directory size at 1000 nodes goes from ~7 GB (v0.2.0 implementation) to ~15 MB (v0.3.0 implementation) — linear in node count, not in time × nodes. |
| 0.2.0 | 2026-05-25 | §7.1 Replica Registration Handshake (Normative) added per Phase 6 charter P6-1.1. `POST /v1/replicas/register` defined: DID resolution + HTTPS + endpoint reachability + SSRF guard; idempotent on `did`; returns `replica_id`, `replica_token`, `since_seq`, `genesis_hash`. New error codes IICP-E040–E044. Conformance DIR-FED-11..14 added (DID validation, SSRF guard, idempotency, genesis_hash parity). Throttle: 5/IP/hour. Closes the "off-protocol — currently manual" gap in §7 step 1. |
| 0.1.1 | 2026-05-17 | §9 Phase Readiness: added CIP-Full prerequisite — replicas MUST propagate pricing, cip_conformance_level, and cip_policy fields in events for CIP-Full consumer compatibility. |
| 0.1.0 | 2026-05-15 | Initial draft — event log wire format, DID document, replica sync lifecycle, redirect protocol, 8 conformance requirements (DIR-FED-01–08) |
