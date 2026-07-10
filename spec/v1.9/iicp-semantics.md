# IICP Semantics — Routing, QoS, and Node Selection

**Version**: 1.6.3
**Date**: 2026-07-02
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

### 1.3 Prohibited-practice intent guardrails

IICP implementations MUST NOT route intents that structurally request prohibited
AI practices. This is a compliance-readiness safety floor, not a complete legal
classifier and not a substitute for operator due diligence. Official clients
SHOULD refuse such intents locally before directory discovery so that no prompt,
task body, or destination request is sent to the directory or to a remote node.

At minimum, official clients MUST reject intent URNs whose domain/action names
plainly map to these prohibited or unsupported families:

- social scoring;
- individual criminal-risk prediction;
- workplace or education emotion recognition;
- biometric categorisation of protected traits;
- untargeted facial-image scraping for recognition databases;
- real-time remote biometric identification;
- non-consensual sexual deepfake or child sexual abuse content generation.

The interoperable refusal code for this local guardrail is `IICP-POLICY-001`.
The error is terminal for that request and clients SHOULD NOT retry it against
other nodes. Direct model prompts under otherwise ordinary intents still require
application-level policy review; the intent guardrail only blocks clear intent
URN families before routing.

### 1.4 Intent routing priority

When a proxy receives multiple nodes for an intent, it SHOULD prefer nodes in
the order returned by the directory (score-descending). The proxy SHOULD NOT
re-score nodes unless implementing Phase 5 Cooperative Inference Profile
local-cost weighting.

### 1.5 Intent URN modifiers

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

Score is computed server-side by the directory. The directory applies one of two
weight sets depending on whether a `?model=` parameter is present (ADR-008,
ADR-012, ADR-021). The proxy MUST NOT re-compute scores; it is filter-only.

#### Phase 3 weights (no `?model=` parameter)

```
score = 0.35 × availability_factor
      + 0.28 × (1 − normalized_load)
      + 0.18 × capacity_ratio
      + 0.09 × region_match
      + 0.10 × reputation_score
```

#### Phase 5 weights (with `?model=<model_id>` — ADR-012 model-aware routing)

When a model is requested, `W_MODEL` and `W_PRICE` are added and the other weights
are reduced proportionally so that a model match drives routing for model-specific
tasks and price becomes a secondary signal.

```
score = 0.25 × availability_factor
      + 0.20 × (1 − normalized_load)
      + 0.15 × capacity_ratio
      + 0.10 × region_match
      + 0.10 × reputation_score
      + 0.10 × model_match        (1.0 if node serves the requested model, else 0.0)
      + 0.10 × price_score        (normalised inverse of node pricing; 1.0 = cheapest)
```

`model_match` is 1.0 when the node advertises the requested model in its
`capabilities.models` list; 0.0 otherwise. Nodes with `model_match = 0.0` are
**not** excluded from results — they appear lower in the sorted list (proxy may
still route to them for non-model-specific tasks).

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

### 6.4 Public reachability fallback (provider SDK → mesh)

Provider SDKs MAY auto-escalate from a local or private listener to a public
reachability method when direct routability is not verified (for example because
the node is behind private IPv4, IPv6 without a verified pinhole, CGNAT, or a
closed firewall). This does not weaken the directory's routability invariant:
the directory still accepts only verified public endpoints for public discovery.

Recommended provider reachability ladder:

1. Operator-supplied `IICP_PUBLIC_ENDPOINT` or another verified direct public endpoint.
2. NAT-derived direct route after evidence shows it is reachable.
3. Accountless external tunnel temporary HTTPS endpoint.
4. Configured or auto-elected relay.
5. Local-only serving, or no public registration, with honest operator guidance.

Accountless external-tunnel creation is a scarce shared-provider operation. SDKs
SHOULD implement the guardrails in `iicp-dir.md §3.1`: host-wide create spacing
(120s default), host-wide create lease (45s default), and persistent provider
rate-limit cooldown (900s default after HTTP 429 or Cloudflare 1015-class
evidence). A pacing, lease, or cooldown hit is a trigger to try the next safe
reachability method; it is not permission to retry tunnel creation in a loop.

If no direct route, tunnel, or relay is verified, a provider MUST NOT claim public
reachability merely because it is listening locally. It MAY continue to serve
local tasks and heartbeat as unavailable/local-only where the implementation
supports that state, but public discovery SHOULD prefer route honesty over
optimistic advertisement.

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

**Counters are advisory (RT-01b, #525)**: any per-node task counters an
implementation keeps for display (e.g. `completed_tasks_count`, `lifetime_jobs`)
are derived from self-reported heartbeat metrics and are therefore **advisory** —
they MUST NOT gate routing, tier eligibility, or recognition on their own.
Because they are throughput tallies (not bounded [0,1] scores), they are not
rate-capped like the score; instead an implementation SHOULD clamp the
**per-heartbeat** success contribution to a realistic single-node throughput
ceiling (so the tally cannot be driven toward the heartbeat validation maximum)
while never rejecting a legitimate bursty heartbeat. Load-bearing signals MUST
use directory-observed facts (reachability, liveness, operator verification) or
verified economic events (below).

**Receipt-derived reputation (optional profile, #525)**: a directory MAY operate
a stronger profile in which reputation deltas are applied only from **verified
`/credits/award` receipts** (signed, counterparty-bearing, self-query-excluded —
see `iicp-cooperative-inference.md` §10.3) rather than from self-reported
heartbeat metrics, which then become advisory telemetry only. Adopting this
profile is a §6.1 (iicp-dir) capability migration, not a silent change.

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

### 11.6 Hourly reputation velocity ceiling (RT-01b / #381)

To prevent rapid reputation escalation via burst-registrations or timing attacks, the
positive reputation gain from a single node MUST be capped at a **per-node hourly window**:

- Maximum positive gain per node per **1-hour rolling window**: **+0.20**
- The window starts at the first positive event within the hour and resets after 3600 seconds
- Negative deltas are not windowed and apply in full
- Implementation: `rep_hourly_gain` and `rep_hourly_window_start` columns on the `nodes` table

Rationale: RT-01 caps per-heartbeat gain at +0.10, but an attacker could send multiple
heartbeats per hour. The hourly ceiling (+0.20) closes this window — a new node takes at
minimum 2.5 hours of sustained legitimate traffic to reach 1.0 from the initial 0.5.

Conformance: REP-04 (conformance-test-suite.md §13.6).

### 11.7 Quorum reporter independence (RT-03b / #382)

When computing the quorum for telemetry reports (proxy-observed latency, `POST /v1/telemetry`),
participating proxy reporters MUST satisfy minimum maturity and reputation gates:

- Reporter node age MUST be **≥ 3 days** since first registration
- Reporter reputation score MUST be **≥ 0.55**
- Reports from nodes that do not meet either gate MUST be acknowledged (HTTP 201/202) but
  MUST NOT count toward the quorum threshold or influence the target node's scoring

Rationale: A Sybil attacker registers many proxy nodes (cost: zero) and uses them to submit
coordinated telemetry that artificially inflates a single target node's latency score or
floods the quorum. The age + reputation gate ensures that only established, reputable
reporters participate in quorum decisions.

Conformance: REP-06 (conformance-test-suite.md §13.6).

### 11.8 Audit-report reporter eligibility (RT-05b / #383)

The per-reporter rate limit in §11.5 can be bypassed by registering new nodes. To prevent
this, directories MUST verify reporter eligibility before accepting a reputation delta:

- Reporter node age MUST be **≥ 3 days** since first registration
- Reporter reputation score MUST be **≥ 0.55**
- Reports from ineligible reporters MUST be acknowledged (HTTP 202) but MUST NOT reduce
  the target's reputation (same behavior as `delta_suppressed: true`)

This gate applies in addition to the rate-limit and global cap in §11.5, not instead of them.

Rationale: Without this gate, a bypass attacker registers fresh proxy nodes (cost: zero)
and immediately submits audit reports, evading the per-reporter 24h rate limit entirely.
The age + reputation gate closes this registration-bypass vector.

Conformance: REP-07 (conformance-test-suite.md §13.6).

---

## 12. Sybil-Resistance and Reputation Integrity

This section consolidates the normative anti-sybil mitigations scattered across §11, the
recognition spec, and the security model. It provides a single threat model, a table of
enumerated mitigations with conformance IDs, an attack verification analysis, and an honest
gap table covering what is **not** yet mitigated. Cross-reference: `project/SECURITY.md` §TC-9,
`spec/iicp-recognition.md` §8.

### 12.1 Threat model

The reputation and discovery system faces Sybil attacks — adversaries registering multiple
identities to farm eligibility gates, manipulate peer telemetry, or exhaust credits.

| Threat ID | Description | Primary target |
|-----------|-------------|----------------|
| T-SYB-01 | **Mass registration**: register N nodes from one IP to multiply the reputation pool | Badge thresholds, discover priority |
| T-SYB-02 | **Heartbeat velocity exploit**: rapid heartbeat spam to inflate self-reported reputation | Discover routing weight |
| T-SYB-03 | **Coordinated quorum poisoning**: use sybil nodes to dominate telemetry quorum for a target | Node latency scoring |
| T-SYB-04 | **Reporter bypass via re-registration**: create fresh nodes to evade per-reporter rate limits | Reputation audit pipeline |
| T-SYB-05 | **Credit laundering**: self-award credits between attacker-controlled nodes | CIP settlement |
| T-SYB-06 | **Identity laundering**: re-register after a reputation flag to start with a clean slate | Reputation continuity |
| T-SYB-07 | **Badge farming via sybil proxies**: satisfy task-count badge thresholds using controlled proxy nodes | Gamification tiers |

### 12.2 Enumerated mitigations

Implementations MUST enforce all mitigations listed as MUST. SHOULD mitigations are recommended
but directory-grade conformance is NOT broken by their absence.

| Mitigation ID | Threat(s) | Rule (MUST) | Detail | Conformance |
|---------------|-----------|-------------|--------|-------------|
| SYB-01 | T-SYB-01 | MUST | Registration rate-limit: directory MUST reject REGISTER after 60 requests/min from the same source IP with HTTP 429 (`IICP-E034` — see iicp-core.md §7 for error catalog). | — |
| SYB-02 | T-SYB-01 | MUST | New nodes start at reputation 0.5 (not 0.0 and not 1.0). | — |
| SYB-03 | T-SYB-02 | MUST | Per-heartbeat positive delta cap: +0.10 maximum per heartbeat (RT-01, §11.2). | REP-01–03 |
| SYB-04 | T-SYB-02 | MUST | Hourly reputation velocity ceiling: +0.20 maximum per 1-hour rolling window regardless of heartbeat frequency (RT-01b, §11.6). | REP-04 |
| SYB-05 | T-SYB-03 | MUST | Quorum reporter independence: proxy reporters that do not satisfy age ≥ 3 days AND reputation ≥ 0.55 MUST be acknowledged but MUST NOT count toward quorum (RT-03b, §11.7). | REP-06 |
| SYB-06 | T-SYB-04 | MUST | Per-reporter audit rate limit: ≤1 audit report per reporter per 24h per target, AND ≤2 distinct reporters per target per day counted toward score (RT-05, §11.5). | REP-03 |
| SYB-07 | T-SYB-04 | MUST | Audit-report reporter eligibility: reporter MUST satisfy age ≥ 3 days AND reputation ≥ 0.55; ineligible reports acknowledged (HTTP 202) but MUST NOT reduce the target score (RT-05b, §11.8). | REP-07 |
| SYB-08 | T-SYB-05 | MUST | Credit laundering rate limit: ≤1,000 credits awarded per `node_id` per hour; excess MUST be rejected with HTTP 429 (TC-9b, `project/SECURITY.md §TC-9b`). | — |
| SYB-09 | T-SYB-06 | MUST | Identity permanence: operator `identity_uri` is pinned on first-use (ADR-034); re-registration with a different `identity_uri` creates a new zero-reputation operator; re-registration with the same `identity_uri` after a flag does NOT clear the flag (`spec/iicp-recognition.md §8` rule 5). | RECOG-AG-05 |
| SYB-10 | T-SYB-07 | MUST | Badge task-count collusion barrier: task counts toward badge thresholds with a `≥1,000` task requirement MUST require ≥3 distinct proxy `node_id` contributors (`spec/iicp-recognition.md §8` rule 3). | RECOG-AG-03 |
| SYB-11 | T-SYB-07 | MUST | Multi-node operator diversity isolation: same operator's multiple nodes MUST NOT multiply operator-diversity scores (Country Pioneer, Diversity Champion, Founding Cohort) (`spec/iicp-recognition.md §8` rule 1). | RECOG-AG-01 |

### 12.3 Attack verification: free-registration burst with perfect self-reported metrics

**Attacker profile**: single-IP operator, no existing reputation, no operator identity, goal is
to reach discover-routing weight ≥ 0.7 on a sybil node as quickly as possible.

**Step 1 — Registration burst**

At 60 registrations/min (SYB-01), the attacker can register 3,600 nodes/hour from a single IP.
Each node starts at reputation 0.5 (SYB-02). The registration burst alone does not produce
usable nodes — no age or reputation threshold is met at `t = 0`.

**Step 2 — Heartbeat inflation (perfect self-reported metrics)**

The attacker sends heartbeats at maximum permitted frequency. Due to SYB-04 (RT-01b,
MAX_HOURLY_GAIN = +0.20), the velocity ceiling is absolute regardless of heartbeat count:

| Target score | Delta required | Minimum real time |
|-------------|----------------|-------------------|
| 0.55 (reporter eligible) | +0.05 | ~15 min |
| 0.70 (moderate routing preference) | +0.20 | ~1 h |
| 1.00 (maximum) | +0.50 | ~2.5 h |

The per-heartbeat cap (SYB-03, RT-01) closes the trivial single-heartbeat shortcut.
The hourly ceiling (SYB-04, RT-01b) closes the multi-heartbeat burst shortcut.

**Step 3 — Quorum and audit-report influence**

Reporter eligibility gates (SYB-05, SYB-07) impose a hard **3-day age requirement** before any
sybil node's telemetry or audit reports count toward peer scoring. This gate binds before the
reputation ceiling and cannot be bypassed by heartbeat inflation.

**Verdict**: a single-IP burst registration achieves **no usable reputation influence for the
first 3 days**, and self-reported reputation is bounded at +0.20/hour thereafter. Perfect
self-reported metrics accelerate the journey to 1.0 but cannot defeat the age gate. The attack
surface shrinks to the patient Sybil variant (see Gap G-03 below).

### 12.4 Honest gap table

The following attacks are **not fully mitigated** by the rules in §12.2. Each entry names the
residual risk, its current partial mitigation (if any), and the intended remediation path.

| Gap ID | Description | Partial mitigation | Remediation path |
|--------|-------------|-------------------|------------------|
| G-01 | **Unverified task metrics**: heartbeat fields (`tasks_total`, `avg_latency_ms`) are self-reported by the adapter; an attacker can fabricate high performance metrics without serving real traffic | SYB-04 velocity ceiling bounds reputation gain rate; SYB-03 per-heartbeat cap bounds single-shot inflation | CIP signed task receipts (Phase 5, #396): receipts are proxy-attested and directory-verified, replacing self-reported fields as the scoring input |
| G-02 | **Multi-IP registration**: SYB-01 rate limit is per source IP; an operator with diverse IP space (residential proxies, large NAT pools, multiple VPSes) can register many nodes across different IPs without triggering the per-IP limit | SYB-09 identity permanence partially limits cross-node reputation laundering when operator identity is linked | Operator challenge-response liveness (#411): directory-initiated verification anchors node identity to a reachable endpoint; IPv6 GUA auto-registration (#416) further anchors to a network-visible address |
| G-03 | **Patient Sybil**: attacker pre-registers a fleet, waits 3 days for the age gate to clear, then has a cohort of "established" reporters capable of coordinated slow-burn audit manipulation on many targets | SYB-06 global 2-reporter cap per target per day limits per-node damage per target; SYB-07 age gate prevents immediate deployment | Full mitigation requires operator identity verification (ADR-030 Tier 1+) so that a single operator cannot control ≥3 "distinct" reporter nodes anonymously |
| G-04 | **Sybil proxy collusion for badge farming**: SYB-10 requires ≥3 distinct proxy `node_id` values, but a sybil operator controlling ≥3 proxy nodes satisfies this structurally; the rule blocks accidental self-contribution but does not block deliberate multi-node operators | SYB-11 blocks operator-diversity badge multiplication | Full mitigation requires cross-node operator identity linkage (ADR-030 + ADR-034): once operators can declare that multiple nodes share an operator identity, "distinct" can be interpreted as distinct operators rather than distinct node IDs |
| G-05 | **Reputation laundering via deregistration + re-registration**: a node with low reputation can deregister and re-register to reset its score to 0.5; this is a net benefit when reputation drops below 0.5 | SYB-09 blocks identity laundering when `identity_uri` is linked; without operator identity, node_id churn is undetectable | Full mitigation is gated on operator identity deployment (ADR-030); until then, the age gate (SYB-05, SYB-07) ensures freshly registered nodes cannot immediately participate in quorum or audit, limiting the value of the reset |

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.6.3 | 2026-07-02 | §1.3 adds compliance-readiness prohibited-practice intent guardrails for official clients: clear prohibited intent URNs are refused locally before discovery/routing with `IICP-POLICY-001`; this prevents prompt/task leakage for structurally unsupported use cases without claiming full legal classification. |
| 1.6.2 | 2026-06-28 | §6.4 adds provider public-reachability fallback semantics for SDK 0.7.75: direct route → accountless external tunnel → relay → local-only, with tunnel pacing/cooldown treated as a fallback trigger rather than a retry loop. |
| 1.0.0 | 2026-05-15 | Initial draft — extracted from ARCHITECTURE.md, RELIABILITY.md, and prior spec work as part of S.5 spec split |
| 1.1.0 | 2026-05-17 | §11 Reputation Update Rules — normative delta table, latency budgets by QoS class, bounded score invariant. Closes #113. |
| 1.2.0 | 2026-05-17 | §2.1 Added `realtime` QoS level row. §2.2 QoS Admission Control — MUST 429 capacity_exceeded with qos_class+retry_after_ms, MUST proxy node-switch. §2.3 renumbered from §2.2. Closes #119 (spec). |
| 1.3.0 | 2026-05-30 | §11.2 Per-heartbeat positive delta cap +0.10 MUST (RT-01 security fix, #375). §11.5 Peer audit-report griefing cap — per-reporter 24h rate limit + 2-reporter global cap per target per day MUST (RT-05 security fix, #379). |
| 1.5.0 | 2026-06-01 | §11.6 Hourly reputation velocity ceiling (RT-01b, MAX_HOURLY_GAIN=+0.20, 1h rolling window, REP-04). §11.7 Quorum reporter independence (RT-03b, age≥3d + rep≥0.55 gate, REP-06). §11.8 Audit-report reporter eligibility (RT-05b, same age+rep gate, REP-07). These three bypass-prevention rules close the gaps that §11.2 (RT-01 per-heartbeat cap) and §11.5 (RT-05 griefing cap) left exploitable via re-registration or burst-register attacks. |
| 1.4.0 | 2026-05-31 | §3.1 Phase 5 model-aware scoring weights documented (ADR-012/ADR-021 normative table — code↔spec gap #384 remaining item). Weights: availability 0.25, load 0.20, capacity 0.15, region 0.10, reputation 0.10, model_match 0.10, price_score 0.10. |
| 1.6.1 | 2026-06-12 | SYB-01 error code corrected: `registration_rate_limit_exceeded` → `IICP-E034` (per iicp-core.md §7 error catalog; spec-vs-spec inconsistency fix). |
| 1.6.0 | 2026-06-10 | §12 Sybil-Resistance and Reputation Integrity — consolidated threat model (T-SYB-01..07), enumerated mitigations table (SYB-01..11 with conformance IDs), attack verification for free-registration burst + perfect self-reported metrics, and honest gap table (G-01..05). Closes #499. |

---

## Sign-off

**Protocol Steward**: iicp-semantics.md captures SHOULD-level routing and fault-tolerance
semantics. It does not introduce new requirements — it formalises behaviour already
implemented across proxy/, adapter/, and iicp-node/. Part of S.5 spec split (issue #17). ✓
