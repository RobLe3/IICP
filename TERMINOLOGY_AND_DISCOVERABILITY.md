# IICP terminology and discoverability map

**Status:** Informative project guidance. This document does not change a
protocol requirement, maturity label, or compatibility claim.

## Preferred identification

Use **Intent-based Inter-agent Communication Protocol (IICP)** on first
reference. The stable descriptive subtitle is:

> A protocol-neutral intent-resolution and execution-selection control plane.

The subtitle describes the control-plane role. It does not mean that IICP
defines every agent task format, identity system, transport, or runtime.
The current mechanism-level boundary is recorded in
[`standards/IICP_PROTOCOL_POSITIONING.md`](standards/IICP_PROTOCOL_POSITIONING.md)
and the dated
[`standards/PROTOCOL_COMPARISON_2026-08-15.md`](standards/PROTOCOL_COMPARISON_2026-08-15.md).

## Term map

| Term people may use | IICP meaning and appropriate use | Do not imply |
| --- | --- | --- |
| Agent discovery | Finding candidate providers from advertised capabilities and constraints. | That discovery alone establishes trust, health, or permission to execute. |
| Intent resolution | Interpreting an intent and constraints to identify eligible execution candidates. | General-purpose semantic reasoning or an agent-planning system. |
| Provider selection | Applying availability, policy, capability, and operational evidence to candidate choice or ranking. | A guarantee of performance or a directory-mediated task payload path. |
| Capability routing | Choosing a route to a provider that advertises a required capability. | That capability advertisement is independently verified in every case. |
| AI mesh | Informal description of a network of participating providers and consumers. Use only in introductory material. | A claim of decentralization, diversity, availability, or independent operation. |
| Agent routing | A broad term for selecting an execution destination. Prefer **intent resolution** or **provider selection** when those are the precise mechanisms. | That IICP forwards task payloads through its directory. |

## Placement guidance

Use the full name and subtitle in repository descriptions, the project README,
standards background, and the website's primary explanatory pages. Use a
precise term from the table in technical specifications and API material.

Website search metadata may use the listed discovery terms when the linked page
explains the corresponding mechanism. It must not add version assertions,
adoption counts, standards status, privacy guarantees, or performance claims
that are not supported by that page's current evidence.

## Boundaries for public prose

- IICP directories select and authorize routes; task payloads are intended to
  travel directly between peers or through an explicitly selected relay.
- IICP can use execution protocols such as MCP or A2A through separate
  bindings; it does not claim to replace their task semantics.
- “Open”, “federated”, “private”, “secure”, “standards-based”, and
  “decentralized” require the qualification and evidence appropriate to the
  page. Do not use them as standalone search labels.
- Keep search-console aggregates and other content-free operational analytics
  private unless a published conclusion is supported by reproducible evidence.

## Maintenance

The public specification repository owns this terminology. The private website
repository owns presentation, metadata, and page-specific implementation.
Website changes should link to this map rather than maintaining another list of
project-defining phrases.
