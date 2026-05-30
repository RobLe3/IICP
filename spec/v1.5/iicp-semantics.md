# IICP Semantics — Routing, QoS, and Node Selection

**Version**: 1.3.0
**Date**: 2026-05-18
**Status**: draft
**Issue**: #17 (S.5 — spec split)
**Authority**: Protocol Steward
**Relation**: iicp-core.md, ARCHITECTURE.md (ADR-008), RELIABILITY.md

---

## Purpose

This document specifies the SHOULD-level behavioural requirements for IICP
implementations: how intents are matched and routed, what QoS levels mean in
practice, how nodes are scored and selected, and what retry and fault-tolerance
behaviour is expected.

Implementations SHOULD follow these semantics to achieve interoperability. The
mandatory wire format and MUST requirements are in `iicp-core.md`.
Extension mechanisms (billing, reputation, CIP) are in `iicp-extensions.md`.

---

## Normative Language

The key words "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY",
and "OPTIONAL" in this document are to be interpreted as described in RFC 2119 /
BCP 14.

---

## 1. Intent URN Semantics

### 1.1 Intent format

An IICP intent URN identifies the type of work requested. There are two tiers:

#### Standard intents (registry-controlled)

```
urn:iicp:intent:<domain>:<action>:v<N>
```

Standard intents are listed in the public registry (`registry/intents.json`). Domains
and actions are lowercase ASCII. The registry is the authority for standard intents.

Examples:
```
urn:iicp:intent:llm:chat:v1
urn:iicp:intent:llm:embed:v1
urn:iicp:intent:code:complete:v1
urn:iicp:intent:image:generate:v1
```

#### Custom intents (vendor-controlled, `x.` prefix)

```
urn:iicp:intent:x.<vendor>:<action>:v<N>
```

The `x.` prefix is a reserved extension subdomain for vendor-specific, application-specific,
and experimental intents that are NOT in the public registry. Any operator MAY define custom
intents under their own vendor label without IICP approval. This enables:

- **Proprietary microservices**: `urn:iicp:intent:x.acme:invoice-classify:v1`
- **Domain-specific applications**: `urn:iicp:intent:x.hospital-alpha:triage-assist:v2`
- **Experimental intents**: `urn:iicp:intent:x.exp:multimodal-audio:v1`
- **Internal platform intents**: `urn:iicp:intent:x.myplatform:sentiment-score:v3`

The `x.` convention follows IETF practice for experimental/extension namespaces (see RFC 2045
`x-` MIME parameter extensions, XMPP `jabber:x:` private namespaces).

**Vendor labels**: lowercase alphanumeric and hyphens; MUST NOT conflict with IICP reserved
domains. IICP commits to never using `x.` prefixed domains in the public registry.

#### Grammar (ABNF, extended)

```abnf
; Any valid IICP intent URN
any-intent-urn    = standard-intent-urn / custom-intent-urn

; Standard: registry-controlled
standard-intent-urn = "urn:iicp:intent:" domain ":" action ":v" version *("+" modifier)

; Custom: vendor-controlled, no registry required
custom-intent-urn   = "urn:iicp:intent:x." vendor-label ":" action ":v" version *("+" modifier)

domain       = 1*(ALPHA / DIGIT / "-")
vendor-label = 1*(ALPHA / DIGIT / "-")
action       = 1*(ALPHA / DIGIT / "-")
version      = 1*DIGIT
modifier     = 1*(ALPHA / DIGIT / "-")
```

#### Upgrade path

A custom intent with demonstrated broad adoption (≥ 3 independent implementations) MAY
be submitted for inclusion in the public registry via the IICP governance process. The
`x.` prefix is removed upon standardization.

The canonical registry of standard intent URNs is maintained in `registry/intents.json`.

### 1.2 Intent matching

A node is eligible to handle a CALL if its registered `capabilities[].intent`
exactly matches the CALL's `intent` field (case-sensitive, full URN comparison).
This rule applies to both standard and custom intents — exact URN match is always required.

The directory MUST accept and store custom intent URNs (`urn:iicp:intent:x.*`) without
registry validation. DISCOVER queries for custom intents return only nodes that have
registered that exact custom URN.

Partial matching (prefix match or version wildcard) is NOT supported in Phase 1.
Phase 2 MAY introduce version-range matching (e.g., `v1.*`).

### 1.3 Intent routing priority

When a proxy receives multiple nodes for an intent, it SHOULD prefer nodes in
the order returned by the directory (score-descending). The proxy SHOULD NOT
re-score nodes unless implementing Phase 5 Cooperative Inference Profile
local-cost weighting.

### 1.4 Intent URN modifiers

Modifiers extend a base intent URN with additional behavioural requirements. A modifier
is appended to the versioned intent using a `+modifier` suffix:

```
urn:iicp:intent:<domain>:<action>:v<N>+<modifier>
```

**Grammar (ABNF)**:
```abnf
intent-urn  = "urn:iicp:intent:" domain ":" action ":v" version *("+" modifier)
domain      = 1*ALPHA
action      = 1*ALPHA
version     = 1*DIGIT
modifier    = 1*(ALPHA / DIGIT / "-")
```

**Defined modifiers**

| Modifier | Semantics | Status |
|----------|-----------|--------|
| `+attested` | Provider MUST return an `attestation_receipt` in the task response. Requires ADR-024 (signed message envelope) and identity slot (#150). Directory MUST exclude non-attesting nodes from discover results when this modifier is present. | Phase 6 prerequisite — MUST NOT be used until ADR-024 is ratified. |

**Example**:
```
urn:iicp:intent:llm:chat:v1+attested
```

**Backward compatibility**: Unrecognised modifiers SHOULD be treated as unknown and the
request SHOULD be routed normally (fail-open). Implementations that wish to enforce a
strict mode MAY reject unrecognised modifiers with `IICP-E028`.

**Dependencies for `+attested`**:
- `attestation_receipt` response field — `iicp-core.md` §3.2
- Signed message envelope — ADR-024 (#155)
- Identity slot — #150

---

## 2. QoS Levels

### 2.1 Level definitions

| Level | Meaning | Timeout guidance | Retry guidance |
|-------|---------|-----------------|----------------|
| `realtime` | Sub-second SLA; streaming preferred | Short (< 3s) | Node-switch on 429; 1 attempt max per node |
| `interactive` | Human-in-the-loop; low latency required | Short (< 10s) | 1–2 attempts max |
| `batch` | Background processing; throughput preferred | Medium (10s–120s) | Up to 3 attempts |
| `best-effort` | Background; can be deferred indefinitely | Long (up to 300s) | Up to 5 attempts |

The `qos` field in a CALL (`constraints.qos`) is a hint to the adapter and proxy.
Adapters SHOULD prioritise task execution accordingly when concurrency limits apply.

### 2.2 QoS Admission Control (normative)

When a node receives a request for a given QoS class and all concurrency slots for
that class are occupied, it MUST refuse the request immediately and MUST NOT degrade
its latency SLA by accepting and queuing the task.

**Adapter MUST** return HTTP 429 with the body:
```json
{
  "error": {
    "code": "capacity_exceeded",
    "message": "<human-readable>",
    "qos_class": "<qos-class-that-is-saturated>",
    "retry_after_ms": <suggested-wait-ms>
  }
}
```
and a `Retry-After: <seconds>` header.

**Proxy MUST** treat `capacity_exceeded` 429 as a node-switch signal — try the next
node in the discovery list immediately. It MUST NOT apply exponential backoff to the
same node for `capacity_exceeded`; that is reserved for transient errors.

### 2.3 QoS in discovery

Proxies SHOULD include `qos` in discovery queries. Directories SHOULD weight
availability window alignment higher for `interactive` queries.

---

## 3. Node Scoring and Selection

Node scoring is governed by ADR-008. This section summarises the semantics
for proxy-side consumers of the discovery response.

### 3.1 Score computation (directory-side)

Score is computed server-side by the directory using the Phase 3 formula:

```
score = 0.35 × availability_factor
      + 0.28 × (1 − normalized_load)
      + 0.18 × capacity_ratio
      + 0.09 × region_match
      + 0.10 × reputation_score
```

See ARCHITECTURE.md §Node Discovery Scoring for term definitions and phase weight
schedule.

**Hard rule**: The proxy MUST NOT re-compute scores. It is filter-only.

### 3.2 Proxy filter behaviour

After receiving a discovery response, the proxy SHOULD:

1. Filter out any node where `available = false`
2. Skip nodes with open circuit breakers (per-node failure state)
3. Use the remaining list in directory score order
4. Never locally reorder by score

### 3.3 Eligibility filter

Nodes with `score < 0.1` are excluded from discovery results by the directory.
Proxies SHOULD assume the list they receive is already eligibility-filtered.

---

## 4. Availability Windows

A node MAY declare time-based sharing windows in its INIT registration:

```json
"availability": [
  { "start": "00:00", "end": "08:00", "share": 0.8 }
]
```

The directory uses these windows to compute `availability_factor` in the scoring
formula. Outside declared windows, `availability_factor = 0.5` (default half-weight).

Proxies SHOULD NOT interpret availability windows directly — the directory handles
all window-to-score translation.

---

## 5. Heartbeat Semantics

- Nodes SHOULD send `POST /v1/heartbeat` every 30 seconds
- The directory marks nodes inactive after 90 seconds without a valid heartbeat
- Nodes SHOULD include current `load`, `active_jobs`, and `available` in each heartbeat
- The `available` flag SHOULD be set to `false` when `active_jobs >= max_concurrent`
- On reconnect, the node SHOULD re-register if it has been inactive for > 90 seconds;
  otherwise a valid heartbeat reactivates it automatically

---

## 6. Retry Policy

### 6.1 Standard retry (proxy → adapter)

Implemented in `proxy/src/proxy/routing/retry.py`.

| Condition | Retriable | Notes |
|-----------|-----------|-------|
| `httpx.ConnectError` | SHOULD retry | Connection refused, DNS failure |
| `httpx.TimeoutException` | SHOULD retry | Read, write, or connect timeout |
| `httpx.RemoteProtocolError` | SHOULD retry | Peer closed connection without complete response |
| HTTP 429 Too Many Requests | SHOULD retry | Node overloaded — retry with backoff |
| HTTP 503 Service Unavailable | SHOULD retry | Node temporarily unavailable |
| HTTP 400 Bad Request | SHOULD NOT retry | Client error — request won't change |
| HTTP 401 Unauthorized | SHOULD NOT retry | Auth failure — fix the token |
| HTTP 403 Forbidden | SHOULD NOT retry | Permanent auth failure |
| HTTP 409 Conflict | SHOULD NOT retry | Duplicate task_id |
| HTTP 422 Unprocessable Entity | SHOULD NOT retry | Schema validation error |
| HTTP 502 Bad Gateway | SHOULD NOT retry | Backend-level error |

Default parameters: max 3 attempts · 200ms base delay · 2× multiplier · ±20% jitter.

### 6.2 Fast retry (adapter → directory heartbeat)

Max 2 attempts · 100ms base delay. Only timeout errors retried.

### 6.3 No-retry (idempotency guard)

Task results are not retried at the result-delivery level. The `task_id` idempotency
guard in the adapter ensures repeated CALL requests for the same `task_id` return
the cached result without re-executing the inference backend.

---

## 7. Circuit Breaker

### 7.1 Per-node circuit breaker

Proxies SHOULD implement a per-node circuit breaker:

- **Threshold**: 5 consecutive failures → circuit opens
- **Open duration**: 30 seconds, then half-open probe
- **Half-open**: single probe request; if success → close; if failure → reopen

When a circuit is open, the proxy skips that node in the discovery result list and
tries the next available node.

### 7.2 Directory circuit breaker

Adapters SHOULD implement a circuit breaker on the directory registration and
heartbeat endpoints with the same parameters as above.

---

## 8. Fallback Chain

When all remote nodes fail, the proxy SHOULD follow this chain:

```
1. Best-scored node from discovery (circuit breaker closed)
2. Second-scored node (on failure of #1)
3. Third-scored node (on failure of #2)
4. Local fallback node (if configured — `proxy.toml [fallback]`)
5. Structured error → caller
```

The proxy MUST NOT silently drop requests. Step 5 MUST always produce a response.

---

## 9. Peer Exchange (Phase 2+)

In Phase 2, nodes supplement directory discovery with direct peer gossip. The
PEER_EXCHANGE message type (specified in `iicp-dir.md §3.6`) allows nodes to share
their known peer lists.

Proxies operating in Phase 2+ SHOULD:
- Bootstrap from `GET /v1/bootstrap` (directory) on startup
- Maintain a local peer cache TTL of 90 seconds
- Prefer cached peers for `interactive` QoS tasks when directory latency > 200ms
- Fall back to directory discovery when peer cache is empty or stale

---

## 10. Observability Semantics

### 10.1 Trace propagation

IICP implementations SHOULD propagate the `trace_id` field across all hops:

- Proxy generates `trace_id` on CALL origination
- Adapter includes `trace_id` in backend HTTP calls as `X-IICP-Trace-Id` header
- All components SHOULD emit OpenTelemetry spans tagged with `trace_id`

### 10.2 Required Prometheus metrics

Components SHOULD emit the following metrics (see RELIABILITY.md §Metrics for labels):

| Component | Metric |
|-----------|--------|
| Adapter | `iicp_tasks_total`, `iicp_task_latency_ms`, `iicp_tokens_used_total` |
| Directory | `iicp_nodes_active`, `iicp_discovery_latency_ms`, `iicp_heartbeat_misses_total` |
| Proxy | `iicp_proxy_routing_ms`, `iicp_proxy_retries_total` |

---

## 11. Reputation Update Rules

This section is **normative** (RFC 2119). It defines the events that cause reputation changes and the per-event deltas. Implementations MUST apply these rules consistently to ensure that `reputation_score` has the same meaning across independent directory deployments.

### 11.1 Latency budgets by QoS class

| QoS class | Budget (ms) |
|-----------|-------------|
| `realtime` | 500 |
| `interactive` | 2000 |
| `batch` | 10000 |
| `best-effort` | no budget (latency is never penalised) |

When the QoS class is unknown (e.g. heartbeat does not carry it), the directory SHOULD use the `interactive` budget (2000 ms) as the default.

### 11.2 Per-task delta rules

| Event | Reputation delta |
|-------|-----------------|
| Task completed, `avg_latency_ms` ≤ budget | **+0.01** |
| Task completed, budget < `avg_latency_ms` ≤ 2 × budget | **+0.00** (no change) |
| Task completed, `avg_latency_ms` > 2 × budget | **−0.05** |
| Task failed (adapter error, 5xx backend) | **−0.05** |
| Task timed out (504 gateway timeout) | **−0.10** |
| Node advertised `available: true` but failed liveness check | **−0.20** |
| Node missed ≥ 3 consecutive heartbeats and reappears | reputation reset to **0.5** (probation default) |

Deltas from a single heartbeat batch MUST be summed and applied atomically:

```
new_score = clamp(old_score + Σ(per_task_delta), 0.0, 1.0)
```

**Per-heartbeat positive delta cap (RT-01 / #375)**: To prevent reputation self-inflation via
self-reported metrics, the positive component of the summed delta from a single heartbeat call
MUST be capped at **+0.10** before the atomic update. Negative deltas (failures, timeouts)
are not capped and apply in full. Rationale: a single heartbeat carrying `tasks_success=100`
would otherwise drive the score from 0.5 to 1.0 in one call; the cap requires at least
5 minutes of sustained legitimate traffic to achieve maximum reputation.

```
positive_delta = min(max(0.0, Σ(per_task_delta)), 0.10)
negative_delta = min(0.0, Σ(per_task_delta))
new_score = clamp(old_score + positive_delta + negative_delta, 0.0, 1.0)
```

### 11.3 Initial value and probation

New nodes start with `reputation_score = 0.5`. Implementations MAY enforce a probation
period (see ADR-008) during which nodes are excluded from certain QoS tiers. Probation
details are implementation-defined; the initial score of 0.5 is normative.

### 11.4 Bounded score invariant

Scores MUST remain within `[0.0, 1.0]` at all times. Implementations MUST clamp before
persisting. Conformance tests: REP-01 through REP-03 (see conformance-test-suite.md §13.6).

### 11.5 Peer audit-report griefing cap (RT-05 / #379)

A registered node MAY submit a peer audit-report (`POST /v1/audit-report`) reporting a
`declaration_divergence` finding against a target node. The directory applies a
`REPUTATION_DELTA = −0.05` on acceptance.

To prevent coordinated reputation griefing (multiple colluding reporters targeting one
node), the following MUST be enforced:

1. **Per-reporter rate limit**: A given reporter node MUST NOT have more than one accepted
   report against the same target accepted within any 24-hour window.
2. **Per-target global cap**: At most **2 distinct reporters** MAY have their delta applied
   against any single target within a 24-hour window. Reports from additional reporters
   within the window MUST be acknowledged (HTTP 202) but MUST NOT reduce the target's
   reputation further. The `delta_suppressed: true` flag SHOULD be included in the event log.

Rationale: without the global cap, 10 colluding nodes each filing one report (within their
individual rate windows) can reduce a target from 0.5 → 0.0 in a single day. The cap limits
total daily damage to −0.10 regardless of how many distinct reporters participate.

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-05-15 | Initial draft — extracted from ARCHITECTURE.md, RELIABILITY.md, and prior spec work as part of S.5 spec split |
| 1.1.0 | 2026-05-17 | §11 Reputation Update Rules — normative delta table, latency budgets by QoS class, bounded score invariant. Closes #113. |
| 1.2.0 | 2026-05-17 | §2.1 Added `realtime` QoS level row. §2.2 QoS Admission Control — MUST 429 capacity_exceeded with qos_class+retry_after_ms, MUST proxy node-switch. §2.3 renumbered from §2.2. Closes #119 (spec). |
| 1.3.0 | 2026-05-30 | §11.2 Per-heartbeat positive delta cap +0.10 MUST (RT-01 security fix, #375). §11.5 Peer audit-report griefing cap — per-reporter 24h rate limit + 2-reporter global cap per target per day MUST (RT-05 security fix, #379). |

---

## Sign-off

**Protocol Steward**: iicp-semantics.md captures SHOULD-level routing and fault-tolerance
semantics. It does not introduce new requirements — it formalises behaviour already
implemented across proxy/, adapter/, and iicp-node/. Part of S.5 spec split (issue #17). ✓
