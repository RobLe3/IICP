# Proposal — Independent Trust-Bundle Rollback Anchor

**Status:** pre-normative recovery decision; native adapter and named review pending

## Problem

The optional dispatch-ticket trust store preserves a bundle and its local
version floor atomically. Restoring that complete store can restore both values
together, so the store cannot prove that it has been rolled back.

## Candidate decision

Use a hybrid boundary:

- prefer a native, independently protected anchor where the platform provides one;
- reject an older bundle, a digest mismatch, an unexpected machine binding or a
  missing anchor in strict mode;
- permit recovery only through a separately authenticated and audited
  administrator action;
- use signed lineage or checkpoints as supporting evidence, not as an
  independent anchor when they are stored beside the bundle.

The portable fixture defines the comparison and recovery outcomes. Native secure
storage, machine binding and recovery-authorizer integration remain local
implementation choices. The anchor contains only bundle identity and monotonic
state; it contains no task content, credentials or endpoint data.

## Consequences and limits

An intact independent anchor can detect restoration of the main trust store.
Anchor loss and legitimate host cloning become explicit recovery events rather
than silent downgrade paths. This may intentionally lock a strict client when
neither its anchor nor an authorized recovery path is available.

The fixture proves deterministic semantics only. It does not prove a platform
secure store, approve a recovery authority, enable strict trust, change the base
wire or ratify the dispatch-ticket Profile.
