# IICP and adjacent protocols: features, chronology and evidence maturity

**Evidence date:** 2026-08-15  
**Status:** informative research; no interoperability or endorsement claim

This report updates the [2026-08-08 landscape](IETF_AGENT_PROTOCOL_LANDSCAPE_2026-08-08.md).
External specifications and Internet-Drafts change independently. Recheck the
linked primary source before using a row in outreach or implementation work.

## Reading the tables

The comparison uses responsibilities rather than feature counts:

| Term | Meaning here |
|---|---|
| Core | The cited protocol defines the behavior as part of its central contract. |
| Profile / extension | Optional interoperable behavior layered on a base contract. |
| Binding | A mapping to another protocol or transport. |
| External | Expected from another protocol, deployment or application. |
| Partial | The source covers part of the responsibility, but not the complete comparison dimension. |
| Not in scope | The source deliberately does not own the responsibility. |
| Not established | The reviewed source does not establish the behavior. |

The report also rates the public evidence behind each work. These ratings do
not name a winner and are not a certification, adoption measure or estimate of
future success. A mature implementation of a different protocol role can score
well without overlapping IICP, while a useful new proposal can score lower
because it has not yet produced implementation or deployment evidence.

| Score | Evidence represented by the score |
|---:|---|
| 0 | No reviewed public evidence for this dimension. |
| 1 | Conceptual or incomplete treatment without an executable interoperability contract. |
| 2 | Concrete specification, schema, flow or project evidence, with material gaps. |
| 3 | Detailed contract plus maintained implementation, test or operational evidence. |
| 4 | Detailed contract plus multiple independently maintained implementations or externally governed interoperability evidence. |
| Unknown | The reviewed evidence was insufficient to assign a score. |

Every machine-readable rating includes a short rationale and primary source in
[`protocol-comparison-v1.json`](protocol-comparison-v1.json). Scores should be
compared by dimension, not added into a composite total.

## Chronology

### First public evidence of each work

`First public` means the earliest dated specification submission, protocol
repository or equivalent artifact found in the reviewed primary sources. It
does not establish invention, influence, implementation maturity or priority.

| Work | First public evidence | Artifact | Relative to IICP's first public draft |
|---|---:|---|---|
| MCP | 2024-09-24 | Public protocol repository | Predates |
| ANP | 2024-10-23 | Public protocol repository | Predates |
| AGNTCY | 2025-02-05 | `agntcy/acp-spec` repository | Predates |
| A2A | 2025-03-25 | Public protocol repository | Predates |
| AIDIP | 2025-10-15 | `draft-cui-ai-agent-discovery-invocation-00` | Predates |
| DNS-AID predecessor | 2025-10-16 | `draft-mozleywilliams-dnsop-bandaid-00` | Predates |
| IICP | 2025-10-27 | IICP v1.4.2 public draft | Baseline |
| IAIP | 2026-02-09 | `draft-sz-dmsc-iaip-00` | Postdates |
| AIPF | 2026-06-23 | `draft-zahed-agent-comm-framework-00` | Postdates |
| IACP | 2026-06-26 | `draft-gebauer-iacp-00` | Postdates |

### Mechanism chronology relevant to the overlap

Protocol age and mechanism age are different. A work can predate IICP while a
particular overlapping mechanism appeared later. The dated record supports the
following narrower statements:

| Date | Work | Public mechanism evidence |
|---:|---|---|
| 2025-10-15 | AIDIP -00 | Agent metadata, discovery and REST invocation |
| 2025-10-27 | IICP v1.4.2 | Intent and capability discovery with route selection |
| 2026-02-09 | IAIP -00 | Intent resolution, matching and selection at an agent gateway |
| 2026-02-12 | AIDIP -01 | Optional intent-based agent selection |
| 2026-05-15 | IICP split suite | Explicit provider-eligibility vocabulary in the public suite |
| 2026-07-06 | AIDIP -02 | Ranked intent-selection candidates |
| 2026-08-15 | IICP positioning | Narrow standards-facing eligibility and selection boundary |

The initial IICP intent-routing draft therefore predates IAIP -00 and AIDIP's
intent-selection extension, but AIDIP's discovery and invocation work predates
IICP. IICP's current explicit provider-eligibility vocabulary postdates both
February 2026 intent-selection drafts. This sequence does not prove that one
project influenced another or owns a mechanism.

## Protocol roles and current status

| Work | Current source | Primary role | Relationship to IICP |
|---|---|---|---|
| IICP | Project suite 1.10.13; stable wire baseline 1.9.0 | Intent registry, effective-capability advertisement, directory discovery, eligibility, selection and dispatch authorization; optional execution bindings | Subject of this comparison; project-normative beta, not externally ratified |
| IAIP | [draft-sz-dmsc-iaip-02](https://datatracker.ietf.org/doc/draft-sz-dmsc-iaip/), active individual I-D, 2026-05-25 | Agent-gateway registration, capability validation, intent resolution, matching, ranking, selection and forwarding | Direct overlap; compare gateway payload path, trust model and selection-result semantics |
| AIDIP | [draft-cui-ai-agent-discovery-invocation-02](https://datatracker.ietf.org/doc/draft-cui-ai-agent-discovery-invocation/), active individual I-D, 2026-07-06 | Common agent metadata, capability/intent discovery, ranked candidates and REST invocation | Direct overlap in discovery and intent-based candidate selection; AIDIP also defines a unified invocation API |
| AIPF | [draft-zahed-agent-comm-framework-01](https://datatracker.ietf.org/doc/draft-zahed-agent-comm-framework/), active individual I-D, 2026-07-19 | Layered framework for interoperable agent-to-agent and agent-to-tool communication | Architecture and federation/trust crosswalk; not a drop-in execution binding |
| IACP | [draft-gebauer-iacp-03](https://datatracker.ietf.org/doc/draft-gebauer-iacp/), active individual I-D, 2026-07-28 | Broad Internet agent communication architecture | Compare identity, locator, session, route authorization and recovery; broader scope than IICP's proposed narrow core |
| A2A | [A2A 1.0 specification](https://a2a-protocol.org/latest/specification/) | Agent Cards, messages, tasks, artifacts, streaming, push updates and JSON-RPC/gRPC/HTTP bindings | Preferred execution binding after selection; do not duplicate its task lifecycle |
| MCP | [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) | LLM-application integration with resources, prompts, tools and opt-in extensions | Tool/context or selected execution binding; not accurately described as tools-only |
| DNS-AID | [draft-mozleywilliams-dnsop-dnsaid-02](https://datatracker.ietf.org/doc/draft-mozleywilliams-dnsop-dnsaid/), active individual I-D, 2026-05-27 | DNS/SVCB publication of agent connectivity and capability-document references | Candidate bootstrap with provenance; DNS data does not establish current IICP eligibility or dispatch authority |
| AGNTCY | [AGNTCY documentation](https://docs.agntcy.org/) | A suite covering directory, OASF descriptions, identity, messaging and observability | Adjacent multi-component ecosystem; compare each component rather than treating AGNTCY as one wire protocol |
| ANP | [ANP 1.1 specifications](https://agent-network-protocol.com/specs/) | Agent description, discovery, identity, messaging, encryption and federation profiles | Broader peer-network suite; possible descriptor or binding crosswalk, not an assumed IICP substrate |

Every IETF item above is an individual Internet-Draft. An I-D is work in
progress and has no IETF endorsement or formal standards standing.

## Evidence maturity by dimension

| Work | Spec | Versioning | Security | Implementations | Conformance | Independent implementations | Deployment | Governance |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| IICP | 3 | 3 | 3 | 3 | 3 | 1 | 2 | 2 |
| IAIP | 2 | 2 | 1 | 0 | 0 | 0 | 0 | 1 |
| AIDIP | 2 | 2 | 1 | 0 | 0 | 0 | 0 | 1 |
| AIPF | 2 | 1 | 2 | 0 | 0 | 0 | 0 | 1 |
| IACP | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 1 |
| A2A | 4 | 4 | 3 | 4 | 2 | 3 | 2 | 4 |
| MCP | 4 | 4 | 3 | 4 | 2 | 4 | 2 | 4 |
| DNS-AID | 3 | 2 | 3 | 0 | 0 | 0 | 0 | 1 |
| AGNTCY | 3 | 3 | 3 | 4 | 2 | 2 | 2 | 4 |
| ANP | 3 | 3 | 3 | 3 | 2 | 1 | 1 | 2 |

The evidence supports several bounded conclusions:

- MCP and A2A have stronger independent implementation and governance evidence
  than IICP. Their roles also differ from IICP's proposed eligibility layer.
- IICP has more same-project implementation and conformance evidence than the
  reviewed individual Internet-Drafts. That is not independent interoperability
  evidence.
- DNS-AID has a precise, security-aware discovery proposal, but the reviewed
  sources do not establish implementations or deployment evidence.
- AGNTCY and ANP are broader suites. Their scores describe their public
  artifacts, not compatibility with IICP or fitness for IICP's narrow role.

### Maturity of the directly overlapping mechanisms

This second table rates only the seven responsibilities in the responsibility
matrix. It helps distinguish a precise execution lifecycle from a precise
eligibility contract.

| Work | Semantic request | Capability advertisement | Eligibility | Selection | Route authorization | Execution lifecycle | Transport |
|---|---:|---:|---:|---:|---:|---:|---:|
| IICP | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| IAIP | 2 | 2 | 2 | 2 | 1 | 1 | 2 |
| AIDIP | 2 | 2 | 2 | 2 | 1 | 2 | 2 |
| A2A | 2 | 4 | 0 | 0 | 2 | 4 | 4 |
| MCP | 2 | 4 | 0 | 0 | 3 | 3 | 4 |
| DNS-AID | 0 | 2 | 0 | 0 | 2 | 0 | 3 |

A zero here means that the reviewed protocol does not provide public evidence
for that comparison dimension. It does not mean the protocol is poor. For
example, A2A and MCP leave provider eligibility and selection to another layer
while defining mature execution or integration contracts.

## Responsibility matrix

| Responsibility | IICP | IAIP | AIDIP | A2A | MCP | DNS-AID |
|---|---|---|---|---|---|---|
| Stable semantic request identifier | Core Intent registry | Partial intent descriptor | Partial intent fields | Skills and messages, not an IICP-style Intent registry | Tool/resource/prompt names | Not in scope |
| Capability advertisement | Core, including effective service-path profiles | Core gateway registry | Core agent metadata | Core Agent Card/skills | Core server discovery | Capability document reference |
| Current operational eligibility | Core directory and client policy | Core gateway function | Partial registry/search filtering | External to task protocol | External to integration protocol | Not in scope |
| Provider ranking/selection | Core with deployment-defined scoring | Core gateway function | Core ranked discovery | External/application choice | External/host choice | External consumer/search service |
| Route authorization after selection | Core dispatch-ticket profile; migration not complete | Partial trust/session mechanism | Authentication discussed; exact authorization varies | Endpoint authorization schemes | OAuth/authorization framework | DNSSEC/DANE can authenticate published data/endpoints |
| Task/message lifecycle | IICP CALL/RESPONSE plus profiles; not the proposed selection core | Partial forwarding lifecycle | REST invocation | Core and detailed | Core requests plus optional Tasks | Not in scope |
| Streaming execution | Negotiated execution behavior | Partial | Partial | Core | Transport/extension dependent | Not in scope |
| Directory stays out of payload path | Architectural default | Gateway participates in forwarding architecture | Direct or gateway invocation are both allowed | Depends on deployment | Depends on host/server path | Direct connection after discovery |
| Content-minimized receipt/correlation | Core/profile work | Partial feedback | Not established as equivalent | Task/artifact state, not equivalent receipt semantics | Progress/results, not equivalent receipt semantics | Not in scope |
| Transport ownership | Binding | Defines transport/security bindings | HTTP invocation | JSON-RPC, gRPC and HTTP bindings | JSON-RPC over supported transports | DNS discovery only |

`Partial` means that related behavior exists; it does not assert wire or
semantic compatibility.

## Composition model

```text
application or agent
        |
        | intent + constraints
        v
IICP discovery / eligibility / selection
        |
        | selected endpoint + bounded authorization evidence
        v
MCP, A2A, HTTP API, IICP peer binding, or another negotiated execution path
        |
        v
selected provider
```

DNS-AID, Agent URI, DID/VC or an AGNTCY component may contribute candidate,
locator, identity or provenance data. They do not automatically establish
current availability, caller policy compliance or permission to dispatch.

## Trust and privacy comparison

| Question | IICP position | Reviewer consequence |
|---|---|---|
| Must a client trust a directory completely? | No. Discovery and signed route material remain subject to local version, identity, freshness, policy and confidentiality checks. | The public contract must make independently checkable evidence and failure behavior explicit. |
| Does a capability advertisement prove the service works? | No. Advertisements describe claimed effective service behavior; provenance and conformance can strengthen, not guarantee, the claim. | False and stale advertisements remain an abuse case. |
| Does encryption hide a task from the executor? | No. Ordinary CX protects the network/relay path. The selected executor receives plaintext. | Executor-blind privacy requires a separately attested confidential-execution profile. |
| Does a route ticket prove correct execution? | No. It binds a selected route and policy context; it does not prove output quality or honest inference. | Execution evidence and semantic evaluation stay separate. |
| Is same-project parity independent evidence? | No. | External implementations and independently operated conformance runs remain open evidence gates. |

## Where IICP may add distinct value

The current evidence supports further review of four separable mechanisms:

1. effective capabilities describe what the complete serving path exposes,
   rather than what a model or component theoretically supports;
2. mandatory policy and capability constraints are applied before ranking;
3. a directory can select without receiving task content, while the client
   retains final policy checks;
4. a short-lived, audience-bound selection result can authorize direct
   dispatch and support content-minimized correlation.

These are candidate contributions, not proof that a separate protocol is
required. IAIP -02 and AIDIP -02 materially overlap the first three. A
standards discussion should seek convergence or reuse before adding another
general agent task format.

## When not to use IICP

- Use MCP directly when the host already knows the server and needs its tools,
  resources or prompts; no provider-selection layer is necessary.
- Use A2A directly when the client already knows the agent endpoint and needs
  its task, message, artifact or streaming lifecycle.
- Use DNS-AID directly when organization-scoped discovery and endpoint
  authentication are sufficient and current policy-aware selection is local.
- Use an ordinary HTTP API when a fixed service contract and endpoint already
  meet the application requirement.

## Standards-facing conclusion

The defensible first question is not whether to standardize the complete IICP
suite. It is whether independent implementations need shared semantics for:

```text
Intent + required constraints
    -> eligible candidate set
    -> selected provider and execution binding
    -> verifiable, bounded dispatch authorization
```

Native framing, credits, marketplace policy, model-quality prediction,
federation and cooperative inference should remain outside that initial
problem statement unless evidence demonstrates that one is necessary to the
minimal exchange.
