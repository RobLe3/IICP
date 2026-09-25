# IICP and adjacent IETF work: September 2026 assessment

**Verified:** 2026-09-25
**Status:** informative project analysis, not an IETF position, endorsement,
interoperability certificate or change to the IICP Protocol Suite.

This supersedes the *current-state* rows in the
[15 August comparison](PROTOCOL_COMPARISON_2026-08-15.md), which remains an
unaltered historical snapshot. Source revisions, dates and the requirement
mapping also appear in [`protocol-comparison-v1.json`](protocol-comparison-v1.json).
Individual Internet-Drafts are work in progress. The [DAWN group page](https://datatracker.ietf.org/wg/dawn/about/)
described a **proposed** working group and draft charter at verification time,
not an adopted WG specification. An intended Standards Track label is not
IETF adoption.

## Sources and roles

| Work and primary source | Revision/date checked | Formal standing and relevant scope |
|---|---|---|
| [IAIP](https://datatracker.ietf.org/doc/draft-sz-dmsc-iaip/02/) | `draft-sz-dmsc-iaip-02`, 2026-05-25 | Individual I-D; agent-gateway registration, constraint filtering, ranking, selection and forwarding (§§6–8). |
| [AIDIP](https://datatracker.ietf.org/doc/draft-cui-ai-agent-discovery-invocation/02/) | `draft-cui-ai-agent-discovery-invocation-02`, 2026-07-06 | Individual I-D; agent discovery, optional intent-aware candidate selection and invocation. |
| [CIRP](https://datatracker.ietf.org/doc/draft-verma-cirp/02/) | `draft-verma-cirp-02`, 2026-08-10 | Individual I-D; scoped capability discovery, authorization tickets, peer sessions and receipts; ranking is outside scope (§§1, 6–10). |
| [Intent Routing Requirements](https://datatracker.ietf.org/doc/draft-feng-dmsc-intent-routing-requirements/00/) | `draft-feng-dmsc-intent-routing-requirements-00`, 2026-08-14 | Individual requirements I-D; REQ-1–17 in §3, not an implemented routing protocol. |
| [DAWN](https://datatracker.ietf.org/wg/dawn/about/) | [charter history](https://datatracker.ietf.org/doc/charter-ietf-dawn/history/) records `charter-ietf-dawn-00-07` on 2026-09-11; group status checked 2026-09-25 | Proposed WG; initial naming/discovery, excluding semantic matchmaking, ranking and selection in the proposed charter. |
| [DNS-AID](https://datatracker.ietf.org/doc/draft-mozleywilliams-dnsop-dnsaid/02/) | `draft-mozleywilliams-dnsop-dnsaid-02`, 2026-05-27 | Individual I-D; DNS-based discovery of connectivity and capability-document references. |
| [DMSC architecture](https://datatracker.ietf.org/doc/draft-li-dmsc-architecture/01/) | `draft-li-dmsc-architecture-01`, 2026-05-29 | Individual architecture I-D; compare domain boundaries and architecture, not an adopted DMSC standard. |
| [DMSC information architecture](https://datatracker.ietf.org/doc/draft-li-dmsc-inf-architecture/07/) | `draft-li-dmsc-inf-architecture-07`, 2026-05-22 | Individual architecture I-D; an additional DMSC context source, not an implementation result. |
| [AIPF](https://datatracker.ietf.org/doc/draft-zahed-agent-comm-framework/01/) | `draft-zahed-agent-comm-framework-01`, 2026-07-19 | Individual framework I-D; broader communication-layer architecture. |
| [IACP](https://datatracker.ietf.org/doc/draft-gebauer-iacp/03/) | `draft-gebauer-iacp-03`, 2026-07-28 | Individual I-D; broader agent communication architecture. |
| [Agent Routing Policy](https://datatracker.ietf.org/doc/draft-ahuja-agent-routing-policy/00/) | `draft-ahuja-agent-routing-policy-00`, 2026-09-17 | Individual I-D; policy grammar for inter-domain delegation, not evidence of a deployed policy engine (§§4–5). |
| [Agent Session Requirements](https://datatracker.ietf.org/doc/draft-feng-agentproto-session-requirements/02/) | `draft-feng-agentproto-session-requirements-02`, 2026-08-20 | Individual requirements I-D; session establishment after discovery. |
| [Security Principal Binding](https://datatracker.ietf.org/doc/draft-bu-agentproto-security-principal-binding/07/) | `draft-bu-agentproto-security-principal-binding-07`, 2026-09-15 | Individual guidance I-D; claim, carrier, verifier and freshness boundaries. |
| [SCITT agent action receipts](https://datatracker.ietf.org/doc/draft-noa-scitt-ai-agent-receipt/01/) | `draft-noa-scitt-ai-agent-receipt-01`, 2026-08-15 | Individual profile I-D, not an adopted SCITT WG result; action-evidence export may be complementary. |

[MCP](https://modelcontextprotocol.io/specification) and
[A2A](https://a2a-protocol.org/latest/specification/) remain complementary
execution and integration protocols in this comparison. They are not IETF
initiatives by association. The source inventory records document metadata,
not an exhaustive search for external implementations; absence of a link in a
draft cannot establish that none exists.

## Responsibility comparison

| Dimension | IICP evidence and limit | Adjacent work and boundary |
|---|---|---|
| Intent and capability | Released project intent registry and effective-capability rules; identifiers are exact, opaque project values, not Internet-scale prefix routes. | IAIP/AIDIP overlap intent matching; CIRP has versioned capability identifiers; DNS-AID can supply discovery input. |
| Required constraints, freshness and eligibility | Directory and client apply hard constraints before any optional ranking; current state and provenance must be revalidated. | IAIP also filters before ranking, so that ordering alone is not a differentiator. DAWN's proposed scope stops at initial discovery. |
| Ranking and selection | Default directory order is preserved absent a declared selection Profile. A local ranker cannot widen eligibility or overwrite directory score. | IAIP ranks; AIDIP can rank candidates; CIRP deliberately returns unranked discovery. |
| Route and endpoint authority | Discovery is not execution permission; single-route IICP dispatch tickets bind one eligible route, and endpoint authentication remains binding-specific. | CIRP ConnectTickets authorize a different session process. Shared terminology does not imply equivalent claims or wire compatibility. |
| Payload path and lifecycle | The Directory is a control plane; the selected executor receives task content directly via the chosen binding. Native TCP is not in the coordinated stable baseline and QUIC is not implemented. | IAIP includes both direct-execution and gateway-forwarding descriptions; compare the path in the cited procedure. MCP/A2A own their execution lifecycles. |
| Domains and policy | Optional restricted-domain/CUG and Management work constrain eligibility while retaining domain-local authority; remote administration is not a deployed Core feature. | Agent Routing Policy proposes a grammar; DMSC work explores domain architecture. Neither is proof of deployed enforcement or interoperable federation with IICP. |
| Security, privacy and receipts | IICP publishes purpose-specific trust, ticket and receipt contracts and same-project fixtures. The chosen remote executor sees the task it performs. | Session, principal-binding and SCITT work offer possible crosswalks, not implicit IICP dependencies or proof of confidential execution. |
| Implementation and compatibility | Published Python, TypeScript and Rust SDKs; PHP and Rust directory flavors; experimental browser node; optional Management preview. Evidence is mostly maintained by one project. | Architectural overlap is not demonstrated wire interoperability. Independent clean-room IICP implementation and cross-project conformance remain open evidence. |

The IICP selection contract is most useful when a caller must choose among
heterogeneous providers using current capability, policy, security and route
evidence. It does not replace initial naming, session protocols or execution
bindings. The exact-match `urn:iicp:` identifier design does **not** establish
prefix aggregation or bounded Internet-wide routing state.

## Direct protocol-feature crosswalk

This table compares the mechanisms in the [exact draft revisions above](#sources-and-roles),
not interchangeable wire formats. “Not specified here” means only that the
cited draft does not define an equivalent contract in that revision. IICP
references are the [suite index](https://github.com/RobLe3/IICP/blob/main/spec/v1.9/README.md),
[directory-state decision](https://github.com/RobLe3/IICP/blob/main/docs/architecture/directory-state-semantics.md),
[effective-capability decision](https://github.com/RobLe3/IICP/blob/main/docs/architecture/effective-service-capability-semantics.md)
and [conformance suite](https://github.com/RobLe3/IICP/blob/main/spec/v1.9/conformance-test-suite.md).

| Mechanism | IICP | IAIP -02 | AIDIP -02 | CIRP -02 |
|---|---|---|---|---|
| Request and capability naming | Versioned, exact-match Intent identifiers. The working-main effective-capability decision makes unknown required extensions ineligible; this is not prefix routing or a retroactive claim about older releases. | `INTENT_REQ` is semantically matched against gateway-held `CAP_ADV` profiles (§§7–8). | Agent metadata supports attribute search and optional natural-language intent selection; matching is implementation-specific (§§4, 6). | Versioned capability identifiers and scoped advertisements; discovery is capability-oriented (§§5–6). |
| Registration and current state | Registration, authenticated heartbeat, route observation, availability and advertisement freshness are distinct eligibility inputs. | Agent identity and capability advertisement populate a local gateway registry with lifecycle maintenance (§§6, 8.3). | Registry metadata, discovery and invocation are described; the optional selection example can carry `expires_at` (§§4, 6). | Registries admit scoped capability advertisements and separate discovery from authorization (§§5–7). |
| Hard constraints and ranking | Required capability, policy, security and live-state checks precede ranking. Default directory order is preserved unless a supported selection Profile applies; a ranker cannot admit an ineligible candidate. | Mandatory constraints are filtered *before* semantic evaluation and ranking; policy can further narrow the set (§8.4). That order is shared, not unique to IICP. | Optional intent selection can evaluate constraints and return ranked candidates. Understood selection constraints should be binding; its match-score scale is registry-specific (§6). | Scope and admission govern visibility. Discovery results are explicitly unranked; preference ordering is outside CIRP (§6). |
| Result and authorization | Discovery does not authorize execution. A dispatch ticket discloses one selected eligible route; binding-specific endpoint authentication remains necessary. | Gateway decision and forwarding follow candidate selection; this revision does not define an IICP-compatible route-disclosure ticket (§§8.4–8.7). | A ranked candidate response can include an endpoint and invocation metadata; the client may inspect more metadata, invoke or decline (§6). Selection alone is not an IICP ticket. | Registry-issued `ConnectTicket` binds consumer, provider and capability for session authorization (§7). It is not an IICP dispatch ticket. |
| Task path and lifecycle | The Directory does not receive task payloads. The selected executor receives them through a supported binding; native TCP is outside the coordinated stable baseline. | Its gateway architecture includes forwarding and loop prevention, while the draft also describes a direct-execution path; topology depends on the procedure (§§6, 8). | Specifies normal invocation using the selected agent's interface; optional selection precedes invocation (§§5–6). | Registry leaves the post-authorization peer session path; the draft specifies a protected session and invocation envelope (§§7–9). |
| Domain policy and evidence | Optional CUG and Management constrain eligibility without granting Management provider-selection authority. Directory observations, provider reports and receipts have separate provenance. | Local gateway policy and routing feedback are defined (§§8–9); no IICP Management compatibility follows. | Registry/host selection constraints and explanations are described; `selection_reason` is not a security assertion (§6). | Visibility scopes, policy receipts and dual-signed fulfillment records are specified (§§6, 10). Their semantics differ from IICP evidence. |

The [Intent Routing Requirements mapping](#intent-routing-requirements-mapping)
tests IICP against each of that draft's 17 requirements; it is not a competing
executable protocol. [DAWN's proposed charter](https://datatracker.ietf.org/wg/dawn/about/)
addresses initial discovery, not semantic selection. [DNS-AID](https://datatracker.ietf.org/doc/draft-mozleywilliams-dnsop-dnsaid/02/)
could supply discovery input. The [Agent Routing Policy draft](https://datatracker.ietf.org/doc/draft-ahuja-agent-routing-policy/00/)
describes policy grammar, not a deployed enforcement service. None of these
roles, by itself, establishes interoperability with IICP.

## Specification and implementation maturity

Protocol responsibility and implementation maturity answer different questions.
The [versioned IICP suite](https://github.com/RobLe3/IICP/blob/main/ecosystem/CURRENT_VERSIONS.md) has a separate
v1.9.0 wire baseline; neither version axis grants a coordinated stable label.
Its [implementation catalogue](https://github.com/RobLe3/IICP/blob/main/IMPLEMENTATIONS.md) links the
[PHP Directory](https://github.com/RobLe3/iicp-directory-php),
[Rust Directory](https://github.com/RobLe3/iicp-directory-rust),
[Python](https://github.com/RobLe3/iicp-client-python),
[TypeScript](https://github.com/RobLe3/iicp-client-typescript) and
[Rust](https://github.com/RobLe3/iicp-client-rust) consumer/provider SDKs,
the [experimental browser node](https://github.com/RobLe3/iicp-web-node) and
the optional [Management developer preview](https://github.com/RobLe3/iicp-management). The
[public schemas](https://github.com/RobLe3/IICP/blob/main/schemas/capability-requirements-v1.json),
[registry](https://github.com/RobLe3/IICP/blob/main/registry/intents.json),
[executable conformance fixtures](https://github.com/RobLe3/IICP/blob/main/spec/v1.9/conformance-test-suite.md),
[negative/security vectors](https://github.com/RobLe3/IICP/tree/main/conformance-runner/src/iicp_conformance/fixtures),
[standalone black-box runner](https://github.com/RobLe3/IICP/blob/main/conformance-runner/README.md),
[clean-room instructions](https://github.com/RobLe3/IICP/blob/main/conformance-runner/CLEAN_ROOM_IMPLEMENTATION.md),
[signed content-free evidence support](https://github.com/RobLe3/IICP/blob/main/conformance-runner/README.md),
[release-integrity manifest](https://github.com/RobLe3/IICP/blob/main/spec/v1.9/release-integrity-manifest.json),
[compatibility-environment records](https://github.com/RobLe3/IICP/blob/main/SDK_QUALITY_EVIDENCE.md) and
[release-candidate controls](https://github.com/RobLe3/IICP/blob/main/RELEASE_CANDIDATES.md) make these claims
inspectable. [Public operational evidence](https://iicp.network/external-evidence)
is project-operated. The [pre-1.0 boundary](https://github.com/RobLe3/IICP/blob/main/pre1/README.md) remains an open
qualification program, not a certificate.

The table compares *located public evidence*, not protocol merit or the
existence of all private work. “Not identified” means that the cited revision,
its references, relevant public repository search and, for AIDIP, the IETF 124
Hackathon record did not establish the stated evidence as of 2026-09-25. IAIP
and CIRP are individual drafts with different scopes; CIRP is technically
detailed, which is distinct from proof of running code. The
[AIDIP draft](https://datatracker.ietf.org/doc/draft-cui-ai-agent-discovery-invocation/02/)
still contains a placeholder source URL. The
[IETF 124 Hackathon record](https://github.com/ietf/wiki.ietf.org/blob/main/meeting/124/hackathon.md)
describes a related implementation plan, not a verified maintained AIDIP
codebase or conformance result.

| Public evidence located | IICP | IAIP | AIDIP | CIRP | Intent Routing Requirements | DAWN |
|---|---|---|---|---|---|---|
| Versioned specification contract | Published project suite; separate wire baseline | Individual draft | Individual draft | Detailed individual draft | Requirements only | Proposed charter |
| Machine-readable schemas/registries | Published schemas and intent registry | Message fields in draft; standalone contract not identified | JSON examples in draft; standalone contract not identified | Binary/CBOR structures in draft; standalone contract not identified | Not applicable | Not applicable |
| Maintained public implementation | PHP/Rust Directories and three SDK families | Not identified | Not identified; Hackathon plan noted | Not identified | Not applicable | Not applicable |
| Multiple maintained codebases | Two Directories, three SDKs, browser and Management preview, mostly same-project | Not identified | Not identified | Not identified | Not applicable | Not applicable |
| Multiple implementation languages | Python, TypeScript, Rust, PHP | Not identified | Not identified | Not identified | Not applicable | Not applicable |
| Executable conformance fixtures | Project-owned, including cross-language parity material | Not identified | Not identified | Not identified | Not applicable | Not applicable |
| Negative/security vectors | Published project-owned refusal, ticket and resource-boundary cases | Not identified | Not identified | Not identified | Not applicable | Not applicable |
| Standalone black-box runner | Directory profiles and offline evidence checks | Not identified | Not identified | Not identified | Not applicable | Not applicable |
| Release-integrity tooling | Manifest and validation tools | Not identified | Not identified | Not identified | Not applicable | Not applicable |
| Packaged component releases | Independently versioned project releases | Not identified | Not identified | Not identified | Not applicable | Not applicable |
| Operational deployment evidence | Project-operated PHP Genesis; not an independent deployment | Not identified | Not identified | Not identified | Not applicable | Not applicable |
| Independent implementation/interoperability | Not independently established | Not identified | Not identified | Not identified | Not applicable | Not applicable |
| Policy/Management implementation | Optional developer preview; not deployed authority | Not identified | Not identified | Not identified | Not applicable | Not applicable |

The external evidence check was bounded to each exact draft, links it provides
and a focused public repository search on the draft identifier. For AIDIP it
also included the [IETF 124 Hackathon record](https://github.com/ietf/wiki.ietf.org/blob/main/meeting/124/hackathon.md).

| Draft | Implementation evidence found in that scope | What remains unestablished |
|---|---|---|
| [IAIP -02](https://datatracker.ietf.org/doc/draft-sz-dmsc-iaip/02/) | A detailed gateway procedure, message fields and examples in the individual draft. | No maintained public implementation, executable conformance suite or operational deployment was identified in the reviewed sources. |
| [AIDIP -02](https://datatracker.ietf.org/doc/draft-cui-ai-agent-discovery-invocation/02/) | Agent metadata, REST examples and optional selection fields in the draft. Its source-repository URL is still a placeholder. The Hackathon record describes related implementation activity as a plan, not a verified release. | No maintained public AIDIP implementation, cross-implementation result, executable conformance suite or deployment was identified in the reviewed sources. |
| [CIRP -02](https://datatracker.ietf.org/doc/draft-verma-cirp/02/) | Detailed scope, binary ticket, session and dual-signed receipt specifications. This is substantial specification detail. | No maintained public implementation, executable conformance suite or operational deployment was identified in the reviewed sources. Draft detail alone cannot settle runtime maturity. |

These are findings about *located evidence*, not claims that no code exists.
The requirements draft and proposed charter are different artifact types, so
their lack of an executable implementation is not scored as a defect.

The [machine-readable evidence rows](protocol-comparison-v1.json) identify
source URLs, artifact class, verification date, bounded search scope and each
limitation. The reviewed evidence supports a material difference: IICP has
substantially stronger *implementation-backed conformance and operational
evidence* than the directly overlapping IAIP, AIDIP and CIRP individual
drafts reviewed here. This does not establish universal design superiority,
equivalent scope, IETF adoption or independent IICP interoperability. The
maintained IICP implementations are predominantly same-project work.

The evidence stages are distinct:

```text
requirements / charter -> individual draft -> executable specification
-> maintained implementation(s) -> cross-implementation fixtures
-> conformance tooling -> packaged releases -> operational deployment
-> independently authored implementation and external interoperability
```

This is not a quality ranking: a narrow charter can be valuable without code,
and project-operated code cannot satisfy an independent-implementation gate.
IICP has passed the specification-only stage through its maintained codebases,
fixtures, tooling, releases and project-operated deployment. Its independent
implementation and externally operated interoperability stage remains open.

## Intent Routing Requirements mapping

The following labels are analytical, not qualification results. Source is
[`draft-feng-dmsc-intent-routing-requirements-00` §3](https://datatracker.ietf.org/doc/draft-feng-dmsc-intent-routing-requirements/00/).
`ALIGNED` means the cited IICP contract addresses the stated property in its
declared scope; it does not mean that Internet-scale operation is measured.

| REQ | IICP contract and evidence class | Disposition and missing evidence |
|---|---|---|
| 1 Open Participation | Core/DIR registration and published SDKs; project implementation evidence. | **PARTIAL** — public-mesh admission exists, but unrestricted Internet participation and independent implementations are not established. |
| 2 Heterogeneous Handlers | Intent and effective-capability contracts plus SDK/provider adapters. | **ALIGNED** in the supported binding scope; arbitrary handler classes are not separately qualified. |
| 3 Control/Data Separation | Core/DIR direct payload path and directory fixtures. | **ALIGNED** for supported paths; performance independence is not inferred from architecture alone. |
| 4 Bounded State | Federation snapshot/event-tail design. | **NOT_ESTABLISHED** for any single node at Internet scale; directory state may grow with registrations. |
| 5 Capability Aggregation | Effective-capability and directory discovery contracts. | **DIFFERENT_DESIGN** — no cross-domain aggregate advertisement equivalent to the draft requirement. |
| 6 Local Forwarding Decisions | Client policy and direct handoff after directory selection. | **DIFFERENT_DESIGN** — IICP permits a directory selection step, not solely local datagram forwarding. |
| 7 Holder-Decided Real-Time State | Provider-reported availability plus directory probes and admission. | **PARTIAL** — the provider retains execution admission, but directory-observed eligibility uses boundedly stale evidence. |
| 8 Handler Delivery Policy | Advertised endpoint and route-authority rules. | **PARTIAL** — direct endpoint choice exists; the draft's alternative callback-delivery model is not a general IICP contract. |
| 9 Session-Agnostic Delivery | Core intent/task identity separated from transport binding. | **PARTIAL** — binding independence is specified; the draft's datagram-delivery invariant is not. |
| 10 Routable Identifier Matching | Stable opaque intent identifiers and directory matching. | **DIFFERENT_DESIGN** — exact matching does not make identifiers routable prefixes. |
| 11 No Data-Path Inference | Control-plane selection and direct data path. | **ALIGNED** in the supported direct path; no Internet-wide deterministic-forwarding benchmark is claimed. |
| 12 Hierarchical Prefix Namespace | Project `urn:iicp:` identifiers. | **DIFFERENT_DESIGN** — textual hierarchy is not prefix routing or aggregability. |
| 13 Domain Isolation | Optional restricted-trust-domain fixtures and local policy authority. | **PARTIAL** — pre-normative profile; cross-domain deployment and independent enforcement not qualified. |
| 14 Bounded Convergence | Signed federation snapshot/event-tail and freshness rules. | **NOT_ESTABLISHED** — no bounded cross-domain convergence result is published for the draft's scale. |
| 15 Delivery Reachability | Directory reachability/availability gates and supported task paths. | **PARTIAL** — an eligible route can fail; IICP does not guarantee delivery to every registered handler. |
| 16 Return Path | Direct CALL/RESPONSE bindings and task identity. | **ALIGNED** for supported request/response paths; adverse-network scale remains unmeasured. |
| 17 Originator Decomposition | Application supplies the intent; directory does not infer it from task content. | **ALIGNED** in the declared Core scope; natural-language-to-intent conversion remains application-owned. |

Each row's source section, IICP references, Profile/release scope, fixture
references and evidence limitations are recorded in the companion dataset.
The mapping leaves 4, 5, 6, 10, 12 and 14 unresolved or deliberately different;
it is not a plan to change IICP merely to improve comparison coverage.

## Chronology and evidence limits

The first inspected IICP repository commit is dated 2025-10-27. This is a
commit timestamp, not independent proof of when the repository became publicly
accessible. AIDIP -00 (2025-10-15) predates it; AIDIP intent selection appeared
in a later revision (2026-02-12), and IAIP -00 appeared on 2026-02-09. Compare
individual mechanisms and dated public artifacts, not project age or alleged
influence. The older comparison records the evidence behind those dates.

No source reviewed here establishes IETF endorsement of IICP, common wire
interoperability with these drafts, Internet-scale routing, a deployed remote
Management authority, independent IICP certification or a winning protocol.
Where source text or implementation evidence was not located, the dataset marks
the limit instead of supplying an inferred result.
