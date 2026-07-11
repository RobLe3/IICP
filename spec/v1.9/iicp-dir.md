# IICP-DIR — Directory Sub-Protocol Specification

**Version**: 1.1.21
**Date**: 2026-07-10
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
  },
  "policy_manifest": {
    "version": "2026-07-02",
    "jurisdiction": "DE",
    "remote_executor_can_read_prompt": true,
    "training_use": "none",
    "retention": {
      "task_payload": "none",
      "logs_days": 7
    },
    "subprocessors": ["self-hosted"],
    "unsupported_intents": [
      "urn:iicp:intent:biometric:protected-trait-classification:v1"
    ]
  }
}
```

**Required fields**: `endpoint`, `region`, `capabilities[].intent`, `limits.max_concurrent`
**Optional**: `node_id` (directory assigns if absent), `availability`, `limits.tokens_per_min`, `transport_endpoint`, `capabilities[].input_modalities`, `operator_delegation`, `policy_manifest`

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
| `transport_method` | enum | `direct \| upnp_mapped \| stun_hole_punch \| turn_relay \| external_tunnel \| webrtc_datachannel` |
| `transport_candidates[]` | array | ICE-style candidates (RFC 8445 §5.1.2.1 priority); clients pick highest-priority working candidate |
| `transport_candidates[].type` | enum | `host \| srflx \| relay` |
| `relay_endpoint` | string\|null | Set only when `transport_method=turn_relay` |
| `nat_type` | string\|null | Observability only (`full_cone`, `restricted_cone`, `port_restricted`, `symmetric`, `unknown`) |

Directory MUST accept registrations without these fields (back-compat with Phase 1-5 nodes). When present, the directory stores them and surfaces them in NODELIST responses.

REGISTER MAY also carry the optional updater-evidence fields listed in §3.2
(`auto_update_enabled`, `auto_update_interval_s`, `sdk_latest_seen`,
`sdk_update_last_checked_at`, `sdk_update_error_class`). They are advisory and do
not replace directory-computed SDK-baseline enforcement.

**`policy_manifest` (v1.1.8, EU/GDPR readiness — signed-manifest phase A)**: an OPTIONAL,
small, public, machine-readable declaration about the node's data-handling posture. The
directory stores and echoes safe fields. Unsigned manifests remain backward-compatible
self-attestations; when `signature` is present the directory MUST verify the detached
Ed25519 signature before accepting registration and MUST reject invalid or expired
signed manifests. A valid signature is tamper evidence for the manifest statement, not
legal identity proof, a DPA, or proof that the operator follows the declaration. Defined
fields include:

| Field | Type | Meaning |
|-------|------|---------|
| `version` | string\|null | Manifest/profile version chosen by the operator. |
| `jurisdiction` | string\|null | Operator-declared jurisdiction or region label. |
| `policy_url` / `contact_url` | URI\|null | Optional public policy/contact links. |
| `remote_executor_can_read_prompt` | boolean | Explicit reminder that normal remote inference exposes the prompt to the selected executor; defaults to `true` if omitted. |
| `training_use` | enum | `none`, `opt_in`, or `provider_defined`. |
| `retention.task_payload` | enum | `none`, `transient`, or `provider_defined`. |
| `retention.logs_days` | integer\|null | Self-declared log retention in days. |
| `subprocessors[]` | string[] | Public subprocessor/backend labels, if any. |
| `unsupported_intents[]` | string[] | Intent URNs the node explicitly refuses to serve. |
| `signed_statement` | string\|null | Optional human-readable signed-policy reference. New implementations SHOULD prefer the structured `signature` block. |
| `signature.algorithm` | string | `Ed25519` for signed-manifest phase A. |
| `signature.key_id` | string\|null | Operator-chosen public key label for rotation/debugging. |
| `signature.public_key` | string | Base64/base64url Ed25519 public key that verifies this manifest statement. This key is policy-signing metadata, not the CX encryption key. |
| `signature.signature` | string | Base64/base64url detached Ed25519 signature over the canonical manifest payload. The canonical payload recursively sorts object keys and excludes only `signature.signature`, so `signed_at` and `expires_at` are covered by the signature. |
| `signature.signed_at` | ISO-8601\|null | Optional signing timestamp. |
| `signature.expires_at` | ISO-8601\|null | Optional expiry. Expired signed manifests MUST be rejected at registration. |

This field is for routing-policy and transparency groundwork only. It is not a legal
compliance certificate, not a DPA, and not proof that the node follows its declaration.

**External tunnel operational guardrails (v1.1.4, SDK 0.7.75):**
`transport_method=external_tunnel` covers operator-provided public tunnels
(Cloudflare Tunnel, ngrok, or equivalent) that expose the node's HTTP transport
as a routable HTTPS `endpoint`. The directory treats a verified external-tunnel
endpoint like any other public endpoint: it MUST still run the normal liveness
and routability checks, and it MUST NOT depend on vendor-specific tunnel APIs or
vendor state.

Accountless or ephemeral external tunnels are an onboarding fallback, not a
durable production reachability guarantee. Provider SDKs SHOULD apply local
creation back-pressure before creating such tunnels so multiple node services on
one host do not hit provider rate limits or enter a create/crash/create loop:

| Guardrail | Recommended default | Purpose |
|-----------|---------------------|---------|
| Host-wide create spacing | 120 seconds | Avoid repeated accountless tunnel creation by several local services. |
| Host-wide create lease | 45 seconds | Let one local node attempt creation while peers wait or fall back. |
| Provider rate-limit cooldown | 900 seconds after HTTP 429 or Cloudflare 1015-class rate-limit evidence | Let the provider-side limit recover before another accountless attempt. |

While the spacing gate, creation lease, or provider cooldown is active, SDKs MUST
NOT spin in a tight tunnel-create retry loop. They SHOULD use the last safe
reachability method that is still valid (existing verified public endpoint,
configured/named tunnel, configured or auto-elected relay), or serve local-only /
skip public registration with honest operator guidance. SDKs MUST NOT advertise
an unverified public `endpoint` merely because a local port is listening.

Persistent production reachability SHOULD use an operator-supplied
`IICP_PUBLIC_ENDPOINT` or a named/authenticated tunnel where available. SDKs MAY
expose implementation-specific environment controls for the guardrails; the
official SDKs use `IICP_TUNNEL_CREATE_MIN_INTERVAL_S`,
`IICP_TUNNEL_CREATE_LEASE_S`, `IICP_TUNNEL_RATE_LIMIT_COOLDOWN_S`,
`IICP_TUNNEL_CREATE_STATE_FILE`, `IICP_TUNNEL_CREATE_LOCK_FILE`, and
`IICP_TUNNEL_RATE_LIMIT_STATE_FILE`. These names are not wire fields; equivalent
behaviour is sufficient for conformance.

**Browser WebRTC transport advertisement (draft, #523):** a browser provider MAY set
`transport_method=webrtc_datachannel` and include a `transport_metadata.webrtc` object that
advertises how consumers should attempt browser-native self-addressing. This is a data-plane
transport advertisement, not a task relay through the directory. The object shape is:

```json
{
  "transport_method": "webrtc_datachannel",
  "transport_metadata": {
    "webrtc": {
      "signaling_directory": "https://iicp.network",
      "mailbox_id": "node-id-or-opaque-handle",
      "expires_at": "2026-06-21T14:30:00Z",
      "ice_servers": [{"urls": ["stun:stun.l.google.com:19302"]}],
      "datachannel_protocol": "iicp-task-v1",
      "relay_fallback": true
    }
  }
}
```

Rules:
- `mailbox_id` MUST identify only a short-lived signaling mailbox (§3.13); it is not a
  payload endpoint and MUST NOT authorize task execution by itself.
- `expires_at` MUST be present and SHOULD be no more than 10 minutes after advertisement.
  Consumers MUST treat expired handles as absent.
- `ice_servers` MAY contain STUN entries. TURN entries are reserved for a later relay-like
  fallback and MUST NOT be required for the first browser-WebRTC profile.
- The DataChannel subprotocol string for task framing is `iicp-task-v1`. Task CALL/RESPONSE
  envelopes carried on the DataChannel are the same IICP task envelopes used by HTTP/relay
  transports; IICP-CX confidentiality rules still apply when required.
- Clients SHOULD attempt WebRTC only while the mailbox is live; on ICE timeout/failure they
  MAY fall back to the relay transport (§7) when the node advertises a safe relay path.

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
  "challenge_response": "<hex HMAC-SHA256 of the prior response's challenge>",
  "auto_update_enabled": true,
  "auto_update_interval_s": 3600,
  "sdk_latest_seen": "0.7.75",
  "sdk_update_last_checked_at": "2026-06-25T08:40:00Z",
  "sdk_update_error_class": null
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

**Updater evidence (optional, advisory)**:
SDKs MAY include `auto_update_enabled`, `auto_update_interval_s`, `sdk_latest_seen`,
`sdk_update_last_checked_at`, and `sdk_update_error_class` on REGISTER and HEARTBEAT.
The directory stores these for operator/debug visibility, but MUST compute
`sdk_status`/`upgrade_required` from the actual reported `sdk_version`, not from the
updater's self-report.

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
| `view` | MAY | `dispatch` (default) or `public` (v1.1.14). `dispatch` is route-bearing data for current clients that submit tasks directly to selected nodes. `public` is a presentation-safe projection for dashboards/research: it MUST omit full `node_id`, `endpoint`, `transport_endpoint`, `transport_metadata`, raw CX key material, and any route URL/host while preserving safe score, region, health, reputation, capability and route-class signals. New clients SHOULD migrate to `POST /v1/dispatch/ticket` for explicit route-bearing dispatch. |

---

### 3.4 NODELIST (Directory → Client)

`GET /v1/discover` defaults to **route-dispatch** data because current IICP
consumers need a serving route to submit tasks node-to-node. The response SHOULD
include `data_class = "route_dispatch"` and `route_fields_present = true` so
callers do not confuse it with a public dashboard API. Public pages, dashboards
and audits that do not need to dispatch SHOULD use `GET /v1/registry/*` or
`GET /v1/discover?...&view=public`; the public view returns the same candidate
set as safe presentation metadata only.

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
      "node_policy_manifest": {
        "version": "2026-07-02",
        "jurisdiction": "DE",
        "remote_executor_can_read_prompt": true,
        "training_use": "none",
        "retention": {
          "task_payload": "none",
          "logs_days": 7
        },
        "subprocessors": ["self-hosted"],
        "unsupported_intents": [],
        "evidence": "self_attested"
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
| `node_policy_manifest` | object\|null | Optional public node policy manifest derived from REGISTER `policy_manifest`. The directory echoes safe fields and adds evidence: `self_attested` for unsigned manifests, `signed_verified` when an Ed25519 signature verifies, and `signed_invalid`/`signed_expired`/`signed_revoked`/`signed_superseded` only on diagnostic/admin or already-registered lifecycle surfaces because invalid, expired, revoked or superseded signed manifests MUST be rejected at registration. Clients MAY use it for policy pre-screening. |
| `node_policy_manifest.remote_executor_can_read_prompt` | boolean | `true` for normal remote inference: the selected executor can read the prompt it executes. This is a disclosure signal, not executor-blind confidentiality. |
| `node_policy_manifest.training_use` | string | One of `none`, `opt_in`, `provider_defined`. Unknown/absent MUST be treated conservatively as provider-defined. |
| `node_policy_manifest.retention` | object | Self-declared retention block; phase-1 clients should treat absent values as unknown/provider-defined. |
| `node_policy_manifest.verification` | object | Directory-computed verification result. Public fields include `status`, `algorithm`, `key_id`, `signed_at`, `expires_at`, `canonical_sha256`, `public_key_sha256`, and a redacted `error` string. |
| `node_policy_manifest.verification.status` | enum | `self_attested`, `signed_valid`, `signed_invalid`, `signed_expired`, `signed_revoked`, or `signed_superseded`. Public NODELIST/DISCOVER SHOULD normally expose only `self_attested` or `signed_valid`; `signed_revoked`/`signed_superseded` can appear for already-registered nodes when a directory-owned policy-key lifecycle record is added after registration. |
| `node_policy_manifest.manifest_identity_level` | string\|null | Directory-computed #602 identity/accountability layer beyond signature verification. Values: `self_attested`, `signed_valid`, `operator_bound`, `known_operator`, `rotated`, `revoked`. `operator_bound` means the policy-signing Ed25519 key matches a directory-verified operator delegation key. `signed_valid` is tamper evidence only; it is not legal identity, DPA acceptance or compliance proof. Strict/private profiles MAY require `operator_bound` or `known_operator` and MUST fail closed on `revoked` or `rotated`. |
| `node_policy_manifest.operator_fingerprint` | string\|null | Short hash of the verified operator key when the manifest is operator-bound. Full operator public keys remain directory-private. |
| `node_policy_manifest.policy_key_fingerprint` | string\|null | Short hash of the policy-signing key for display/revocation matching. Full policy/operator public keys are not exposed. |
| `node_policy_manifest.revoked_at` | ISO-8601\|null | Present only when the signed manifest or directory lifecycle registry carries a public-safe revocation timestamp. Past timestamps cause registration refusal with `signed_revoked`. |
| `node_policy_manifest.rotation_epoch` | integer\|null | Public-safe monotonically increasing rotation epoch when the operator declares policy-key rotation state or the directory lifecycle registry marks a key superseded. It is not sufficient by itself to prove a replacement key. |
| `node_policy_manifest.revocation_reason_class` | string\|null | Redacted revocation category such as `operator_request`, `compromise`, `superseded`, or `policy_violation`. Free-form details, private contact data and identity documents MUST NOT be exposed. |
| `node_policy_manifest.operator_governance` | object | Safe known-operator evidence for strict/private routing profiles: `known_operator`, current/outdated/missing terms and DPA status, accepted versions, acceptance method, and evidence class. It MUST NOT expose emails, identity documents, raw operator keys, raw nonces, or acceptance evidence documents. `known_operator=true` requires current terms and current DPA acceptance via operator-key challenge or an equivalent future verifier. This is not legal certification. |

**Directory-owned policy-key lifecycle registry (v1.1.15 / #608)**:
Directories MAY maintain an authoritative `policy_key_sha256 → status` lifecycle registry outside
the node's manifest. `status=revoked` yields `verification.status=signed_revoked` and
`manifest_identity_level=revoked`; `status=superseded` yields
`verification.status=signed_superseded` and `manifest_identity_level=rotated`. Both states MUST
fail closed for strict/private policy profiles and MUST be rejected on new REGISTER attempts using
that policy key. Public APIs expose only redacted lifecycle fields (`revoked_at`,
`rotation_epoch`, `revocation_reason_class`, short fingerprints); raw policy keys, replacement-key
hashes and private evidence references remain directory-private.

### 3.4.1 Client remote-routing policy profiles

Clients MAY apply prompt-safety routing profiles after DISCOVER and before submitting any task payload to a node. The directory remains prompt-free: policy evaluation uses discovery metadata such as region, CX key presence, and `node_policy_manifest`.

| Profile | Required behavior |
|---------|-------------------|
| `standard` | Default mesh use. Require CX/key-ready nodes unless an explicit debug plaintext override is active. |
| `sensitive` | Fail closed for remote executors. No task prompt is sent to remote nodes; local/browser execution is the preferred path. |
| `eu_restricted` | Require key-ready nodes whose region is inside the caller's EU/EEA allowlist. If none remain, refuse before prompt dispatch. |
| `strict_policy` | Require key-ready nodes and a signed-valid node policy manifest that declares no task-payload retention. Missing/unknown or unsigned policy values are treated conservatively and MUST be rejected before prompt dispatch. |
| `operator_bound_policy` | Require key-ready nodes plus `node_policy_manifest.manifest_identity_level >= operator_bound`. This is stricter accountability than `strict_policy`, but still not legal/DPA compliance proof. |
| `debug_override` | Explicit unsafe transition/debug mode. May allow plaintext/keyless dispatch only with a visible warning; MUST NOT be the default. |

If a routing policy rejects every candidate, clients MUST fail before task submission and MUST NOT include the prompt in directory requests, logs, telemetry, or rejected node calls.

#### Strict allowed-region profile (#600)

`region` in QUERY remains a preference, not exclusion. Compliance-sensitive callers that
need transfer-aware routing MUST apply an explicit fail-closed profile after prompt-free
discovery and before task submission.

| Profile | Parameters | Required behavior |
|---------|------------|-------------------|
| `allowed_regions_strict` | `allowed_regions: string[]`; optional `require_signed_policy_manifest`; optional `jurisdiction_allowlist` | Keep only key-ready nodes whose directory-safe `region` is in `allowed_regions`. If `require_signed_policy_manifest=true`, also require a signed-valid manifest whose `jurisdiction` or equivalent policy field is in `jurisdiction_allowlist`. If no eligible node remains, refuse before prompt dispatch. |
| `eu_restricted` | Convenience profile for EU/EEA allowlists | Alias of `allowed_regions_strict` with an EU/EEA region set chosen by the caller/controller. |

Region policy is a technical routing control, not GDPR transfer compliance proof. A region
label may be self-attested or directory-observed and must be interpreted with its trust source,
contracts/DPAs, subprocessors, transfer mechanisms and operator identity. Clients MUST NOT send
the prompt to the directory to evaluate region policy. Redacted routing receipts MAY record the
selected region and policy decision, but MUST NOT include prompt or response content.

#### Intent risk taxonomy (#613)

Public IICP directories classify intent URNs with a technical compliance-readiness
vocabulary: `prohibited`, `high_risk`, `transparency_risk`, and
`minimal_or_general`. The shared fixture is `spec/intent-risk-taxonomy.json`.
This is not legal advice and is not prompt-content moderation; it is a structural
routing guard for declared intent families.

Public mesh default behavior:

| Category | Public mesh default |
|----------|---------------------|
| `prohibited` | Refuse before registration, discovery, ticket issuance, or task dispatch. |
| `high_risk` | Refuse by default unless a future explicit private/compliance profile is configured. |
| `transparency_risk` | Allow, but user-facing surfaces SHOULD show AI/generated-content notice metadata where applicable. |
| `minimal_or_general` | Allow normal routing subject to ordinary privacy/security policy. |

Initial high-risk patterns cover employment/workforce decisions, education
admission/grading, credit or essential-services access, law enforcement,
migration/asylum/border/justice/democratic-process decisions, healthcare
decisions, critical-infrastructure safety components, and robotics/physical-world
control. The taxonomy MUST NOT block ordinary generic LLM chat, coding help,
summarization, translation, or educational explanation intents merely because a
prompt mentions those domains.

#### MCP/tool risk vocabulary (#601)

IICP may advertise MCP/CIP/tool capabilities, but public unknown callers MUST NOT receive
arbitrary remote-code, filesystem, browser, credential or system-control capability by default.
Tool manifests SHOULD include a risk label and required controls.

| Risk label | Examples | Public unknown default |
|------------|----------|------------------------|
| `benign_read` | static calculator, format conversion, schema validation | MAY be advertised if authenticated task endpoint and redacted logging are in place. |
| `data_read` | read selected document, list limited resource, query bounded database view | DENY unless explicit data scope and caller authorization exist. |
| `network_fetch` | fetch URL, crawl site, call third-party API | DENY unless SSRF/rate/domain controls exist. |
| `file_read` | read local file or directory | DENY unless sandboxed path allowlist and caller authorization exist. |
| `file_write` | write/modify/delete local files | DENY unless sandbox, least privilege, approval policy and rollback/audit exist. |
| `shell_exec` | bash/shell/exec/run command/eval | DENY by default for public callers; requires explicit dangerous-tool policy, sandbox, authz and audit. |
| `browser_control` | remote browser/computer-use actions | DENY by default; requires sandbox, origin policy, approval and audit. |
| `credential_access` | read/use secrets, wallets, tokens, SSH keys | DENY by default; public mesh exposure SHOULD be prohibited unless a private controller policy explicitly permits it. |
| `system_control` | service restart, package install, firewall, kernel/OS settings | DENY by default; requires privileged sandbox/agent, human approval gates and rollback. |
| `physical_world` | robot, drone, IoT actuator, medical/industrial device | DENY by default; requires permissioned deployment and safety case. |
| `regulated_decision` | employment, credit, education, healthcare, public benefits or legal/significant decisions | DENY by default unless a domain-specific high-risk compliance package and human oversight are in force. |

Minimum controls for any non-`benign_read` public tool are: explicit advertisement, caller
authentication, caller authorization, bounded input schema, sandbox/least privilege, rate limits,
redacted logs/receipts, retention policy, and an operator-visible audit trail. These controls are
risk-reduction measures, not legal compliance proof.

| `cip_conformance_level` | string | One of `"CIP-None"`, `"CIP-Consumer"`, `"CIP-Provider"`, `"CIP-Full"`. `"CIP-None"` means the node has not opted into any CIP role (equivalent to not declared). Per spec §5.2. |
| `health_label` | string\|null | ADR-044 composed health label: `"healthy"` (score ≥0.85), `"degraded"` (≥0.65), `"impaired"` (≥0.40), `"critical"` (<0.40), `"offline"`. Computed from endpoint-liveness signals only — reachability 0.70, latency 0.30 (50–500 ms curve). Reputation and task-success were removed in #492 (ADR-044 amendment) — health reflects operational liveness, not earned history. Score is a float in [0.0, 1.0] (normalised from internal 0–100 scale by v1.10.6+). A reachable node with no latency evidence is capped below `"healthy"` until latency evidence arrives; consumers SHOULD treat the additive `health.confidence`/`evidence_level` fields on node detail/registry profile as the proof-strength signal. `null` against directories predating v1.10.0. |
| `exposure_mode` | string\|null | ADR-043 8-category network exposure classification (e.g. `"ipv4_public_direct"`, `"cgnat_upnp"`, `"ipv6_gua"`). `null` if node has not run qualification. |
| `reachability_tier` | string | v1.10.0, ADR-047: `"direct"` (dial-back-verified) or `"relay"` (heartbeating with a routable surface but not directly dial-back-verified — reachable via relay; e.g. CGNAT/IPv6 where the directory has no egress). Default discover returns `direct`+`relay`; a heartbeating node is never hidden purely for lacking dial-back. Clients SHOULD prefer `direct` and fall back to `relay`. |
| `route_evidence` | string\|null | Evidence basis for the currently advertised route. Values: `directory_observed_ipv4`, `directory_observed_ipv6`, `external_probe_ipv6`, `directory_observed` (legacy aggregate), `self_attested`, or `missing`. Absence of IPv6 egress proof is not failure; IPv6 literal routes without independent proof remain self-attested/direct-unverified. |
| `probe_source` | string\|null | Optional low-entropy source label for independent reachability evidence, e.g. `seed_directory`, `external_ipv6_worker`. Must not expose private worker credentials or raw probe logs. |
| `input_modalities` | array | v1.10.0, ADR-046: union of input modalities the node's capabilities for this intent accept (`["text"]` default; `["text","image"]` for vision). Lets clients confirm multimodal support without a second round-trip; see `?modality=` (§3.3). |
| `backend` | string\|null | Detected backend server flavor the node runs — one of `ollama`/`lmstudio`/`vllm`/`llamacpp`/`anthropic`/`custom`. Self-attested at REGISTER (the SDK auto-detects it by fingerprinting the backend's endpoints/headers); informational (operator/consumer visibility), not used for routing. `null` if unreported. Also accepted as an optional REGISTER field (§3.1). |
| `transport_method` | string\|null | How the node is reachable for the native IICP transport (`"direct"`, `"upnp_mapped"`, `"stun_hole_punch"`, `"turn_relay"`, `"external_tunnel"`, `"webrtc_datachannel"`, …). Mirrors the REGISTER value (§3.1 / ADR-041). `external_tunnel` may be an operator-managed stable tunnel or an accountless temporary tunnel; clients treat it as an endpoint reachability shape, not as a guarantee about provider durability. |
| `nat_type` | string\|null | Detected NAT topology (ADR-041). Advisory; clients MAY prefer `"direct"`/`"full_cone"`. |
| `transport_metadata` | object\|null | Transport-specific detail (relay endpoint, candidate list). Shape per ADR-041; opaque to clients that only use `endpoint`. |
| `address_family` | string\|null | `"ipv4"`, `"ipv6"`, or `"dual"` (maintainer directive 2026-05-27). Lets IPv6-only clients filter. |
| `relay_capable` | boolean | `true` if the node can act as a relay for NAT-bound peers (Tier-3 reachability). |
| `cx_public_key` | object\|null | Canonical IICP-CX confidentiality key (iicp-confidentiality §3.2): `{algorithm, encoding, key, key_id, not_after, hybrid_pq}`. Present when the node advertises E2E payload encryption support. `null` = node accepts plaintext only. Clients MUST use this to encrypt payloads when `X-IICP-Require-E2E` is set. |
| `sdk_language` / `sdk_version` | string\|null | Advisory provenance of the serving node's SDK (#338). Informational only. |
| `sdk_status` / `sdk_baseline_version` / `upgrade_required` | string/string/boolean | Directory-computed SDK-baseline posture. `sdk_status` is `"current"`, `"downlevel"`, or `"unknown"` against the directory's current baseline. Downlevel/unknown nodes remain visible during transition but are demoted and SHOULD NOT be preferred for privacy-sensitive routing. |
| `key_ready` / `privacy_routing_status` | boolean/string | `key_ready=true` when the node advertises canonical `cx_public_key`. `privacy_routing_status` is `"key_ready"` or `"transitional"`; transitional nodes can serve legacy/plaintext paths but MUST NOT be treated as fully CX-ready. |
| `auto_update` | object | Optional self-reported updater evidence: `{enabled, interval_s, latest_seen, last_checked_at, error_class, evidence}`. Advisory only; the directory still computes routing/compliance from observed `sdk_version` and `cx_public_key`. |
| `models` / `quantization` / `inference_engine` | array\|string\|null | Advisory capability detail (iicp-core §2.1). The directory MUST NOT reject unrecognized values. |
| `operator_display_name` | string\|null | v0.10.3, #463: the operator's public `display_name`, resolved from the operator record by `operator_pubkey` for nodes bound via a verified ADR-045 delegation (§3.1). `null` when the node is not operator-bound. The `operator_pubkey` itself is directory-private and is **never** served; only the human-readable display_name appears. Surfaced in `/v1/discover` and node-detail so consumers see who operates a node. |
| `operator_fingerprint` | string\|null | v1.1.1, #525: a short public fingerprint derived from the verified operator key, surfaced only alongside `operator_display_name`. It lets clients disambiguate look-alike names without exposing the directory-private `operator_pubkey`. `null` when the node is not operator-bound or no display name is set. |

**`probation` (clarification, R3)**: `probation` is computed server-side and used to *filter* discover results (probation nodes are excluded from `?qos=interactive`/`realtime`), but the discover NODELIST does **not** include a `probation` field per node. The full `probation` boolean is surfaced only by `GET /v1/node/{id}` (node-detail). Clients needing the flag query node-detail.

Only nodes with `available = true` AND `last_seen` within 90s are returned.
Score computed per ADR-008. Nodes with score < 0.1 are excluded.

**Public presentation view (v1.1.14 / #611)**:

```json
{
  "nodes": [
    {
      "node_id_prefix": "b30aee67",
      "region": "eu-central",
      "score": 0.91,
      "route_class": "external_tunnel",
      "key_ready": true,
      "reputation_tier": "gold",
      "models": ["qwen2.5:0.5b"]
    }
  ],
  "view": "public",
  "data_class": "public_presentation",
  "route_fields_present": false,
  "redaction": {
    "node_id": "node_id_prefix_only",
    "endpoint": "omitted",
    "transport_endpoint": "omitted",
    "transport_metadata": "omitted",
    "cx_public_key": "key_ready_boolean_only"
  }
}
```

In `view=public`, directories MUST NOT expose full endpoint URLs, tunnel hostnames,
native transport URLs, full UUID node IDs, raw CX public keys or opaque transport
metadata. This view is not sufficient for task dispatch. During the adoption
window, existing consumers MAY still use default route-dispatch discovery; new
consumers SHOULD request an explicit dispatch ticket before task submission.

**Ticketed dispatch discovery (v1.1.16 / #612)**:

```
POST /v1/dispatch/ticket
{
  "intent": "urn:iicp:intent:llm:chat:v1",
  "exclude_node_id_prefixes": ["b30aee67"]
}
```

The request is control-plane only. It MUST NOT contain `prompt`, `messages`,
`payload`, `input`, `chat`, `content`, `response`, or any task body. The
directory returns one concrete route plus an Ed25519-signed ticket:

```json
{
  "ticket": "b64url_payload.sig_hex",
  "ticket_id_prefix": "a1b2c3d4e5f6",
  "expires_at": 1780000000,
  "intent": "urn:iicp:intent:llm:chat:v1",
  "node_id": "uuid",
  "node_id_prefix": "b30aee67",
  "route": {
    "node_id": "uuid",
    "endpoint": "https://node.example.com",
    "transport_endpoint": "iicpsec://node.example.com",
    "cx_public_key": {"algorithm": "X25519", "key": "..."}
  },
  "algorithm": "ed25519",
  "data_class": "ticketed_route_dispatch",
  "route_fields_present": true,
  "prompt_payload_accepted": false
}
```

Tickets use domain `iicp:dispatch-route-ticket:v1`, type
`dispatch-route-ticket`, audience `iicp.directory.dispatch`, and are scoped to
one `node_id`, one `intent`, and a short expiry. They authorize route disclosure
only; they do not move the task payload through the directory and do not prove
legal/privacy compliance. Implementations MUST treat ticket IDs as log-safe only
when redacted/truncated; full tickets are bearer route material and SHOULD NOT be
written to public logs. A node selector is optional: without `node_id` or a
unique `node_id_prefix`, the directory MAY ticket the top eligible candidate.
Clients MAY send up to ten `exclude_node_id_prefixes` after failed direct
attempts. The directory MUST exclude those candidates before issuing the next
route. This preserves bounded client fallback without returning a bulk list of
active route addresses.

Directories MAY publish anonymous adoption evidence in public stats as
`dispatch_discovery_adoption`. Such counters MUST be aggregate-only and MUST
NOT retain caller addresses, identifiers, route URLs, ticket tokens or task
content. Read-only dashboards, documentation examples and operational inventory
checks MUST use `view=public`; otherwise they contaminate route-migration
evidence. The reference directory retains daily aggregate mode counts for 30
days and reports ticketed, legacy route-discovery and public-view request totals
over a seven-day window. It also reports a configured measurement epoch, minimum
sample, sustained-day threshold and `cutover_eligible`; pre-epoch rows remain
retained but MUST NOT influence a strict cutover decision. Anonymous counters
remain heuristic and MUST NOT be represented as verified unique-user adoption.


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
> uses the sender's Ed25519 gossip `public_key` — already registered with the directory
> and served on node detail / peer cache — so any receiver can verify offline, and no
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
  body bytes, produced with the secret key whose public half the sender registered as the
  gossip signing `public_key` (stored internally as `gossip_public_key`). Receiver MUST verify
  it against that Ed25519 gossip key, resolved from the receiver's peer cache or from directory
  node detail (`GET /v1/node/{sender_id}`, `public_key` field). This is distinct from the
  IICP-CX X25519 `cx_public_key`. Invalid or unverifiable signature → 403.
- Sender MUST NOT include `Authorization: Bearer <node_token>` — the directory credential
  never travels to peers. Receiver MUST ignore any Authorization header on this endpoint
  (it carries no trust).
- A sender without a registered gossip `public_key` cannot participate in signed gossip;
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
| `unauthorized` | 401 | Missing sender identity or missing `X-IICP-Signature` |
| `forbidden` | 403 | Invalid or unverifiable Ed25519 gossip signature |
| `conflict` | 409 | Replayed Ed25519 signature within the replay window |
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
> transition event whenever a node's direct `public_reachable` flag flips. That flag is one
> route-eligibility signal, not the only discovery switch: relay-tier nodes may remain visible
> when `reachability_tier="relay"` and route evidence supports the relay path (§3.4/§7).
> A direct-route demotion that changes discoverability is otherwise invisible in the audit trail. Emitted at the two
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
| `sdk_adoption` | **Adoption telemetry (#531)** for the §6.1 capability-migration framework: `total_active` (count of active nodes), `by_language` (`{rust,python,typescript,browser,unknown}` → count), `by_version` (`sdk_version` → count, descending). Self-reported provenance (advisory), but the objective input that gates adoption-thresholded hard-enforcement stages. SHOULD be exposed per DIR-MIG-01. |

**Directory DB retention (operational, non-payload):** implementations SHOULD bound raw operational telemetry so the directory database grows slowly without weakening control-plane evidence. The reference directory retains raw `iicp_telemetry_probes` for 14 days, detailed `iicp_telemetry_aggregates` for 30 days, `proxy_telemetry` for 30 days, and high-volume `HEARTBEAT` events for 1 day by default. Retention jobs MUST NOT drop credits, reputation, node/operator records or signed ledger events, and they MUST NOT export prompt payloads. Production migrations or pruning runs SHOULD be surrounded by pre- and post-change database backups.

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
| `IICP-E034` | 429 | Too many registration attempts from this source IP (60/min per source IP — see iicp-core.md §7) |
| `IICP-E035` | 422 | Non-routable endpoint host (ADR-041 invariant; `RoutableEndpoint` validator, iter-1365 / #325) |
| `IICP-E049` | 403 | Re-registration with a changed `cx_public_key` requires a valid `current_node_token` proving ownership. **Normative (MUST)**: if a re-registration request supplies a `cx_public_key` that differs from the stored value, the directory MUST verify that `current_node_token` bcrypt-matches the stored token hash. Failure → 403 IICP-E049. This gate prevents unauthenticated key-substitution attacks. (RT-6-1, #390, iter-1807) |
| `IICP-E050` | 403 | Re-registration that changes a **routing-critical field** (`endpoint`, `transport_endpoint`, `relay_endpoint`) requires proof that the caller controls the existing `node_id`. **Normative (MUST)**: if a re-registration request changes any routing-critical field from the stored value, the directory MUST accept the change only if **either** (a) `current_node_token` bcrypt-matches the stored token hash (**ownership proof**), **or** (b) the node's previously-stored endpoint is **verified absent** — a directory liveness probe `GET {stored_endpoint}/iicp/health` fails within the registration liveness budget (**old-endpoint absence**, the legitimate-rotation path: a rotating tunnel/CGNAT node's prior URL is already dead). If neither holds (old endpoint still answers AND no valid `current_node_token`), the directory MUST reject with 403 IICP-E050. This extends the RT-6-1 ownership pattern (IICP-E049) to routing fields, preventing unauthenticated endpoint-substitution (node-traffic hijack) while preserving token-less re-registration for genuine endpoint rotation. **Hardening (E′, MUST once adoption-gated per §6.1)**: for nodes that have an `operator_pubkey` or `cx_public_key` on record (**secured nodes**), the directory MUST require path (a) — `current_node_token` — regardless of old-endpoint liveness, so a secured node cannot be hijacked by an attacker who first disables its old endpoint. (RT-6-2, #529, #522) |

### 3.12 Consumer Token Issuance (Phase 2, #496)

**Phase**: 2
**Status**: Implemented (PHP directory v1.10.32, iicp-client v0.7.52)

The directory acts as a trusted issuer of short-lived consumer tokens that allow a proxy
(caller) to authenticate to a provider (adapter/node) without sharing its `node_token`.

**Token format**: `<base64url_payload>.<sig_hex>`
where the payload is a JSON object and the signature is Ed25519 over
`b"iicp:consumer-token:v1\n" + base64url_payload_bytes`.

**Payload fields:**

| Field | Type | Description |
|-------|------|-------------|
| `v` | integer | Version — always `1` |
| `iss` | string | Issuer — the directory's domain |
| `sub` | string | Subject — caller node_id |
| `aud` | string | Audience — target node_id |
| `intent` | string | Intent URN (or `"*"` for any intent) |
| `iat` | integer | Issued-at (Unix seconds) |
| `exp` | integer | Expiry (Unix seconds; `iat + 300` by default) |

**Endpoints:**

`GET /api/v1/directory-key` — Returns the directory's Ed25519 public key. No auth required.

Response (200):
```json
{ "public_key": "<64-char hex>", "algorithm": "ed25519" }
```

Returns `503` when the genesis key is not configured on the directory.

`POST /api/v1/consumer-token` — Issues a consumer token. Requires `Authorization: Bearer <node_token>` (JWT form, identifies the caller).

Request body:
```json
{ "target_node_id": "<uuid>", "intent": "urn:iicp:intent:..." }
```

Response (201):
```json
{ "token": "<b64url>.<sig_hex>", "expires_at": <unix_s>, "caller_node_id": "...", "target_node_id": "...", "intent": "..." }
```

Error responses: `401` when caller auth missing, `503` when genesis key not configured, `404` when `target_node_id` is not registered.

**Provider validation (normative):**

A provider (adapter or node) MUST accept `X-IICP-Consumer-Token: <token>` on `POST /v1/task` as an alternative to `body.auth.node_token` when:
- The signature is valid (Ed25519 over domain+payload using the directory's public key).
- `exp` is in the future (providers MAY allow a 10-second grace).
- `aud` matches the provider's own `node_id`.
- `intent` matches the task's intent or is `"*"`.

The provider obtains the directory public key from `GET /api/v1/directory-key` during registration and caches it. If the key is unavailable, the provider MUST fall back to `auth.node_token` validation only.

**Rate limiting**: `GET /api/v1/directory-key`: 30 req/min. `POST /api/v1/consumer-token`: 60 req/min (per authenticated node).

---

### 3.13 WebRTC Signaling Mailbox (Directory control plane, draft, #523)

A browser tab cannot bind a public socket or spawn an external tunnel process. For browser
providers, the directory MAY provide a short-lived **signaling mailbox** so a consumer and
a browser provider can exchange WebRTC setup metadata (SDP offer/answer and ICE candidates).
The mailbox is control-plane only. It MUST NOT carry task CALL payloads, model prompts, tool
inputs, files, or task results. Once WebRTC establishes a DataChannel, task framing flows
peer-to-peer over that channel.

This section defines the API contract before implementation; directories MAY omit it and
remain conformant with the base IICP-DIR profile.

#### 3.13.1 Resources

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/v1/signal/mailboxes` | node token | Provider creates or refreshes its own mailbox and receives `mailbox_id`, `expires_at`, and posting/polling URLs. |
| `POST` | `/v1/signal/mailboxes/{mailbox_id}/messages` | consumer token or node token | Sender posts one SDP/ICE signaling message addressed to the mailbox owner. |
| `GET` | `/v1/signal/mailboxes/{mailbox_id}/messages?after=<cursor>` | node token for provider mailbox owner; consumer token/node token for caller-owned reply mailbox | Long-poll (≤25 s) for messages after the cursor. |
| `DELETE` | `/v1/signal/mailboxes/{mailbox_id}` | mailbox owner node token | Owner explicitly closes the mailbox. |

A consumer that cannot receive messages directly MAY create an ephemeral **reply mailbox** using
the same resource model. Reply mailboxes MUST have the same or shorter TTL and MUST be scoped to
the initiating handshake.

#### 3.13.2 Message envelope

```json
{
  "message_id": "uuid-v4",
  "type": "offer",
  "from": "consumer-or-node-id",
  "to": "provider-node-id",
  "reply_mailbox_id": "optional-opaque-id",
  "session_id": "uuid-v4",
  "body": {"sdp": "..."},
  "created_at": "2026-06-21T14:00:00Z",
  "expires_at": "2026-06-21T14:02:00Z"
}
```

`type` MUST be one of `offer`, `answer`, `ice_candidate`, `end_of_candidates`, `close`,
or `error`. `body` MUST contain only WebRTC signaling metadata. The directory MAY validate
message shape and size but MUST NOT interpret SDP semantics beyond abuse controls.

#### 3.13.3 TTL, size, auth and abuse controls

- Mailbox TTL: REQUIRED, maximum 10 minutes; RECOMMENDED default 120 seconds. A refresh
  requires the owner node token and MUST NOT extend a single mailbox beyond 30 minutes total.
- Message TTL: REQUIRED, maximum 120 seconds; expired messages MUST NOT be returned.
- Size cap: each message body MUST be capped (RECOMMENDED ≤ 64 KiB after JSON encoding);
  oversize messages return `413 IICP-E053`.
- Rate limits: directories MUST rate-limit mailbox creation, message posting and polling per
  source IP, mailbox and authenticated principal. Recommended initial ceilings: 30 creates/hour
  per node, 120 posts/minute per mailbox, and 30 concurrent long-polls per mailbox.
- Auth: provider mailbox create/refresh/delete MUST require the provider's node token. Posting
  to a provider mailbox MUST require either a short-lived consumer token (§3.12) or a node token;
  anonymous public posting is non-conformant. Polling a provider mailbox MUST require its owner
  node token.
- Cleanup: directory implementations MUST delete expired mailboxes/messages opportunistically
  and SHOULD run a periodic cleanup job.

#### 3.13.4 Privacy, routing and fallback semantics

SDP and ICE can reveal network metadata (candidate IPs, ports and user-agent/network hints).
Clients and UI SHOULD say this plainly. Signaling metadata is still control-plane metadata;
task payloads MUST remain off-directory. A directory that observes task content through this
mailbox is non-conformant.

WebRTC is best-effort. Consumers SHOULD attempt it only for live `webrtc_datachannel` metadata,
SHOULD bound ICE setup time (RECOMMENDED 8–15 seconds), and MAY fall back to relay (§7) when the
node advertises a relay path and relay trust/confidentiality policy allows it. TURN fallback is
reserved for a later profile because it reintroduces relay trust, cost and privacy concerns.

### 3.14 Operational timers profile (reference defaults)

These defaults are gathered here to reduce implementation drift. A deployment MAY
tune them, but SHOULD keep public behaviour compatible unless a sub-spec says
otherwise.

| Area | Default / range | Source / note |
|------|-----------------|---------------|
| Provider heartbeat interval | 30 seconds | Directory PONG `next_heartbeat_ms=30000` reference default. |
| Directory stale-node window | 90 seconds | Nodes older than this are excluded from default discover/active-node counts unless a relay-tier policy explicitly keeps them routable. |
| Directory node probe interval | 300 seconds | Active endpoint probe cadence (`DIR-PROBE-NODE-01`). |
| Directory node probe timeout | 5 seconds | Probe connect/HTTP timeout. |
| Relay long-poll maximum | ≤25 seconds | HTTP relay `pull` upper bound. |
| Relay session liveness | 90 seconds | Bound session alive while native connection is held or HTTP-poll worker has pulled within this window. |
| WebRTC ICE attempt | 8–15 seconds | Consumer setup bound before fallback. |
| WebRTC mailbox default TTL | 120 seconds | Mailbox/messages are short-lived control-plane metadata. |
| WebRTC mailbox maximum TTL | 10 minutes | Advertised handles SHOULD NOT live longer without renewal. |
| SDK updater check interval | 3600 seconds | Current official SDK default for unattended update checks; minimum accepted value is 300 seconds. |
| Accountless external-tunnel create spacing | 120 seconds | Host-wide SDK back-pressure default (§3.1). |
| Accountless external-tunnel create lease | 45 seconds | Host-wide SDK serialization default (§3.1). |
| Accountless external-tunnel provider cooldown | 900 seconds | Persistent cooldown after 429 / Cloudflare 1015-class evidence (§3.1). |
| External-tunnel health probe interval | 30 seconds | Reference SDK tunnel monitor cadence. |
| External-tunnel rebuild threshold | 2 failed health probes | Reference SDK treats repeated failed probes as twilight/recovery before rebuilding. |
| External-tunnel dead retry backoff | 30–300 seconds | Reference SDK bounded retry/backoff range; supervised services may exit/restart according to `IICP_TUNNEL_DEAD_POLICY`. |

### 3.15 Route self-recovery contract (#581)

A node process can be alive and heartbeating while its advertised route is stale,
rate-limited, sleeping, or not visible from the directory/browser path. SDKs MUST
treat this as a deterministic recovery state machine, not as a reason for manual
or LLM-based diagnosis.

#### 3.15.1 Local observations

Reference SDKs SHOULD evaluate these observations on every recovery tick (30s
recommended, aligned with heartbeat/tunnel probe cadence):

| Observation | Meaning |
|-------------|---------|
| `local_health` | `GET /iicp/health` on the serving process succeeds locally. |
| `backend_health` | Configured model/backend health check succeeds or returns a recoverable busy/loading state. |
| `directory_heartbeat` | Last heartbeat/register call was accepted by the directory. |
| `directory_visible` | The node appears in discover/registry for at least one advertised intent when it claims public, relay or browser-usable reachability. |
| `route_probe` | The current advertised endpoint passes the SDK's local/directory-compatible health probe. |
| `tunnel_state` | External tunnel is `not_needed`, `starting`, `healthy`, `dead`, `rate_limited`, or `cooldown`. |
| `supervisor_mode` | `supervised` when launchd/systemd/Docker restart policy is expected; otherwise `unsupervised`. |

#### 3.15.2 Recovery states

SDKs SHOULD expose these states in `doctor --json` and MAY send the safe subset
in heartbeat metadata. Directory implementations MAY surface the same labels in
registry `recovery_state`/`route_recovery_hint` fields.

| State | Required interpretation | Directory routing posture |
|-------|-------------------------|---------------------------|
| `stable` | Backend, local health, directory heartbeat and current route evidence agree. | Eligible if ordinary routing rules pass. |
| `route_mismatch` | The SDK is serving on a different endpoint/route than the directory currently advertises. | Old dead/stale endpoint MUST NOT remain discover-routable after confirmed failure. |
| `endpoint_dead` | Advertised endpoint fails bounded health probes. | Remove/demote route until re-register publishes a valid route or cooldown clears. |
| `tunnel_starting` | Direct route failed and the SDK is creating or binding a tunnel/relay fallback. | May be visible as recovering; clients SHOULD prefer stable alternatives. |
| `tunnel_cooldown` | Tunnel provider rate limit or 1015-class evidence triggered host-wide cooldown. | Do not create tunnel storms; show recovery/cooldown without leaking tunnel secrets. |
| `backend_attention` | Backend/model is unavailable, loading too long, or repeatedly errors while route is otherwise valid. | Node may heartbeat but should not be preferred for matching intents until backend recovers. |
| `supervisor_restart_pending` | Bounded retries were exhausted and a supervised process should exit with a distinct temporary-failure code. | Temporary recovery window; supervisor should restart the node. |
| `operator_action_needed` | Unsupervised recovery exhausted or configuration is missing/invalid. | Not discover-routable for affected intents until operator fixes configuration. |
| `unavailable` | No recent heartbeat or process cannot prove liveness. | Not eligible for default discover. |

#### 3.15.3 Recovery action enum

`doctor --json` and SDK logs SHOULD use this action enum so operators and tests
can compare clients:

| Action | When to use |
|--------|-------------|
| `none` | State is stable or no action is needed. |
| `reregister` | Route changed, stale endpoint was withdrawn, or public/direct/tunnel metadata must be refreshed. |
| `wait_cooldown` | Tunnel provider back-pressure or bounded retry backoff is active. |
| `restart_self` | Supervised retry budget exhausted; exit with a documented temporary-failure code so launchd/systemd/Docker restarts. |
| `operator_endpoint_needed` | No routable/direct/tunnel/relay route can be established without configuration or credentials. |
| `backend_attention` | Backend/model health blocks serving and route changes would not help. |

Supervised clients SHOULD prefer bounded retry followed by `restart_self`.
Unsupervised clients SHOULD prefer bounded retry plus a clear local message and
MUST NOT spin up repeated tunnel creation attempts while cooldown is active.

#### 3.15.4 Safe directory-visible fields

Heartbeat/registry metadata MAY include only low-entropy recovery summaries:

```json
{
  "recovery_state": "tunnel_cooldown",
  "route_recovery_hint": "tunnel_provider_rate_limited",
  "recovery_action": "wait_cooldown",
  "recovery_next_retry_at": "2026-07-08T16:50:00Z",
  "recovery_attempt": 2,
  "recovery_supervised": true
}
```

These fields MUST NOT include full node tokens, tunnel secret subdomains beyond
what is already the active dispatch endpoint, provider account identifiers,
private IP addresses, raw probe logs, prompts, or backend credentials. They are
advisory explanation signals only; they MUST NOT weaken the existing rule that a
confirmed dead endpoint is not discover-routable until a valid current route is
published or verified.

#### 3.15.5 Cross-SDK parity matrix

All official SDK flavours SHOULD converge on this matrix before self-recovery is
called stable:

| Scenario | Expected state/action | Required test shape |
|----------|-----------------------|---------------------|
| Docker direct route healthy | `stable` / `none` | Container starts, registers, heartbeats, discover sees current endpoint. |
| Laptop sleep/wake | transient `route_mismatch` or `tunnel_starting`, then `stable` / `reregister` | Simulate heartbeat gap plus stale tunnel; verify automatic re-register without manual restart. |
| Tunnel dead after route was published | `endpoint_dead` → `tunnel_starting` / `reregister` | Kill tunnel, verify stale endpoint withdrawal and new route registration. |
| Tunnel provider rate limit | `tunnel_cooldown` / `wait_cooldown` | Mock 429/1015, verify host-wide cooldown and no tunnel storm. |
| Backend down but route alive | `backend_attention` / `backend_attention` | Stop backend, verify route logic does not rebuild tunnel unnecessarily. |
| Supervised retry budget exhausted | `supervisor_restart_pending` / `restart_self` | Mock persistent tempfail, verify distinct exit code and supervisor restart. |
| Unsupervised retry budget exhausted | `operator_action_needed` / `operator_endpoint_needed` | Run without supervisor, verify actionable local output and no endless restarts. |
| Browser-node relay missing | `tunnel_starting` or `operator_action_needed` depending relay discovery | Browser/web-node test verifies no directory secret leakage and clear UI state. |

Implementation issues for Rust, Python, TypeScript and browser-node MUST link to
this section and report which rows are passing in Docker or browser tests.

### 3.16 Operator-key self-service and identity lifecycle (#599/#609/#618)

The reference directory exposes a prompt-free, operator-key authenticated API for
current governance acceptance and data-subject requests. It is a technical
self-service foundation, not a legal-compliance certificate or a substitute for
operator-specific controller/processor analysis.

| Route | Purpose | Additional rule |
|-------|---------|-----------------|
| `POST /v1/operator/challenge` | Issue a single-use five-minute nonce for a known operator key. | Response is `no-store` and exposes only a short fingerprint plus current terms/DPA versions. |
| `POST /v1/operator/acceptance` | Record current terms and DPA version acknowledgement. | Requires a fresh challenge and operator Ed25519 signature. |
| `POST /v1/operator/key/rotate` | Move an active operator identity to a successor key. | Requires one fresh challenge plus signatures from both the current and successor Ed25519 keys; linked node continuity moves atomically while independently signed policy manifests are not rewritten. |
| `POST /v1/operator/key/revoke` | Revoke an active operator identity. | Requires a signed `confirm=true`; linked nodes become operator-unverified until explicitly re-delegated while historical ledgers follow existing retention rules. |
| `POST /v1/operator/dsr/export` | Export records linked to the authenticated operator. | Selector is derived from the signed operator key, never caller-provided identity data. |
| `POST /v1/operator/dsr/restrict` | Restrict matching operator records. | Requires signed `confirm=true`. |
| `POST /v1/operator/dsr/anonymize` | Anonymize matching operator records under the existing retention rules. | Requires signed `confirm=true`; no cross-operator selector is accepted. |

Canonical signing bytes are UTF-8:

```text
iicp:operator:self-service:v1\n
<compact JSON object with alphabetically sorted top-level keys>
```

The JSON object contains `action`, `operator_pub`, `nonce`, `ts`, and the
action-specific fields, but excludes `sig` and (for rotation) `new_key_sig`.
`action` is `accept`, `key_rotate`, `key_rotate_successor`, `key_revoke`,
`dsr_export`, `dsr_restrict`, or `dsr_anonymize`. `ts` MUST be within ±300 seconds. A challenge
MUST be single-use and expire after 300 seconds. Signatures use Ed25519 and are
base64 encoded. Error responses and successful responses MUST be `no-store` and
MUST NOT return raw stored operator keys, raw nonces, private evidence documents,
tokens, contact data, or task content.

Normal rotation is an explicit continuity operation, not a silent key replacement:
the old key becomes `rotated` and cannot create new self-service or delegation
claims; the new key becomes active only after both key-control proofs verify. Only
safe fingerprints, timestamp, epoch and redacted reason class may be public. A lost
or compromised key MUST NOT receive automatic continuity transfer.

Official SDKs SHOULD expose byte-identical canonicalization/signing helpers so a
future portal or CLI can keep the private operator key local. Browser self-service
MUST NOT upload the private key to the directory.

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
- PEER_EXCHANGE MUST NOT use or transmit node_token credentials. It MUST validate
  `X-IICP-Signature` as an Ed25519 detached signature from the sender's registered
  gossip public key, and MUST apply timestamp/replay checks. [→ DIR-HB-05, Phase 2]

### 6.1 Capability Migration Framework (normative)

This section is **normative** (RFC 2119). It governs how any behaviour change
that affects clients is rolled out, so a security or protocol upgrade can never
fracture the running mesh by requiring a capability before clients can provide
it.

**Core rule (MUST)**: a directory **MUST NOT require** a client capability
before clients can provide it. Every client-affecting change MUST pass through
five stages, in order:

1. **Spec-normative** — the new rule is written here (or in the relevant
   sub-spec) before any enforcing code ships.
2. **Additive client capability** — clients gain the capability (a new field,
   signature, or behaviour) in a **published, backwards-compatible** release.
   The directory MUST accept requests both with and without it (accept-but-do-
   not-require).
3. **Measured adoption** — the directory measures real-world uptake via the
   recorded `sdk_version` of active nodes (see below). Adoption is **measured,
   not assumed**.
4. **Soft-enforce** — the directory **uses the capability when present** but
   MUST NOT reject a request for lacking it.
5. **Hard-enforce** — the directory **requires** the capability. This stage
   MUST be gated on a published **adoption threshold** (RECOMMENDED: ≥ 90% of
   active nodes on a version that provides it, sustained ≥ 14 days), MUST
   provide a **grace window**, and MUST reject non-compliant requests with a
   distinct, documented upgrade error (`IICP-Exxx`, message naming the required
   capability and minimum version).

**Adoption measurement (SHOULD)**: a directory SHOULD expose the `sdk_version`
(and `sdk_language`) distribution of active nodes (e.g. in the Public Stats
endpoint or an operator-only endpoint) so the Stage-3 threshold can be
evaluated objectively.

**Deprecation/grace pattern (MUST for removals)**: removing or tightening an
existing behaviour MUST follow the same ladder in reverse — announce in the
changelog, soft-deprecate (warn, still accept), then hard-remove only after the
adoption threshold + grace window, with a documented error.

**Conformance**: a hard-enforcement change that ships without a preceding
additive-capability release and a measured adoption gate is **non-conformant**
with this framework. [→ DIR-MIG-01]

---

## 7. Relay Transport (normative)

The relay-as-last-resort transport (ADR-041 Tier-3, #341/#450) lets a worker
behind CGNAT/symmetric-NAT serve tasks without inbound reachability: it holds an
**outbound** session to a `relay_capable` node, which forwards tasks to it and
returns results. The directory advertises relay capability and reachability
(`relay_capable`, `reachability_tier`, `transport_method=turn_relay`, §3.1/§3.4)
and, under §7.4, mediates relay-bind authorization. The relay endpoints below
are served by the **relay node**, not the directory.

"Last resort" is a policy boundary, not an ordering mandate for every SDK
startup path. §7 defines the relay contract once relay routing is chosen. The
reference SDK reachability policy in §3.1/`iicp-semantics.md §6.4` may try a
safe external tunnel before auto-electing a relay, unless tunnel fallback is
disabled or an operator explicitly configures relay-first behaviour.

### 7.1 Transports

A relay MUST offer at least one of:
- **Native TCP** (`RELAY_BIND`/`RELAY_ACK` over the IICP framing, §iicp-framing) —
  the worker connects out and is pushed `CALL` frames.
- **HTTP long-poll** (browser/runtime workers, #450): `POST /v1/relay/bind`,
  `GET /v1/relay/pull` (long-poll ≤ 25 s), `POST /v1/relay/result`,
  `POST /v1/relay/unbind`. Consumers reach the worker through the relay via the
  path-scoped `/v1/relay-for/{worker_id}/...` prefix.

### 7.2 Session liveness & non-displacement (normative)

- A bound session is **alive** while the worker holds its TCP connection (native)
  or has pulled within the liveness window (HTTP-poll, RECOMMENDED 90 s).
- An **alive** bound `worker_id` MUST NOT be displaced by a new bind for the same
  `worker_id` (`409`/`RELAY_ACK error`). A **dead** session MAY be displaced.
  [→ DIR-RELAY-01, #510 interim-C]

### 7.3 Session caps (normative)

A relay MUST bound its concurrent sessions (RECOMMENDED default 256). A bind that
would exceed the cap MUST be rejected (`503 IICP-E039` / `RELAY_ACK error`); a
**rebind of an already-bound `worker_id` is exempt**. Relays SHOULD additionally
rate-limit binds per source IP. This caps a bind-flood memory-exhaustion DoS.
[→ DIR-RELAY-02, F5, shipped 0.7.58]

### 7.4 Bind authorization — bind ticket (normative, adoption-gated per §6.1)

`RELAY_BIND` is otherwise unauthenticated: an attacker who learns a `worker_id`
could bind it when the real worker drops and intercept its tasks. To close this:

- A worker MUST obtain a short-lived **bind ticket** from the directory
  (`POST /v1/relay/ticket`, authenticated with the worker's `node_token`),
  scoped to its `node_id`, with a short TTL and a relay-audience claim, signed by
  the directory. Every ticket MUST carry a cryptographically random, signed
  `jti` with at least 128 bits of entropy.
- The worker presents the ticket in `RELAY_BIND` / `POST /v1/relay/bind`. The
  relay MUST verify the directory signature, the audience, the TTL, and that the
  ticket's `node_id` equals the `worker_id` being bound, before admitting the
  session. A relay MUST atomically consume the `jti` on the first successful bind
  and reject another bind using the same `jti` until at least the ticket's
  expiration time. [→ DIR-RELAY-03, F1, #510]
- Migration: the bind ticket follows §6.1 — additive in the SDKs first, soft
  (relay accepts ticketed and legacy binds), then hard (ticket required) once the
  adoption threshold is met.

### 7.5 Relay-path confidentiality (normative intent)

A relay forwards task payloads and can therefore read them. Where confidentiality
matters, workers and consumers SHOULD use end-to-end payload confidentiality
(IICP-CX, `iicp-confidentiality.md`) over the relay path so the relay handles only
ciphertext; a relay then affects **availability**, not confidentiality. Relays
MUST NOT log plaintext task payloads. [→ DIR-RELAY-04, F3]

### 7.6 Trust for auto-discovered relays (normative)

A consumer or browser worker that **auto-selects** a relay from `/v1/discover`
MUST NOT bind a relay whose `reputation_score` is below a floor (RECOMMENDED 0.1,
i.e. actively-demoted), SHOULD prefer non-probationary, higher-reputation relays,
and SHOULD surface the chosen relay's `node_id`/reputation to the operator (the
relay can see forwarded tasks absent §7.5). [→ DIR-RELAY-05, F3, shipped 1.9.144]

---

## 8. Optional Extensions

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
| `GET`  | `/v1/credits/summary` | Lifetime credit summary for the authenticated node: `total_earned` (sum of `credit` rows), `total_spent` (sum of `debit` rows), `balance`, `tx_count`, and a `reconciles` boolean. `reconciles` is an integrity invariant — `true` iff `balance == total_earned − total_spent` (4-decimal precision); a tampered or inconsistent ledger MUST surface as `false`. Implementations that support the billing extension v0.4.0+ also return the additive `operator_wallet` rollup defined in iicp-billing-extension §7; clients MUST treat it as optional and keep the node-local ledger as the audit trail. Conformance DIR-CRED-04. |
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

### IICP-DIR-EXT-ATTEST: Signed Compliance Attestation

Lets external verifiers confirm a directory's conformance state with ONE signed JSON fetch
instead of re-running a probe suite — the fast path for federation bootstrap and third-party
audits (#508). A directory that omits this extension is fully IICP-DIR conformant.

**Endpoint (unauthenticated, rate-limited):**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/compliance-attestation` | Signed snapshot of the most recent conformance probe run. Conformance DIR-COMPLIANCE-ATTEST-01 (SHOULD). |

**Response document** (all fields REQUIRED):

```json
{
  "endpoint": "https://iicp.network",
  "spec_version": "iicp-dir v1.0.0",
  "purpose": "compliance-attestation",
  "probe_run_id": "<uuid of the attested REACH run>",
  "probe_run_at": "<ISO8601>",
  "passed_probes": ["DIR-AUTH-01", "DIR-DISC-01", "..."],
  "failed_probes": [],
  "generated_at": "<ISO8601>",
  "valid_until": "<ISO8601 — generated_at + 900s>",
  "attestation_hash": "<sha256 hex of the canonical document>",
  "signature": "<ed25519 detached signature, hex>",
  "signer_did": "did:web:<directory-host>"
}
```

**Verification rule**: strip `attestation_hash`, `signature`, and `signer_did`; canonicalize
the remaining document (key-sorted, no whitespace, `JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES`
— the same rule as event-log payloads, S.13 §3.4); then check
`attestation_hash == SHA256_hex(canonical)` and verify `signature` over `SHA256(canonical)`
(binary) against the Ed25519 key published at `/.well-known/did.json`
`verificationMethod[0].publicKeyJwk.x`. Verifiers MUST reject an attestation past
`valid_until` and SHOULD reject one whose `purpose != "compliance-attestation"`
(cross-protocol replay guard — the event log signs with the same key).

**Trust model**: self-attestation is a fast-path supplement, never the sole verifier —
independent probes (REACH) keep running out-of-band, so a directory falsely attesting
compliance is still caught. Verifiers bootstrapping trust SHOULD spot-check a random
subset of attested probes directly.

**Failure modes**: `503 attestation_unavailable` when the directory has no signing key
(fail-closed — an unsigned attestation is unverifiable); `503 no_probe_data` before the
first conformance run is recorded.

Signing key: the genesis Ed25519 key (S.13 §3.4) — one trust root per directory.
Tracking: #508

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.1.21 | 2026-07-10 | #557 completes the CX discovery-name cutover: discover/NODELIST and authenticated dispatch routes emit only canonical `cx_public_key`. The deprecated CX `public_key` alias is removed from directory output and schema; SDK consumers may retain read fallback for one further release. Node-detail `public_key` remains the distinct Ed25519 gossip key. |
| 1.1.17 | 2026-07-09 | #613 intent-risk taxonomy: added shared `prohibited`/`high_risk`/`transparency_risk`/`minimal_or_general` vocabulary, public-mesh fail-closed defaults for prohibited/high-risk declared intents, and the non-legal-advice scope caveat. |
| 1.1.18 | 2026-07-09 | #612 ticketed-dispatch adoption: added bounded failed-node prefix exclusion, safe policy-manifest route evidence, anonymous seven-day migration counters with 30-day retention, and automatic-client downgrade guardrails. |
| 1.1.20 | 2026-07-10 | #599/#609 operator-key self-service foundation: single-use signed challenges for current terms/DPA acceptance and operator-scoped export, restriction and anonymization, with no-store/redaction requirements and cross-SDK canonical signing helpers. |
| 1.1.19 | 2026-07-10 | #612 measurement integrity: read-only callers use `view=public`; adoption stats carry a post-cleanup measurement epoch, sample and sustained-window eligibility, while anonymous request counts remain explicitly heuristic. |
| 1.1.16 | 2026-07-09 | #612 ticketed dispatch discovery: added `POST /v1/dispatch/ticket`, a prompt-free, short-lived, intent/node-scoped route-ticket path so new clients can obtain concrete dispatch routes without using public presentation discovery or relying permanently on default route-bearing GET discovery. |
| 1.1.15 | 2026-07-09 | #608/#609 policy-key lifecycle and known-operator governance records: directory-owned revocation/supersession can change already-registered manifest status without node re-registration, and `known_operator` requires current terms+DPA acceptance metadata without exposing raw keys, nonces or evidence documents. |
| 1.1.14 | 2026-07-09 | #611 public presentation discovery view: `view=public` returns safe scored candidates with endpoint URLs, transport endpoint URLs, full UUID node IDs, opaque transport metadata and raw CX keys redacted; default discover remains explicit route-dispatch data for current clients. |
| 1.1.13 | 2026-07-08 | #558 IPv6 reachability evidence decision: prefer production directory IPv6 egress; use signed external IPv6 worker only as fallback; keep self-attested IPv6 separate from directory/external observed evidence. |
| 1.1.12 | 2026-07-08 | #599/#602 research decision: operator-key challenge is the preferred DSR portal verifier; policy-manifest identity levels distinguish self-attested, signed-valid, operator-bound, known-operator, rotated and revoked without treating signatures as legal compliance proof. |
| 1.1.11 | 2026-07-08 | #600/#601 strict region-policy and MCP/tool-risk gate staging: fail-closed allowed-region profile, tool risk vocabulary, public-unknown dangerous-tool denial defaults, and compliance-proof caveat. |
| 1.1.10 | 2026-07-08 | #581 route self-recovery contract: states/actions, safe directory-visible recovery fields, and cross-SDK parity matrix for Docker/sleep-wake/tunnel-dead/cooldown/supervisor scenarios. |
| 1.1.9 | 2026-07-08 | #557 cutover staging: live key-ready/current-SDK adoption may stage removal of the discover/NODELIST CX `public_key` alias, but directory alias emission stays for one compatibility release window and client alias fallback stays one further release; malformed/missing CX keys remain fail-closed. |
| 1.1.8 | 2026-07-02 | Added signed node policy manifest phase A: optional Ed25519 detached signatures over canonical policy manifests, directory rejection for invalid/expired signed manifests, NODELIST/DISCOVER verification evidence, and `strict_policy` client requirement for signed-valid no-retention manifests. |
| 1.1.7 | 2026-07-02 | Added client remote-routing policy profiles (`standard`, `sensitive`, `eu_restricted`, `strict_policy`, `debug_override`) and the fail-before-dispatch requirement for policy-rejected candidates. |
| 1.1.6 | 2026-07-02 | EU/GDPR readiness phase-1: added optional REGISTER `policy_manifest` and NODELIST `node_policy_manifest` as a public self-attested node-policy declaration. Clarified that it is transparency/routing-policy metadata only, not a verified legal compliance certificate; signed manifest verification remains future work. |
| 1.1.5 | 2026-06-30 | IICP-DIR-EXT-CREDITS: clarified that `GET /v1/credits/summary` remains the node-local DIR-CRED-04 ledger summary and may additionally include the `operator_wallet` rollup defined by iicp-billing-extension §7. This aligns the directory summary with operator-wallet CLI output without changing the wire contract. |
| 1.1.4 | 2026-06-28 | §3.1 documents accountless external-tunnel guardrails shipped in SDK 0.7.75: host-wide create spacing (120s), creation lease (45s), persistent provider-rate-limit cooldown (900s), and fallback to prior safe reachability methods instead of spinning or advertising unverified routes. §3.4 reconciles transport_method enum wording, §3.6/§6 remove stale peer-exchange node-token/HMAC wording, §3.14 centralizes operational timer defaults, and §3.2 refreshes the updater-evidence example to SDK 0.7.75. |
| 1.1.3 | 2026-06-25 | §3.4 adds SDK-baseline/key-readiness demotion fields and optional `auto_update` evidence; health text now caps no-latency nodes below `"healthy"` until latency evidence exists. |
| 1.1.2 | 2026-06-21 | §3.4 clarifies IICP-CX discovery naming after the key-alias hotfix: `cx_public_key` is the canonical CX X25519 key; `public_key` is a deprecated compatibility alias in discover/NODELIST and remains a separate Ed25519 gossip key in node-detail/peer-exchange contexts. |
| 1.1.1 | 2026-06-21 | Draft §3.13 WebRTC signaling mailbox contract for browser self-addressing (#523): short-lived SDP/ICE control-plane mailbox, transport metadata shape (`webrtc_datachannel`), TTL/auth/size/rate-limit requirements, task-payload-off-directory invariant, and conservative relay fallback semantics. §3.4 also documents `operator_fingerprint` for display-name disambiguation (#525). |
| 0.1.0 | 2026-05-14 | Initial draft — fills SPEC_ANALYSIS.md GAP-1; REGISTER, HEARTBEAT, QUERY, NODELIST, BOOTSTRAP, PEER_EXCHANGE message types |
| 0.1.1 | 2026-05-15 | Added Changelog section (A6 spec cleanup) |
| 0.2.0 | 2026-05-17 | §3.4 NODELIST: added `probation`, `completed_tasks_count`, `cip_policy` fields + QoS probation filter table (ADR-023, CIP-D1, spec §11.3) |
| 0.3.0 | 2026-05-17 | §3.4 Consensus mode discovery note: proxy discovers N workers for consensus; directory unaware of consensus mode; cip_policy.allow_remote_inference filter requirement. |
| 0.7.0 | 2026-05-26 | §3.1 REGISTER + §3.4 NODELIST: optional `transport_endpoint` field added (`iicp://` / `iicpsec://` scheme; default port 9484). Splits control plane (`endpoint`, HTTP) from data plane (`transport_endpoint`, native binary framing per ADR-040). Directory's HTTP liveness probe targets `endpoint` only; clients SHOULD prefer `transport_endpoint` when present. Back-compat: nodes without `transport_endpoint` continue to behave exactly as v0.6.x. |
| 0.9.4 | 2026-06-01 | §3.9c Directory-initiated node probing added (Phase 5 #373 Phase B): DIR-PROBE-NODE-01, TCP probe every 300s, SSRF-guarded, 5s timeout, results in iicp_telemetry_probes. NodeHealthService reachability uses independently observed signal when recent probe exists (observed: true). Activation requires IPv4+IPv6 egress. References conformance-test-suite.md §3.3i. |
| 1.0.0 | 2026-06-10 | §3.12 Consumer Token Issuance added (Phase 2, #496): `GET /api/v1/directory-key` + `POST /api/v1/consumer-token` endpoints; Ed25519-signed short-lived tokens (`b64url_payload.sig_hex`, 300s TTL); `X-IICP-Consumer-Token` header accepted as alternative to `auth.node_token` on `POST /v1/task`. Implemented across PHP directory (v1.10.32), Python adapter, Python proxy, TypeScript client, Rust iicp-client, Rust iicp-node. |
| 0.9.0 | 2026-05-30 | Code↔spec drift closeout (#384): §7 credit endpoints corrected to shipped routes (award/balance/transactions/quote — R4 fix); §3.9b Public Stats schema added (/v1/stats — server/probes/credit_schedule/mesh_health/directory_health); §3.4 NODELIST table + transport_method/nat_type/transport_metadata/address_family/relay_capable/public_key(CX object; now deprecated alias for canonical `cx_public_key`)/sdk_*/models fields; probation clarified as node-detail-only (R3); §3.7 event-type enum reconciled to snapshot+event-tail live set (R2 — HEARTBEAT/SCORE_UPDATE retired). |
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
| 0.11.0 | 2026-06-10 | **§3.6 PEER_EXCHANGE auth model corrected** (external security review, #495): the HMAC-keyed-with-node_token + Bearer-node_token design was unverifiable (receiver never has the sender's token; directory stores bcrypt only) and leaked the directory credential to peers. Replaced with ed25519 detached signature over the raw body using the sender's registered gossip `public_key` (resolvable via peer cache or `GET /v1/node/{id}`); `node_token` MUST NOT travel to peers; Authorization header carries no trust on this endpoint. Replay rules preserved (signature-replay 409 + ±60s timestamp inside the signed body). Phase 2+ surface — no Phase 1 conformance impact; adapter gossip implementation update tracked in #495. |
| 0.10.2 | 2026-06-05 | IICP-DIR-EXT-CREDITS: added `GET /v1/credits/summary` (DIR-CRED-04) — lifetime `total_earned`/`total_spent`/`balance`/`tx_count` for the authenticated node plus a `reconciles` integrity invariant (`balance == earned − spent`, MUST be `false` for a tampered/inconsistent ledger). Additive/back-compatible; powers the `iicp-node credits` command (#456). Shipped in PHP + Rust directories (parity #385). |
| 0.10.1 | 2026-06-03 | §3.2 HEARTBEAT: documented dormant-node auto-restore — a heartbeat from a previously-dormant node MUST set `status=active`, clear `dormant_since`, and default `available=true` unless the body carries `available:false` (corrects a directory regression where a resumed heartbeat left `available=false`, hiding a live node from discover forever; dir v1.10.17). §3.4/§3.7 event log: added `REACHABILITY_DEMOTE` / `REACHABILITY_RESTORE` to the live federated event-type set with payload schema (#413 — the `public_reachable` transition that makes a node vanish from discover is now in the signed, federatable audit trail; emitted transition-only at the demote/promote edges). Both additive/back-compatible. |
| 0.10.0 | 2026-06-03 | Four shipped additions (dir v1.10.14): §3.1 REGISTER `capabilities[].input_modalities` (ADR-046 vision/multimodal — `["text"]` default; image-in is a chat modality, not a new intent) + optional `operator_delegation` ed25519 token (ADR-045 Phase A — offline-verified operator→node binding, `did_key`/`did_web` trust tiers); §3.2 HEARTBEAT challenge-response (ADR-047 Part A — `challenge` nonce in PONG, `challenge_response`=HMAC-SHA256(node_hmac_key,nonce) — cryptographic liveness without dial-back, for CGNAT/IPv6); §3.3 QUERY `?modality=` filter; §3.4 NODELIST `reachability_tier` (`direct`/`relay` — relay-tier nodes no longer hidden, ADR-047) + `input_modalities`. All additive/back-compatible. Protocol Suite MINOR bump (→ v1.10.0) is the separate maintainer-ratified release step (VERSIONING.md Current + /spec page, per check_spec_versions.py). |
| 1.1.0 | 2026-06-11 | IICP-DIR-EXT-ATTEST optional extension — `GET /v1/compliance-attestation` signed compliance snapshot (#508); DIR-COMPLIANCE-ATTEST-01 (SHOULD) |

---

## Sign-off

**Protocol Steward**: IICP-DIR fills GAP-1 from SPEC_ANALYSIS.md. SUB_PROTOCOL binding
keeps core opcode table stable per ADR-009. Phase 1 REST form is a valid stepping stone.
Closes GitHub issue #14 (draft). ✓
