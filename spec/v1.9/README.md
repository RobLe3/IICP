# IICP Protocol Specification Index

**Current Protocol Suite version**: [`VERSION`](./VERSION) — see the generated
[current-version projection](../../ecosystem/CURRENT_VERSIONS.md) and
[CHANGELOG](../../CHANGELOG.md) for the labeled release axes and history.

This directory contains the normative and informational protocol documents for IICP.

Before interpreting IICP as a replacement for another agent protocol, read the
informative [protocol positioning](../../standards/IICP_PROTOCOL_POSITIONING.md)
and dated [adjacent-protocol comparison](../../standards/PROTOCOL_COMPARISON_2026-08-15.md).
They separate IICP's intent-resolution and provider-selection role from MCP,
A2A, discovery inputs and transports.

---

## Recommended reading order

Start here when you are new to the protocol. Each document builds on the previous ones.

| # | File | What it covers |
|---|------|----------------|
| 1 | [`iicp-core.md`](./iicp-core.md) | **Start here.** Wire format, message types (CALL/RESPONSE/INIT), mandatory fields, error codes (IICP-E001–E033), retry/idempotency rules, QoS hints. |
| 2 | [`iicp-dir.md`](./iicp-dir.md) | Directory sub-protocol — register, heartbeat, discover, probe endpoints; node token auth; observed-IP recording. |
| 3 | [`iicp-semantics.md`](./iicp-semantics.md) | Routing semantics, QoS, node selection, intent URN grammar (including `x.<vendor>` custom namespace). |
| 4 | [`IICP-core-phase1-profile.md`](./IICP-core-phase1-profile.md) | Accepted Phase 1 conformance baseline — the minimal implementation contract. |
| 5 | [`iicp-service-lifecycle-profile.md`](./iicp-service-lifecycle-profile.md) | Proposed optional lifecycle profile — streaming, cancellation, retry, and idempotency. |
| 6 | [`iicp-provider-admission-profile.md`](./iicp-provider-admission-profile.md) | Proposed optional provider-admission profile — readiness, bounded capacity, and deadlines. |
| 7 | [`iicp-confidentiality.md`](./iicp-confidentiality.md) | IICP-CX — key advertisement, payload encryption, keyless-node refusal, relay opacity, and Tier-2 confidentiality targets. |
| 8 | [`iicp-cooperative-inference.md`](./iicp-cooperative-inference.md) | CIP — multi-node cooperative inference (Phase 5). Coordinator/worker roles, HMAC receipt, credit flow, conformance levels. |
| 9 | [`iicp-federated-directory.md`](./iicp-federated-directory.md) | Federated control plane — Genesis Seed, replica sync, Ed25519 event log (Phase 6). |
| 10 | [`iicp-framing.md`](./iicp-framing.md) | Binary framing layer (active draft) — 12-byte frame header, CBOR schemas, version negotiation, HTTP fallback. |

---

## Supporting specifications

| File | What it covers | ADRs |
|------|----------------|------|
| [`iicp-extensions.md`](./iicp-extensions.md) | Billing, reputation, and sub-protocol bindings (umbrella doc) | ADR-008 |
| [`iicp-billing-extension.md`](./iicp-billing-extension.md) | Declarative pricing, credit cost multiplier | ADR-007, ADR-008, ADR-019 |
| [`iicp-telemetry.md`](./iicp-telemetry.md) | Telemetry trust model — proxy token auth, sybil quorum, outlier weighting | ADR-012, ADR-023 |
| [`iicp-mcp-binding.md`](./iicp-mcp-binding.md) | IICP↔MCP protocol bridge binding | ADR-007, ADR-009 |
| [`iicp-cbor-wire.md`](./iicp-cbor-wire.md) | CBOR wire format reference (Phase 4+) | — |
| [`iicp-identity-slot.md`](./iicp-identity-slot.md) | Directory-anchored operator identity slot and DID binding | ADR-030, ADR-034 |
| [`iicp-deployment-provenance.md`](./iicp-deployment-provenance.md) | Signed mapping from a running directory to its release and artifact | — |
| [`node-capability-format.md`](./node-capability-format.md) | Node capability envelope schema | ADR-007 |
| [`iicp-recognition.md`](./iicp-recognition.md) | Operator recognition / gamification (draft skeleton — PS review pending) | ADR-030 |

---

## Testing and methodology

| File | What it covers |
|------|----------------|
| [`conformance-test-suite.md`](./conformance-test-suite.md) | **Canonical test IDs** (DIR-REG-*, DIR-DISC-*, PROXY-ROUTE-*, etc.) — use this to map spec requirements to test files. |
| [`conformance-badges.md`](./conformance-badges.md) | Self-attested conformance badge system (S.14) |
| [`validation-methodology.md`](./validation-methodology.md) | How conformance is measured; k6 latency targets; REACH probe descriptions |

Machine-readable policy fixtures shared by implementations live one level above this versioned
suite: [`intent-risk-taxonomy.json`](../intent-risk-taxonomy.json) and
[`mcp-tool-risk-taxonomy.json`](../mcp-tool-risk-taxonomy.json).

---

## Spec-to-ADR cross-reference

Which ADR is authoritative for a given spec section:

| Spec file | Key sections | Authoritative ADR(s) |
|-----------|-------------|----------------------|
| `iicp-core.md` | Wire format, retry | ADR-002 (JSON/HTTPS), ADR-010 (idempotency) |
| `iicp-core.md` | Intent URN format | ADR-007 |
| `iicp-core.md` | Error codes | ADR-002 + spec §7 |
| `iicp-dir.md` | Node auth (node_token) | ADR-006 |
| `iicp-dir.md` | Discovery scoring | ADR-008 |
| `iicp-dir.md` | Event log / replica sync | ADR-013 |
| `iicp-dir.md` | OTel trace spans | ADR-014 |
| `iicp-dir.md` | Declarative pricing | ADR-019 |
| `iicp-semantics.md` | Node selection, client scoring | ADR-008, ADR-024 |
| `iicp-confidentiality.md` | Payload confidentiality and CX keys | ADR-001, ADR-003, privacy-first track (#360) |
| `iicp-cooperative-inference.md` | CIP scoring, reputation | ADR-012, ADR-026 |
| `iicp-cooperative-inference.md` | Credit substrate | ADR-019 |
| `iicp-federated-directory.md` | Federated control plane | ADR-013 |
| `iicp-telemetry.md` | Telemetry trust | ADR-014, ADR-023 |
| `iicp-framing.md` | Binary framing, CBOR | ADR-002 (Phase 1+), ADR-024 |
| `iicp-billing-extension.md` | Pricing declaration | ADR-019 |

The public specifications and architecture records in `docs/architecture/`
state the current decisions. Historical implementation ADR identifiers in the
table above are provenance labels; they are not required to interpret the
normative text.

---

## Spec status legend

| Status | Meaning |
|--------|---------|
| `Project-normative` | Binding for implementations claiming conformance to the named suite release |
| `Stable` | Project-normative behavior protected by the compatibility and deprecation policy |
| `Active draft` | Reviewed work under development; not required unless a released profile incorporates it |
| `Experimental` | Research or implementation work without enough interoperability and operational evidence for promotion |
| `Externally ratified` | Approved by the named external standards body and backed by a public reference |

See [`SPEC_STATUS.md`](../../SPEC_STATUS.md) for the authoritative definitions.
