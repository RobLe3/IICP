# Dispatch-ticket trust v2 operator proposal

Status: pre-normative and not deployed. This runbook is a review artifact, not
authorization to rotate production keys.

## Bootstrap

1. Obtain the initial bundle through an authenticated administrative channel or
   an SDK/application release; never bootstrap it from the route response it
   will authenticate.
2. Verify the bundle issuer, version, validity interval and pinned update key.
3. Store the last accepted bundle version and a known-good prior bundle outside
   ordinary route-response caches.
4. Enable `strict_pinned` only for callers that can fail closed and recover
   through the administrative channel. Leave current v1 behavior explicitly
   labelled `open_compat` elsewhere.

## Rotation

1. Publish the new active key in an authenticated bundle before signing with it.
2. Keep the old key `retiring` for a declared overlap interval.
3. Verify both old- and new-key fixtures from every maintained SDK.
4. Begin new-key signing, observe verification failures, then expire the old key
   only after the overlap gate passes.

## Revocation and recovery

- Revocation overrides validity immediately after an authenticated bundle update.
- Unknown keys fail closed in strict mode; the route origin cannot supply an
  emergency replacement trust root.
- Reject lower bundle versions by default. An operator-authorized rollback must
  be audited, preserve the last known-good bundle, and never rewrite accepted
  terminal receipts.
- Recovery changes local trust configuration only. It does not redeem tickets,
  rotate node identity, or change the base IICP frame.

## Promotion gates

Require cross-SDK bootstrap, overlap, expiry, revocation, missed-rotation,
rollback and compromised-origin drills before enabling runtime integration.
Production signing-key or Directory changes require a separate deployment plan,
backup/rollback evidence and explicit maintainer authorization.
