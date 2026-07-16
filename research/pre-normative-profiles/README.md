# IICP proposal drafts

These documents are pre-normative design proposals. They do not change the
ratified IICP suite, existing wire contracts, or client behavior. A proposal
may advance only after deterministic simulation, cross-SDK fixture tests,
implementation review, a migration path and spec-only repository release
synchronization.

## Current strategic decision

The current direction is **a small stable intent core plus explicit capability,
policy, evidence and extension profiles**. Stable URNs are preserved; MCP and
A2A are compatibility inputs rather than IICP core task models. The 2026-07-11
simulation pass supports hybrid client/node receipts with redacted directory
metadata and identifies composite inverse-load weighting as the only selection
candidate ready for implementation research. It does not ratify a new wire
contract or a broad domain ontology.

Tracking: `iicp.network#619` and spec-source synchronization
`RobLe3/IICP#2`.

The shared fixture set contains
[`fixtures/profile-compatibility-v0.json`](./fixtures/profile-compatibility-v0.json)
[`fixtures/dispatch-route-ticket-v1.json`](./fixtures/dispatch-route-ticket-v1.json),
and [`fixtures/endpoint-security-v1.json`](./fixtures/endpoint-security-v1.json).
Its manifest pins both digests and it is consumed by maintained SDK, directory
and browser checks. The profile compatibility evaluator is additive and
pre-normative; it is intentionally not a new runtime requirement until a
negotiated profile and ratified release process exist. The policy/data-handling
schema and `selection-profile-v1.md` are likewise drafts, not a routing-default
or wire-format change.

The intent/capability/extension registry proposal has completed its
cross-implementation experimental-candidate gate. This means its fixtures and
release workflow are ready for explicit opt-in research; it is not a normative
promotion.

The policy operational-evidence fixture adds only an opt-in compatibility
check for locally authenticated, digest-bound and unexpired evidence records.
It is not a legal certification and does not change default routing.

The lifecycle accounting fixture defines reservation and idempotent settlement
cardinality for replay, cancellation, partial delivery and explicit new tasks.
It does not define prices or mount production economic behavior.

`endpoint-security-profile-v1.md` is a client-side transport-hardening profile.
It requires DNS-aware validation and address-pinned provider connections without
adding directory fields or changing the IICP wire envelope.

`service-lifecycle-v1-amendment.md` completes the proposed asynchronous task
state machine, observation, replay, cancellation and idempotency semantics. It
now has three transport-neutral SDK stores, runtime cancellation/observer
controls in all three SDKs, and two explicitly mounted HTTP adapters. Portable
evidence distinguishes transport abort from backend acknowledgement, confirmed
execution stop and local cleanup without importing backend-private topology.
The work remains profile-level research and does not change the fixed native
frame or ordinary node routes.

`service-lifecycle-persistence-v1.md` defines the bounded implementation
contract for opt-in, single-host transactional stores. Python and Rust provide
reference SQLite adapters behind their lifecycle storage ports; this does not
mount lifecycle routes by default or standardize SQLite as protocol state.

`dispatch-ticket-trust-profile-v2.md` proposes independently anchored Directory
signing keys, overlap rotation and explicit strict/open compatibility modes. It
now has opt-in caller-supplied-bundle verifiers and owner-local durable store
ports in all three SDKs. They are not wired into default dispatch, do not claim
whole-store rollback resistance and do not change or overstate the
disclosure-only v1 ticket contract.
The shared `dispatch-ticket-trust-store-v1.json` fixture pins canonical bundle
digests and cross-SDK storage transitions without enabling the profile.
