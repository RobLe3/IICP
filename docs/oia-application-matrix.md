# IICP and the Open Intelligence Architecture Application Matrix

**Status:** submission evidence for committee review, 21 August 2026  
**Submission:** [agenticsorg/community-projects#51](https://github.com/agenticsorg/community-projects/issues/51)

The Open Intelligence Architecture (OIA) Application Matrix currently places
IICP in its pending-review band using an automated repository scan. That scan is
an intake signal, not a code audit or endorsement. This page gives a reviewer
the narrower, evidence-backed interpretation of IICP's place in the matrix.

## Intended placement

IICP is cross-layer infrastructure for resolving a requested intent into a
currently eligible execution provider. Its centre of gravity is OIA **L7,
Orchestration & Workflow**: discovery, eligibility, selection and route
authority happen before an execution binding such as HTTP, MCP or A2A performs
the task.

IICP also has bounded supporting presence in:

| OIA layer | IICP responsibility | Evidence |
| --- | --- | --- |
| L2, Sovereign Infrastructure | Self-hosted public, private and local control-plane designs without a mandatory commercial service | [Portability and non-capture](architecture/portability-and-non-capture.md), [restricted trust-domain Profile](../research/pre-normative-profiles/restricted-trust-domain-v0.md) |
| L3, Agent Data Substrate | Provider, capability, health and routing-evidence records; task payloads remain outside the directory | [Directory state semantics](architecture/directory-state-semantics.md), [privacy threat model](security/privacy-adversary-and-trust-model.md) |
| L5, Inference & Retrieval | Selection among eligible inference or retrieval providers; IICP does not define model internals | [Effective service capabilities](architecture/effective-service-capability-semantics.md), [protocol positioning](../standards/IICP_PROTOCOL_POSITIONING.md) |
| L7, Orchestration & Workflow | Intent resolution, policy-aware eligibility, provider selection, route authorization and binding handoff | [Core specification](../spec/v1.9/iicp-core.md), [mechanism comparison](../standards/PROTOCOL_COMPARISON_2026-08-15.md) |
| L8, Continuity Fabric | Signed events, receipts, provenance and conformance evidence with explicit claim boundaries | [Conformance suite](../spec/v1.9/conformance-test-suite.md), [public evidence access](public-evidence-access.md) |

This mapping does not claim that IICP owns each layer. Models, agent runtimes,
identity systems, transports and execution protocols remain independent and can
be combined with IICP through documented boundaries.

## Cross-cutting spans

- **Security and identity:** authenticate actors and validate route authority
  without treating identity, membership, dispatch authorization and execution
  outcome as one claim.
- **Sovereignty:** preserve self-hosting, directory choice and local policy;
  public IICP infrastructure is not a mandatory dependency of the protocol.
- **Auditability and provenance:** distinguish advertised, verified, deployed
  and observed facts and attach bounded evidence to claims.

## Review evidence

The repository already provides the artifacts normally needed for a technical
review:

- public issue tracking and contribution rules;
- versioned specifications, schemas, registries and conformance fixtures;
- recorded architecture decisions under `docs/architecture/`, `research/strategic/`
  and `standards/`;
- release-integrity manifests and independently runnable conformance tooling;
- diagrams embedded in the relevant architecture and specification documents.

These protocol artifacts are the applicable review evidence. The project will
not create a product-requirements document, rename decisions or add a decorative
infographic solely to influence an automated qualification heuristic. If the
committee identifies a substantive missing artifact, it should be added under
the repository's normal specification and evidence process.

## Maturity boundary

IICP is a project-normative beta suite. Its IETF engagement is a request for
scope and venue guidance, not standards adoption. The public directory remains
the PHP Genesis deployment; the Rust directory is an operator preview. OIA
pending review does not change those facts or establish protocol conformance.
