# IICP v1.5 Specification Documents

This directory contains the canonical IICP v1.5 specification split into focused documents.

## Reading order

1. **[iicp-core.md](iicp-core.md)** — Start here. MUST requirements. Wire format, message types, error codes.
2. **[IICP-core-phase1-profile.md](IICP-core-phase1-profile.md)** — Phase 1 field subset for minimal implementations.
3. **[iicp-dir.md](iicp-dir.md)** — IICP-DIR sub-protocol: how to register, heartbeat, discover.
4. **[iicp-semantics.md](iicp-semantics.md)** — Routing, QoS, scoring, retry policy.
5. **[iicp-extensions.md](iicp-extensions.md)** — Billing, reputation, CIP, post-quantum (future).

## All documents

| File | Status | Phase |
|------|--------|-------|
| [iicp-v1.5-overview.md](iicp-v1.5-overview.md) | Draft | — |
| [iicp-core.md](iicp-core.md) | Draft | 1 |
| [iicp-semantics.md](iicp-semantics.md) | Draft | 1 |
| [iicp-extensions.md](iicp-extensions.md) | Draft | 3+ |
| [IICP-core-phase1-profile.md](IICP-core-phase1-profile.md) | Draft signed | 1 |
| [iicp-dir.md](iicp-dir.md) | Draft signed | 1–2 |
| [iicp-mcp-binding.md](iicp-mcp-binding.md) | Draft signed | 2 |
| [node-capability-format.md](node-capability-format.md) | Draft signed | 1 |
| [iicp-billing-extension.md](iicp-billing-extension.md) | Draft signed | 3 |
| [iicp-cbor-wire.md](iicp-cbor-wire.md) | Draft | 3 |
| [conformance-test-suite.md](conformance-test-suite.md) | Draft signed | 1 |
| [validation-methodology.md](validation-methodology.md) | Draft signed | 1 |
| [VERSION](VERSION) | — | — |

## Normative language

All MUST / SHOULD / MAY / MUST NOT in these documents are interpreted per RFC 2119 / BCP 14.

Documents marked "Draft signed" have received Protocol Steward review and are stable for implementation. "Draft" documents are still being revised.
