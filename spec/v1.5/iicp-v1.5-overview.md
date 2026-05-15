# IICP v1.5 — Draft Specification

**Version**: 1.5.0-draft
**Date**: 2026-05-15
**Status**: draft
**Issue**: #18 (S.6)
**Authority**: Protocol Steward
**Supersedes**: IICP_draft_1.4.2.txt
**Relation**: iicp-core.md, iicp-semantics.md, iicp-extensions.md

---

## Abstract

IICP (Intent-based Inter-agent Communication Protocol) v1.5 reorganises the v1.4.2
specification into three focused canonical documents and adds formally specified
sub-protocols for the directory service, MCP binding, node capability format, and
billing extension. The wire format is unchanged; v1.5 is fully backward compatible
with any v1.4.x implementation.

---

## 1. What Changed in v1.5

### 1.1 Spec reorganisation (S.5)

v1.4.2 was a single large Internet-Draft. v1.5 splits it into three canonical
documents with clear scope boundaries:

| Document | Scope | Normative level |
|----------|-------|----------------|
| `spec/iicp-core.md` | Wire format, message types, field requirements, error codes | MUST only |
| `spec/iicp-semantics.md` | Intent routing, QoS, node scoring, retry, circuit breaker | SHOULD / MAY |
| `spec/iicp-extensions.md` | Billing, reputation, MCP binding, CIP, post-quantum | MAY / future |

**Compatibility**: No wire format changes. Any v1.4.x implementation is
automatically v1.5 conformant if it satisfies the MUST requirements in
`iicp-core.md`.

### 1.2 New sub-protocol specifications

The following sub-protocol documents are new in v1.5:

| Document | Fills gap | Phase |
|----------|-----------|-------|
| `iicp-dir.md` (IICP-DIR) | GAP-1: directory sub-protocol | 1 |
| `iicp-mcp-binding.md` | GAP-3: MCP ↔ IICP translation | 2 |
| `node-capability-format.md` | GAP-4: capability object schema | 1 |
| `iicp-billing-extension.md` | Credits / billing fields | 3 |
| `validation-methodology.md` | Performance claim disclosure | 1 |
| `IICP-core-phase1-profile.md` | Phase 1 field subset | 1 |
| `conformance-test-suite.md` | Machine-verifiable test IDs | 1 |

### 1.3 What is NOT changing in v1.5

- Message opcodes (INIT, ACK, CALL, RESPONSE, PING, PONG, CLOSE, etc.)
- Intent URN format (`urn:iicp:intent:<domain>:<action>:v<N>`)
- Header field names
- Error code semantics
- Phase 1 conformance requirements (unchanged from `IICP-core-phase1-profile.md`)

---

## 2. Conformance in v1.5

### 2.1 Core conformance

A v1.5 conformant implementation MUST satisfy all requirements in `iicp-core.md`.
The machine-readable checklist is in `conformance-test-suite.md`.

### 2.2 Semantic conformance

A v1.5 semantically conformant implementation additionally satisfies the SHOULD
requirements in `iicp-semantics.md`. This is RECOMMENDED for production nodes
but not required for basic interoperability.

### 2.3 Extension conformance

Extensions (`iicp-extensions.md`) are optional. An implementation that supports
an extension MUST satisfy the MUST requirements within that extension section.
Partial extension support is permitted where extensions are independent.

### 2.4 Phase gating

Conformance claims MUST specify the phase:

```
IICP v1.5 Phase 1 Core Conformant
IICP v1.5 Phase 2 Directory Conformant
IICP v1.5 Phase 3 Billing Extension Conformant
```

---

## 3. Document Map

```
IICP v1.5
├── Core (MUST)
│   └── spec/iicp-core.md
│       → Phase 1 field subset: spec/IICP-core-phase1-profile.md
│       → Test suite: spec/conformance-test-suite.md
│
├── Semantics (SHOULD)
│   └── spec/iicp-semantics.md
│       → Scoring formula: project/ARCHITECTURE.md §ADR-008
│       → Retry policy: project/RELIABILITY.md §Retry
│
├── Sub-protocols
│   ├── spec/iicp-dir.md        (IICP-DIR — directory)
│   └── spec/iicp-mcp-binding.md (MCP ↔ IICP)
│
├── Formats
│   └── spec/node-capability-format.md
│
└── Extensions (MAY)
    ├── spec/iicp-billing-extension.md  (Phase 3)
    └── spec/iicp-extensions.md         (billing + reputation + CIP + PQ)
```

---

## 4. Protocol Version Header

Implementations SHOULD include the following header in IICP messages to
declare the protocol version in use:

```
X-IICP-Version: 1.5
```

Older implementations not sending this header are assumed to be v1.4.x.
v1.5 nodes SHOULD accept messages without this header and treat them as v1.4.x.

---

## 5. Migration from v1.4.2

No migration is required. v1.5 is a reorganisation and specification completion
of v1.4.2. The implementation changes are:

1. **Directory nodes**: No changes required. Phase 1 field set unchanged.
2. **Adapter nodes**: No changes required. Task contract unchanged.
3. **Proxy clients**: No changes required. Discovery API unchanged.
4. **Rust nodes**: No changes required. Execution contract unchanged.

If an implementation was conformant with `IICP-core-phase1-profile.md v1.0.0`,
it is conformant with IICP v1.5 Phase 1 Core.

---

## 6. Version History

| Version | Date | Key changes |
|---------|------|-------------|
| 1.4.2 | 2025-06 | Harmonised error handling, QuDAG transport references |
| 1.5.0-draft | 2026-05-15 | Spec split (S.5): iicp-core + iicp-semantics + iicp-extensions; 7 sub-protocol documents; Phase 1 conformance profile formalised |

---

## 7. Roadmap to v2.0

v2.0 targets the Cooperative Inference Profile (CIP) as a first-class, normative
extension. The `policy` and `pricing` blocks become required for CIP nodes (Phase 5).
All Phase 1–4 nodes remain conformant with v1.5 semantics.

- S.12: CIP spec (issue #23) — Phase 5
- ADR-012: Extended scoring formula (price + model_match terms)

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.5.0-draft | 2026-05-15 | Initial v1.5 draft — spec reorganisation, sub-protocol index, conformance levels, migration guide |

---

## Sign-off

**Protocol Steward**: v1.5 draft consolidates the Phase 1 through Phase 4 specification
work into a coherent multi-document structure. No breaking changes. Closes GitHub
issue #18 (S.6 draft). ✓
