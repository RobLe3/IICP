# Selection trust and revalidation boundaries

Status: **project architecture candidate for review**. This document collects
current IICP trust boundaries. It does not define a universal credential, change
the stable wire baseline, activate a pre-normative Profile or authorize a
deployment.

## Decision boundary

A directory result means that a candidate satisfied the directory's current
eligibility rules when the result was produced. It does not prove that the
selected endpoint still owns the route, that the endpoint will authorize the
caller, that execution occurred or that a result is correct.

The consumer preserves the chain of decisions:

```text
advertisement evidence
  → directory eligibility
  → client policy
  → route authority
  → endpoint authentication and authorization
  → execution
  → bounded outcome evidence
```

No earlier decision substitutes for a later verifier. An implementation may
combine exchanges, but it must preserve these distinct claims and failure
semantics.

## Claims, verifiers and freshness

| Claim | Current IICP artifact | Authoritative verifier | Freshness and replay basis | What it does not prove |
|---|---|---|---|---|
| Stable provider identity | DID/key binding and registered node identity | Client or directory using the configured trust anchor and current key state | Key lifecycle, rotation and revocation state | Current reachability, membership or task authority |
| Effective capability | Capability advertisement plus applicable evidence/provenance | Directory and client policy | Advertisement validity, observation time and policy freshness | Present capacity, output quality or permission to dispatch |
| Current eligibility | Redacted discovery result or candidate set | Directory for its rules; client for its non-weakenable local policy | Short response cache window plus current policy and availability checks | Endpoint authentication or execution permission |
| Restricted-domain membership | Authority-signed, domain-scoped membership assertion | Configured trust-domain authority and receiving peer/client | Issuer, audience, domain, scope, expiry, generation and revocation | Reputation, public-network authority or dispatch permission |
| Route authority | Directory-issued dispatch ticket or relay ticket | Intended endpoint or relay using the directory key and bound claims | Signature, audience, route, intent, expiry and replay/redemption policy | Provider correctness, membership outside its stated claim or completed execution |
| Endpoint identity | Binding-specific endpoint authentication | Client and endpoint under the selected binding | Binding-specific key validity, channel binding, nonce or signature freshness | Directory policy correctness or result quality |
| Execution outcome | Response and purpose-specific receipt | Caller plus the receipt's stated verifier | Task/attempt correlation, signature or MAC, expiry and idempotency/replay rules | Truth of inputs, semantic correctness or physical-world effects |

Offline-verifiable signatures establish only the signed claim within their
validity and scope. Live checks can add current reachability, revocation or
capacity evidence. Neither class silently supplies the other.

## Consumer revalidation before dispatch

Before releasing a task, a maintained consumer must:

1. Confirm that required Intent, capability, Profile, policy, region and
   confidentiality constraints still hold.
2. Reject expired, revoked, wrong-audience, wrong-intent, wrong-route or
   unsupported-version authority.
3. Preserve the ticket's selected route. A single-route ticket cannot be reused
   for another provider or relay.
4. Apply endpoint-safe resolution and redirect rules before connecting.
5. Authenticate the endpoint according to the selected binding.
6. Refuse when a required check cannot be completed. It must not fall back to a
   public, plaintext, unauthenticated or foreign-domain route unless the caller's
   explicit policy authorizes that route.

A retry is a new delivery or execution attempt under the same logical task. It
requires authority valid for the new route and attempt; transport retry alone
does not authorize duplicate logical execution.

## Adversarial cases

| Case | Required disposition |
|---|---|
| Malicious directory returns a provider outside caller policy | Client rejects it before task disclosure. Local hard constraints cannot be weakened by directory ranking. |
| Directory returns a forged or attacker-controlled route | Ticket or signature validation and endpoint authentication fail; no connection is treated as authorized. |
| Advertisement was valid but is now stale | Candidate becomes ineligible when required freshness cannot be established. Cached presence does not establish current dispatch eligibility. |
| Provider membership was revoked | Generation/revocation state prevents new admission; bounded assertion lifetime limits stale offline acceptance. Cached membership cannot remain authoritative indefinitely. |
| Route ticket is expired, replayed or for another audience | Intended verifier rejects it. No automatic downgrade to legacy unauthenticated dispatch is allowed. |
| Candidate changes between discovery and dispatch | Re-evaluate the changed identity, route and authority. A prior ticket does not transfer. |
| Endpoint authenticates but refuses the caller | Return a bounded authorization refusal. Discovery does not override endpoint policy. |
| Receipt verifies cryptographically | Treat it only as evidence of what the issuer signed. Do not infer correctness, safety or external side effects without separate evidence. |

## Directory compromise boundary

A compromised directory can suppress candidates, bias its own ranking, issue
misleading unsigned metadata and observe Intent plus bounded routing metadata.
It must not receive task payloads. Consumer-side policy, purpose-specific ticket
verification, endpoint authentication and result validation limit what the
directory can authorize by itself.

A directory signing-key compromise can create artifacts accepted under that key
until rotation or revocation takes effect. Implementations must therefore keep
key scope, ticket lifetime, audience and operation scope narrow. This document
does not claim that client revalidation removes all consequences of a trusted
key compromise.

Public receipts and errors must not expose task content, credentials, full route
addresses, private membership lists, internal scores or private topology.

## Purpose-specific artifacts remain separate

IICP keeps identity, membership, dispatch authority, relay authority and outcome
evidence separate because they have different issuers, audiences, lifetimes and
verifiers. Implementations must not convert one artifact into another merely
because an external proposal combines similar claims. A future mapping may
cryptographically bind selected claims while preserving their separate meaning
and validation rules.

## Current public sources

- [Selection and eligibility problem statement](SELECTION_ELIGIBILITY_PROBLEM_STATEMENT.md)
- [`iicp-semantics.md`](../spec/v1.9/iicp-semantics.md), section 3
- [`iicp-dir.md`](../spec/v1.9/iicp-dir.md), current eligibility and dispatch-ticket sections
- [Directory state semantics](../docs/architecture/directory-state-semantics.md)
- [Endpoint security Profile](../research/pre-normative-profiles/endpoint-security-profile-v1.md)
- [Dispatch ticket trust Profile](../research/pre-normative-profiles/dispatch-ticket-trust-profile-v2.md)
- [Restricted trust-domain membership](../research/pre-normative-profiles/restricted-trust-domain-membership-v0.md)
- [Task time semantics](../docs/architecture/task-time-semantics.md)
- [Privacy adversary and trust model](../docs/security/privacy-adversary-and-trust-model.md)
