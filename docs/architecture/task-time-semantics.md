# Architecture decision: task time semantics

**Status:** Accepted semantic boundary; additive delivery profile deferred  
**Recorded:** 2026-08-14  
**Machine-readable contract:**
[`task-time-semantics-v1.json`](task-time-semantics-v1.json)  
**Related work:** IICP #3, #160 and #162

## Decision

IICP distinguishes five task-related time axes:

- **Execution timeout** limits provider-side admission and execution work after
  the provider receives an attempt. The current `constraints.timeout_ms` field
  represents this provider attempt budget for compatibility.
- **Delivery lifetime** limits how long a delivery binding may retain or
  forward an attempt before provider receipt.
- **Task deadline** is the latest acceptable completion time for the logical
  task, independent from any single attempt.
- **Result validity or retrieval lifetime** limits how long a completed result
  remains useful or retrievable.
- **Caller wait timeout** is local caller patience. Its expiry is not evidence
  that the provider cancelled or stopped execution.

Only the first axis has a general current-wire field. The other four are
semantic definitions reserved for a separately reviewed additive Profile or
local API behavior. Implementations must not infer them from `timeout_ms`, HTTP
timeouts, token expiry, cache TTL, heartbeat freshness or native framing key 22.

## Current compatibility mapping

For base HTTP and current service-lifecycle calls,
`constraints.timeout_ms` begins when the provider receives the attempt and
covers admission, queueing under that provider, execution and terminal response
creation. A provider rejects before acceptance when it cannot honor the budget
and reports `timed_out` after acceptance when the budget expires.

Native CALL key 6 carries the same provider attempt budget in seconds. Native
key 22 remains a legacy binding-local TTL hint. It is not a logical task
deadline, result-retention promise or general delivery lifetime unless a future
negotiated Binding/Profile defines that mapping.

A client may use a shorter or longer local network/wait timeout. If it stops
waiting, the task becomes locally ambiguous until cancellation is acknowledged
or lifecycle state is retrieved. The client must not report confirmed
`cancelled` solely because a socket, HTTP request or local timer ended.

## Task and attempt identity

`task_id` identifies one logical task. Under the negotiated lifecycle profile,
retries retain `task_id` and the idempotency key while each new attempt uses a
new `call_id`. Retransmission of the same attempt does not create a task or an
execution.

An unprofiled base HTTP CALL has one attempt, so its `task_id` is unique for that
CALL and logical task. This compatibility form does not redefine `task_id` as
attempt identity. A retry that may encounter an accepted or completed task must
use lifecycle/idempotency semantics rather than create an untracked duplicate.

## Clock and expiration rules

Implementations use monotonic clocks for local intervals. Absolute deadlines,
when a future Profile introduces them, must declare UTC encoding, clock-skew
tolerance and behavior when the deadline is already elapsed. A provider or
binding may refuse a requested retention interval that exceeds its bounded
resources; it must report the refusal rather than silently shorten a required
deadline.

Credential, route-ticket, evidence, advertisement, cache and heartbeat
expirations retain their existing owners. They are security or control-plane
freshness limits, not task execution or delivery semantics.

## Required outcomes

- A caller wait timeout leaves provider execution state unknown.
- A confirmed cancellation produces `cancelled`; a completed task is never
  relabelled cancelled.
- A task deadline that expires before dispatch rejects without execution.
- A result arriving after caller wait expiry may still be valid when the task
  deadline and result-validity policy permit it.
- Clock adjustment does not change a monotonic local execution budget.
- Retention and delivery limits remain bounded and may fail closed before work
  is accepted.

## Non-goals

This decision adds no request field, queue, result store, DTN/BPv7 behavior,
exactly-once delivery guarantee or timeout-default change. It does not require a
provider to support disconnected submission or late result retrieval.
