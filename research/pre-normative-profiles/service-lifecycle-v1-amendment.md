# Proposal — Asynchronous Service Lifecycle Amendment

**Version:** 0.4.0-draft
**Status:** pre-normative amendment to the proposed service-lifecycle profile  
**Profile:** `urn:iicp:profile:service-lifecycle:v1`  
**Tracking:** iicp.network #668

## Scope and compatibility

This amendment completes the task-level lifecycle without changing the 12-byte
native frame, intent payload schemas, provider schedulers, model runtimes, or
MeshLLM/Skippy stage traffic. It refines the existing proposed lifecycle profile.
A caller MUST negotiate it before relying on status observation, replay or resume.
Unknown optional profiles preserve base CALL/RESPONSE behavior; an unsupported
required profile fails before acceptance.

## Roles and identifiers

The caller creates an immutable `task_id` and `idempotency_key`. The provider
owns task-state transitions after receipt. An authorized observer may read state
but cannot mutate it. Reuse of either identifier with a different intent, payload
digest, route constraints or execution constraints is a terminal `conflict`
without execution or charge.

## State machine

| State | Initiator | Required event fields | Legal next states |
|---|---|---|---|
| `submitted` | caller | task/idempotency IDs, intent, deadline | `accepted`, `rejected`, `expired` |
| `accepted` | provider | sequence, accepted timestamp | `queued`, `running`, `completed`, `cancelled`, `failed`, `expired` |
| `queued` | provider | sequence | `running`, `waiting`, `cancelled`, `failed`, `expired` |
| `running` | provider | sequence | `waiting`, `streaming`, `completed`, `cancelled`, `failed`, `expired` |
| `waiting` | provider | sequence, safe reason code | `queued`, `running`, `cancelled`, `failed`, `expired` |
| `streaming` | provider | sequence | `streaming`, `waiting`, `completed`, `cancelled`, `failed`, `expired` |
| `rejected` | provider | sequence, safe reason | terminal |
| `completed` | provider | sequence, final result or reference | terminal |
| `failed` | provider | sequence, safe error | terminal |
| `cancelled` | provider | sequence, cancellation outcome | terminal |
| `expired` | provider | sequence, deadline outcome | terminal |

`timed_out` from the earlier draft is accepted as a deprecated wire alias for
`expired` during migration. Emitters of this amendment use `expired`.
No event follows a terminal event. Exactly one terminal event is authoritative.
A disconnect is not a state transition and does not cancel work by default.

## Event and progress envelope

Every provider event contains `task_id`, a zero-based strictly increasing
`sequence`, `state`, `is_final`, and `observed_at`. It MAY include a stable
`event_id`, progress (`completed_units`, `total_units`, unit), a safe reason,
an intent-specific partial/final result, and a redacted receipt.

The receiver deduplicates by `event_id` where present and otherwise by
`(task_id, sequence)`. A repeated event must be byte-equivalent. A conflicting
duplicate is a protocol error. Events below the accepted sequence are ignored.
A forward gap pauses delivery and triggers replay/status; it is not silently
treated as completion. Progress is advisory and MUST NOT contain prompt, response,
credentials, raw endpoint, private runtime topology, shard, queue, or checkpoint
contents.

## Observation, reconnect and resume

An authorized caller may request:

- `status(task_id)`: current state, latest sequence and terminal receipt if any;
- `observe(task_id, after_sequence)`: replay retained events greater than the
  offset, then continue live observation;
- `resume(task_id, after_sequence)`: synonym for observe when a prior delivery
  connection ended; it never restarts execution.

Providers advertise `event_replay_window_ms` and `terminal_status_ttl_ms`.
Within the replay window, retained events MUST be returned in order without
duplication. Outside it, the provider returns `resume_unavailable`, current
state and latest sequence, without creating a second execution. If terminal
status has also expired, it returns `unknown_task`. A client MUST NOT submit a
new billable execution merely because replay is unavailable.

A checkpoint reference is optional, opaque, authorization-scoped, expiring and
integrity-bound. It MUST NOT reveal tensor data, cache contents, filesystem paths,
peer topology or scheduler state. This profile does not standardize migration or
restoration from a checkpoint.

## Cancellation matrix

| Request time | Provider behavior |
|---|---|
| before acceptance | reject; no execution or charge |
| `accepted` / `queued` / `waiting` | stop admission/queueing and emit `cancelled` |
| `running` / `streaming` | acknowledge `cancellation_requested`; emit `cancelled` when stopped or the already-committed terminal result |
| after terminal | return the existing terminal state; never rewrite it |
| immediate stop unsupported | continue bounded cleanup and expose `cancellation_pending`; deadline still applies |

Cancellation is idempotent and propagates through coordinators to owned
subtasks. It does not authorize cancellation of unrelated tasks.

## Retry, idempotency and accounting

| Observed point | Retry rule | Accounting rule |
|---|---|---|
| no acceptance observed | same IDs; query status first | no duplicate charge |
| accepted, no partial event | status/observe only | one execution reservation |
| partial stream observed | observe after last sequence | one execution; replay is not billable |
| terminal observed | return cached terminal state/receipt | settlement is idempotent |
| `resume_unavailable` | status/fail safely; new task requires explicit caller decision | a new task is a separate execution |
| conflicting IDs/content | reject `conflict` | no execution or charge |

## Transport-neutral mapping

| Semantic operation | HTTP JSON/CBOR | Native TCP/QUIC |
|---|---|---|
| submit | `POST /v1/tasks` | CALL |
| status | `GET /v1/tasks/{task_id}` | OBSERVE action `status` |
| observe/resume | event stream with `after_sequence` | OBSERVE stream |
| cancel | `POST /v1/tasks/{task_id}/cancel` | CONTROL action `cancel` |
| events/terminal | JSON/CBOR event envelopes | RESPONSE/OBSERVE envelopes |

Bindings may provide equivalent paths, but MUST preserve the same state,
sequence, terminality, authorization, deadline and idempotency semantics.
Transport flow control does not replace provider admission control.

## Privacy and security

Status, progress and receipts are authorization-scoped. Public directory data
contains capability support and coarse retention limits only, never per-task
state. Lifecycle records do not repeat task content by default. Error and reason
fields are bounded enums or redacted text without stack traces. Resume tokens,
if used by a binding, are audience-bound, expiring and replay-limited.

## Conformance gate

The companion `fixtures/service-lifecycle-v1.json` defines valid and invalid
transitions, disconnect/resume, cancellation, duplicate and privacy vectors.
Python, TypeScript and Rust reference stores consume the same fixture. Python
and Rust provide explicitly mounted HTTP adapters; TypeScript remains
transport-neutral. All three exercise idempotent submission, bounded replay,
restart snapshot restoration and terminal cancellation. Snapshots are an
implementation hook, not a standardized persistence format or proof of
multi-process durability. This is sufficient prototype evidence, not
ratification evidence.

The amendment remains draft until live observation under backpressure,
cancellation during real backend execution, replay-window expiry, authorization
integration and bounded-retention behavior have cross-implementation evidence.
No base-wire change is authorized by this draft.

## Authorization port

An implementation exposing lifecycle submit, status, observe or cancel surfaces
MUST authenticate and authorize each operation. The profile does not mandate an
identity provider or token format. An implementation MAY expose a pluggable
authorization port whose input is limited to the presented credential,
operation and opaque `task_id`.

An unauthenticated request returns `401`. An authenticated principal lacking a
general operation scope returns `403`. Status, observation or cancellation of a
task outside that principal's task scope SHOULD be concealed as `404` to avoid
task-identifier enumeration. A deployment authorizer is responsible for binding
a verified principal to a task identifier at submission; the lifecycle store
format and identity database remain implementation-specific. Authorization
responses MUST NOT expose principal identifiers, credentials, task content,
endpoints or backend topology. The existing single bearer-token helper is only
a compatibility/test adapter and is not a production identity design.
## Runtime cancellation and observer backpressure

Cancellation changes lifecycle state only after the provider has attempted to
signal the active execution handle. Implementations distinguish
`cancel_signalled`, `cancel_unsupported` and `already_terminal`; a cancellation
request MUST NOT silently imply that backend execution stopped immediately.
Portable evidence then distinguishes `cancel_requested`,
`transport_aborted`, `backend_acknowledged`, `execution_stopped`,
`cancel_unsupported` and `already_terminal`. These levels are evidence, not
aliases: a closed HTTP request proves neither backend acknowledgement nor
execution termination. `cleanup_complete` proves only that the provider
released its local task-scoped cancellation handle. Backend-specific handles
and acknowledgement mechanisms remain implementation details.

Sustained observation uses a bounded provider buffer. When an observer's last
accepted sequence precedes the earliest retained event, the provider returns
`observer_lagged` with only the earliest available and latest sequence. The
observer reconnects through ordinary bounded replay; the provider MUST NOT grow
an unbounded queue for a slow or disconnected consumer. Terminal events close
the observer after delivery and disconnect releases its slot.

The pre-normative fixture
`fixtures/service-lifecycle-runtime-control-v1.json` defines the portable
outcomes. It adds no transport-specific frame or default runtime mounting.

## Partial-delivery accounting cardinality

The companion `fixtures/service-lifecycle-accounting-v1.json` defines only
whether a lifecycle action creates, reuses, releases or leaves unchanged an
execution reservation and whether it creates or reuses a settlement. It does
not define prices, settlement amounts, credit units, refunds or commercial
terms.

One execution has at most one reservation. Terminal and post-acceptance
cancellation outcomes have at most one idempotent settlement. Status,
observation and replay never create a reservation or settlement. A repeated
terminal or cancellation action returns the existing settlement. Cancellation
before acceptance releases an existing reservation without settlement.

`resume_unavailable` never authorizes automatic resubmission. A new execution
requires an explicit caller decision plus a fresh `task_id` and fresh
`idempotency_key`; it then receives its own reservation. The amount due for a
completed, failed, expired, cancelled or partially delivered execution remains
an implementation/profile policy and MUST be bound to the terminal outcome.
This draft helper is not mounted into production lifecycle or credit paths.
