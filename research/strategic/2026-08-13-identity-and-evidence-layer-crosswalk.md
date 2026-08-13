# IICP identity and evidence layer crosswalk

**Date:** 2026-08-13  
**Status:** research decision; no trust-root or runtime change  
**Issue:** #63

## Decision

IICP should not create one credential that simultaneously represents an
operator, authenticates a workload, authorizes a task and proves the state of
the execution platform. Those claims have different issuers, lifetimes,
revocation paths and privacy risks.

The current Ed25519/JCS and DID-based evidence remains the implemented
baseline. The following division is the recommended direction:

| Function | Primary mechanism | Disposition |
| --- | --- | --- |
| Stable operator and directory identity | Existing DID and Ed25519/JCS evidence | **Reuse** |
| Portable provenance or conformance claim | W3C VC Data Model 2.0, when a portable holder-presented claim is demonstrated | **Prototype narrowly** |
| Workload-to-workload authentication inside a managed trust domain | SPIFFE X.509-SVID, with SPIRE as one possible implementation | **Defer optional adapter** |
| Single-task route disclosure or execution authority | Short-lived IICP dispatch ticket | **Reuse; never replace with VC/SVID** |
| Post-execution result and route evidence | Existing signed IICP receipts and content-free result bundles | **Reuse** |
| Confidential-platform and execution-key evidence | RATS roles with EAT/CWT and COSE as selected by #136 | **Research under #136** |

VC 2.0 is the stable W3C Recommendation used by this decision. VC 2.1 is a
Candidate Recommendation Draft and is monitored rather than used as the
baseline. A verifiable credential proves that an issuer made a current,
tamper-evident statement; it does not prove that the statement is true or grant
authorization by itself.

## Existing IICP state

- Directory and federation evidence already uses DID documents and Ed25519
  verification material.
- Operator delegation, directory deployment records, replica events, route
  tickets, receipts and conformance results already have purpose-specific
  signatures or verification rules.
- Node credentials and dispatch tickets remain operational authorization. A
  portable claim cannot silently widen their scope.
- #136 defines fresh platform appraisal separately from operator identity. It
  binds an ephemeral execution key, request challenge, candidate and ticket to
  RATS-style attestation results.

## Claim decisions

### Operator identity and provenance

Keep DID as the stable public identifier and current key-discovery mechanism.
A future VC can carry an operator-verification or deployment-provenance claim
only when a distinct trusted issuer exists and portability across verifiers is
needed. The holder may be the operator; the subject may be an operator,
directory deployment or released implementation. The verifier still applies
its own policy.

Minimum future requirements are issuer allowlisting, schema pinning, validity
times, credential status or short expiry, key-rotation handling, purpose
restriction and offline verification. A directory must not become the sole
issuer for ecosystem-wide operator legitimacy.

**Disposition:** reuse DID now; prototype VC only for portable provenance after
an external verifier use case exists.

### Conformance evidence

The signed, content-free result bundle is the source evidence. A VC could wrap
the digest, profile version, evidence class and result expiry for presentation
to another verifier. It must not upgrade `self-attested` or `project-verified`
evidence into `independent`, and it must not embed test payloads or operator
topology.

**Disposition:** retain the existing result format; consider a VC presentation
adapter after an independent conformance result exists.

### Workload identity

SPIFFE identifies workloads within operator-controlled trust domains and
delivers short-lived SVIDs and rotating trust bundles. This is useful for
managed service authentication, especially between a directory, verifier and
confidential worker. It does not establish portable operator reputation,
public directory membership, platform integrity or task authorization.

Prefer X.509-SVID for mutually authenticated channels. A JWT-SVID requires a
narrow audience and short expiration and remains bearer-replay sensitive.
SPIFFE trust-domain federation is an operator decision, not IICP directory
federation.

**Disposition:** defer a platform adapter until a managed deployment needs it;
do not add SPIFFE fields to the IICP wire or directory records now.

### Dispatch authority

Route tickets are short-lived, target-, audience- and intent-bound. Their
purpose and expiry are narrower than operator credentials, SVIDs or portable
VCs. Replacing them with a general credential would enlarge replay and
privilege scope.

**Disposition:** keep IICP tickets; credentials may support authentication but
never substitute for the ticket or bypass eligibility and policy.

### Platform evidence

RATS distinguishes the Attester, Verifier and Relying Party. Evidence is
appraised against endorsements, reference values and policy; Attestation
Results support but do not make the relying party's decision. EAT expresses
claims about a device, hardware or software entity. It is not an operator
credential or an ordinary authentication token.

**Disposition:** continue only under #136. Fresh platform evidence and hardware
identifiers stay out of stable directory capability records.

## Lifecycle and privacy comparison

| Layer | Typical lifetime | Revocation or freshness | Main privacy risk |
| --- | --- | --- | --- |
| DID verification material | long-lived with rotation | DID document/key status and overlap policy | stable cross-service correlation |
| VC provenance claim | bounded issuance/expiry | credential status or short expiry plus issuer policy | issuer, subject and presentation correlation |
| X.509-SVID | short-lived, automatically rotated | expiry and current trust bundle | trust-domain and workload correlation |
| JWT-SVID | short-lived bearer token | expiry, audience and bundle validation | replay and audience overbreadth |
| Dispatch ticket | per selection/task window | expiry, signature, audience, target and optional redemption | route and task correlation |
| Receipt/result bundle | post-execution evidence | signature, profile version and evidence provenance | timing and operational correlation |
| EAT/RATS result | challenge/session scoped | nonce, expiry, TCB/reference-value appraisal | hardware fingerprinting and verifier correlation |

Apply data minimization at every layer. Do not aggregate stable operator DID,
SPIFFE ID, hardware identity, task identifier and receipt into a globally
linkable public record. Selective disclosure does not remove correlation from
stable identifiers, signatures, issuers or validation calls.

## Recommended prototype gates

No implementation is warranted today. A later prototype must start with one
demonstrated consumer and one claim type. It must:

1. preserve the original signed evidence and bind its digest rather than copy
   mutable claims;
2. define issuer trust, subject, holder, verifier policy, status and expiry;
3. prove that presentation adds portability beyond current JSON/JCS evidence;
4. reject expired, revoked, wrong-issuer, wrong-purpose and over-broad claims;
5. measure identifier, issuer and status-check correlation;
6. leave dispatch tickets, node credentials and RATS appraisal unchanged.

## Sources

- W3C, [Verifiable Credentials Data Model v2.0](https://www.w3.org/TR/vc-data-model-2.0/), Recommendation, 15 May 2025.
- W3C, [Decentralized Identifiers v1.0](https://www.w3.org/TR/did-1.0/).
- W3C, [Verifiable Credentials Data Model v2.1](https://www.w3.org/TR/vc-data-model-2.1/), Candidate Recommendation Draft monitored on 13 August 2026.
- SPIFFE, [SPIFFE concepts](https://spiffe.io/docs/latest/spiffe/concepts/) and [SPIFFE ID/SVID specification](https://spiffe.io/docs/latest/spiffe-specs/spiffe-id/), reviewed at v1.15.2.
- IETF, [RFC 9334: RATS Architecture](https://www.rfc-editor.org/rfc/rfc9334.html).
- IETF, [RFC 9711: Entity Attestation Token](https://www.rfc-editor.org/rfc/rfc9711.html).
- IICP, [execution-privacy assessment](2026-08-12-execution-privacy-and-attested-confidential-execution.md) and [pre-normative feasibility profile](execution-privacy-feasibility/profile-v0.md).

