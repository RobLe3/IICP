# IICP Service Lifecycle Profile

**Version:** 0.1.0-draft
**Status:** proposed semantic profile; not required for base IICP conformance
**Authority:** Protocol Steward
**Relation:** `iicp-core.md`, `iicp-framing.md`, `iicp-semantics.md`, `iicp-cooperative-inference.md`

## 1. Purpose

`urn:iicp:profile:service-lifecycle:v1` makes asynchronous and streaming task
behavior interoperable without changing the native frame header or allocating a
new base message type. It applies to a single `task_id` after the provider has
been selected. It does not define model tokens, tool semantics, tensor traffic,
or provider scheduling internals.

## 2. Negotiation

A caller declares profile requirements in the CALL constraint extension:

```json
{
  "constraints": {
    "required_profiles": ["urn:iicp:profile:service-lifecycle:v1"],
    "optional_profiles": []
  }
}
```

Providers advertise supported profile URNs in their capability envelope. A
provider that does not support a required profile MUST reject before accepting
work with `unsupported_profile`. Unknown optional profiles MUST be ignored.
Profile negotiation is not a directory task payload and MUST NOT cause prompt
content to be sent to the directory.

## 3. States and terminality

| State | Meaning | Allowed next state |
|---|---|---|
| `submitted` | Caller has sent the task. | `accepted`, `rejected`, `timed_out` |
| `accepted` | Provider committed to one execution. | `streaming`, `completed`, `failed`, `cancelled`, `timed_out` |
| `streaming` | Provider emits ordered partial events. | `streaming`, `completed`, `failed`, `cancelled`, `timed_out` |
| `rejected` | Provider did not accept work. | terminal |
| `completed` | Final successful result. | terminal |
| `failed` | Final execution failure. | terminal |
| `cancelled` | Cancellation was accepted. | terminal |
| `timed_out` | The declared deadline elapsed. | terminal |

No state may follow a terminal state. A provider MUST emit exactly one terminal
outcome for every accepted task, even when the execution engine cannot stop
immediately. `is_final=true` is required on that terminal event or response.

## 4. Partial-event envelope

Every partial event and terminal event uses this additive result envelope:

| Field | Requirement | Meaning |
|---|---|---|
| `task_id` | MUST | Original task identifier. |
| `sequence` | MUST | Zero-based, strictly increasing integer. |
| `event` | MUST | `accepted`, `partial`, `completed`, `failed`, `cancelled`, or `timed_out`. |
| `is_final` | MUST | `false` except on a terminal event. |
| `result` | MAY | Partial or final intent-specific data. |
| `error` | MUST on failure | Safe machine-readable error; no stack trace or payload echo. |
| `receipt` | SHOULD on terminal | Redacted execution/billing evidence when another profile requires it. |

Receivers MUST discard an event whose `sequence` is not greater than the last
accepted sequence for that `task_id`. This profile does not define stream
resumption: a missing sequence, disconnect, or ambiguous terminal state is a
terminal `failed` outcome from the caller perspective unless a later profile
explicitly negotiates resumption.

## 5. Deadline, cancellation, retry, and idempotency

- `constraints.timeout_ms` is an end-to-end deadline measured from provider
  receipt. A provider MUST reject before acceptance when it cannot honor the
  deadline, and MUST transition an accepted task to `timed_out` when it expires.
- A caller cancels with a CONTROL message over native transport or the
  HTTP-equivalent cancellation control endpoint. The control payload contains
  only `task_id` and `reason`; it MUST NOT repeat task payload content.
- Cancellation before acceptance resolves as `rejected`; cancellation after
  acceptance resolves as `cancelled` or the already-committed terminal result.
  Providers MUST NOT report a task as cancelled after completing it.
- Retrying a request before an `accepted` outcome is safe only with the same
  `task_id` and idempotency key. Once accepted, a duplicate MUST return the
  same known state or terminal receipt and MUST NOT create another execution or
  charge.
- Reusing a `task_id` with a different intent, payload digest, constraints, or
  idempotency key MUST return `conflict` and MUST NOT execute.
- A retry after an ambiguous disconnect MUST use the same identifiers and query
  the known task state before requesting another provider. A caller MAY submit a
  new task identifier to another provider only after declaring the first result
  unavailable; any separate billing is a new execution.

## 6. Transport mapping

Native TCP/QUIC uses the existing CALL, RESPONSE, CONTROL, and OBSERVE message
families. HTTP uses the existing task response shape plus an event stream and a
cancellation control resource. Implementations MAY choose transport-specific
delivery mechanics, but the state table, ordering, finality, and idempotency
requirements above remain identical.

## 7. Conformance

`research/native-ai-infrastructure/fixtures/service-profiles-v1.json` defines
the minimum state-transition vectors. Implementations claiming this profile
MUST pass `SERVICE-LIFECYCLE-01` through `SERVICE-LIFECYCLE-08` in the
conformance suite.

## 8. Security and privacy

Task payloads and generated content MUST NOT be copied into lifecycle events,
error messages, traces, or cancellation records by default. Receipts identify
the selected provider and policy result only to the extent permitted by the
applicable privacy profile. This profile does not make a remote executor blind
to the prompt it processes.
