# Signed message envelope boundary decision

**Date:** 2026-08-13
**Status:** research decision; reject a universal envelope for the current line
**Issue:** #52

## Decision

IICP should not add a universal signed message envelope or a second general
authentication header to the current protocol line. Existing signatures are
purpose-specific because their authors, verifiers, lifetimes, replay stores and
failure consequences differ. Wrapping every message in one envelope would not
resolve those differences and would create another signature domain beside
TLS, IICP-CX, node credentials, dispatch tickets, policy manifests, federation
events, receipts and attestation evidence.

The general requirement is therefore rejected. A future profile may define a
signature only for a demonstrated message-level evidence gap and must reuse the
existing identity, canonicalization and replay primitives where compatible.
This decision changes no wire field, authentication default or deployment.

## Current integrity and authority map

| Purpose | Current mechanism | Why a universal envelope is not a substitute |
| --- | --- | --- |
| Transport peer authentication | TLS and protocol-specific credentials | A message signature does not establish channel policy or endpoint authorization |
| Payload confidentiality | IICP-CX | Integrity without encryption does not hide payloads or metadata |
| Route disclosure and task authority | Short-lived signed dispatch ticket | A broad identity signature would enlarge authority and replay scope |
| Operator policy statement | Ed25519 signature over the canonical policy manifest | It proves authorship of one statement, not task permission or legal truth |
| Directory federation | Signed events and replica responses | Trust root, sequence and freshness rules are directory-specific |
| Execution/accounting evidence | Routing, task and CIP receipts | Each receipt has distinct counterparties and anti-replay/accounting invariants |
| Confidential execution | Fresh RATS-style evidence bound to an ephemeral CX key | Platform appraisal cannot be replaced by a node identity signature |

## Historical contradictions resolved

Several pre-ratification passages describe ADR-024 as though it already signs
CALL, RESPONSE, INIT, FEEDBACK and TELEMETRY messages. No ADR-024 document,
ratified schema, shared fixture or interoperable implementation exists. Those
passages are dependency markers, not current protocol behavior. They must not
be used to claim message-level end-to-end integrity or require deterministic
CBOR solely for a nonexistent envelope.

Deterministic CBOR remains valuable for stable encoding and any future
signature profile. It does not itself create authentication. The historical
`X-IICP-Hash` is not restored: an unkeyed payload hash detects corruption but
does not prevent an intermediary from replacing both data and digest.

The dormant `+attested` modifier and `attestation_receipt` field remain
unavailable. Execution privacy and attestation continue under #136 with their
own evidence and key-binding threat model; they do not wait for a universal
message envelope.

## Future profile admission test

A new signed-message proposal is admissible only when all of these are true:

1. a concrete attacker can modify evidence after TLS termination or across an
   authorized intermediary;
2. no current ticket, receipt, manifest, federation or attestation signature
   already covers the required statement;
3. the signer, verifier, purpose, covered fields, key authority, freshness,
   replay store, rotation and failure behavior are explicit;
4. deterministic signing input and domain separation are versioned;
5. confidentiality and visible metadata limits remain explicit;
6. valid, tamper, replay, wrong-purpose and rotated-key vectors pass in at
   least two independent implementations before normative promotion.

Algorithm agility belongs inside that bounded profile. The current Ed25519 and
deterministic JSON/CBOR baselines remain unchanged. QuDAG's experimental
post-quantum dependencies do not supply IICP interoperability evidence.

## Compatibility and issue disposition

- No SDK, directory, browser or wire implementation work is required.
- No authentication header is added or advertised.
- Existing purpose-specific signatures remain authoritative for their narrow
  contracts.
- Editorial references that imply ADR-024 is implemented should be corrected
  in a later specification release without changing runtime behavior.
- Issue #52 may close with this rejected-universal/research-gate decision. Any
  later concrete message-evidence gap receives its own narrowly scoped issue.
