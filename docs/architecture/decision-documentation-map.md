# Architecture decisions and public documentation

This map explains where a protocol decision should be documented. It prevents
an accepted design decision from remaining visible only in an implementation
repository, and it prevents a proposed decision from being described to users
as released behaviour.

## Sources and audiences

| Source | What it owns | What it does not own |
| --- | --- | --- |
| Versioned specification, schemas, registries, and fixtures | Interoperable protocol meaning and conformance | Product instructions or deployment claims |
| Architecture decisions in this repository | Cross-component boundaries and the reason for them | Evidence that every implementation or deployment has adopted the decision |
| SDK and directory repositories | Released command, API, configuration, and implementation behaviour | New protocol meaning by implementation alone |
| iicp.network documentation | Plain-language explanation and operator guidance | A parallel normative specification |
| Deployment manifests and live evidence | What is running and observable at a stated time | What has merely been published or planned |

Research that materially led to a protocol decision belongs with the public
decision record or its references. Personal development workflows, private
operations, credentials, raw logs, and agent tooling do not.

## Decision coverage

| Decision area | Public architecture authority | Required user-facing explanation |
| --- | --- | --- |
| Intent, capability, and effective service behaviour | [Effective service capabilities](effective-service-capability-semantics.md) and the registries | Explain that intent states the requested operation; capability states what the complete service path can actually expose |
| Directory state, reachability, availability, and eligibility | [Directory state semantics](directory-state-semantics.md) | Explain why a known service may be temporarily unreachable or ineligible without ceasing to exist |
| Task time, delivery time, and caller waiting | [Task time semantics](task-time-semantics.md) | Keep timeout examples explicit about which clock they bound |
| Context ownership and runtime self-description | [Context and service-event ownership](context-and-service-event-ownership.md) | Explain which runtime facts are authoritative and require unknown facts to remain unknown |
| Transport, encoding, profiles, bindings, and environmental independence | [Environmental independence and extension architecture](environmental-independence-and-extension-architecture.md) | Explain that a new transport or environment does not create a new intent or logical task |
| Identifiers and registry governance | [Identifier and registry architecture](identifier-and-registry-architecture.md) | Treat released identifiers as opaque, stable project identifiers without implying IANA assignment |
| Portability and independent continuation | [Portability and non-capture](portability-and-non-capture.md) | Explain how users can choose implementations and operate without a mandatory commercial control plane |
| Node health and third-party operator tooling | [Node observability interfaces](node-observability-interfaces.md) | Distinguish authoritative health, directory-reported state, local observation, and inference |

## Publication rule

Before a public guide describes a decision as available:

1. The decision must be accepted by its stated authority.
2. Required wire or schema changes must appear in the versioned contract.
3. The relevant maintained implementation must expose the behaviour through a
   released interface.
4. Conformance evidence must exist when the behaviour crosses implementations.
5. Deployment-specific language must identify the deployed version and
   verification time instead of inheriting the source release claim.

Proposed decisions may be discussed as direction or research. They must remain
labelled as proposed and must not be converted into setup instructions.

## Review checklist

For each accepted or superseded decision, reviewers should ask:

- Is interoperable meaning present in the specification rather than only an ADR?
- Is the operator-visible consequence explained in the relevant guide?
- Does the guide link to the authority instead of copying unstable details?
- Are published, deployed, adopted, and experimental states kept separate?
- If a later decision replaced this one, are stale examples removed or clearly historical?

