# IICP-DIR — Directory Sub-Protocol Specification

**Version**: 0.11.0  
**Date**: 2026-06-10  
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
      "max_tokens": 8192,
      "input_modalities": ["text"]
    }
  ],
  "limits": {
    "max_concurrent": 4,
    "tokens_per_min": 20000
  },
  "availability": [
    { "start": "00:00", "end": "08:00", "share": 0.8 }
  ],
  "operator_delegation": {
    "node_id": "uuid-v4",
    "operator_pub": "<base64 ed25519 pubkey>",
    "not_after": 1893456000,
    "sig": "<base64 ed25519 signature>"
  }
}
```

**Required fields**: `endpoint`, `region`, `capabilities[].intent`, `limits.max_concurrent`  
**Optional**: `node_id` (directory assigns if absent), `availability`, `limits.tokens_per_min`, `transport_endpoint`, `capabilities[].input_modalities`, `operator_delegation`

**`input_modalities` (v1.10.0, ADR-046 — multimodal)**: an OPTIONAL array on each capability object
declaring the input modalities that capability accepts; one of `text`, `image`, `audio`, `video`.
Defaults to `["text"]` when absent (back-compatible). A vision-language model advertises
`["text","image"]`. Vision (image-in) is a **modality of chat**, NOT a separate intent — a node MAY
register multiple capability objects with the same `intent` but different `input_modalities` (e.g. a
text-only chat capability and an image-capable chat capability). The directory stores the set and
exposes it on discover (§3.4); clients filter on it via `?modality=` (§3.3).

**`operator_delegation` (v1.10.0, ADR-045 Phase A — verifiable operator identity)**: an OPTIONAL
ed25519 token binding this node to a fleet operator. Fields: `node_id` (MUST equal the registering
node's id), `operator_pub` (base64 32-byte ed25519 public key), `not_after` (unix seconds; short-TTL
is the revocation baseline), `sig` (base64 ed25519 signature over the canonical bytes
`{"node_id":…,"not_after":…,"operator_pub":…}` — key-sorted, no whitespace, unescaped slashes). The
directory verifies it OFFLINE against the operator public key (no phone-home) and, on success, records
the verified `operator_pubkey` + trust tier (`did_key` self-asserted in Phase A; `did_web`
domain-verified in Phase B). An invalid delegation leaves the node operator-unverified but does NOT
reject the registration (no false binding is possible without the operator's signature). [→ DIR-OPID-01]

**Dual-endpoint model (v1.5.0, optional — default to HTTP-only)**:

A node MAY advertise two endpoints with distinct roles:

| Field | Scheme | Role | Used by |
|-------|--------|------|---------|
| `endpoint` | `http://` / `https://` | Control plane: health probe, registration heartbeat, HTTP fallback transport | Directory `assertLive`; legacy clients |
| `transport_endpoint` | `iicp://` / `iicpsec://` | Data plane: native binary framing per ADR-040 (default port 9484) | Clients preferring native transport |

Rules:
- `endpoint` is REQUIRED (no change from prior versions).
- `transport_endpoint` is OPTIONAL. When present its URI scheme MUST be `iicp` (plaintext binary framing) or `iicpsec` (TLS-wrapped framing). Default port for both is 9484 (ADR-040 §3).
- The directory MUST NOT perform an HTTP probe against `transport_endpoint` — its liveness is implied by `endpoint`'s `/iicp/health` response (Phase 5.x scope; native-protocol dial-back is Phase 6).
- Clients SHOULD prefer `transport_endpoint` when issuing task CALLs. When absent or unreachable, clients fall back to `endpoint` (HTTP transport per spec §3.3).
- Both endpoints MUST resolve to the same node (operator MUST NOT advertise a `transport_endpoint` belonging to a different host).
- `endpoint` and `transport_endpoint` MAY share the same host:port: a node MAY multiplex the HTTP control plane and the native binary transport on one listener via first-byte protocol detection (the IICP frame magic `IICP` distinguishes a native connection from an HTTP request line). Single-port operation lets a CGNAT node serve both planes through one pinhole, so the native transport is reachable exactly when `endpoint` is (#457; the reference SDKs default to this).

Example with both endpoints:

```json
{
  "endpoint": "http://203.0.113.5:8080",
  "transport_endpoint": "iicp://203.0.113.5:9484",
  ...
}
```

When only `endpoint` is set, the directory and clients behave exactly as in v1.4.x (HTTP-only transport). [→ ADR-040 binary framing, #325 routability, #331 NAT observability]

**ADR-041 additions (Phase 5.x, optional — default to current behavior)**:

```json
{
  "message_type": "REGISTER",
  "endpoint": "https://203.0.113.5:8090",
  ...
  "transport_method": "upnp_mapped",
  "transport_candidates": [
    {"type": "host",  "address": "192.168.1.10", "port": 8090, "priority": 126},
    {"type": "srflx", "address": "203.0.113.5",  "port": 8090, "priority": 100, "base": "192.168.1.10:8090"}
  ],
  "relay_endpoint": null,
  "nat_type": "full_cone"
}
```

| Field | Type | Meaning |
|-------|------|---------|
| `transport_method` | enum | `direct \| upnp_mapped \| stun_hole_punch \| turn_relay \| external_tunnel` |
| `transport_candidates[]` | array | ICE-style candidates (RFC 8445 §5.1.2.1 priority); clients pick highest-priority working candidate |
| `transport_candidates[].type` | enum | `host \| srflx \| relay` |
| `relay_endpoint` | string\|null | Set only when `transport_method=turn_relay` |
| `nat_type` | string\|null | Observability only (`full_cone`, `restricted_cone`, `port_restricted`, `symmetric`, `unknown`) |

Directory MUST accept registrations without these fields (back-compat with Phase 1-5 nodes). When present, the directory stores them and surfaces them in NODELIST responses.

**Endpoint routability invariant (`RoutableEndpoint`, iter-1365 / IICP-E035)**: in `APP_ENV in (production, staging)`, the directory MUST reject endpoints whose host is `localhost`, in `127.0.0.0/8`, `::1`, `RFC1918` ranges, `169.254.0.0/16` link-local, a reserved suffix (`.local`, `.test`, `.example`, `.invalid`, `.lan`, `.internal`), or a bare hostname without TLD. `APP_ENV in (local, testing)` bypasses this check for dev workflows. [→ ADR-041 invariant + #325]

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

Periodic liveness signal. Absence for > 90 seconds marks the node inactive (dormant).

A heartbeat received from a previously-dormant node MUST fully restore it: the directory
sets `status = active`, clears `dormant_since`, and — unless the heartbeat explicitly
carries `available: false` — restores `available = true`. The `available` field is
OPTIONAL in the heartbeat body; when absent the directory MUST default it to `true` (a
heartbeating node is, by definition, alive and serving). A node therefore auto-recovers
into discover within one heartbeat cycle after a transient gap (e.g. host sleep), with no
re-registration required. (v1.10.17 — corrects a directory regression where a resumed
heartbeat left `available = false`, hiding a live node from discover indefinitely.)

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
  },
  "challenge_response": "<hex HMAC-SHA256 of the prior response's challenge>"
}
```

Authorization: `Bearer <node_token>` header REQUIRED.

**Response (PONG)**:

```json
{ "ok": true, "next_heartbeat_ms": 30000, "reputation_score": 0.82, "challenge": "<hex nonce>" }
```

`reputation_score` — the node's current reputation [0.0, 1.0] as stored in the directory. Allows operators to observe their reputation on every heartbeat cycle. Default 0.5 for nodes with no history.

**Liveness challenge-response (v1.10.0, ADR-047 Part A — cryptographic liveness without dial-back)**:
The directory issues a fresh `challenge` nonce in each PONG. On the next HEARTBEAT the node SHOULD return
`challenge_response = lowercase-hex HMAC-SHA256(node_hmac_key, challenge)` using its ADR-019
`node_hmac_key`. A match upgrades "holds a node_token" to "controls the HMAC key" (anti-replay /
anti-token-theft) and is recorded as a verified-liveness timestamp — established WITHOUT any dial-back,
so it works for CGNAT/IPv6 nodes the directory cannot reach. OPTIONAL + back-compatible: absent
`challenge_response` simply leaves liveness cryptographically-unverified. [→ DIR-HB-LIVE-01]

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
| `modality` | MAY | One of `text`/`image`/`audio`/`video` (v1.10.0, ADR-046); if set, directory MUST return only nodes whose capability for the requested `intent` accepts that input modality (e.g. `?modality=image` → vision-capable nodes). |

---

### 3.4 NODELIST (Directory → Client)

```json
{
  "nodes": [
    {
      "node_id": "uuid",
      "endpoint": "https://node1.example.com",
      "transport_endpoint": "iicp://node1.example.com:9484",
      "region": "eu-central",
      "score": 0.91,
      "available": true,
      "load": 0.2,
      "active_jobs": 1,
      "max_concurrent": 4,
      "reputation_score": 0.87,
      "latency_estimate_ms": 120,
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
      "cip_conformance_level": "CIP-Provider",
      "health_label": "healthy",
      "exposure_mode": "ipv4_public_direct"
    }
  ],
  "count": 1,
  "query_ms": 8
}
```

**Field semantics:**

| Field | Type | Notes |
|-------|------|-------|
| `transport_endpoint` | string\|null | Native IICP binary endpoint (ADR-040). Scheme `iicp://` (plaintext) or `iicpsec://` (TLS). Clients SHOULD prefer this over `endpoint`. `null` = node only serves HTTP transport via `endpoint`. |
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
| `health_label` | string\|null | ADR-044 composed health label: `"healthy"` (score ≥0.85), `"degraded"` (≥0.65), `"impaired"` (≥0.40), `"critical"` (<0.40), `"offline"`. Computed from endpoint-liveness signals only — reachability 0.70, latency 0.30 (50–500 ms curve). Reputation and task-success were removed in #492 (ADR-044 amendment) — health reflects operational liveness, not earned history. Score is a float in [0.0, 1.0] (normalised from internal 0–100 scale by v1.10.6+). `null` against directories predating v1.10.0. |
| `exposure_mode` | string\|null | ADR-043 8-category network exposure classification (e.g. `"ipv4_public_direct"`, `"cgnat_upnp"`, `"ipv6_gua"`). `null` if node has not run qualification. |
| `reachability_tier` | string | v1.10.0, ADR-047: `"direct"` (dial-back-verified) or `"relay"` (heartbeating with a routable surface but not directly dial-back-verified — reachable via relay; e.g. CGNAT/IPv6 where the directory has no egress). Default discover returns `direct`+`relay`; a heartbeating node is never hidden purely for lacking dial-back. Clients SHOULD prefer `direct` and fall back to `relay`. |
| `input_modalities` | array | v1.10.0, ADR-046: union of input modalities the node's capabilities for this intent accept (`["text"]` default; `["text","image"]` for vision). Lets clients confirm multimodal support without a second round-trip; see `?modality=` (§3.3). |
| `backend` | string\|null | Detected backend server flavor the node runs — one of `ollama`/`lmstudio`/`vllm`/`llamacpp`/`anthropic`/`custom`. Self-attested at REGISTER (the SDK auto-detects it by fingerprinting the backend's endpoints/headers); informational (operator/consumer visibility), not used for routing. `null` if unreported. Also accepted as an optional REGISTER field (§3.1). |
| `transport_method` | string\|null | How the node is reachable for the native IICP transport (`"direct"`, `"upnp"`, `"stun"`, `"relay"`, …). Mirrors the REGISTER value (§3.1 / ADR-041). |
| `nat_type` | string\|null | Detected NAT topology (ADR-041). Advisory; clients MAY prefer `"direct"`/`"full_cone"`. |
| `transport_metadata` | object\|null | Transport-specific detail (relay endpoint, candidate list). Shape per ADR-041; opaque to clients that only use `endpoint`. |
| `address_family` | string\|null | `"ipv4"`, `"ipv6"`, or `"dual"` (maintainer directive 2026-05-27). Lets IPv6-only clients filter. |
| `relay_capable` | boolean | `true` if the node can act as a relay for NAT-bound peers (Tier-3 reachability). |
| `public_key` | object\|null | IICP-CX confidentiality key (iicp-confidentiality §3.2): `{algorithm, encoding, key, key_id, not_after, hybrid_pq}`. Present when the node advertises E2E payload encryption support. `null` = node accepts plaintext only. Clients MUST use this to encrypt payloads when `X-IICP-Require-E2E` is set. |
| `sdk_language` / `sdk_version` | string\|null | Advisory provenance of the serving node's SDK (#338). Informational only. |
| `models` / `quantization` / `inference_engine` | array\|string\|null | Advisory capability detail (iicp-core §2.1). The directory MUST NOT reject unrecognized values. |
| `operator_display_name` | string\|null | v0.10.3, #463: the operator's public `display_name`, resolved from the operator record by `operator_pubkey` for nodes bound via a verified ADR-045 delegation (§3.1). `null` when the node is not operator-bound. The `operator_pubkey` itself is directory-private and is **never** served; only the human-readable display_name appears. Surfaced in `/v1/discover` and node-detail so consumers see who operates a node. |

**`probation` (clarification, R3)**: `probation` is computed server-side and used to *filter* discover results (probation nodes are excluded from `?qos=interactive`/`realtime`), but the discover NODELIST does **not** include a `probation` field per node. The full `probation` boolean is surfaced only by `GET /v1/node/{id}` (node-detail). Clients needing the flag query node-detail.

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

Response: a lightweight peer list — **not** the full NODELIST shape. Only the
fields needed to dial a peer are included (no scoring weights, reputation fields,
or capabilities). Default limit: 5; maximum: 50.

```json
{
  "peers": [
    {
      "node_id":   "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "endpoint":  "https://node1.example.com:8090",
      "region":    "eu-central",
      "last_seen": "2026-05-31T16:00:00Z"
    }
  ],
  "count": 1
}
```

Liveness filter: only nodes whose `last_seen` is within the directory's stale-node
window (90 s default) are eligible. Sorted by `last_seen DESC` so cold-starting
nodes receive the freshest peers first.

---

### 3.6 PEER_EXCHANGE (Node → Node)

**Phase**: 2+ (not required for Phase 1 conformance — see `@phase2` mark in conformance suite)

Peer gossip — exchange known peer lists between nodes to bootstrap mesh connectivity without directory dependency. Each node maintains a local peer cache and periodically synchronises it with a random selection of known peers.

#### Request

```
POST /v1/peers
X-IICP-Signature: <ed25519-signature-hex>
Content-Type: application/json
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `sender_id` | UUID-v4 | MUST | `node_id` of the sending node |
| `known_peers` | string[] | MUST | List of `node_id` UUIDs the sender already knows |
| `timestamp_ms` | integer | MUST | Unix epoch milliseconds — used for replay detection |
| `ttl_s` | integer | SHOULD | Sender's suggested peer cache TTL; receiver MAY ignore |

> **Errata v1.5.1 (auth model corrected).** Earlier drafts required
> `Authorization: Bearer <node_token>` plus an HMAC-SHA256 of the body *keyed with
> node_token*. That design was broken twice over: (1) the receiving peer never
> possesses the sender's `node_token` (the directory stores only a bcrypt hash —
> DIR-REG-07 — and offers no introspection), so the HMAC was unverifiable as
> specified; (2) sending `node_token` to an arbitrary peer hands the sender's
> directory credential to a potentially malicious node. The corrected model below
> uses the sender's ed25519 `cx_public_key` — already registered with the directory
> and served on node detail / discover — so any receiver can verify offline, and no
> directory credential ever leaves its owner. **`node_token` MUST NOT be sent to
> peers under any circumstances.**

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

- `X-IICP-Signature` MUST be the hex-encoded ed25519 detached signature of the raw request
  body bytes, produced with the secret key whose public half the sender registered as
  `cx_public_key`. Receiver MUST verify it against the sender's `cx_public_key`, resolved
  from the receiver's peer cache or from directory node detail (`GET /v1/node/{sender_id}`,
  `public_key` field). Invalid or unverifiable signature → 403.
- Sender MUST NOT include `Authorization: Bearer <node_token>` — the directory credential
  never travels to peers. Receiver MUST ignore any Authorization header on this endpoint
  (it carries no trust).
- A sender without a registered `cx_public_key` cannot participate in signed gossip;
  receivers MUST reject unsigned requests from unknown senders → 403.
- Receiver MUST reject replayed signatures: if the same signature value has been seen
  within the last 5 minutes → 409. [→ SEC-NONCE-01]
- `timestamp_ms` MUST be within ±60 seconds of receiver's wall clock. Stale request → 422.
  (`timestamp_ms` is inside the signed body, so replaying with a fresh timestamp breaks
  the signature.)

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

The event log enables a replica directory to maintain a consistent, cryptographically verifiable view of the Genesis Seed's state without a shared database. Replicas consume events via `GET /v1/events` and replay them on top of a periodic snapshot to reconstruct current state.

> **Snapshot + event-tail model (db-D4prime / S.13 v0.3.0, reconciled 2026-05-30)**: high-frequency
> operational events are NOT logged — replicas read current reputation/load from the node snapshot
> (`nodes.*` columns), not from a per-heartbeat event stream. **Live federated event types**:
> `REGISTER`, `DEREGISTER`, `AUDIT_REPORT`, `CREDIT_AWARD`, `REPUTATION_DECAY`,
> `REPUTATION_UPDATE` **only** for the `heartbeat_metrics` source (adapter-reported task outcomes),
> and `REACHABILITY_DEMOTE` / `REACHABILITY_RESTORE` (#413, see below).
> `HEARTBEAT` and `SCORE_UPDATE` events are NOT emitted (the directory updates the snapshot instead).
> Earlier drafts listed `HEARTBEAT`/`SCORE_UPDATE` in the enum; they are retired from the live set.

> **`REACHABILITY_DEMOTE` / `REACHABILITY_RESTORE` (#413)** — the directory MUST emit a
> transition event whenever a node's `public_reachable` flag flips, because that flag is the
> single switch governing whether the node appears in default `/v1/discover` and `active_nodes`.
> A node "vanishing" from discover is otherwise invisible in the audit trail. Emitted at the two
> natural edges only (transition, never per-probe, to avoid flooding; flap-bounded by the
> never-downgrade-on-a-single-failure confirm-probe rule): `REACHABILITY_DEMOTE` when a dial-back
> re-probe fails (directory-side liveness sweep), `REACHABILITY_RESTORE` when an active probe
> re-confirms a previously-demoted node. Payload: `{ from: bool, to: bool, reason:
> "probe_success"|"probe_non_2xx"|"probe_connect_failed", endpoint: string, transport_method?:
> string, probe_source: "node_lifecycle"|"directory_active_probe", latency_ms?: number }`.
> Additive to the signed chain; consumers that don't recognise the type ignore it.

#### Event Envelope

All events share a common envelope:

```json
{
  "event_id": "uuid-v4",
  "event_type": "REGISTER | DEREGISTER | AUDIT_REPORT | CREDIT_AWARD | REPUTATION_DECAY | REPUTATION_UPDATE",
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

### 3.9 AUDIT_REPORT (Node → Directory)

**Phase**: 3 (#118 Part D)
**Status**: Implemented in `AuditReportController`
**Endpoint**: `POST /api/v1/audit-report` — authenticated via `node_token` (the reporter).

A registered node (the *reporter*) submits a peer-divergence finding about a *target* node.

**Request:**

| Field | Type | Notes |
|-------|------|-------|
| `target_node_id` | string (≤36, `^[a-zA-Z0-9][a-zA-Z0-9._:-]*$`) | Node being reported. MUST differ from reporter. |
| `finding` | string | Enum. v1: `declaration_divergence` (target's `/iicp/health` models[] omits a registered model). |

**Behaviour (normative):**

- A reporter MUST NOT report on itself → `422 invalid_target`.
- **Per-reporter rate limit**: at most one accepted report per `(reporter, target)` per 24h → `429` with `reason: "rate_limited"`.
- **Per-target griefing cap (RT-05, spec §11.5)**: at most **2 distinct reporters** MAY apply a reputation delta against one target per 24h. Reports beyond the cap return `202` but MUST NOT reduce reputation further; the emitted event carries `delta_suppressed: true`.
- On an applied report: reputation delta = **−0.05**, floored at 0.0 (see iicp-semantics §11.2).
- Every report (applied or suppressed) emits an `AUDIT_REPORT` event to the append-only event log with `{reporter_node_id, finding, reputation_delta, delta_suppressed, old_score, new_score}`.
- The directory MUST dual-write the new score to both `reputations.score` and `nodes.reputation_score`.

**Response**: `202 {"accepted": true}` on success; `429`/`422` per above.

### 3.9b Public Stats (`GET /v1/stats`)

**Phase**: 3+
**Status**: Implemented in `StatsController`
**Auth**: none (public, CDN-cacheable). Consumed by the website and by the DG6 live-state discipline.

```json
{
  "server": { "active_nodes": 3, "version": "v1.10.3" },
  "probes": { "last_probe_at": "2026-05-30T11:30:19+00:00", ... },
  "credit_schedule": {
    "formula": "ceil(output_tokens / tokens_per_credit) × tier_weight × node_multiplier",
    "tokens_per_credit": 1000,
    "tier_weights": { "sub_1b": 0.05, "7b": 1.0, "13b": 2.0, "30b": 6.5, "70b": 32.0, "100b_plus": 75.0 },
    "evaluation_grant": { "credits": 5, "interval_seconds": 21600 },
    "burn_rate_pct": 2.0
  },
  "mesh_health": { "score": 0.65, "label": "degraded", "mean": 0.65, "p10": 0.42, "distribution": {"healthy": 1, "degraded": 1, "impaired": 0, "critical": 0, "offline": 0}, "sample": 3, "basis": "active_provider_nodes", "window": "live" },
  "directory_health": { "score": ..., "label": ... }
}
```

**Field semantics (normative):**

| Field | Notes |
|-------|-------|
| `server.active_nodes` | Count of nodes with `last_seen` within the 90s liveness window. |
| `server.version` | Directory software version (`config/app.php iicp_version`). |
| `credit_schedule.tier_weights` | **Normative pricing schedule** — credits per 1000 output tokens scale by model size class. Operators and clients MAY key pricing on this. |
| `credit_schedule.evaluation_grant` | Free-tier allocation mirror of §3.10 (5 credits / 21600s = 6h). |
| `mesh_health` | ADR-044 node-aggregate (median over active provider nodes). `score`/`mean`/`p10` are floats in **[0.0, 1.0]** (v1.10.6+; internal computation uses 0–100 scale then normalises). `label` thresholds: `healthy` ≥0.85, `degraded` ≥0.65, `impaired` ≥0.40, `critical` <0.40. `insufficient_sample` when sample <3; `unavailable` (score 0.0) when no active nodes. |
| `directory_health` | Directory-infrastructure signal: `0.6·discover_latency + 0.4·conformance` (the signal REACH probes feed). Distinct from `mesh_health`. |

### 3.9c Directory-initiated node probing (Directory internal, Phase 5)

**Phase**: 5 (active reachability, #373 Phase B)  
**Status**: Implemented — `iicp:probe-nodes` PHP command + `run_probe_nodes_loop` Rust background task  
**Conformance ID**: DIR-PROBE-NODE-01 (conformance-test-suite.md §3.3i)

Directories SHOULD actively probe the endpoint of each registered node to verify
reachability independently of the node's self-attested `public_reachable` flag. This is
distinct from the client-initiated SSRF probe (`GET /v1/probe`, §3.11) — it is initiated
by the directory itself on a periodic schedule.

**Probe mechanics**:
- Fires every **300 seconds** (5 minutes) over all available (non-dormant) nodes
- Probe method: **TCP connect** to the `endpoint` host/port with a **5-second timeout**
- **SSRF guard**: RFC1918 ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), loopback (127.0.0.0/8), and link-local (169.254.0.0/16) are rejected without attempting connection
- Probe result recorded in `iicp_telemetry_probes` with `test_id = "DIR-PROBE-NODE-01"` and the probed `node_id`
- `probe_token_id` is NULL for directory-initiated probes (no operator probe token involved)

**Effect on node health**:

When `GET /v1/node/{id}` returns the node's `health.components.reachability`, the
directory SHOULD prefer an **independently observed** signal from a recent probe (within
10 minutes) over the node's self-attested value:

```json
"health": {
  "components": {
    "reachability": {
      "score": 0.9,
      "observed": true,
      "last_probe_at": "2026-06-01T06:00:00Z",
      "test_id": "DIR-PROBE-NODE-01"
    }
  }
}
```

When no recent directory probe exists, `observed: false` and the self-attested
`public_reachable` value is used as the fallback.

**Activation condition**: Requires directory origin to have IP-level reachability to the
node's endpoint. On IPv4-only hosting (e.g. shared web space), probes to DS-Lite or IPv6
endpoints will fail. Full activation requires IPv4 + IPv6 egress (e.g. VPS-level hosting).

### 3.10 Free-credit allocation (Directory internal)

**Phase**: 3 (ADR-019 credit economy)
**Status**: Implemented in `CreditService::maybeAllocateFreeCredits()`

The directory grants a small free-credit allocation to bootstrap new nodes into the credit economy.

**Rules (normative):**

- Allocation amount: **5.0 credits** (`FREE_CREDITS_AMOUNT`).
- Eligibility: the node's credit balance is 0 **AND** either it has no prior free-credit allocation, **OR** at least **6 hours** (`FREE_CREDITS_PERIOD_HOURS`) have elapsed since its last allocation (`free_credit_last_allocation_at`).
- **RT-02 (credit-survival)**: the `credits` row MUST survive node deletion (no cascade-on-delete). Re-registration with the same `node_id` finds the preserved row and respects the 6-hour gate — deregister/re-register does not reset eligibility.
- **Known limitation (RT-02b, tracked #380)**: the gate is keyed on `node_id`. A fresh `node_id` per registration bypasses it. Closure requires operator-scoped accounting (ADR-030) and/or an IP-aggregate ceiling. This is acceptable pre-Phase-5D (credits have no exchange value) and MUST be closed before external-operator launch.

---

## 5. Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `unauthorized` | 401 | Missing or invalid node_token |
| `not_found` | 404 | node_id not registered |
| `rate_limited` | 429 | Registration rate limit exceeded |
| `liveness_failed` | 422 | Endpoint did not respond to health check |
| `validation_error` | 422 | Required field missing or invalid |
| `IICP-E034` | 429 | Too many registration attempts from this source IP (10/15min — W-033) |
| `IICP-E035` | 422 | Non-routable endpoint host (ADR-041 invariant; `RoutableEndpoint` validator, iter-1365 / #325) |
| `IICP-E049` | 403 | Re-registration with a changed `cx_public_key` requires a valid `current_node_token` proving ownership. **Normative (MUST)**: if a re-registration request supplies a `cx_public_key` that differs from the stored value, the directory MUST verify that `current_node_token` bcrypt-matches the stored token hash. Failure → 403 IICP-E049. This gate prevents unauthenticated key-substitution attacks. (RT-6-1, #390, iter-1807) |

### 3.11 Supplementary routes (scope note, #384)

The following routes are present in the reference implementation but **outside the
normative IICP-DIR message catalogue** — they are either operator/infrastructure
concerns or live in a separate sub-spec:

| Route | Scope |
|-------|-------|
| `GET /metrics` | Prometheus text/plain exposition. Metrics semantics and label names are defined by ADR-014 (OTel/Prometheus) and `iicp-telemetry.md §T5`; not repeated here. |
| `GET /v1/probe` | External reachability SSRF guard. Defined in `iicp-dir.md §3.3e` + REACH conformance test DIR-PROBE-01/02; operator reference in ADR-022. |
| `GET /v1/conformance/…`, `GET /v1/badge/{tier}` | Conformance badge pipeline (submit, verify, SVG shield). Defined in S.14 `iicp-recognition.md §10` + `conformance-badges.md`; not duplicated here. |
| `POST /v1/replicas/register`, `GET /v1/snapshot` | Phase 6 federation handshake and snapshot bootstrap. Defined in S.13 `iicp-federated-directory.md §7.1/§5.5` (ADR-013 gated). |
| `POST /_deploy/migrate` | Operator-only HMAC-gated database migration endpoint. **Out of protocol scope** — deploy tooling, not part of the IICP wire contract. |

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
| `POST` | `/v1/credits/award` | Credit a worker after a validated CIPWorkerReceipt (HMAC-SHA256 + `response_hash` verified; IICP-E027 on failure). Conformance DIR-CRED-03. |
| `GET`  | `/v1/credits/balance` | Current credit balance for the authenticated node. Conformance DIR-CRED-01. |
| `GET`  | `/v1/credits/transactions` | Recent credit transaction history for the authenticated node. Conformance DIR-CRED-02. |
| `GET`  | `/v1/credits/summary` | Lifetime credit summary for the authenticated node: `total_earned` (sum of `credit` rows), `total_spent` (sum of `debit` rows), `balance`, `tx_count`, and a `reconciles` boolean. `reconciles` is an integrity invariant — `true` iff `balance == total_earned − total_spent` (4-decimal precision); a tampered or inconsistent ledger MUST surface as `false`. Conformance DIR-CRED-04. |
| `GET`  | `/v1/credits/quote` | Quote the credit cost of a prospective task (tokens × multiplier). iicp-billing-extension §8 / CIP §2.2. |

Free-tier allocation (5 credits / 6h gate) is automatic on registration — see §3.10. There is
no separate "spend" endpoint: routing cost is deducted by the coordinator at award/settlement
time, not via a pre-route debit call.

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
| 0.7.0 | 2026-05-26 | §3.1 REGISTER + §3.4 NODELIST: optional `transport_endpoint` field added (`iicp://` / `iicpsec://` scheme; default port 9484). Splits control plane (`endpoint`, HTTP) from data plane (`transport_endpoint`, native binary framing per ADR-040). Directory's HTTP liveness probe targets `endpoint` only; clients SHOULD prefer `transport_endpoint` when present. Back-compat: nodes without `transport_endpoint` continue to behave exactly as v0.6.x. |
| 0.9.4 | 2026-06-01 | §3.9c Directory-initiated node probing added (Phase 5 #373 Phase B): DIR-PROBE-NODE-01, TCP probe every 300s, SSRF-guarded, 5s timeout, results in iicp_telemetry_probes. NodeHealthService reachability uses independently observed signal when recent probe exists (observed: true). Activation requires IPv4+IPv6 egress. References conformance-test-suite.md §3.3i. |
| 0.9.0 | 2026-05-30 | Code↔spec drift closeout (#384): §7 credit endpoints corrected to shipped routes (award/balance/transactions/quote — R4 fix); §3.9b Public Stats schema added (/v1/stats — server/probes/credit_schedule/mesh_health/directory_health); §3.4 NODELIST table + transport_method/nat_type/transport_metadata/address_family/relay_capable/public_key(CX object)/sdk_*/models fields; probation clarified as node-detail-only (R3); §3.7 event-type enum reconciled to snapshot+event-tail live set (R2 — HEARTBEAT/SCORE_UPDATE retired). |
| 0.9.3 | 2026-05-31 | §3.11 Supplementary routes: scope annotations for /metrics, /v1/probe, /v1/conformance/*, /v1/badge/{tier}, /v1/replicas/register, /v1/snapshot, /_deploy/migrate (closes #384 LOW undocumented-routes items). |
| 0.9.2 | 2026-05-31 | §3.9b mesh_health: score/mean/p10 documented as float [0.0,1.0] (v1.10.6 wire normalisation); example updated from integer 65 to float 0.65; label thresholds expressed in [0,1]; basis/window fields added. health_label thresholds in §3.4 NODELIST also corrected to [0,1] scale. |
| 0.9.1 | 2026-05-31 | §3.5 BOOTSTRAP: documented actual response shape `{peers:[{node_id,endpoint,region,last_seen}], count}` — was incorrectly described as "same as NODELIST" (code↔spec drift R5, #384). |
| 0.8.0 | 2026-05-30 | §3.9 AUDIT_REPORT endpoint documented (was in code + semantics §11.5 but absent from the dir message-type catalogue — code→spec drift, GAPS-022). §3.10 Free-credit allocation rules documented (amount, 6h gate, RT-02 credit-survival, RT-02b known limitation). |
| 0.7.0 | 2026-05-30 | §3.4 NODELIST: added `health_label` (ADR-044 composed health score label) and `exposure_mode` (ADR-043 network classification) fields. Both `null`-safe for backward compatibility with pre-v1.10.0 directories. |
| 0.6.1 | 2026-05-20 | §3.3 DISCOVER: `cip_capable` query parameter added — boolean, server-side filter for CIP-Provider nodes (`allow_remote_inference=true`). Existing params `min_reputation`, `max_multiplier`, `min_quality_score` documented in table. CIP coordinators SHOULD pass `cip_capable=true` to avoid client-side filtering (S.12 §5.2). |
| 0.6.0 | 2026-05-20 | §3.4 NODELIST: `cip_conformance_level` type changed from `string\|null` to `string`; `"CIP-None"` added as explicit non-CIP value (consistent with implementation in RegisterController + NodeScorer). S.12 §5.2 updated to include `CIP-None` in profile table. |
| 0.5.0 | 2026-05-19 | §3.2 HEARTBEAT PONG: added `reputation_score` field (operator feedback on current standing). §3.7 REPUTATION_UPDATE event: dual-source schemas (`heartbeat_metrics` from HEARTBEAT pipeline, `proxy_telemetry` from SCORE_UPDATE pipeline). §3.7 CREDIT_AWARD event: corrected to actual CIPWorkerReceipt fields (`task_id`, `tokens_used`, `amount`, `new_balance`, `cip_parent_task_id`, `cip_session_key`). |
| 0.4.0 | 2026-05-17 | §3.4 NODELIST: added ADR-019 `pricing` block (credit_cost_multiplier, pricing_model, currency, effective_from, effective_until, attested); `cip_conformance_level` field (CIP-Consumer/Provider/Full per S.12 §5.2); `cip_policy.pricing_credits_per_1000` DEPRECATED in favor of pricing.credit_cost_multiplier. |
| 0.10.4 | 2026-06-09 | §3.4 NODELIST `health_label`: updated formula — reachability 0.70, latency 0.30; removed task-success (0.25) and reputation (0.20). Health now reflects operational liveness only (#492 / ADR-044 amendment). New nodes with no task history score 85 ("healthy") rather than 65 ("degraded"). Shipped in PHP + Rust directories. |
| 0.10.3 | 2026-06-07 | §3.4 NODELIST: added `operator_display_name` (#463 / ADR-045 Phase A) — the operator's public `display_name`, resolved by `operator_pubkey` for delegation-bound nodes; `null` when not operator-bound. `operator_pubkey` itself is directory-private; only display_name is served. Additive/back-compatible. |
| 0.11.0 | 2026-06-10 | **§3.6 PEER_EXCHANGE auth model corrected** (external security review, #495): the HMAC-keyed-with-node_token + Bearer-node_token design was unverifiable (receiver never has the sender's token; directory stores bcrypt only) and leaked the directory credential to peers. Replaced with ed25519 detached signature over the raw body using the sender's registered `cx_public_key` (resolvable via peer cache or `GET /v1/node/{id}`); `node_token` MUST NOT travel to peers; Authorization header carries no trust on this endpoint. Replay rules preserved (signature-replay 409 + ±60s timestamp inside the signed body). Phase 2+ surface — no Phase 1 conformance impact; adapter gossip implementation update tracked in #495. |
| 0.10.2 | 2026-06-05 | IICP-DIR-EXT-CREDITS: added `GET /v1/credits/summary` (DIR-CRED-04) — lifetime `total_earned`/`total_spent`/`balance`/`tx_count` for the authenticated node plus a `reconciles` integrity invariant (`balance == earned − spent`, MUST be `false` for a tampered/inconsistent ledger). Additive/back-compatible; powers the `iicp-node credits` command (#456). Shipped in PHP + Rust directories (parity #385). |
| 0.10.1 | 2026-06-03 | §3.2 HEARTBEAT: documented dormant-node auto-restore — a heartbeat from a previously-dormant node MUST set `status=active`, clear `dormant_since`, and default `available=true` unless the body carries `available:false` (corrects a directory regression where a resumed heartbeat left `available=false`, hiding a live node from discover forever; dir v1.10.17). §3.4/§3.7 event log: added `REACHABILITY_DEMOTE` / `REACHABILITY_RESTORE` to the live federated event-type set with payload schema (#413 — the `public_reachable` transition that makes a node vanish from discover is now in the signed, federatable audit trail; emitted transition-only at the demote/promote edges). Both additive/back-compatible. |
| 0.10.0 | 2026-06-03 | Four shipped additions (dir v1.10.14): §3.1 REGISTER `capabilities[].input_modalities` (ADR-046 vision/multimodal — `["text"]` default; image-in is a chat modality, not a new intent) + optional `operator_delegation` ed25519 token (ADR-045 Phase A — offline-verified operator→node binding, `did_key`/`did_web` trust tiers); §3.2 HEARTBEAT challenge-response (ADR-047 Part A — `challenge` nonce in PONG, `challenge_response`=HMAC-SHA256(node_hmac_key,nonce) — cryptographic liveness without dial-back, for CGNAT/IPv6); §3.3 QUERY `?modality=` filter; §3.4 NODELIST `reachability_tier` (`direct`/`relay` — relay-tier nodes no longer hidden, ADR-047) + `input_modalities`. All additive/back-compatible. Protocol Suite MINOR bump (→ v1.10.0) is the separate maintainer-ratified release step (VERSIONING.md Current + /spec page, per check_spec_versions.py). |

---

## Sign-off

**Protocol Steward**: IICP-DIR fills GAP-1 from SPEC_ANALYSIS.md. SUB_PROTOCOL binding
keeps core opcode table stable per ADR-009. Phase 1 REST form is a valid stepping stone.
Closes GitHub issue #14 (draft). ✓
