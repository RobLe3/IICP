# Attested execution-privacy research profile v0

**Status:** pre-normative research; not an IICP capability, conformance claim,
or production security guarantee

This document fixes the choices needed for the next hardware feasibility test.
It does not authorize SDK, directory, provider, deployment, or wire changes.

## Selected standards boundary

The external representation for a normalized attestation result should be an
EAT Claims-Set encoded as a CWT, signed in a tagged `COSE_Sign1` structure, and
transported as:

```text
application/eat+cwt;
  eat_profile="tag:iicp.network,2026:execution-privacy-attestation-result-v0"
```

This uses the profile mechanism and media type defined by RFC 9711 and RFC
9782. The profile identifier is provisional. The JSON vectors in this directory
are a readable projection of the selected claims; they are not COSE or CWT
interoperability vectors.

Vendor evidence remains vendor-specific. An AMD SEV-SNP adapter may submit a
raw report and certificate material to a local verifier or a verification
service. The relying party consumes the normalized result only after the
verifier has checked the vendor signature chain, current endorsements,
reference values, measurement, TCB state, debug state, and report-data binding.
The media type is not proof that those checks happened.

## Verifier trust

Two verifier deployments are permitted for a later prototype:

1. The consumer runs a local verifier and configures vendor trust roots,
   endorsements, reference values, and appraisal policy locally.
2. The consumer explicitly configures a remote verifier and pins or otherwise
   validates the key that signs its `COSE_Sign1` results.

The directory, provider, or an untrusted host may relay evidence, but none is a
verifier trust anchor. A key identifier alone is insufficient. Failure to
obtain or authenticate a configured verifier result rejects a task that
requires execution privacy.

The signed result should use the EAT nonce and standard CWT time and audience
claims. It should use the RFC 8747 `cnf` claim with an X25519 public
`COSE_Key`. Profile-specific claims are still needed for the opaque candidate
reference, route-ticket digest, runtime/reference-value result, protected
components, security/TCB state, and the platform binding digest.

## Required binding

The hardware report and normalized result must cover a digest of:

```text
profile identifier
consumer nonce
consumer-session audience
opaque candidate reference
SHA-256 digest of the selected dispatch ticket
ephemeral X25519 public key and key identifier
runtime measurement/profile
debug and TCB state
protected-component set
```

For AMD SEV-SNP, the next prototype should encode a domain-separated SHA-512
digest of this structure into the 64-byte `REPORT_DATA` field. The normalized
result then carries the appraised claims. The consumer recomputes the binding
from its own challenge and selected route state rather than accepting host
supplied values.

The consumer nonce must contain at least 64 bits of entropy, as required by RFC
9711. The first prototype should use 32 random bytes. A result is valid only for
the exact nonce, audience, candidate and dispatch ticket requested by the
consumer.

## Freshness, replay, and proof of possession

- The verifier result has explicit issue and expiry times. The initial test
  window is at most 60 seconds; this value is a test bound, not a future
  protocol constant.
- The consumer stores a digest of every accepted result until its expiry and
  rejects reuse. Restart-safe replay storage is required before production.
- The consumer confirms possession of the X25519 private key before releasing
  a protected task. The research prototype encrypts a random preflight
  challenge under the attested key and requires an authenticated CX response
  derived from the same shared secret.
- Proof of possession shows that the responding worker holds the corresponding
  private key. It does not prove hardware containment. Containment requires a
  measured worker that generates the key internally and a hardware report that
  binds its public half.
- If attestation or proof of possession fails, required execution privacy
  rejects the candidate. Ordinary CX is used only when the caller explicitly
  allowed that downgrade before selection.

## Route and IICP-CX composition

The safe sequence is:

```text
policy-filtered candidate
  -> signed dispatch ticket
  -> fresh challenge bound to the ticket digest and candidate
  -> vendor evidence
  -> authenticated normalized attestation result
  -> proof of possession
  -> existing IICP-CX request envelope
  -> encrypted response
```

The software prototype shows that the existing request envelope fields and
IICP-CX X25519/HKDF/AES-GCM construction can carry an attestation-bound
recipient key unchanged. Cross-task substitution is already resisted by the
`task_id|intent` request AAD and task-id idempotency. Response substitution is
resisted by the existing `task_id|resp` AAD. The per-task attested key and
attestation binding add the candidate, profile and dispatch-ticket context.

This conclusion is limited to the current one-shot envelope. It does not prove
streaming-frame, relay, cancellation, retry, or multi-task session behavior.
No new IICP-CX field is justified by the software proof. A later hardware test
must revisit that decision if the measured-worker boundary cannot preserve the
same semantics.

## Key lifecycle decision

The first hardware prototype should use one ephemeral execution key per
attestation and task:

- generate the key inside the measured confidential worker after receiving the
  consumer challenge;
- never serialize or export the private key;
- bind the public key to the fresh hardware report and normalized result;
- use the key for proof of possession and one task request/response exchange;
- erase or make the key unreachable after completion, cancellation, expiry, or
  worker restart;
- reject duplicate task IDs and any result or key reused after expiry.

Per-boot, sealed, or reusable session keys are deferred. They increase replay,
rollback, revocation, correlation, and recovery complexity and are not needed
to answer the first feasibility question.

## Decision gate

The software result supports a hardware prototype. It does not yet justify a
Rust confidential-worker implementation issue because the defining claim,
private-key and plaintext containment against the operator, remains unproven.

The next decision requires all of the following on a representative SEV-SNP
confidential VM:

1. the measured worker generates the ephemeral key internally;
2. `REPORT_DATA` binds the exact challenge structure;
3. current VCEK, endorsement, firmware and TCB appraisal passes;
4. the untrusted host cannot obtain the private key or plaintext through the
   supported interface;
5. request and response use the existing CX envelope successfully;
6. negative tests cover replay, restart, key substitution, wrong ticket,
   verifier outage, debug state, stale TCB and plaintext escape;
7. evidence and code receive an external security review before any public
   implementation claim.
