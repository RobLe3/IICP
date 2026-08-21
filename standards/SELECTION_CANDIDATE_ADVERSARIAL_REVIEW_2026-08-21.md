# Adversarial review of the IICP selection candidate

**Evidence date:** 2026-08-21  
**Disposition:** **ready for review**. The candidate has not been submitted,
adopted, endorsed or externally ratified.

This review asks whether IICP's narrow selection and eligibility function is a
necessary interoperability boundary, whether it duplicates adjacent work, and
whether its trust claims survive a hostile reading. It reviews the candidate
described in the [problem statement](SELECTION_ELIGIBILITY_PROBLEM_STATEMENT.md)
and [trust model](SELECTION_TRUST_AND_REVALIDATION.md), not the complete IICP
suite.

## Method and severity

The review compared current project artifacts with primary specifications and
repositories for MCP, A2A, IAIP, AIDIP, ANP, AGNTCY and DRISAC. Individual
Internet-Drafts are proposals, not IETF consensus or standards. External work
is used to challenge IICP's boundaries; it is not an implementation dependency.

- **P0:** the candidate is unsafe or internally contradictory and must not be
  reviewed externally.
- **P1:** the architecture or claimed scope is materially incomplete.
- **P2:** evidence, maturity or presentation work remains, but the bounded
  architecture can be reviewed.

No composite score or protocol winner is assigned. The protocols own different
parts of the system and can be composed.

## Adjacent-work challenge

| Work | Primary-source responsibility | Adversarial question | Disposition |
|---|---|---|---|
| [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) | Host/server integration for tools, resources, prompts and negotiated extensions | Why not let the MCP host choose a known server? | **Boundary retained.** A host that already knows the server does not need IICP. The candidate is limited to selection among independently advertised providers before MCP execution. It must not duplicate MCP tool or task semantics. |
| [A2A 1.0](https://a2a-protocol.org/latest/specification/) | Agent descriptions, messages, tasks, artifacts, streaming and execution bindings | Why add another agent task protocol? | **Boundary retained.** IICP may select an A2A endpoint, but A2A owns the subsequent task lifecycle. The selection candidate excludes a general task format. |
| [IAIP -02](https://datatracker.ietf.org/doc/draft-sz-dmsc-iaip/) | Gateway registration, capability validation, intent resolution, matching, ranking, routing and forwarding | Is IICP merely a differently named gateway? | **Material overlap.** Any standards discussion must seek convergence and vocabulary reuse. IICP's narrower candidate keeps task payloads out of the directory by default and leaves execution to a binding, but neither distinction establishes novelty or protocol necessity by itself. |
| [AIDIP -02](https://datatracker.ietf.org/doc/draft-cui-ai-agent-discovery-invocation/) | Agent metadata, capability and intent discovery, ranked candidates and a REST invocation interface | Does AIDIP already supply discovery, selection and invocation? | **Material overlap.** IICP must not claim ownership or chronology-based priority for intent selection. Its reviewable delta is effective end-to-end capability, hard eligibility before ranking, bounded route authority and client revalidation. These are candidate contributions, not proof that a separate protocol is required. |
| [ANP 1.1](https://agent-network-protocol.com/specs/) | Agent description, identity, discovery, messaging, encryption and federation profiles | Why not use a broader peer-network suite? | **Composition possible.** ANP descriptors or messaging can be mapped without making ANP an IICP substrate. IICP should remain useful only where its eligibility decision is independently interoperable. |
| [AGNTCY](https://docs.agntcy.org/) | A suite spanning descriptions, directory, identity, secure messaging and observability | Does a mature infrastructure suite make IICP redundant? | **Component-level crosswalk required.** AGNTCY is not one wire protocol. IICP should reuse or bind to suitable components rather than recreate identity, messaging or observability. Its narrow claim remains current policy-aware eligibility and route handoff. |
| [DRISAC -01](https://datatracker.ietf.org/doc/draft-wang-dmsc-drisac/) | Hierarchical capability classification, domain aggregation, synchronization and capability-aware forwarding | Can IICP's directory model scale beyond full provider state? | **P2 limitation recorded.** IICP has bounded historical federation state, not evidence of Internet-scale current-state aggregation. Hierarchy, summaries and sharding remain research; they are outside this candidate and must not be implied by it. |

The [dated comparison](PROTOCOL_COMPARISON_2026-08-15.md) records chronology
and evidence maturity. Age does not establish invention, influence, fitness or
standards priority. AIDIP's discovery work predates IICP; IICP's first public
intent-routing draft predates IAIP and AIDIP's later intent-selection additions;
IICP's explicit provider-eligibility vocabulary came later. Public material
must retain those qualified statements.

## Objections and dispositions

### 1. A local gateway can do all of this

**Objection:** selection is application policy, not a protocol problem.

**Disposition:** valid unless independently maintained clients, directories and
providers need common identifiers, effective-capability semantics, refusal,
freshness, route authority and safe handoff. The problem statement now makes
that condition explicit. Deployments with a fixed endpoint should use their
ordinary gateway or API. **No unresolved P1; external demand remains P2.**

### 2. Discovery output could be mistaken for authorization

**Objection:** a malicious or compromised directory could return an attacker,
stale evidence or an unauthorized substitute.

**Disposition:** the trust document assigns separate verifiers and lifetimes to
advertisements, eligibility, membership, route authority, endpoint identity and
outcomes. Clients revalidate non-weakenable policy and freshness; endpoints
authenticate and authorize independently. A directory can still suppress or
bias candidates, and revalidation cannot detect every omission. That limitation
is explicit. **Resolved as an architectural P1; deployment trust remains local.**

### 3. One credential or score will accumulate unrelated authority

**Objection:** membership, identity, dispatch, reputation and proof of execution
could collapse into one convenient but unsafe artifact. Likewise, a composite
provider score can hide whether a penalty came from latency, failure, integrity
or quality.

**Disposition:** artifacts stay purpose-specific and selection inputs remain
labelled. Membership does not grant execution. A route ticket does not prove an
outcome. `outcome-v2` separates successful execution from latency, health,
semantic-quality and integrity evidence. Ranking formulas remain deployment
policy rather than a universal protocol score. **No unresolved P1.**

### 4. Intent and capability are too vague to interoperate

**Objection:** natural-language intent or vendor capability labels cannot
produce deterministic matching.

**Disposition:** the candidate uses exact versioned Intent identifiers,
effective service-path capabilities, required versus preferred requirements,
quantitative limits and bounded refusal. It does not standardize natural-
language interpretation or model marketing labels. Namespace governance and a
possible future IANA strategy remain separate standards-readiness work. **No
candidate P1; registry governance remains P2 before submission.**

### 5. Native framing makes this another transport protocol

**Objection:** a new TCP frame and provisional port obscure the selection
problem and duplicate HTTP, QUIC, MCP or A2A.

**Disposition:** the [transport decision](TRANSPORT_BINDING_AND_PORT_DECISION_2026-08-21.md)
keeps native framing optional and outside the candidate. No IANA port, UDP,
QUIC or ALPN request is proposed. **Resolved.**

### 6. Privacy claims exceed the architecture

**Objection:** keeping task content out of a directory does not provide private
inference.

**Disposition:** the candidate claims only a payload-minimized control-plane
boundary. The chosen executor receives the task it executes. Metadata privacy,
traffic analysis, anonymity and executor-blind inference are not solved by the
selection exchange. **Resolved by claim narrowing.**

### 7. Federation and global scale are unproven

**Objection:** a protocol pitched for general discovery must prove multi-root
operation, conflict handling and scale.

**Disposition:** federation topology is excluded from the initial candidate.
Current IICP evidence does not support an Internet-scale claim. Scaling research
can later change directory deployment or federation advertisements without
changing the bounded selection semantics, but that remains to be demonstrated.
**P2 limitation; no broad scale claim permitted.**

### 8. Same-project conformance is not interoperability evidence

**Objection:** cross-language SDKs and project fixtures remain under one project
authority.

**Disposition:** accepted. The standalone conformance runner enables outside
evidence but does not create it. The independent node monitor is adoption and
integration evidence, not a clean-room protocol implementation. Independent
implementation remains a standards-maturity gate. **P2, blocks a maturity
claim but not architecture review.**

### 9. Governance and identifiers are not externally administered

**Objection:** founder-led release authority and unregistered `urn:iicp:` names
are not ready for an external standards lifecycle.

**Disposition:** accepted. Released identifiers are stable project identifiers,
not claimed IANA assignments. Governance, registry policy and identifier
migration need explicit disposition before submission or external transfer.
**P2 for internal review; submission remains unauthorized.**

### 10. Published, deployed and adopted behavior can drift

**Objection:** a reviewer could assess source semantics that are not active on
the public directory or used by current nodes.

**Disposition:** the review bundle labels project-normative, implemented,
published, deployed and independently evidenced states separately. A release is
not proof of deployment or adoption. Operational claims require a dated
deployment manifest or live evidence. **No architectural P1; deployment truth
remains an operational gate.**

## Residual review gates

The bounded architecture has no unresolved P0 or P1 objection identified by
this review. The following issues remain material before a standards submission
or maturity claim:

1. an independent clean-room implementation and conformance result;
2. multi-person governance and release-authority evidence;
3. identifier and registry policy, including the status of `urn:iicp:`;
4. federation and large-population state research before any scale claim;
5. dated deployed-version evidence where public runtime behavior is discussed.

These gates do not authorize a generic follow-up message, Internet-Draft, IANA
request, protocol release or production deployment.

## Final disposition

The defensible candidate is not “inter-agent communication” in full. It is the
narrow, protocol-neutral decision between a described need and a currently
eligible execution provider, followed by explicit endpoint authentication and
execution through another binding. Direct overlap with IAIP and AIDIP is real
and must be presented candidly. MCP, A2A, ANP and AGNTCY may own adjacent or
downstream functions. DRISAC exposes an unresolved scale question rather than a
feature to copy.

The candidate is **ready for review** as a bounded architecture question. It is
not ready to be described as necessary by consensus, independently proven,
submitted, adopted, endorsed or externally standardized.
