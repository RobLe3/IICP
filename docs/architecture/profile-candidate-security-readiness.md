# Policy and dispatch Profile candidate security readiness

**Evidence date:** 2026-08-25  
**Status:** first-party pre-normative assessment

This assessment separates work that the project can verify from gates that need
independent evidence or an explicit release decision.

## Policy and data handling

The request/declaration fixture already fails closed for hard policy conflicts,
unknown critical requirements, missing negotiated encryption and missing receipt
evidence. Operational evidence remains locally authenticated, digest-bound and
time-bounded. Authenticated detail disclosure conceals target, intent and
manifest mismatches and returns only its fixed allow-list.

The provider boundary previously distinguished missing, invalid and expired
consumer authentication but did not name revoked consumer credentials or the
invalid, expired and revoked dispatch-ticket states required by issue #56. The
0.2 fixture adds those outcomes ahead of disclosure authorization. It changes no
public discovery route and does not turn a provider declaration into evidence.

Still open: independent adoption, qualified security/privacy/compliance review,
a reviewed production adapter, migration review and an explicit protocol release
decision.

## Dispatch tickets and receipts

The candidate suite already binds v2 tickets to a caller-controlled bundle,
key, issuer, audience, provider, intent, constraint digest and validity window.
It covers overlap rotation, revocation, unknown keys, tampering, replay and
required-profile downgrade. Version 1 remains disclosure-only and does not gain
node-admission or network-wide redemption semantics.

The durable trust store cannot detect restoration of its entire state directory.
The rollback-anchor fixture now makes that limitation and the recovery boundary
reconstructable in the Protocol repository: an independent surviving anchor can
reject rollback, while anchor loss or host cloning requires separately
authenticated administrator recovery. Same-store checkpoints are not treated as
independent protection.

Still open: native/platform anchor evidence or an approved portable recovery
boundary, named governance review, trust-root distribution and disaster-recovery
drills, production migration review, independent adoption and explicit
ratification.

## Release disposition

These additions improve candidate evidence only. They do not modify the released
1.10.16 compatibility environment, enable a default, publish a package, deploy a
service or close issues #56 or #58.
