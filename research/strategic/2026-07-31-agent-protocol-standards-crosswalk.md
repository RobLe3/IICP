# Agent protocol standards crosswalk — 2026-07-31

**Status:** research input, not normative IICP text  
**Evidence date:** 2026-07-31  
**Scope:** architecture and standards positioning; no claim of endorsement,
interoperability, adoption, or IANA assignment

## Working position

IICP is best scoped as an **intent-resolution and execution-selection control
plane**. It resolves an intent, evaluates provider eligibility, health, policy,
capacity, trust, and route constraints, and issues routing or authorization
material. The selected endpoint may then use MCP, A2A, an OpenAI-compatible API,
or another negotiated execution protocol. Task payloads do not need to pass
through an IICP directory.

This boundary avoids presenting IICP as a replacement for tool protocols, agent
task-lifecycle protocols, DNS identity, or workload identity.

## Status and overlap

| Work | Status observed on 2026-07-31 | Overlap with IICP | IICP action |
|---|---|---|---|
| [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) | Published MCP protocol revision | Tool discovery and invocation, authorization context, optional Tasks/Skills/Apps | Maintain a version-negotiated S.15 binding. Keep IICP selection and policy outside MCP tool semantics. |
| [A2A](https://a2a-protocol.org/latest/specification/) | Released agent task protocol with maintained SDKs | Agent descriptions, invocation, task lifecycle, streaming | Define an adapter after IICP provider selection; do not duplicate the A2A task lifecycle. |
| [IETF agentproto](https://datatracker.ietf.org/group/agentproto/about/) | IETF BOF activity, not a chartered working group | Broad agent-protocol problem space | Participate through comparisons and implementation evidence; do not describe BOF documents as IETF standards. |
| [IAIP](https://datatracker.ietf.org/doc/draft-sz-dmsc-iaip/) | Individual Internet-Draft; no IETF endorsement | Registration, intent resolution, gateway validation, matching, and routing | Publish a field-by-field comparison and identify reusable operational evidence. |
| [AIPF](https://datatracker.ietf.org/doc/draft-zahed-agent-comm-framework/) | Individual Internet-Draft; no IETF endorsement | Federated discovery, signed capabilities, delegation, sessions, and transport | Compare trust roots, failure semantics, tickets, and federation convergence. |
| [IACP](https://datatracker.ietf.org/doc/draft-gebauer-iacp/) | Individual Internet-Draft; no IETF endorsement | Identity/locator separation, sessions, routing tickets, distributed lookup | Compare identifiers, route authorization, replay boundaries, and state recovery. |
| [Agent Infrastructure Discovery](https://datatracker.ietf.org/doc/draft-nemethi-aid-agent-identity-discovery/) | Individual Internet-Draft; no IETF endorsement | DNS-first agent discovery | Evaluate as a verified bootstrap input rather than a replacement for live eligibility. |
| [Agent Information and Naming Service](https://datatracker.ietf.org/doc/draft-vandemeent-ains-discovery/) | Individual Internet-Draft; no IETF endorsement | HTTPS discovery, identity, capabilities, provenance | Map descriptors into untrusted candidate records, then apply IICP verification and health checks. |
| [Agent URI scheme](https://datatracker.ietf.org/doc/draft-narvaneni-agent-uri/) | Individual Internet-Draft; no IETF endorsement | Agent addressing and transport selection | Avoid registering conflicting syntax; evaluate a reversible mapping. |
| [DNS-AID](https://github.com/dnsaid/dnsaid) | Linux Foundation project; not an IETF standard | DNSSEC/DANE-rooted endpoint and capability publication | Prototype import/export with provenance retained and live IICP state kept separate. |
| Agent Name Service | Announced project intent; maturity must be rechecked before implementation | Portable identity, domain proof, lifecycle transparency | Track as an identity input; do not make protocol requirements depend on an announced design. |
| [AGNTCY](https://docs.agntcy.org/) | Linux Foundation project | Directory, identity, credentials, observability, schemas, secure messaging | Compare resolver metadata and identity portability; preserve IICP's live intent-selection boundary. |
| [DID Core](https://www.w3.org/TR/did-core/) and [VC Data Model](https://www.w3.org/TR/vc-data-model/) | DID Core and VC 2.0 are W3C Recommendations; later VC drafts have separate status | Node/operator identity, provenance, conformance, federation membership | Define an optional mapping profile before inventing new credential vocabulary. |
| [OpenAPI 3.2](https://spec.openapis.org/oas/v3.2.0.html) | Published OpenAPI specification | HTTP operation contracts and agent-facing API metadata | Keep the Directory OpenAPI projection first-class and machine-checked. |

## Architectural mapping

| Stage | IICP responsibility | Compatible external responsibility |
|---|---|---|
| Describe | Normalize intent and constraints | A2A Agent Cards, MCP tool metadata, OpenAPI descriptions, DNS capability documents |
| Discover | Produce candidate providers from configured or verified sources | DNS-AID/AID/AINS may provide bootstrap candidates |
| Verify | Check identity, health, policy, capacity, route, and trust evidence | DID/VC, DNSSEC/DANE, OAuth metadata, workload identity |
| Select | Rank or filter eligible providers under caller policy | Remains IICP control-plane behavior |
| Authorize | Issue audience-bound route or dispatch material | OAuth or protocol-specific authorization continues at the selected endpoint |
| Execute | Keep task payloads off the directory | MCP, A2A, OpenAI-compatible HTTP, or negotiated native framing |
| Account | Correlate content-minimized receipts and telemetry | External receipt or observability formats may be mapped where semantics match |

## Rules for standards-facing claims

1. Distinguish a Recommendation, published protocol release, chartered working
   group, BOF, individual Internet-Draft, Community Group report, and project
   announcement.
2. An Internet-Draft is temporary work in progress and is not IETF endorsement.
3. Port `9484`, media types, URI schemes, and other IANA-facing identifiers remain
   provisional until assigned. One requested service port is the current design
   preference, not an allocation.
4. Same-maintainer PHP/Rust/SDK parity is implementation evidence, not independent
   interoperability.
5. Searches that find no independent implementation or publication are bounded
   observations, not proof of absence.
6. Project-reported adoption numbers must be attributed to the reporting project.
7. A bridge prototype imports candidates or maps execution semantics; it does not
   make the external protocol part of normative IICP core.

## Ordered work

1. Complete the MCP modern/legacy binding and shared negative fixtures.
2. Publish field-level comparisons for IAIP, AIPF, IACP, AID/AINS, and the agent
   URI proposal.
3. Define an A2A execution adapter after provider selection.
4. Prototype DNS-AID import/export with DNSSEC provenance and explicit trust
   policy; keep mDNS/DNS-SD as a separate link-local bootstrap profile.
5. Define optional DID/VC mappings for operator identity, deployment provenance,
   conformance, and federation membership.
6. Make the conformance runner independently installable and its result bundle
   machine-verifiable.
7. Bring implementation and failure evidence to relevant public standards
   discussions without claiming IETF or IANA acceptance.

Re-verify every external status immediately before publication or outreach.
