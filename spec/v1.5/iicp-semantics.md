# IICP Semantics — Routing, QoS, and Node Selection

**Version**: 1.0.0
**Date**: 2026-05-15
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

An IICP intent URN identifies the type of work requested:

```
urn:iicp:intent:<domain>:<action>:v<N>
```

Examples:
```
urn:iicp:intent:llm:chat:v1
urn:iicp:intent:llm:embed:v1
urn:iicp:intent:code:complete:v1
urn:iicp:intent:image:generate:v1
```

The canonical registry of intent URNs is maintained in `registry/intents.json`.

### 1.2 Intent matching

A node is eligible to handle a CALL if its registered `capabilities[].intent`
exactly matches the CALL's `intent` field (case-sensitive, full URN comparison).

Partial matching (prefix match or version wildcard) is NOT supported in Phase 1.
Phase 2 MAY introduce version-range matching (e.g., `v1.*`).

### 1.3 Intent routing priority

When a proxy receives multiple nodes for an intent, it SHOULD prefer nodes in
the order returned by the directory (score-descending). The proxy SHOULD NOT
re-score nodes unless implementing Phase 5 Cooperative Inference Profile
local-cost weighting.

---

## 2. QoS Levels

### 2.1 Level definitions

| Level | Meaning | Timeout guidance | Retry guidance |
|-------|---------|-----------------|----------------|
| `interactive` | Human-in-the-loop; low latency required | Short (< 10s) | 1–2 attempts max |
| `batch` | Background processing; throughput preferred | Medium (10s–120s) | Up to 3 attempts |
| `best-effort` | Background; can be deferred indefinitely | Long (up to 300s) | Up to 5 attempts |

The `qos` field in a CALL (`constraints.qos`) is a hint to the adapter and proxy.
Adapters SHOULD prioritise task execution accordingly when concurrency limits apply.

### 2.2 QoS in discovery

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

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-05-15 | Initial draft — extracted from ARCHITECTURE.md, RELIABILITY.md, and prior spec work as part of S.5 spec split |

---

## Sign-off

**Protocol Steward**: iicp-semantics.md captures SHOULD-level routing and fault-tolerance
semantics. It does not introduce new requirements — it formalises behaviour already
implemented across proxy/, adapter/, and iicp-node/. Part of S.5 spec split (issue #17). ✓
