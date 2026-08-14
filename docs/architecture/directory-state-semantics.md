# Architecture decision: directory state and dispatch eligibility

**Status:** Accepted semantic boundary; current connected-directory behavior retained  
**Recorded:** 2026-08-14  
**Machine-readable contract:**
[`directory-state-semantics-v1.json`](directory-state-semantics-v1.json)  
**Related work:** IICP #39, #63, #160 and #163

## Decision

An IICP Directory treats five properties as separate axes:

- **Identity validity** says whether the node identity is valid or revoked.
- **Advertisement state** says whether a signed or authenticated capability and
  locator advertisement is current, superseded, stale, revoked or invalid.
- **Reachability evidence** says whether a route was independently verified,
  freshly self-reported, stale, failed or is unknown.
- **Execution availability** says whether the advertised service is ready,
  degraded, unavailable or unknown.
- **Dispatch eligibility** is the result of applying current freshness,
  availability, policy, security, capability and Profile rules. It is either
  eligible or ineligible for the requested operation.

No one axis implies another. A valid identity may have a valid but currently
offline advertisement. A reachable endpoint may be policy-ineligible. A stale
advertisement is not revoked, and an unavailable service does not cease to
exist.

## Current connected-directory mapping

The existing public Directory remains a connected-mesh Profile. Its default
discovery contract does not change:

- Registration establishes a current advertisement only after identity,
  authorization, endpoint-safety and liveness checks pass.
- An authenticated heartbeat refreshes self-reported reachability and runtime
  state. `available: false` keeps the node unavailable and ineligible.
- More than 90 seconds without a valid heartbeat makes reachability stale,
  marks the node dormant/unavailable and removes it from default discovery.
- A later valid heartbeat reactivates the record. It restores availability
  unless the heartbeat explicitly reports `available: false`; all other
  eligibility gates are recalculated.
- A current active probe is stronger route evidence than a self-report. A
  confirmed probe failure demotes the failed route. Another independently
  supported route, such as an authenticated relay path, may remain eligible.
- Endpoint replacement supersedes the old locator only after the new endpoint
  passes ownership, safety and liveness validation. Failure leaves the old
  advertisement unchanged rather than publishing an unverified route.

`GET /v1/discover` and dispatch tickets return only candidates that are
eligible now. The `public` discovery view is a redacted projection of that same
current candidate set; it is not an archive of offline advertisements.
Authenticated owner or operator detail may expose an existing dormant record.

## Advertisement and federation evidence

Signed events and snapshots provide provenance and integrity, not perpetual
freshness. Recipients verify the signature, signer, sequence and timestamp, then
apply their local freshness and policy rules before dispatch. A valid cached
advertisement may remain known after reachability expires, but it is not a
current route.

The current snapshot plus event-tail design keeps high-frequency heartbeat,
load and availability state in snapshots. A replica whose synchronization lag
exceeds the specified bound must not serve discovery. A delayed snapshot does
not become current merely because its signature remains valid.

Evidence sources have explicit scope:

| Evidence | What it can establish | Freshness rule |
|---|---|---|
| Registration liveness probe | The registered route responded during admission | Current registration transaction only |
| Authenticated heartbeat | The node credential/key holder recently reported local state | Current heartbeat window |
| Directory active probe | The directory recently observed the route | Probe-specific bounded window |
| Signed snapshot or event | A directory attested to recorded state at a sequence and time | Signature validity plus replica-lag and state-freshness rules |
| Operator assertion | A declared configuration or policy fact | Never sufficient by itself to prove current route reachability |

Verification may use cached trust anchors and signed evidence; it does not
require a live central lookup for every check. Consumers must still reject
expired, revoked, superseded or policy-ineligible evidence.

## State examples

- **Valid offline:** identity valid, advertisement current, reachability stale,
  availability unavailable, dispatch ineligible. The record may be retained,
  but default discovery omits it.
- **Superseded:** an accepted newer advertisement replaces the old one. The old
  locator cannot be selected even if it still responds.
- **Revoked:** identity or advertisement revocation makes dispatch ineligible
  regardless of reachability.
- **Policy-ineligible:** route and service may be healthy, but an unmet policy,
  security Profile or request constraint prevents dispatch.
- **Delayed federation:** a valid signature proves origin and integrity, while
  excessive lag prevents the replica from serving current discovery.

Scheduled or predicted reachability is reserved for a future optional Profile.
It cannot make a node eligible in the current default view.

## Implementation parity boundary

The Rust operator preview now clears `dormant_since` and emits one `REACTIVATE`
event when a dormant node resumes heartbeats. Its active probe confirms a
failure before changing direct-route state and emits one demotion or restoration
event per state transition. The implementation consumes this decision's shared
scenario fixture. Release and operator evidence remain separate from this
source-level parity result, and PHP remains the Genesis authority.

Internal schemas and module names may differ, but neither implementation may
collapse retained identity or advertisement state into current dispatch
eligibility.

Future implementation work must use the shared fixture before adding an
offline, scheduled or historical view. Such a view must be explicit and must
not change the default dispatch contract.

## Non-goals

This decision does not add a wire field, offline-discovery endpoint, contact
plan, persistent task queue, DTN/BPv7 behavior or space-specific availability
model. It does not return dormant nodes from default discovery, weaken endpoint
validation, or make any Directory a universal identity or availability
authority.
