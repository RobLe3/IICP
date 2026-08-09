# Architecture decision: context and signed service-event ownership

**Status:** Accepted portability boundary  
**Recorded:** 2026-08-09  
**Machine-readable contract:**
[`context-event-ownership-v1.json`](context-event-ownership-v1.json)  
**Related work:** IICP #31, #52, #93; Rust directory #38

## Decision

Every public directory state transition and signed event type has one owning
bounded context. Ownership is a protocol responsibility, not a deployment
instruction: one process may implement several contexts, and splitting a
process does not change public routes or event semantics.

The event type determines the owning context. A signed `service_id` records
which deployed service emitted an event, but it does not grant authority,
select a handler, change the event owner, or authorize routing. Unknown valid
service identifiers are retained as opaque signed metadata. Invalid identifiers
and signature failures are rejected.

The current event envelope remains backward compatible:

- a missing or null `service_id` uses the released legacy signing transcript;
- a present `service_id` selects the domain-separated v2 transcript;
- implementations must not emit non-null service identifiers merely because
  storage and verification support them;
- runtime emission requires an independently operated pilot, replay evidence,
  backup and restoration evidence, and a rollback decision.

## Context boundaries

The machine-readable contract assigns provider registry, selection,
reachability, reputation, ledger, federation membership, operator evidence,
telemetry, and recognition state. Cross-context work uses stable identifiers
and signed events; it must not require another context's private database
tables or framework-specific types.

The seven-event federated set is closed for the current profile:

`REGISTER`, `DEREGISTER`, `CREDIT_AWARD`, `REPLICA_REGISTERED`,
`REPLICA_DEREGISTERED`, `REPUTATION_DECAY`, and `OPERATOR_OBSERVED`.

High-frequency snapshots, local audit events, and the planned recognition
chain are separate:

- heartbeat, score, load, current availability and task-derived reputation are
  snapshot state rather than federated event-tail traffic;
- uptime, reachability, health, audit-report and detailed ledger events may be
  kept on a directory-local signed chain;
- `FOUNDER_LOCKIN` and `FOUNDER_SUCCESSION` belong to a dedicated,
  non-federated recognition chain and remain planned until that chain exists.

A replica applies only event types whose replication action is `apply_state`.
It records `OPERATOR_OBSERVED` without changing state and ignores local,
retired, dedicated-chain and unknown event types for state mutation.

## Public routes and implementation structure

Existing routes remain owned by their protocol context even when a monolith
dispatches them. A refactor may move handlers and types into modules without
changing route paths, authentication, request and response schemas, signing
transcripts, persistence effects, or error behavior.

`service_id` is not a public service-discovery mechanism. Deployment topology,
internal queue names and database placement stay outside the event contract.

## Consequences

- PHP remains Genesis and Rust remains an operator preview until their separate
  operational gates pass.
- Rust directory decomposition can use the context map without introducing
  services or changing wire behavior.
- An independent implementation can assign routes, transitions and event
  consumers without reading PHP or Rust source.
- New event types require one owner, an explicit scope, a replication action,
  security and privacy review, and conformance evidence.
- A new service identifier does not require clients to understand that
  identifier, but emitting it changes the signing transcript and therefore
  requires compatibility evidence.

## Non-goals

This decision does not authorize microservices, production federation, a Rust
shadow, a PHP deprecation, a new event type, a service registry, or a wire
version change.
