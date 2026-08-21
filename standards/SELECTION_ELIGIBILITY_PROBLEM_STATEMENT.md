# IICP selection and eligibility problem statement

Status: **project architecture candidate for review**. This document is not an
Internet-Draft, an IETF submission, an IANA request or an externally ratified
standard. It does not change the stable IICP wire baseline.

## The interoperability problem

An application that can use several AI services needs to decide which service
may handle a request now. The answer can depend on the requested operation,
effective service capabilities, current availability, caller policy, region,
confidentiality requirements and route authorization. Today that decision is
often embedded in one application, gateway or provider platform. Independent
clients, directories and providers then lack a common way to describe the need,
reject an ineligible candidate and hand an authorized selection to an execution
interface.

IICP isolates that decision as an application-layer control-plane function. A
caller identifies the semantic operation and its requirements. A directory or
other resolver returns only candidates that satisfy its current eligibility
rules. The client applies its own non-weakenable policy, selects an authorized
candidate or refuses, authenticates the selected endpoint, and invokes it
through a supported binding.

The narrow sequence is:

```text
intent and requirements
        ↓
candidate discovery
        ↓
directory eligibility filtering
        ↓
client policy and selection, or refusal
        ↓
route authority and endpoint authentication
        ↓
execution through HTTP, MCP, A2A, native framing or another binding
```

Discovery does not authenticate the eventual endpoint. Eligibility does not
grant task authority. Selection does not prove execution. The consumer must
revalidate evidence whose freshness or authority matters before dispatch.

## Actors and decisions

| Actor | Interoperable responsibility | Local or deployment responsibility |
|---|---|---|
| Caller/application | State an Intent and required constraints; handle a bounded refusal | Decide business purpose, user consent and application policy |
| Provider | Advertise the effective capability exposed by the complete service path | Choose model, runtime, hardware and internal implementation |
| Directory/resolver | Filter current advertisements under declared eligibility rules; return a redacted candidate or authorized route | Choose scoring implementation, storage and deployment topology |
| Client | Preserve hard eligibility gates, apply local policy, select only where authorized, authenticate and dispatch | Choose preferences and application-specific ranking within the eligible set |
| Execution endpoint | Authenticate the caller or route authority and execute the selected operation | Implement HTTP, MCP, A2A, native framing or another supported binding |

A restricted trust-domain membership assertion can be one eligibility input. It
is not endpoint authentication, a dispatch ticket, reputation or proof of a
completed action.

## Minimum shared information

Independent implementations need consistent meaning for only a bounded set of
information:

- a stable, versioned Intent identifier naming the requested operation;
- required capabilities, quantitative constraints and policy requirements;
- effective provider capability advertisements, including freshness and
  provenance where required by policy;
- candidate identity references and safe route or binding metadata;
- current eligibility or a bounded refusal reason;
- the authority and lifetime of a route ticket or equivalent dispatch decision;
- version and required-Profile negotiation needed to fail safely;
- correlation identifiers that distinguish the logical task from delivery and
  execution attempts.

The directory does not need the task payload to perform this function. The
selected executor receives the task it executes and can read plaintext made
available to its runtime unless a separately supported confidentiality mechanism
provides a stronger property.

## Rules that require common meaning

The following rules affect interoperability rather than one implementation's
quality:

1. Intent identifiers compare according to the published registry and extension
   rules.
2. Unknown or unsupported required capabilities and Profiles make a candidate
   ineligible; unavailable preferences do not.
3. Hard authorization, policy, confidentiality and capability gates run before
   ranking. A client cannot restore an ineligible provider.
4. Directory scores and local selection values remain distinguishable.
5. A single-route ticket does not authorize substitution of another endpoint.
6. Stale, expired, revoked or wrong-scope evidence cannot authorize dispatch.
7. Failure to find an eligible candidate produces a bounded refusal rather than
   an unauthorized fallback.
8. The selected endpoint performs its own authentication and authorization
   checks before execution.

These rules are already represented across the current IICP semantics,
directory contract, effective-capability decision and restricted-domain work.
This document collects their narrow architectural purpose; it does not silently
promote pre-normative profiles.

## What remains outside the candidate

The selection candidate does not standardize:

- model architecture, prompts, reasoning or benchmark choice;
- ranking formulas, learned routers or a universal composite score;
- pricing, credits, marketplaces or provider business terms;
- agent sessions, tool semantics or execution-protocol internals;
- HTTP, QUIC, MCP, A2A or native framing as the definition of an Intent;
- federation topology, cooperative inference or enterprise orchestration;
- identity issuance, general-purpose PKI or a universal credential;
- executor-blind inference, anonymity or legal compliance certification.

Those concerns may supply inputs, bindings or deployment policy. They do not
need to become part of the narrow selection exchange.

## Why an application-local gateway is not enough

A local gateway can select providers for one application without a protocol.
Shared rules become useful when independently maintained clients, directories
and providers must agree on identifiers, required capabilities, refusal,
freshness, route authority and safe handoff. If deployments do not need that
cross-implementation agreement, they can keep the decision local. IICP does not
require every AI invocation to use a directory.

The standards question is therefore bounded: **do independent implementations
need common semantics for resolving a described AI workload into a currently
eligible, authorized execution provider?** The reviewer bundle must answer that
question before broader IICP features are considered.

## Current public sources

- [`iicp-semantics.md`](../spec/v1.9/iicp-semantics.md), sections 1 and 3:
  Intent matching, non-overridable eligibility gates and client selection.
- [`iicp-dir.md`](../spec/v1.9/iicp-dir.md), sections 3.2a and 3.7:
  current eligibility, redacted discovery and ticketed dispatch.
- [Effective service capability semantics](../docs/architecture/effective-service-capability-semantics.md):
  required, preferred, limit, policy and provenance distinctions.
- [Directory state semantics](../docs/architecture/directory-state-semantics.md):
  identity, advertisement, reachability, availability and dispatch eligibility.
- [Environmental independence and extension architecture](../docs/architecture/environmental-independence-and-extension-architecture.md):
  Core, Profile, Binding and Registry ownership.
- [Privacy adversary and trust model](../docs/security/privacy-adversary-and-trust-model.md):
  directory and executor visibility boundaries.
- [Protocol comparison](PROTOCOL_COMPARISON_2026-08-15.md): dated overlap and
  maturity evidence for adjacent work.
