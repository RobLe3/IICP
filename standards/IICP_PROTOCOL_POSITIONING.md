# IICP protocol positioning for reviewers

**Evidence date:** 2026-08-15  
**Status:** informative project material; not an IETF submission or endorsement

## The narrow problem

An application may know the work it needs without knowing which current
provider may perform it. The interoperable decision is not only discovery. It
can require a shared description of the requested operation, effective
capabilities, mandatory constraints, policy eligibility, current operational
state and an authorized route to the selected provider.

IICP's narrow proposed role is **intent resolution and provider eligibility /
selection**:

```text
describe need
    -> discover candidates
    -> verify evidence and apply policy
    -> select an eligible provider
    -> authorize a route
    -> execute through a negotiated binding
```

The directory is a control plane. It need not receive the task payload. The
selected provider executes the task directly through IICP framing, HTTP, an
OpenAI-compatible API, MCP, A2A or another supported binding.

## What IICP does not replace

- **MCP** supplies an integration protocol for context, resources, prompts,
  tools and optional task-like extensions.
- **A2A** supplies agent discovery objects and a task/message lifecycle with
  streaming and several protocol bindings.
- **DNS-AID and related discovery work** can publish endpoints, protocol
  metadata and capability-document references.
- **HTTP, QUIC, WebSocket and gRPC** carry protocol exchanges.
- **OAuth, TLS, DID/VC and related mechanisms** supply reusable security or
  identity components.

IICP can consume or bind to those mechanisms. It should not reproduce their
semantics in its Core.

## Where the overlap is real

Current individual Internet-Drafts such as IAIP and AIDIP also cover
capability advertisement, intent-aware discovery, candidate matching and
selection. This is direct overlap, not a naming difference. The question for
review is whether IICP's combination of effective service capabilities,
caller-visible policy eligibility, content-minimized directory operation and
short-lived dispatch authorization forms a useful separable contract, or
whether those parts should converge with adjacent work.

## The smallest interoperability claim

Independent implementations would need to agree on:

1. stable Intent and capability identifiers;
2. required versus optional constraints;
3. capability advertisement and freshness semantics;
4. eligibility and refusal semantics;
5. selection-result and route-authorization semantics;
6. version and extension negotiation;
7. structured errors and content-minimized correlation evidence.

Ranking algorithms, commercial terms, model architecture, marketplace policy
and the internal reasoning of a provider are not part of this minimum.

## Trust boundary

Discovery is information, not permission to execute. A client must retain its
own policy and reject a candidate when required identity, freshness,
confidentiality or authorization evidence is absent. Signed advertisements and
route tickets reduce substitution and replay risks; they do not prove model
quality, honest execution or executor-blind privacy. A remote provider can read
the task it executes unless a separately verified confidential-execution
profile applies.

## Current evidence and limits

IICP publishes a specification suite, two directory implementations, three
SDK families, a browser implementation, fixtures and a conformance runner.
Most are maintained by the same project. Their agreement is parity evidence,
not independent interoperability or standards adoption. The native peer draft
is an unsubmitted individual-draft candidate. `urn:iicp:` identifiers and port
9484 have no IANA assignment.

For the mechanism-level comparison and primary sources, read
[`PROTOCOL_COMPARISON_2026-08-15.md`](PROTOCOL_COMPARISON_2026-08-15.md). The
same dated facts are available as
[`protocol-comparison-v1.json`](protocol-comparison-v1.json).

