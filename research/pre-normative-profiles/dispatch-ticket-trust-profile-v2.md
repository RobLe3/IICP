# Proposal — Dispatch Ticket Trust Profile v2

**Version:** 0.1.0-draft  
**Status:** pre-normative trust-profile proposal  
**Tracking:** iicp.network #621  
**Relation:** disclosure-only `dispatch-route-ticket:v1`

## Purpose and boundary

Version 1 verifies a short-lived route disclosure with a key obtained from the
same Directory origin. That detects corruption relative to that origin, but does
not independently authenticate a compromised Directory or TLS path. This
optional v2 profile anchors ticket verification in a caller-controlled trust
bundle without changing IICP framing or putting task content in the Directory.

The v1 route-disclosure contract remains supported and is not reinterpreted as
node admission or stateful single-use redemption. A v2 `jti` supports
correlation and duplicate detection in one client; network-wide single-use
enforcement still requires a separately negotiated redemption profile.

## Ticket claims

A v2 signed ticket contains:

- `ticket_profile = urn:iicp:profile:dispatch-ticket-trust:v2`;
- `key_id`, `issuer`, `audience`, `issued_at`, `expires_at`, and `jti`;
- selected provider identifier, requested intent and route/profile-constraint digest;
- optional policy-decision class and redacted directory evidence reference.

It contains no prompt, response, credentials, node token, raw endpoint, signing
secret or private provider topology. The `key_id` is authenticated by the
signature; replacing both the ticket and an untrusted key response is not
sufficient in strict mode.

## Trust bundle

A local trust bundle contains a monotonically increasing `bundle_version`,
bundle issuer, validity interval and keys with:

- stable `key_id` and Ed25519 public key;
- `active`, `retiring` or `revoked` status;
- `valid_from`, `valid_until` and allowed ticket profiles;
- optional Directory issuer/audience restrictions.

The public seed trust bundle may ship with an SDK or application release.
Administrators may pin an independent bundle. Bundle updates MUST be signed by
an already trusted update key or installed through an explicit administrative
channel. A lower bundle version is rejected unless an explicit, audited recovery
procedure authorizes rollback.

## Verification modes

- `strict_pinned`: v2 tickets require a known, currently valid, non-revoked key.
  Unknown keys and unavailable bundles fail before endpoint disclosure/dispatch.
- `open_compat`: callers may continue the separately labelled v1 same-origin
  verification path. It MUST NOT accept a v2 ticket under an unknown replacement
  key or represent v1 as independently anchored.
- A required v2 profile never silently downgrades to v1.

## Rotation and revocation

Rotation publishes a new active key before use and keeps the old key
`retiring` for an explicit overlap window. Both verify only within their
individual validity intervals. After overlap, the old key expires. Revocation
overrides an otherwise valid interval and fails closed immediately after the
client receives an authenticated bundle update.

If a client misses rotation, it obtains an authenticated newer bundle or
requires administrator recovery; it does not trust the same unverified route
response as its recovery authority. Rollback preserves at least one known-good
bundle and never rewrites an already accepted terminal receipt.

## Verification order

1. Load and validate the local bundle and anti-rollback version.
2. Parse bounded ticket bytes and require the v2 profile and `key_id`.
3. Resolve `key_id` only inside the trusted bundle.
4. Check key status/validity/profile/issuer/audience.
5. Verify signature and ticket time bounds.
6. Bind intent, provider, route/profile constraints and caller audience.
7. Apply replay cache policy for `jti` without claiming global redemption.
8. Only then disclose/use the endpoint and execute local policy selection.

Every failure is non-retryable until trusted configuration, rotation state or a
new ticket changes. Receipts expose only ticket/profile IDs, a redacted key ID
prefix, verification outcome and expiry class.

## Compatibility and migration

SDKs first add bundle parsing and fixture-only verification. A later coordinated
release may ship `strict_pinned` as opt-in while v1 remains the default. Strict
mode becomes a public default only after bundle distribution, rotation overlap,
offline recovery, clock skew and rollback drills pass across maintained clients.
No base-wire change is required.

## Conformance gate

`fixtures/dispatch-ticket-trust-v2.json` covers active/retiring/expired/revoked
keys, unknown keys, same-origin replacement, claim mismatch, bundle rollback and
v1 compatibility labeling. Cryptographic signed-token vectors and adversarial
rotation/recovery tests are required before implementation or ratification.
