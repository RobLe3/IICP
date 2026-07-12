# Proposal — Route Ticket and Routing Receipt Profile

**Status:** fixture-gated pre-normative draft · **Depends on:** directory dispatch ticket work, #616, Rust directory parity issue #1.

## Purpose

Allow a client to obtain an endpoint-safe dispatch authorization and explain a
routing decision without placing a task payload, endpoint, credential or full
operator secret in public discovery or directory receipts.

## Proposed evidence split

- **Directory metadata:** ticket identifier, intent, policy decision class, expiry and redacted selection evidence.
- **Client receipt:** selected provider reference, policy/constraint decision, prompt hash and local routing attempt sequence.
- **Node receipt:** ticket reference, execution outcome, response hash and provider-side evidence.

## Required properties

- v1 ticket is short-lived, intent-bound, signature-verifiable and excludes task payload.
- v1 authorizes route disclosure only: it is not a node-admission credential and does not provide stateful single-use redemption. A future v2 admission profile may add that stronger guarantee.
- Directory-visible metadata contains no prompt, response, secret, node token or raw endpoint.
- Receipts are useful independently but correlate through a shared ticket/trace reference.
- A client can reject stale, revoked, policy-incompatible or unverified tickets before dispatch.
- Ticket and receipt fixtures expose only redacted evidence and a stable
  failure reason. An implementation may report unsupported draft semantics but
  may not treat a failed ticket check as an eligible route.

## Evidence gate

The receipt-boundary simulation rejects directory-only evidence, marks client-only/node-only as partial, and selects the hybrid client/node plus redacted-directory model. Production parity requires canonical expiry/tamper/claim-mismatch fixtures and cross-SDK verification next. Stateful replay redemption and node admission remain a future v2 design, not an implied v1 guarantee. The profile fixture manifest and the existing dispatch-ticket fixture are both required inputs to a future normative release.
