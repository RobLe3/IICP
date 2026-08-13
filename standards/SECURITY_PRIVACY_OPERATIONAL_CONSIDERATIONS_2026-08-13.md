# IICP security, privacy and operational considerations

**Date:** 2026-08-13  
**Status:** external-review preparation; implementation and research truth only  
**Issues:** #45 and #54

## Reading this record

This document separates current protocol requirements, implementation evidence,
experimental profiles and future work. It does not promote a pre-normative
profile or authorize an Internet-Draft submission.

| Label | Meaning |
| --- | --- |
| Normative | Requirement in the published v1.10.13 suite or its stable v1.9 wire baseline |
| Implemented | Behavior tested in maintained implementations; not automatically protocol authority |
| Experimental | Additive, negotiated or pre-normative behavior with project-run evidence |
| Future | Accepted risk, external evidence gate or unimplemented proposal |

## Trust boundaries

The directory is a control plane. It can supply candidates, eligibility data,
policy evidence and route authorization, but it does not receive task payloads.
A malicious or compromised directory can omit providers, rank dishonestly,
return an attacker-controlled route, replay stale state or misstate unsupported
claims. Consumers must validate provider identity, route-ticket bindings,
expiry, policy and capability at use time. A directory response alone is not
provider authentication.

The selected provider sees plaintext after ordinary transport or IICP-CX
decryption. IICP-CX protects content from directories, relays and passive
network intermediaries when correctly negotiated; it does not hide content or inference
state from the executor. Attested confidential execution remains research in
#136 and must not be presented as implemented privacy.

A relay is on the transport path. Without IICP-CX it can read task content; with
IICP-CX it can still observe endpoints, timing, sizes and availability. Relay
eligibility, authenticated binding, abuse controls and independent operation
remain incomplete. Relay operation is experimental.

## Discovery and route disclosure

**Normative/implemented:** `view=public` redacts endpoints, raw node identifiers,
transport metadata and CX keys for presentation. The compatibility dispatch
projection remains route-bearing for existing clients. Endpoint-safe route
tickets are short-lived and bound to target, intent, issuer and audience.

**Risk:** public route-bearing discovery permits harvesting and makes providers
easier to scan or overload. A malicious candidate endpoint may target internal,
link-local or otherwise prohibited address space.

**Mitigation:** consumers and directories validate routable endpoints, apply
SSRF guards, authenticate providers independently and treat DNS/mDNS records as
untrusted bootstrap candidates. Ticketed-dispatch adoption and any retirement
of the legacy projection require a separate measured cutover decision.

**Future:** root #612 and profile gate #58. No current document should imply
that all discovery is route-free or that route tickets provide single-use task
admission.

## Authentication and authorization

Node bearer credentials, DID/Ed25519 evidence, workload identity, route tickets
and receipts have different purposes. A valid identity or credential does not
grant task authority. The identity-layer decision in #63 keeps the dispatch
ticket as the narrow task/route authorization mechanism.

**Normative/implemented controls:** issuer, audience, target, intent, expiry,
signature and policy validation; key-status handling; bounded clock skew;
fail-closed required profiles; OAuth issuer/resource/audience checks for the
reviewed MCP binding; rejection of token passthrough to downstream services.

**Risks:** credential theft, audience confusion, replay, stale key bundles,
overlap-window mistakes and algorithm or profile downgrade. Bearer credentials
remain replayable until expired or revoked if stolen.

**Future:** stateful provider admission and globally single-use redemption are
not v1 properties. #57 owns that research. #58 retains trust-root rotation,
revocation and recovery gates before normative ticket promotion.

## Replay, retry and cancellation

Task identifiers bind execution attempts to an authenticated context. A
conflicting identifier reuse must be rejected. Retrying a task after a timeout
can duplicate execution because a consumer timeout does not prove that the
provider stopped. Automatic retry is safe only for an explicitly replay-safe
operation or a lifecycle profile with the necessary idempotency semantics.

**Normative/implemented:** bounded local replay caches, signed nonces, ticket
expiry, MCP replay-safe retry classification, ordered lifecycle events and
explicit replay gaps in negotiated profiles.

**Experimental:** distributed lifecycle persistence and cancellation evidence.
These profiles do not create a global transaction or billing guarantee.

**Accepted risk:** process-local replay state can be lost on restart. Global
redemption would add availability, split-brain and privacy costs and remains
future work.

## Version and downgrade handling

Production peer transport uses authenticated TLS. Negotiation must select a
mutually supported version and reject a changed or out-of-range selection.
Required policy, confidentiality, managed-operation, ticket and streaming
profiles fail closed rather than silently falling back.

Unknown optional extensions can be ignored only where the negotiated profile
allows it. Unknown mandatory semantics, unsupported eras and malformed
capabilities are rejected. A legacy interoperability path must preserve its
issuer, audience, resource, consent, sandbox and tool-risk requirements.

The project convention of TCP port 9484 is not an assignment and supplies no
trust. No current release claims a QUIC mapping or an IICP ALPN registration.

## Parsing and resource exhaustion

Peers must validate frame headers and configured size limits before allocating
from a declared payload length. The peer draft uses a 16 MiB default frame
limit and prohibits indefinite-length CBOR for core messages. Malformed magic,
length, version, type and CBOR fail before application dispatch.

Implementations must bound concurrent connections, incomplete frames,
reassembly bytes, task and header sizes, streaming buffers, lifecycle replay,
diagnostics, queues, timeouts and retries. Cheap validation and authentication
should precede expensive matching, cryptography or backend work where the
protocol permits it. Rate limiting must distinguish registration, heartbeat,
discovery, task, receipt and relay costs.

**Implemented evidence:** parser, framing, malformed-input, size, SSRF and
timeout cases exist across the conformance suite and maintained components.

**Future:** registration burst and steady-state tuning remains PHP issue #65;
relay production abuse hardening remains root #524. Neither absence authorizes
unbounded defaults.

## Endpoint exposure, NAT and local discovery

UPnP, tunnels, relays, WebRTC signalling, DNS and mDNS solve reachability or
bootstrap problems, not identity or trust. Automatic exposure can publish a
service more broadly than its operator expects. Tunnel ownership and browser
signalling can leak addresses and connection metadata.

Operators must be able to disable automatic public exposure and unattended
updates. Explicit directory configuration takes precedence over discovered
candidates. Local discovery observations must remain link-local and must not be
federated. Browser WebRTC, mDNS/DNS-SD and relay eligibility remain separate
research issues (#4 in the web-node repository, #39 and #59).

## Confidentiality and metadata privacy

TLS protects a transport hop. IICP-CX can protect payloads end to end through a
relay when the consumer verifies the provider key and refuses downgrade.
Neither mechanism provides anonymity. Observable metadata can include intent,
candidate queries, endpoints, task timing, ciphertext length, volume, provider
selection, model hints and failure patterns.

Logs, receipts and public evidence must exclude prompts, responses, credentials,
private keys, bearer tokens, private topology and raw operator identifiers.
Content-free evidence can still permit correlation through stable identifiers,
timestamps or uncommon configurations. Retention, aggregation and public
cardinality must be bounded.

## Federation and directory compromise

Federation is not production-enabled. A compromised directory could sign false
events within its authority, withhold updates, return stale snapshots or create
conflicting state. Signatures prove origin and integrity; they do not prove an
event is honest.

The pre-normative model uses authenticated bootstrap, signed snapshots/event
tails, sequence continuity, snapshot-scoped replica credentials, rotation,
decommissioning and bounded event types. Remaining risks include split brain,
revocation propagation, malicious-but-valid events, recovery-authority capture
and operational rollback.

No replica should become Genesis authority without persistent shadow evidence,
complete REACH parity, recovery and credential-rotation tests, rollback
rehearsal and explicit maintainer approval.

## Receipts, credits and reputation

Receipts and signatures are evidence, not proof of semantic result quality.
Retries, cancellation and partial output can create ambiguity about completion
and accounting. Nonces and database constraints must prevent duplicate awards;
consumer/provider bindings must prevent charging an unrelated party.

Reputation and health remain distinct. Health describes operational liveness;
reputation reflects accumulated history. Neither creates identity proof.
Economic and recognition profiles retain manipulation, collusion and Sybil
risks and must not be promoted from project simulations alone.

## Operational recovery

The internal node supervisor handles recoverable tunnel, directory and provider
failures. The runtime-health layer distinguishes local liveness, readiness,
subsystem health and external connectivity. An OS service manager handles final
process recovery. External network failure must not cause a watchdog restart
loop.

The systemd notifier is opt-in. Controlled x86-64 and ARM64 tests do not classify
the historical Raspberry Pi incident or justify default enablement. A single
environment should have one final restart authority to avoid watchdog races.

Operators need immutable release provenance, an explicit configuration scope,
healthcheck/doctor output, updater verification, rollback and predictable
uninstall. These requirements are consolidated in #96.

## Profile disposition

| Profile area | Current evidence | Disposition |
| --- | --- | --- |
| Intent/capability/extension registry (#55) | schemas, lifecycle rules and project parity | pre-normative; await independent adoption |
| Policy/data handling (#56) | shared vectors and fail-closed SDK behavior | pre-normative; await independent adapter/review |
| Route tickets/receipts (#58) | offline crypto, directory/SDK parity and conformance runner | pre-normative; await external evidence and recovery decision |
| Stateful admission (#57) | deterministic research only | research; no v1 implication |
| Signed message envelope (#52) | existing signatures are purpose-specific | universal envelope rejected; admit only a demonstrated narrow evidence profile |
| Relay eligibility (#59) | project-operated relay evidence only | research; require independent operator |
| A2A binding (#60) | pre-normative loopback interoperability | completed research; no default |
| DNS-AID/ANS (#61) | offline import/export mapping | completed research; no runtime publication |
| Independent conformance (#31) | public runner and clean-room packet | external gate open |
| Identity/evidence (#63) | dated crosswalk and negative fixtures | completed research; no credential rollout |
| Execution privacy (#136) | software composition proof | hardware and external-review gates open |

This explicit disposition satisfies the coordination purpose of #54. It does
not satisfy the independent-evidence gates of #55, #56 or #58.

## External-review checklist

- Every privacy statement says whether the provider sees plaintext.
- Every mitigation is identified as normative, implemented, experimental or
  future work.
- Operational fallbacks are not described as cryptographic authentication.
- Port 9484, QUIC, federation, relay stability and confidential execution are
  not overstated.
- Conformance links show tested behavior without treating project tests as
  independent implementation evidence.
- Accepted risks include malicious-but-valid authorities, traffic analysis,
  availability failure, local replay-state loss and operator misconfiguration.

## Evidence references

- `spec/v1.9/iicp-framing.md`, sections 6 and 9.
- `spec/v1.9/iicp-confidentiality.md`, including fail-closed CX behavior.
- `spec/v1.9/iicp-dir.md`, public/dispatch discovery, ticket and federation contracts.
- `spec/v1.9/iicp-mcp-binding.md`, authorization and downgrade behavior.
- `spec/v1.9/conformance-test-suite.md`.
- `research/pre-normative-profiles/` for explicitly non-normative profiles.
- `standards/ietf/draft-roble-iicp-peer.md` for the minimal external transport subset.
