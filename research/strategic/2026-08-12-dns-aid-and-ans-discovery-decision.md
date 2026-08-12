# DNS-AID and Agent Name Service discovery decision

**Date:** 12 August 2026  
**Status:** Research decision for IICP #61  
**Wire impact:** None

## Decision

Prototype the DNS-AID mapping only as an offline, optional candidate-discovery
adapter. Defer any public DNS publication, runtime resolver, or IICP capability
schema change while `draft-mozleywilliams-dnsop-dnsaid-00` remains a changing
Internet-Draft and its agent-specific SVCB parameters remain provisional.

Monitor, but do not prototype, Agent Name Service. The reviewed ANS
Internet-Draft, `draft-narajala-ans-00`, expired on 17 November 2025. Its
registry, lifecycle, PKI, capability resolution, and protocol-adapter functions
substantially overlap IICP directory concerns. IICP can later import an ANS
record as a provenance-bearing candidate if a stable, independently implemented
contract emerges; it must not treat an ANS registration or trust score as IICP
eligibility or dispatch authority.

## Sources checked

- DNS-AID revision 00, published 23 February 2026 and scheduled to expire on
  27 August 2026;
- RFC 9460 SVCB/HTTPS processing, RFC 4033 DNSSEC, RFC 6698 and RFC 7671 DANE,
  RFC 2308 negative caching, and RFC 6763 DNS-SD;
- ANS revision 00 and the OWASP Agentic Security Initiative publication;
- current IICP capability, endpoint-security, discovery-evidence, provider
  admission, federation, and route-ticket research profiles.

The decision uses the archived revisions named above. A later implementation
must recheck the current drafts and must not silently inherit an incompatible
record layout.

## Layer boundary

DNS-AID may answer: “Which candidate descriptor or service endpoint did this
domain publish?” IICP still answers:

- whether the intent and required capability match;
- whether policy, privacy, region, trust, and protocol requirements pass;
- whether the provider is operationally eligible now;
- which candidate is selected;
- whether a short-lived route ticket authorizes disclosure and dispatch.

DNSSEC proves the integrity of a DNS answer under a DNS trust chain. It does not
prove that a provider is healthy, capable, safe, policy-compliant, or authorized
for an IICP task. DANE can bind an endpoint certificate to the DNS name; it does
not replace application authorization. Address hints are connection hints and
must be resolved and checked under the endpoint-security profile before use.

## Export mapping

The offline prototype maps an eligible IICP descriptor to a DNS-AID candidate:

| IICP source | DNS-AID projection | Rule |
| --- | --- | --- |
| operator-controlled domain | owner suffix | Domain control must be established out of band before publication. |
| stable service label | `_iicp._agents.<domain>` SVCB owner | The label is a lookup key, not an intent registry. |
| HTTPS provider or descriptor origin | SVCB ServiceMode target and port | No credentials, paths, queries, fragments, private addresses, or transient relay URLs. |
| protocol support | standard ALPN only | Do not claim an unregistered IICP ALPN or QUIC mapping. |
| capability document | HTTPS URL plus SHA-256 digest in provisional metadata | The URI and digest are candidates until stable SvcParam assignments exist. |
| descriptor version and expiry | capability document | Volatile data does not belong in long-lived DNS records. |

The fixture uses symbolic `keyNNNNN` parameters because the reviewed draft does
not provide stable registered code points. It is not a deployable zone file.

## Import path

An importer records the queried name, record type, TTL, DNSSEC status, DANE
status, resolver observation time, capability URL and digest, and the raw source
class. It then applies these rules:

1. DNSSEC-bogus is rejected. Unsigned or indeterminate evidence may be retained
   only as an untrusted candidate when the caller explicitly allows it.
2. Required SVCB parameters must be understood. Unknown mandatory keys reject
   the record; unknown optional keys remain opaque.
3. Alias loops, malformed targets, excessive indirection, expired observations,
   and records outside the requested domain are rejected.
4. The capability document is fetched over HTTPS under endpoint-security rules.
   Its digest must match the DNS projection.
5. The imported endpoint remains untrusted until normal IICP validation,
   eligibility, and route authorization complete.
6. TTL expiry removes the DNS evidence. It does not deregister or revoke an
   independently known IICP provider.

Split-horizon answers are distinct source observations, not globally equivalent
records. A resolver must retain view provenance and must not merge conflicting
answers into one trusted record. NXDOMAIN and other negative answers follow DNS
negative caching and never prove that an agent does not exist elsewhere.

## Failure and downgrade behavior

- DNS unavailable: continue with configured directories; do not reuse expired
  DNS evidence as current.
- DNSSEC bogus: reject the DNS-derived candidate.
- unsigned record when secure discovery is required: reject without fallback.
- digest mismatch, HTTPS downgrade, rebinding, private target, or DANE failure
  when DANE is required: reject the candidate.
- stale record: remove its DNS freshness evidence; do not convert it to live
  health or trust.
- ANS unavailable or ambiguous: no ANS candidate is imported; IICP behavior is
  otherwise unchanged.

## Why runtime implementation is deferred

The narrow DNS substrate is relevant to IICP, but deploying it now would couple
IICP to provisional names and parameters, create misleading trust expectations,
and duplicate existing directory bootstrap without adoption evidence. The
offline mapping and negative vectors are enough to preserve the architectural
boundary and let a future adapter be evaluated without changing IICP core.

Reopen implementation only when a stable DNS-AID revision or interoperable
deployment exists, parameter assignments are usable, DNSSEC and DANE behavior
can be tested against at least two independent implementations, and operators
request domain-controlled discovery. ANS should be revisited only with a stable
technical contract and a clear import-only use case that does not duplicate
IICP registration, scoring, policy, federation, or ticketing.

