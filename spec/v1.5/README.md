# IICP Protocol Specification Index

**Current Protocol Suite version**: see [`VERSION`](./VERSION) — `v1.9.0` as of 2026-05-30.

> **About this directory name**: `spec/v1.5/` is a **frozen path label** from when the
> monolithic v1.4.2 Internet-Draft was split into modular sub-protocol documents. The path
> will not change as the suite version advances — only the `VERSION` file and the `CHANGELOG`
> in the repo root track the current version. Wire compatibility with v1.4.2 is maintained.

This directory contains the normative and informational protocol documents for IICP.

---

## Recommended reading order

Start here when you are new to the protocol. Each document builds on the previous ones.

| # | File | What it covers |
|---|------|----------------|
| 1 | [`iicp-core.md`](./iicp-core.md) | **Start here.** Wire format, message types (CALL/RESPONSE/INIT), mandatory fields, error codes (IICP-E001–E033), retry/idempotency rules, QoS hints. |
| 2 | [`iicp-dir.md`](./iicp-dir.md) | Directory sub-protocol — register, heartbeat, discover, probe endpoints; node token auth; observed-IP recording. |
| 3 | [`iicp-semantics.md`](./iicp-semantics.md) | Routing semantics, QoS, node selection, intent URN grammar (including `x.<vendor>` custom namespace). |
| 4 | [`IICP-core-phase1-profile.md`](./IICP-core-phase1-profile.md) | Accepted Phase 1 conformance baseline — the minimal implementation contract. |
| 5 | [`iicp-cooperative-inference.md`](./iicp-cooperative-inference.md) | CIP — multi-node cooperative inference (Phase 5). Coordinator/worker roles, HMAC receipt, credit flow, conformance levels. |
| 6 | [`iicp-federated-directory.md`](./iicp-federated-directory.md) | Federated control plane — Genesis Seed, replica sync, Ed25519 event log (Phase 6). |
| 7 | [`iicp-framing.md`](./iicp-framing.md) | Binary framing layer (draft) — 11-byte frame header, CBOR schemas, version negotiation, HTTP fallback. NOT YET RATIFIED. |

---

## Supporting specifications

| File | What it covers | ADRs |
|------|----------------|------|
| [`iicp-extensions.md`](./iicp-extensions.md) | Billing, reputation, and sub-protocol bindings (umbrella doc) | ADR-008 |
| [`iicp-billing-extension.md`](./iicp-billing-extension.md) | Declarative pricing, credit cost multiplier | ADR-007, ADR-008, ADR-019 |
| [`iicp-telemetry.md`](./iicp-telemetry.md) | Telemetry trust model — proxy token auth, sybil quorum, outlier weighting | ADR-012, ADR-023 |
| [`iicp-mcp-binding.md`](./iicp-mcp-binding.md) | IICP↔MCP protocol bridge binding | ADR-007, ADR-009 |
| [`iicp-cbor-wire.md`](./iicp-cbor-wire.md) | CBOR wire format reference (Phase 4+) | — |
| [`node-capability-format.md`](./node-capability-format.md) | Node capability envelope schema | ADR-007 |
| [`iicp-recognition.md`](./iicp-recognition.md) | Operator recognition / gamification (draft skeleton — PS review pending) | ADR-030 |

---

## Testing and methodology

| File | What it covers |
|------|----------------|
| [`conformance-test-suite.md`](./conformance-test-suite.md) | **Canonical test IDs** (DIR-REG-*, DIR-DISC-*, PROXY-ROUTE-*, etc.) — use this to map spec requirements to test files. |
| [`conformance-badges.md`](./conformance-badges.md) | Self-attested conformance badge system (S.14) |
| [`validation-methodology.md`](./validation-methodology.md) | How conformance is measured; k6 latency targets; REACH probe descriptions |

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
| `iicp-cooperative-inference.md` | CIP scoring, reputation | ADR-012, ADR-026 |
| `iicp-cooperative-inference.md` | Credit substrate | ADR-019 |
| `iicp-federated-directory.md` | Federated control plane | ADR-013 |
| `iicp-telemetry.md` | Telemetry trust | ADR-014, ADR-023 |
| `iicp-framing.md` | Binary framing, CBOR | ADR-002 (Phase 1+), ADR-024 |
| `iicp-billing-extension.md` | Pricing declaration | ADR-019 |

For the full ADR list, see [`project/decisions/README.md`](../project/decisions/README.md).

---

## Spec status legend

| Status | Meaning |
|--------|---------|
| `accepted` | Ratified — implementations MUST conform |
| `draft` | Active and normative within the project; not yet externally ratified |
| `Draft (skeleton)` | Structure committed; normative bodies pending review |
| `NOT YET RATIFIED` | Experimental — do not implement without maintainer sign-off |
