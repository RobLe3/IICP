# Emerging session, principal, HTTP authentication and receipt work

**Evidence date:** 2026-08-21  
**Status:** research crosswalk; no adoption or implementation decision

This crosswalk tests IICP's boundaries against five individual Internet-Drafts.
An Internet-Draft is work in progress and is not IETF endorsement or consensus.
The `agentproto` group is currently a BOF with a draft charter and is not yet a
chartered working group. IICP remains authoritative for IICP semantics; an
external draft changing or expiring does not change a stable IICP contract.

## Disposition summary

| Concern | IICP artifact and verifier | External proposal | Disposition |
|---|---|---|---|
| Discovery before a session | Intent, eligibility and selection are verified by directory and client policy; endpoint authentication follows selection | `draft-feng-agentproto-session-requirements-02` assumes peers already know one another and places how they were found outside its scope | **BOUNDARY CLARIFICATION.** IICP selection precedes session establishment. Do not duplicate session lifecycle in the selection candidate. |
| Distinct security claims | Identity, membership, route authority and receipts have purpose-specific issuers and verifiers | `draft-bu-agentproto-security-principal-binding-06` separates user authority, live identity, resource identity, delegation, session continuity and action evidence | **ALREADY COVERED / BOUNDARY CLARIFICATION.** Use its verifier-facing questions to audit IICP, but do not make it an IICP dependency. |
| Delegated invocation authority | IICP membership, dispatch and relay tickets remain separate and locally constrained | `draft-prakash-aip-01` proposes invocation-bound capability tokens with compact and chained delegation modes | **MONITOR.** AIP attenuation may be relevant to future multi-hop delegation, but no current IICP gap justifies replacing or coalescing purpose-specific credentials. |
| Action evidence | IICP receipts state bounded routing, execution or accounting claims and name their issuer/verifier | `draft-noa-scitt-ai-agent-receipt-01` profiles signed, hash-chained action records and optional SCITT registration | **MONITOR / POSSIBLE FUTURE MAPPING.** Reuse may be useful for exportable transparency evidence, but current IICP receipts must not grow into a general audit format. |
| Automated HTTP client authentication | Current HTTP bindings use their existing endpoint/client authentication and IICP route authority | `draft-meunier-webbotauth-httpsig-protocol-02` defines `Signature-Agent`, HTTP Message Signatures and key discovery | **MONITOR FOR HTTP BINDINGS.** It is not IICP identity, membership or dispatch authority. No mandatory integration is justified. |

No row establishes a demonstrated missing requirement in the current narrow
selection candidate. The concrete result is boundary documentation, not a new
wire format or dependency.

## Claim-by-claim analysis

| Claim | IICP verifier | Freshness or replay basis | External comparison | Keep separate? |
|---|---|---|---|---|
| Candidate discovery and eligibility | Directory rules plus non-weakenable client policy | Current advertisement, policy, availability and bounded cache lifetime | Session Requirements deliberately starts after peers know one another | Yes. Discovery cannot substitute for endpoint authentication or session authorization. |
| Stable provider identity | Client/directory under configured identity trust anchors | Key validity, rotation and revocation | Principal Binding distinguishes live instance identity from other claims | Yes. A stable identity does not imply route ownership or membership. |
| Restricted-domain membership | Configured domain authority and receiving peer/client | Domain, issuer, audience, scope, expiry, generation and revocation | Principal Binding and AIP both discuss authority-related claims | Yes. Membership is neither task authority nor public-network authority. |
| Dispatch and relay authority | Intended provider or relay verifies the signed ticket | Audience, route, Intent, expiry and replay/redemption policy | AIP IBCT carries scoped invocation authority and supports attenuation | Yes for the current profile. Consider a mapping only if a real cross-protocol delegation case cannot preserve these checks. |
| HTTP request signer | HTTP endpoint under the binding's authentication policy | Covered request components, signature lifetime, nonce and key discovery state | Web Bot Auth identifies an automated HTTP signer | Yes. HTTP signer authentication does not establish IICP membership, eligibility or caller policy. |
| Outcome or action evidence | Caller or stated receipt verifier | Task/attempt binding, signature/MAC, expiry, idempotency and evidence class | SCITT receipt profile supports signed registration and offline verification | Yes semantically. A future export mapping must retain what the issuer actually observed and must not claim correctness or external effects. |

## Session boundary

The Session Requirements draft covers transport-independent interaction
binding, endpoint authentication, prospective capability negotiation, session
establishment, authorization and lifecycle after entities know one another. It
also permits sessionless interaction. This supports the following composition:

```text
IICP intent discovery and eligibility
        ↓
selected endpoint and bounded route authority
        ↓
endpoint authentication and optional session establishment
        ↓
execution protocol lifecycle
```

IICP must not make the peer transport or session state part of Intent meaning.
A session protocol must not treat an IICP directory decision as the endpoint's
own authentication or authorization decision.

## Principal and credential boundary

The Principal Binding draft's main test is applicable to IICP: for each claim,
name the carrier, verifier, freshness rule, failure behavior and constrained
result. The IICP selection trust document now applies that test.

AIP deliberately co-binds identity, authorization, scope and provenance in an
IBCT. IICP currently keeps stable identity, membership, dispatch authority,
relay authority and outcome evidence separate. That separation remains the
safer default because these artifacts have different issuers, audiences and
lifetimes. A future bridge would need to show which exact claims require
cryptographic co-binding and how attenuation, revocation, privacy and downgrade
work. Similar terminology is not enough evidence to change the credential
model.

## Receipt boundary

The SCITT action-receipt draft offers properties IICP may eventually reuse:
canonical signed statements, offline verification, chaining and optional
transparency-service registration. It also states an important limit: a receipt
records an issuer's claim; it does not by itself prove correctness or a
real-world result.

Any future IICP mapping should export only the minimum selection or outcome
claim needed by the relying party. Task content, private routes, membership
lists, internal scores and credentials remain excluded. SCITT integration would
require a separate reviewed issue after the external profile and IICP use case
are stable.

## HTTP authentication boundary

Web Bot Auth may provide an interoperable way to authenticate an automated HTTP
signer and discover verification keys. Its signatures must cover enough request
components and use freshness/replay controls appropriate to the request. A
`Signature-Agent` value alone is a claim, not verified identity.

For IICP, this mechanism could sit inside an HTTP binding. It would not replace:

- the Intent and eligibility decision;
- restricted-domain membership;
- dispatch or relay tickets;
- endpoint authorization policy;
- execution receipts.

A prototype is warranted only if a concrete independent HTTP implementation
needs it. No such gap is established here.

## Primary sources reviewed

- [Agent Session Requirements -02](https://datatracker.ietf.org/doc/draft-feng-agentproto-session-requirements/02/), 20 August 2026
- [Security Principal Binding -06](https://datatracker.ietf.org/doc/draft-bu-agentproto-security-principal-binding/06/), 17 August 2026
- [Agent Identity Protocol -01](https://datatracker.ietf.org/doc/draft-prakash-aip/01/), 19 August 2026
- [SCITT AI Agent Receipt -01](https://datatracker.ietf.org/doc/draft-noa-scitt-ai-agent-receipt/01/), 15 August 2026
- [HTTP Message Signatures for automated traffic -02](https://datatracker.ietf.org/doc/draft-meunier-webbotauth-httpsig-protocol/02/), 19 August 2026 Datatracker revision timestamp
- [agentproto BOF status](https://datatracker.ietf.org/group/agentproto/about/)

The corresponding IICP sources are the [selection problem statement](SELECTION_ELIGIBILITY_PROBLEM_STATEMENT.md), [selection trust and revalidation boundaries](SELECTION_TRUST_AND_REVALIDATION.md), restricted trust-domain membership Profile, dispatch-ticket trust Profile and the dated protocol comparison.
