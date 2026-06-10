# IICP Core — Wire Format and Mandatory Requirements

**Version**: 1.2.8
**Date**: 2026-06-10
**Status**: draft
**Issue**: #17 (S.5 — spec split)
**Authority**: Protocol Steward
**Relation**: IICP_draft_1.4.2.txt, IICP-core-phase1-profile.md, iicp-dir.md

---

## Purpose

This document specifies the mandatory (MUST) requirements for any IICP implementation.
It covers the wire format, core message types, required fields, transport constraints,
error codes, and security minimums that define IICP conformance.

Optional semantics (SHOULD/MAY), routing behaviour, and extension mechanisms are in
companion documents:
- **`iicp-semantics.md`** — intent routing, QoS, node selection, retry policy
- **`iicp-extensions.md`** — billing, reputation, sub-protocol bindings, Phase 3+ extensions

Any implementation that satisfies every MUST in this document is
**IICP Core conformant** regardless of which extensions it supports.

---

## Protocol Design Principles

IICP makes four structural choices that distinguish it from point-to-point API calls or
service-level agreements. These principles appear throughout this document and its
companion specs; they are stated here so implementors and reviewers share a common
reference frame.

**1. Intent is a capability address, not a semantic goal.**  
The `intent` field on the wire is a stable URN (e.g. `urn:iicp:intent:llm:chat:v1`).
It identifies *what kind of capability is being invoked*, not the user's natural-language
request. The user's actual task lives in the `payload` field (CALL §5.1). Intent URNs are
versioned and registry-controlled (stable across operator changes); payloads are ephemeral
and private. See `iicp-semantics.md §1` for the full URN grammar.

**2. Payload is private and MUST NOT be logged or forwarded by the control plane.**  
The directory service (ADR-003) MUST NOT see, log, or forward task payloads. Telemetry
carries protocol-layer metadata (task_id, intent URN, region, model, latency, status)
but never payload content. This boundary is hard — it is not a configuration option.

**3. Constraints and QoS are enforced by the protocol, not advisory SLA hints.**  
Fields such as `timeout_ms`, `qos`, and `max_credits` in the CALL envelope are
first-class wire fields. A conforming adapter that accepts a CALL MUST respect these
bounds or return a structured failure (e.g., `IICP-E006 timeout`, `IICP-E021
capacity_exhausted`). Silent degradation or ignoring the constraint envelope is a
conformance violation. See ADR-008 for how QoS influences routing and admission.

**4. Observability is redacted protocol evidence.**  
Operators and the mesh itself can observe task_id, intent, model, latency, and outcome
without touching payload content. Stronger correlation (session-level audit trails,
per-task receipts) requires explicit opt-in via signed receipts (ADR-019 CIP billing,
ADR-014 OTel). No telemetry path may log the payload or derive payload content from
observable fields.

In short:

```
intent      = stable capability address (URN)
payload     = private semantic content (never logged by control plane)
constraints = enforced execution envelope (wire-level, not advisory)
observability = redacted protocol evidence (metadata only, opt-in for more)
```

---

## Protocol Scope

This document covers the *core* protocol layer: wire format, task lifecycle, error codes,
security minimums, and conformance requirements that all IICP implementations share.

The following concerns are **outside the core protocol** and are governed by companion
documents or operator policy:

- **Credit economy** (S-Credits, earn/spend/Mint governance) — a directory-layer optional
  extension. An IICP directory that does not implement credits is fully conformant.
  See `spec/iicp-dir.md` §Optional Extensions and ADR-031.
- **Reputation scoring** — a directory-layer SHOULD (ADR-026). Operators MAY skip.
- **Operator identity & anti-Sybil** — optional layer (ADR-030), required for
  gamification and diversity badges but not for task routing.
- **Federated control plane** — Phase 6+ (ADR-013).

CIP receipt HMAC integrity (ADR-019) *is* core — it prevents token inflation and is a
MUST for any implementation that issues CIP worker task receipts.

---

## Normative Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in RFC 2119 / BCP 14.

---

## 1. Core Message Types

IICP defines 14 message types. This document specifies the 7 required for Phase 1
conformance. The remaining 7 are specified in `iicp-semantics.md` and
`iicp-extensions.md`.

| IICP Message | Phase 1 Form | Direction |
|-------------|-------------|-----------|
| INIT | `POST /v1/register` | Node → Directory |
| ACK | Registration response | Directory → Node |
| CALL | `POST /v1/task` | Proxy → Adapter |
| RESPONSE | Task result | Adapter → Proxy |
| PING | `POST /v1/heartbeat` | Node → Directory |
| PONG | Heartbeat response | Directory → Node |
| CLOSE | HTTP connection close | Implicit |

---

## 2. INIT — Node Registration

### 2.1 Request (Node → Directory)

`POST /v1/register`  
Content-Type: `application/json`

**Required fields (MUST)**

| Field | Type | Constraint |
|-------|------|-----------|
| `endpoint` | string (URL) | HTTPS only; MUST be validated by directory liveness check before token issued [→ DIR-REG-04] |
| `region` | string | IANA-style tag (e.g., `us-west`, `eu-central`); max 64 chars |
| `capabilities` | array | MUST contain at least one capability object |
| `capabilities[].intent` | string | Standard: `urn:iicp:intent:<domain>:<action>:v<N>`; Custom: `urn:iicp:intent:x.<vendor>:<action>:v<N>` — see `iicp-semantics.md §1.1` |
| `capabilities[].models` | array | At least one model name string |
| `capabilities[].max_tokens` | integer | MUST be > 0 |
| `limits.max_concurrent` | integer | MUST be in range 1–256 |
| `limits.tokens_per_min` | integer | MUST be > 0 |

**Optional fields**

| Field | Type | Notes |
|-------|------|-------|
| `node_id` | UUID v4 | Client MAY provide; directory generates if absent |
| `public_key` | base64 string | Phase 2 signing key; ignored in Phase 1 |
| `availability` | array | Time-based sharing windows (see `iicp-semantics.md`) |
| `capabilities[].quantization` | string | Advisory. One of `fp16`, `q8`, `q5_k_m`, `q4_k_m`. Helps trust scoring and output fingerprinting. Directory MUST NOT reject an unrecognised value; treat as absent. |
| `capabilities[].inference_engine` | string | Advisory. One of `vllm`, `llama.cpp`, `tgi`, `ollama`. Used by trust auditors to build per-engine fingerprint references. Directory MUST NOT reject an unrecognised value; treat as absent. |
| `capabilities[].input_modalities` | array | Input modalities the capability accepts (`["text"]` default; `["text","image"]` for vision). Specced normatively in **`iicp-dir.md §3.1`** (ADR-046, v1.10.0). |
| `operator_delegation` | object | Verifiable operator→node binding `{node_id, operator_pub, not_after, sig}` (ed25519). Specced normatively in **`iicp-dir.md §3.1`** (ADR-045 Phase A); a valid delegation binds the node to an operator identity (`operator_pubkey`). |

### 2.2 Response (ACK)

HTTP 201 Created

```json
{
  "node_id": "uuid-v4",
  "node_token": "opaque-32-byte-hex",
  "expires_at": null,
  "directory": "https://iicp.network",
  "observed_source_ip": "203.0.113.42"
}
```

MUST requirements:
- `node_token` MUST be ≥ 32 bytes cryptographically random [→ DIR-REG-05]
- `node_token` MUST be returned exactly once in plaintext; the directory MUST store only the bcrypt hash [→ DIR-REG-07]
- Directory MUST perform a liveness check (`GET {endpoint}/iicp/health`) before issuing a token [→ DIR-REG-04]
- Directory MUST rate-limit: 10 INIT requests per minute per source IP [→ DIR-RL-01]
- ACK MUST include `observed_source_ip` — the source IP the directory observed for this request [→ DIR-ADDR-02]

---

## 3. CALL — Task Submission

### 3.1 Request (Proxy → Adapter)

`POST /v1/task`  
Authorization: `Bearer <node_token>`  
Content-Type: `application/json`

**Required fields (MUST)**

| Field | Type | Constraint |
|-------|------|-----------|
| `task_id` | UUID v4 | Generated by proxy; MUST be unique per execution [→ DIR-HB-02] |
| `intent` | string (URN) | MUST match a capability intent registered at the adapter |
| `payload` | object | Intent-specific; passed through to inference backend |
| `constraints.timeout_ms` | integer | MUST be > 0; adapter MUST abort execution if exceeded [→ TASK-4] |
| `auth.node_token` | string | Adapter MUST validate on every request [→ TASK-1] |

> **Errata v1.5.1 (TASK-1 scope clarified).** The adapter validates `auth.node_token` by
> **equality against its own token** — the one the directory returned to it at registration.
> The directory stores only a bcrypt hash (DIR-REG-07) and offers no introspection endpoint,
> so no third party can validate this token, and the adapter never could validate anyone
> else's. Consequence (normative): in Phase 1, `node_token` on `POST /v1/task` is an
> **operator capability credential** — only callers the node operator has explicitly given
> the token to (the operator's own proxy, a trusted consumer) are authorized. It is NOT a
> mechanism for arbitrary discovered consumers to submit tasks. Open-mesh consumer
> authorization is a Phase 2 surface: directory-issued, offline-verifiable consumer tokens
> (signed by the directory's published key so adapters verify without callback) — tracked
> in the repository as the successor to this errata. Until then, implementations MUST NOT
> document or imply that any discover-result consumer can submit tasks without an
> operator-granted credential.

**Optional fields**

| Field | Type | Notes |
|-------|------|-------|
| `constraints.qos` | string | `realtime` \| `interactive` \| `batch` \| `best-effort` — see `iicp-semantics.md` §2.1 |
| `constraints.priority` | string | `low` \| `normal` (default) \| `high` \| `critical` — client-declared task urgency, orthogonal to `qos`. Adapter SHOULD use this to order tasks when concurrency slots are contested (higher priority tasks scheduled ahead of lower). Proxy SHOULD prefer nodes with available `critical`/`high` capacity when routing high-priority tasks. MAY be ignored by Phase 5 adapters. |
| `constraints.consensus` | string | `none` (default) \| `first_completed` \| `majority_of_3` \| `majority_of_5` — see §3.3 |
| `trace.trace_id` | 16-byte hex | Propagated for observability |
| `trace.origin_node` | UUID | Identifies the requesting proxy |

MUST requirements:
- Adapter MUST check `task_id` uniqueness (idempotency guard) [→ TASK-2]
- Adapter MUST enforce `max_concurrent` concurrency limit [→ TASK-3]
- Task payload MUST NOT appear in any log output [→ SEC-LOG-01]

### 3.2 Response (RESPONSE)

HTTP 200 OK

```json
{
  "task_id": "uuid",
  "status": "success | error | timeout",
  "result": {},
  "metrics": {
    "latency_ms": 320,
    "tokens_used": 120
  },
  "model_used": "llama-3-8b",
  "error": null
}
```

**Optional response fields**

| Field | Type | Notes |
|-------|------|-------|
| `model_used` | string | Actual model identifier used for this inference. Adapter SHOULD include in every successful response. Allows proxy to verify declared model matches execution. |
| `attestation_receipt` | string (base64) | Signed execution proof. OPTIONAL — Phase 6 prerequisite. Requires ADR-024 (signed message envelope, #155) and identity slot (#150). Adapters MUST NOT include until ADR-024 is ratified. |

On error: `status = "error"`, `result = null`, `error = {"code": "...", "message": "..."}`.
Error responses MUST NOT include stack traces, file paths, or database structure [→ ERR-2].

### 3.3 Consensus Mode (`constraints.consensus`)

**Phase 5 — opt-in cross-validation inference.**

When `constraints.consensus` is set to a value other than `none`, the proxy MUST submit the
task to N nodes in parallel and apply the specified aggregation strategy:

| Value | Nodes | Agreement rule | Credit cost |
|-------|-------|----------------|-------------|
| `none` | 1 (default) | First success returned | 1× |
| `first_completed` | N (configured) | Fastest response wins | N× |
| `majority_of_3` | 3 | ≥ 2 agree (exact match or embedding similarity ≥ 0.95) | 3× |
| `majority_of_5` | 5 | ≥ 3 agree | 5× |

**Normative requirements:**

- Proxy MUST charge N× credits when consensus mode is active [→ billing, ADR-019].
- When ≥ 2 nodes disagree and no majority is reached, proxy MUST return HTTP 502
  with error code `no_consensus`.
- Outlier nodes (response outside the consensus cluster) MUST receive a reputation
  delta of −0.15 per `iicp-semantics.md` §11 delta rules.
- `first_completed` mode MUST cancel in-flight requests to other nodes after the
  first successful response (resource cleanup obligation).

**Mapping to full CIP `cip` block** (for implementations using the detailed protocol):
`constraints.consensus` is a shorthand over the `cip` object in `spec/iicp-cooperative-inference.md`:

| `constraints.consensus` | `cip.policy` | `cip.replicas` |
|------------------------|--------------|----------------|
| `none` | — (no `cip` block) | — |
| `first_completed` | `best_of_n` | 2+ (impl choice) |
| `majority_of_3` | `majority_vote` | 3 |
| `majority_of_5` | `majority_vote` | 5 |

Implementations MAY accept either form; the `cip` block takes precedence if both are present.

---

## 4. PING / PONG — Heartbeat

### 4.1 Request (Node → Directory)

`POST /v1/heartbeat`  
Authorization: `Bearer <node_token>`  
Content-Type: `application/json`

**Required fields (MUST)**

| Field | Type | Notes |
|-------|------|-------|
| `node_id` | UUID | MUST match a registered node |

Authorization header MUST be present and valid. Invalid or absent token → 401 [→ DIR-HB-02].

**Optional fields**

| Field | Type | Notes |
|-------|------|-------|
| `load` | float 0–1 | `active_jobs / max_concurrent` |
| `active_jobs` | integer | Current concurrent task count |
| `available` | boolean | Whether node is currently accepting tasks |
| `sla_p95_ms` | integer ≥ 0 | Declared p95 latency SLA in milliseconds. Directory stores this and MAY expose it in discovery responses. When declared, the directory SHOULD compare against observed telemetry (§T4) and flag nodes whose observed p95 consistently exceeds their declared SLA. Absence means the node makes no latency SLA declaration. |

### 4.2 Response (PONG)

```json
{ "ok": true, "next_heartbeat_ms": 30000 }
```

Directory MUST mark a node inactive after 90 seconds without a valid PING [→ DIR-HB-03].
Discovery MUST exclude inactive nodes from results [→ DIS-3].

---

## 5. Discovery

Discovery in Phase 1 is a directory REST query.

`GET /v1/discover?intent=<urn>&qos=<level>&region=<tag>&limit=<n>`

| Parameter | Required | Constraint |
|-----------|---------|-----------|
| `intent` | MUST | Standard: `urn:iicp:intent:*:v*`; Custom: `urn:iicp:intent:x.<vendor>:*:v*` |
| `qos` | SHOULD | `interactive` \| `batch` \| `best-effort` |
| `region` | MAY | Preference, not exclusion |
| `limit` | MAY | Default 10, max 50 |

Response:

```json
{
  "nodes": [
    {
      "node_id": "uuid",
      "endpoint": "https://node.example.com",
      "region": "eu-central",
      "score": 0.91,
      "available": true,
      "latency_estimate_ms": 120
    }
  ],
  "count": 1,
  "query_ms": 8
}
```

MUST requirements:
- Directory MUST filter: only nodes with `available = true` AND `last_seen` within 90s [→ DIS-3]
- Score MUST be computed server-side per ADR-008 formula [→ DIS-2]
- Nodes with score < 0.1 MUST be excluded from results [→ DIS-4]

---

## 6. Transport

**Port assignment**: Port **9484** is the canonical IICP protocol port (TCP and UDP). All
node-to-node and node-to-directory communication MUST use port 9484 unless an alternative
is explicitly negotiated during registration. See §11.3 for address-learning requirements.

| Aspect | Phase 1 (deployed) | Phase 2 (deployed) | Phase 3 (target) | Phase 4+ (roadmap) |
|--------|-------------------|--------------------|-------------------|---------------------|
| Port | 9484 TCP (MUST) | 9484 TCP (MUST) | 9484 TCP (MUST) | 9484 TCP + UDP (MUST) |
| Encoding | JSON | JSON + CBOR optional | CBOR preferred (`application/cbor`) | CBOR (default) |
| Transport | HTTPS/1.1 or HTTPS/2 | HTTPS/2 | HTTP/2 on port 9484 | QUIC on port 9484 UDP |
| Framing | REST (no custom framing) | REST + HMAC-SHA256 envelope | REST (IICP binary framing optional) | Native IICP binary framing |
| TLS version | TLS 1.3 MUST [→ SEC-TLS-01] | TLS 1.3 MUST | TLS 1.3 MUST | TLS 1.3 + PQ option |
| Auth | Bearer node_token | JWT HS256 | W3C DID (Phase 3+) | PQ — Dilithium3 |
| Peer discovery | Directory REST | Gossip (PEER_EXCHANGE) | DID-resolved mesh | — |

**Phase 1 rationale (ADR-002)**: JSON over HTTPS was chosen for Phase 1 to maximise
tooling compatibility and minimise implementation risk at PoC scale. CBOR and QUIC were
deferred explicitly to Phase 3 (see `project/decisions/ADR-002-phase1-transport.md`).

**Phase 3 transport resolution**: Phase 3 is now deployed. HTTP/2 on port 9484 TCP is
the current mandatory transport for node-to-node CALL/RESPONSE exchanges. CBOR is accepted
as an alternative encoding when the client sends `Content-Type: application/cbor` — the
directory and adapter MUST respond in CBOR if the request was CBOR-encoded. QUIC on port
9484 UDP is the Phase 4 target and is tracked in issue #230.

**Network standard intent**: IICP is designed to become a network-level standard for
AI-to-AI communication — analogous to HTTP for web resources or SQL for data. The
IETF Standards Track intent from v1.4.2 (QUIC + CBOR + QuDAG + port 9484) was never
abandoned; it was phased. All implementations SHOULD register on port 9484 to build the
network effect needed for standardisation.

All components MUST validate TLS certificates on outbound connections.
Plaintext HTTP connections to IICP endpoints MUST be rejected.

---

## 7. Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `unauthorized` | 401 | Missing or invalid node_token |
| `forbidden` | 403 | Token valid but insufficient rights |
| `not_found` | 404 | node_id not in registry |
| `conflict` | 409 | Duplicate task_id (idempotency — ADR-010) |
| `rate_limited` | 429 | Registration rate limit exceeded |
| `capacity_exceeded` | 429 | max_concurrent reached at adapter; body MUST include `qos_class` and `retry_after_ms` (§2.2) |
| `task_timeout` | 504 | Task exceeded constraints.timeout_ms |
| `backend_error` | 502 | Inference backend failed (details not exposed) |
| `no_consensus` | 502 | Consensus mode active and no majority agreement reached (§3.3) |
| `validation_error` | 422 | Input schema validation failed |

All error responses MUST use structured JSON:

```json
{ "error": { "code": "<code>", "message": "<human-readable>" } }
```

The full IICP-E numeric code registry (IICP-E001 through IICP-E032) is maintained in
`project/ARCHITECTURE.md §Error Codes`. Implementations MUST use those codes on the wire;
the slug codes above are the Phase 1 canonical names. Phase 2 / Phase 3 / Phase 5 codes
in active use:

**Phase 5 — Cooperative Inference (S.12)**

| Code | HTTP | Component | Meaning |
|------|------|-----------|---------|
| `IICP-E020` | 403 | Adapter (Worker) | Coordinator reputation below provider's `minimum_reputation` floor |
| `IICP-E021` | 503 | Adapter (Worker) | Worker at `max_concurrent_remote` capacity — reject without queuing |
| `IICP-E022` | 503 | Proxy (Coordinator) | No CIP-eligible workers available for dispatch (S.12 §2.2) |
| `IICP-E023` | 429 | Adapter (Worker) | Policy evaluation rate limit exceeded (TC-9b / resource protection) |
| `IICP-E024` | 504 | Proxy (Coordinator) | All dispatched workers timed out within `worker_timeout` |
| `IICP-E025` | 422 | Proxy (Coordinator) | Invalid replica count for `majority_vote` — must be odd ≥ 3 |
| `IICP-E026` | 422 | Proxy (Coordinator) | Incomplete map-reduce split — coverage gaps detected before dispatch |
| `IICP-E027` | 422 | Directory | CIPWorkerReceipt HMAC-SHA256 signature invalid, absent, or HMAC key not provisioned; credit ceiling violation (TC-9c: amount exceeds `ceil(tokens/1000)×multiplier×1.1`); nonce replay (TC-9d: nonce already seen); credit award rate limit exceeded (TC-9b: >1000 credits/hour per node_id, per S.12 §10.6) |
| `IICP-E028` | 422 | Proxy / Adapter | Invalid CIP field value — `cip.policy` enum, `cip.replicas` range, `cip_role` value, or `cip_parent_task_id` format |

**Phase 2 / Phase 3 — Mesh + Model Routing**

| Code | HTTP | Component | Meaning |
|------|------|-----------|---------|
| `IICP-E029` | 404 | Adapter | Model not registered on this adapter node (model_task handler) |
| `IICP-E030` | 404 | Adapter | Relay target peer not in peer list — peer list may be stale (30 s gossip cycle) |
| `IICP-E031` | 502 | Adapter | Relay forwarding to target peer failed — peer unreachable or returned error |
| `IICP-E032` | 401 | Directory | Invalid or missing proxy_token — `POST /v1/telemetry` requires proxy_token Bearer, not node_token |
| `IICP-E033` | 503 | Proxy (Client) | No nodes serve this intent — directory was reachable and returned 0 candidates after intent + region + reputation filtering. Distinct from generic "no_available_node" (which conflates this with directory unreachability). Operator next-step: verify intent URN, check `/nodes` page for matching capabilities, or wait for new providers. |
| `IICP-E034` | 429 | Directory | Too many registration attempts from this source IP within the rate-limit window (**60 per 60s** per source IP, W-033; response carries `retry_after`). Operator next-step: wait `retry_after` seconds or use a different source IP. |
| `IICP-E036` | 402 | Proxy (Client) | InsufficientCredits — consumer S-Credit balance below the computed routing cost (`ceil(output_tokens/1000) × tier_weight × multiplier`). The proxy MUST run this pre-check before dispatch. See iicp-billing-extension §6/§10.1. (Distinct from `IICP-E028` = invalid CIP field value; the credit-economy research originally drafted this under E028 — collision resolved here.) |
| `IICP-E035` | 422 | Directory | Non-routable endpoint at `POST /v1/register` — host is localhost, in 127.0.0.0/8, ::1, RFC1918 (10/8, 172.16-31/12, 192.168/16), 169.254/16 link-local, a reserved suffix (`.local`, `.test`, `.example`, `.invalid`, `.lan`, `.internal`), or a bare hostname without TLD (Docker-compose service name). Operator next-step: register with a publicly-routable DNS name or IP; for local dev set `APP_ENV=local` against a local directory (issue #325 Layer 1). |

---

## 8. Security Requirements (Phase 1 minimum)

- TLS 1.3 MUST be enforced on all endpoints [→ SEC-TLS-01]
- `POST /v1/register` rate limit: 10/min per IP MUST be enforced [→ DIR-RL-01]
- `node_token`: 32+ bytes cryptographically random, stored bcrypt-hashed, returned once [→ DIR-REG-05, DIR-REG-07]
- Adapter MUST validate `node_token` on every `POST /v1/task` [→ TASK-1]
- Error responses MUST NOT include stack traces, file paths, or DB structure [→ ERR-2]
- Task payloads MUST NOT appear in logs [→ SEC-LOG-01]
- **Privacy (PA-1..PA-4)**: Implementers and operators MUST inform clients that the inference-executing node receives the full task payload in plaintext, including any user-provided content. IICP provides confidentiality for transit (TLS 1.3) and isolation of the directory from payload content; it does not provide confidentiality against the inference-executing node. [→ SEC-PRIV-01]
- Relay nodes and directory operators MUST NOT log task payload content beyond the TTL required for rate-limiting. [→ SEC-PRIV-03]
- Registration `node_id` MUST default to an anonymized UUID not tied to hardware or operator identity. [→ SEC-PRIV-08]
- All IICP connections MUST use TLS 1.3 or higher with ephemeral key exchange (forward secrecy). [→ SEC-TLS-01, SEC-PRIV-09]
- **Privacy adversary model** (PA-1..PA-4) and IICP Privacy Tier taxonomy are normative in `project/SECURITY.md §Privacy Adversary Model` and SHALL be considered when implementing any component that handles task routing or node metadata.

---

## 9. Conformance Reference

The machine-readable Phase 1 conformance checklist is in
`spec/IICP-core-phase1-profile.md §10`. The test suite mapping is in
`spec/conformance-test-suite.md`.

Conformance test IDs referenced above (e.g., `[→ DIR-REG-04]`) map to rows in the
conformance test suite. Any conformant implementation MUST pass all tests with a
`level: MUST` marker.

---

## 10. Phase Mapping

| Feature | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---------|---------|---------|---------|---------|
| Auth | Bearer node_token | JWT HS256 | W3C DID | Post-quantum (Dilithium3) |
| Replay protection | task_id uniqueness | HMAC nonce | DID challenge | PQ nonce |
| Transport | HTTPS/1.1 | IICP SUB_PROTOCOL | QUIC | QuDAG |
| Peer discovery | Directory REST | Gossip (PEER_EXCHANGE) | DID-resolved mesh | — |
| Signing | None | HMAC-SHA256 | Signed requests | PQ signatures |

---

## 11. Implicit Address Learning

IICP directories observe the source IP of every authenticated request and make
this observation available to the registering node. Nodes have no reliable way
to self-report their externally-visible IP; the directory provides an authoritative
view.

### 11.1 Requirements (DIR-ADDR-01 — DIR-ADDR-07)

**DIR-ADDR-01** — The directory MUST record the source IP address observed on
every `POST /v1/register` request, independent of any `endpoint` field supplied
by the registering node.

**DIR-ADDR-02** — The directory MUST include `observed_source_ip` in the ACK
response body (HTTP 201) of every successful registration. The value MUST be the
IP the directory observed for that specific HTTP request, not a cached or inferred
value.

**DIR-ADDR-03** — The directory MUST update the stored `observed_source_ip` on
every valid (authenticated) `POST /v1/heartbeat` from a registered node. The
most-recently-observed IP is the authoritative value.

**DIR-ADDR-04** — The directory MUST expose `GET /v1/me` as an authenticated
endpoint. A node presenting a valid `node_token` MUST receive:

```json
{
  "node_id": "uuid-v4",
  "observed_source_ip": "203.0.113.42",
  "endpoint": "https://node.example.com"
}
```

The `endpoint` field is the value the node registered; `observed_source_ip` is
what the directory currently records for that node.

**DIR-ADDR-05** — The directory MUST extract the client IP from the
`CF-Connecting-IP` header when present (Cloudflare proxy). If absent, it MUST
fall back to `X-Forwarded-For` (first value), then to the raw TCP source IP.
The directory MUST NOT trust these headers on unauthenticated requests for any
security-sensitive decision; address observation is informational only.

**DIR-ADDR-06** — The directory MUST persist address history. Each observed IP
event (register, heartbeat) MUST be stored as an immutable record with the
request type and timestamp. The history MUST be retained for at least 30 days.

**DIR-ADDR-07** — The directory MUST NOT expose address history records to any
caller other than the owning node. `GET /v1/me` returns only the current
observed IP, not the full history. History access is operator-internal only.

### 11.2 Proxy Client Behaviour

A conformant proxy MUST parse `observed_source_ip` from the ACK on registration.

If the `observed_source_ip` does not match the hostname resolved from the
configured `endpoint`, the proxy SHOULD log a warning at WARNING level:

```
[WARN] Observed external IP <ip> does not match endpoint host <host> —
       this node may be behind NAT or a misconfigured reverse proxy.
```

The proxy MUST expose the most-recently-observed IP in the output of any
status or health command (e.g., `iicp-proxy status`).

### 11.3 Default Port

Port **9484** (TCP and UDP) is the default IICP port for node-to-directory
and node-to-node communication. This port is IANA-unassigned and is reserved
for IICP use. Implementations SHOULD listen on port 9484 by default and MUST
advertise it in registered `endpoint` URLs when no other port is specified.

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-05-15 | Initial draft — extracted from IICP_draft_1.4.2.txt and IICP-core-phase1-profile.md as part of S.5 spec split |
| 1.1.0 | 2026-05-15 | Added §11 Implicit Address Learning (DIR-ADDR-01..07) and default port 9484 |
| 1.2.0 | 2026-05-17 | §3.1: added constraints.consensus optional field; added realtime to constraints.qos values. §3.3: Consensus Mode — majority_of_3, majority_of_5, first_completed; no_consensus 502; N× credit cost; outlier −0.15 reputation. §7: no_consensus error code; capacity_exceeded note (qos_class+retry_after_ms). Closes #120 (spec). |
| 1.2.7 | 2026-06-06 | §7: corrected the `IICP-E034` rate-limit description — was "10/15min", reconciled to the **shipped** behavior **60 per 60s per source IP** (PHP RegisterController REGISTER_RATE_LIMIT=60 / REGISTER_RATE_TTL=60; Rust dir parity 289bc0e3). Spec-vs-shipped drift fix (ALIGN). |
| 1.2.8 | 2026-06-10 | **TASK-1 scope errata** (external security review, #496): §3.1 clarifies that `auth.node_token` is validated by the adapter by equality against its OWN token — an operator capability credential, NOT a mechanism for arbitrary discovered consumers (directory stores bcrypt only, no introspection). Open-mesh consumer authorization is normatively deferred to Phase 2 directory-issued offline-verifiable tokens. Implementations MUST NOT imply discover-result consumers can submit tasks without an operator-granted credential. |
| 1.2.6 | 2026-06-06 | §7: registered `IICP-E036` (Proxy 402 — InsufficientCredits, consumer balance below computed routing cost). Resolves the credit-economy research E028 collision: E028 stays *invalid CIP field value*; InsufficientCredits is the distinct E036. See iicp-billing-extension §6/§10.1. (Header version reconciled to 1.2.6 — it trailed the changelog, which already carried 1.2.3–1.2.5.) |
| 1.2.5 | 2026-05-21 | §7: added IICP-E033 (Proxy 503 — no nodes serve this intent, distinct from "no_available_node" runtime-failure code). Actionable next-step text included (verify intent URN / check /nodes / wait for providers). Closes WQ-030 friction #3 from iter-318 happy-path audit. |
| 1.2.4 | 2026-05-20 | §2.1: added optional `capabilities[].quantization` and `capabilities[].inference_engine` advisory fields. Enables output fingerprinting (#118) and per-engine trust scoring. Directory MUST NOT reject unrecognised values. |
| 1.2.3 | 2026-05-20 | §7: IICP-E027 description extended to cover TC-9b credit award rate limit rejection (>1000 credits/hour per node_id, per S.12 §10.6). Cross-references TC-9b/TC-9c/TC-9d inline. |
| 1.2.2 | 2026-05-19 | §7: added Phase 5 CIP error codes IICP-E020..E028 to the active-use table; split Phase 2/3 and Phase 5 sections; IICP-E027 description updated to cover hmac_key_not_provisioned sub-case and ceiling/nonce sub-cases. |
| 1.2.1 | 2026-05-19 | §7: registered IICP-E029..E032 (Phase 2/3/5 adapter + directory codes); added IICP-E numeric code registry pointer. Closes #186 (spec). |

---

## Sign-off

**Protocol Steward**: iicp-core.md extracts MUST-level requirements from IICP v1.4.2
into a standalone normative document. All MUST statements cross-reference the
conformance test suite. This document is part of the S.5 spec split (issue #17). ✓
