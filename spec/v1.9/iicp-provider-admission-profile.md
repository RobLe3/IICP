# IICP Provider Admission Profile

**Version:** 0.1.0-draft
**Status:** proposed semantic profile; not required for base IICP conformance
**Authority:** Protocol Steward
**Relation:** `iicp-core.md`, `iicp-semantics.md`, `node-capability-format.md`, `iicp-service-lifecycle-profile.md`

## 1. Purpose

`urn:iicp:profile:provider-admission:v1` defines a bounded, privacy-preserving
provider boundary for readiness, admission, deadlines, overload, and retry
guidance. It standardizes what a client needs to route safely without exposing
queue depth, peer topology, model placement, scheduler state, or hardware
inventory.

## 2. Capability advertisement

A supporting capability MAY include this additive block:

```json
{
  "admission": {
    "availability": "ready",
    "capacity_class": "standard",
    "deadline_support": true,
    "supported_profiles": [
      "urn:iicp:profile:provider-admission:v1",
      "urn:iicp:profile:service-lifecycle:v1"
    ],
    "observed_at": "2026-08-09T10:00:00Z",
    "valid_until": "2026-08-09T10:02:00Z"
  }
}
```

| Field | Requirement | Values / meaning |
|---|---|---|
| `availability` | MUST | `ready`, `draining`, or `unavailable`. |
| `capacity_class` | SHOULD | `limited`, `standard`, or `high`; a coarse self-attested class, not a queue metric. |
| `deadline_support` | MUST | Whether the provider enforces caller deadlines. |
| `supported_profiles` | MUST | Semantic profile URNs supported by this capability. |
| `observed_at` | MUST | RFC 3339 time when the provider observed this state. |
| `valid_until` | MUST | RFC 3339 expiry, later than `observed_at` and at most 300 seconds later. |
| `retry_after_ms` | COND | Required when unavailable, optional when draining; 100 through 300000. |

An unavailable or draining provider MUST NOT advertise itself as ready. The
directory MAY relay these safe fields but MUST NOT infer them from task payloads
or publish private runtime details. Clients treat an expired block as unknown
capacity, not continued availability. A missing block preserves legacy
eligibility and does not mean unlimited capacity.

## 3. Admission outcome

Before execution, a provider returns exactly one admission outcome:

| Outcome | HTTP equivalent | Meaning |
|---|---|---|
| `accepted` | 2xx / accepted event | One bounded execution has been reserved. |
| `unsupported_profile` | 422 | Required profile cannot be honored. |
| `deadline_unachievable` | 408 or 504 | Provider cannot meet the supplied deadline. |
| `capacity_exceeded` | 429 | No bounded execution slot is available. |
| `temporarily_unavailable` | 503 | Provider is draining, warming, or unavailable. |
| `policy_rejected` | 403 | A declared provider policy rejects the request before execution. |

The provider response carries `task_id`, `outcome`, and, when accepted,
`accepted_until`. The latter MUST NOT exceed the request deadline. A deferred
`capacity_exceeded` or `temporarily_unavailable` outcome carries
`retry_after_ms`; an accepted outcome MUST NOT. Optional
`capacity_class` uses the same bounded vocabulary as the advertisement.

Rejections MUST occur before task execution and MUST NOT consume a billable
execution. `capacity_exceeded` and `temporarily_unavailable` MUST include a
`retry_after_ms` from 100 through 300000 so the caller does not busy-loop the
same provider.

## 4. Bounded admission and deadlines

- Providers MUST bound admitted work and MUST NOT silently create an unbounded
  queue.
- A provider that lacks a bounded slot or cannot honor `timeout_ms` MUST reject
  before acceptance using the table above.
- `draining` means already-accepted tasks may finish but new work MUST be
  rejected as `temporarily_unavailable`.
- A caller SHOULD prefer another eligible provider after `capacity_exceeded`.
  It MAY retry the same provider only after `retry_after_ms` and with the same
  idempotency identifiers when the original task was not accepted.

## 5. Client routing rules

Clients MUST treat readiness and capacity as short-lived hints, not trust or
quality claims. They MUST apply encryption, region, policy, and required-profile
filters before admission. If no eligible provider can honor a required profile
or deadline, clients MUST fail closed rather than silently weakening those
constraints.

## 6. Conformance

`research/native-ai-infrastructure/fixtures/service-profiles-v1.json` defines
the lifecycle admission vectors. The focused
`research/pre-normative-profiles/fixtures/provider-admission-v1.json` adds
portable freshness, deadline, backpressure, field-combination and redaction
cases. Implementations claiming this profile MUST pass both fixture sets.

## 7. Privacy boundary

The profile intentionally excludes precise concurrency, queue length, GPU/CPU
memory, peer identity, network route, model shard, and scheduler information.
Those are implementation-specific runtime details. A MeshLLM-backed provider
is one logical provider at this boundary; its internal mesh is not an IICP
admission surface.
