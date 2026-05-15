# IICP Extensions — Billing, Reputation, and Sub-Protocol Bindings

**Version**: 1.0.0
**Date**: 2026-05-15
**Status**: draft
**Issue**: #17 (S.5 — spec split)
**Authority**: Protocol Steward
**Relation**: iicp-core.md, iicp-semantics.md, iicp-billing-extension.md, iicp-mcp-binding.md

---

## Purpose

This document collects IICP extension mechanisms: optional protocol features that
implementations MAY support to gain additional capabilities. Extensions do not break
conformance — a Phase 1 node is fully conformant without implementing any extension.

Extensions covered:
1. **Credits / Billing** — compute unit economy (Phase 3)
2. **Reputation** — trust scoring across nodes (Phase 3)
3. **Sub-protocol bindings** — MCP, QuDAG (Phase 2+)
4. **Cooperative Inference Profile (CIP)** — share spare inference capacity (Phase 5)
5. **Post-quantum cryptography** — Dilithium3, Falcon512, ML-DSA (Phase 4)

---

## Normative Language

The key words "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", "MAY", and "OPTIONAL"
in this document are to be interpreted as described in RFC 2119 / BCP 14.

---

## 1. Credits / Billing Extension (Phase 3)

Full specification: `spec/iicp-billing-extension.md`

### 1.1 Overview

The credits extension introduces a compute unit economy. One credit ≈ 1000 tokens
(configurable). Nodes earn credits for inference they provide; clients spend credits
for inference they consume.

### 1.2 CALL extension fields

When billing is enabled, a CALL message MAY include a `billing` block:

```json
{
  "task_id": "uuid",
  "intent": "urn:iicp:intent:llm:chat:v1",
  "payload": { ... },
  "constraints": { "timeout_ms": 5000 },
  "billing": {
    "max_credits": 10,
    "priority": "premium"
  }
}
```

| Field | Type | Notes |
|-------|------|-------|
| `billing.max_credits` | integer | Maximum credits client is willing to spend on this task |
| `billing.priority` | string | `standard` \| `premium` — affects queue priority at adapter |

### 1.3 RESPONSE extension fields

Adapters MAY include a `billing` block in task responses:

```json
{
  "task_id": "uuid",
  "status": "success",
  "result": { ... },
  "metrics": { "latency_ms": 320, "tokens_used": 120 },
  "billing": {
    "credits_used": 0.12,
    "receipt_id": "uuid"
  }
}
```

### 1.4 Discovery extension

The directory MAY include pricing in discovery responses when billing is enabled:

```json
{
  "nodes": [
    {
      "node_id": "uuid",
      "endpoint": "https://node.example.com",
      "score": 0.91,
      "available": true,
      "price_per_1k_tokens": 0.5,
      "accepts_credits": true
    }
  ]
}
```

### 1.5 Ledger phases

| Phase | Ledger model |
|-------|-------------|
| 3 | Central ledger on iicp.network (Laravel) |
| 4 | Signed receipts — worker signs proof of execution |
| 5+ | Decentralised — off-chain proof verification |

---

## 2. Reputation Extension (Phase 3)

### 2.1 Reputation score

Each node accumulates a reputation score ∈ [0, 1] maintained by the directory.

```
reputation_score = EMA(success_rate × latency_consistency)
```

Where:
- `success_rate` = tasks completed successfully / total tasks submitted in rolling window
- `latency_consistency` = 1 − (p99_latency / p50_latency − 1) clamped to [0, 1]
- Default for new nodes: 0.5 (neutral — no penalty, no bonus)

### 2.2 Score update

The directory SHOULD update `reputation_score` after each heartbeat that includes
`metrics.tasks_success` and `metrics.tasks_failed`.

Exponential moving average with α = 0.1:
```
new_score = α × current_window_score + (1 − α) × previous_score
```

### 2.3 Score in discovery

Reputation contributes `W_REP × reputation_score` to the ADR-008 node score
(Phase 3 weight = 0.10). See ARCHITECTURE.md §Node Discovery Scoring.

Nodes with `reputation_score < 0.2` SHOULD be excluded from discovery results
regardless of other score components.

---

## 3. Sub-Protocol Bindings

### 3.1 Extension mechanism

IICP supports sub-protocol extensions via the `SUB_PROTOCOL` message type. A
sub-protocol binding defines how an external protocol's semantics are expressed
within an IICP session.

Sub-protocol negotiation uses the INIT registration field `sub_protocol` (Phase 2):

```json
{
  "endpoint": "https://node.example.com",
  "sub_protocol": "mcp",
  "sub_protocol_version": "2025-06-18"
}
```

### 3.2 MCP binding

The formal MCP–IICP binding is specified in `spec/iicp-mcp-binding.md`.

Summary: An IICP node MAY expose an MCP server endpoint. MCP tool calls are
translated to IICP CALL messages. The binding preserves MCP's JSON-RPC framing
while routing task execution through the IICP mesh.

### 3.3 QuDAG binding (Phase 2+)

QuDAG (Quorum Directed Acyclic Graph) is the planned high-performance transport
substrate for Phase 2+. When a QuDAG transport is detected:

- The `X-IICP-Transport-Hint: qudag` header SHOULD be included in INIT
- QuDAG handles message ordering and DAG-based delivery guarantees
- REST endpoints remain available as fallback

Full QuDAG binding is deferred to Phase 2. See IICP_draft_1.4.2.txt §QuDAG Integration
for the original specification.

---

## 4. Cooperative Inference Profile (Phase 5)

Full specification: deferred to `spec/iicp-cip.md` (issue #23).

### 4.1 Overview

The Cooperative Inference Profile (CIP) enables AI assistant runtimes to
participate in the IICP mesh as both consumers and providers of spare inference
capacity — settled via the credit extension.

### 4.2 Policy fields (Phase 5)

CIP introduces optional policy blocks in INIT registration and CALL messages:

**INIT `policy` block**:
```json
{
  "policy": {
    "share_inference": true,
    "max_share_percent": 30,
    "allowed_intents": ["urn:iicp:intent:llm:chat:v1"],
    "min_credit_balance": 100,
    "prohibited_capabilities": ["shell", "file_access", "browser"]
  }
}
```

**CALL `policy` block** (consumer constraint):
```json
{
  "policy": {
    "local_first": true,
    "max_price_per_1k_tokens": 1.0,
    "min_reputation_score": 0.7
  }
}
```

### 4.3 Safety boundary

The CIP explicitly prohibits the following capabilities from being shared across
peers, regardless of policy configuration:

- Remote shell execution or command running
- File system access (read or write)
- Browser automation
- Credential sharing or proxy authentication
- Private memory or context access from other sessions

These are enforced at the provider policy gate in the adapter/node, not by convention.

### 4.4 New intent URNs for CIP

| URN | Description |
|-----|-------------|
| `urn:iicp:intent:cip:inference:v1` | Generic CIP inference request |
| `urn:iicp:intent:cip:embed:v1` | CIP embedding/vectorisation |
| `urn:iicp:intent:cip:rerank:v1` | CIP result reranking |

---

## 5. Post-Quantum Cryptography (Phase 4)

### 5.1 Algorithms

IICP Phase 4 adds post-quantum signature support:

| Algorithm | Purpose |
|-----------|---------|
| Dilithium3 (ML-DSA-65) | Node identity signatures, HMAC replacement |
| Falcon512 | Compact signatures for resource-constrained nodes |
| ML-DSA | Standardised version of Dilithium (NIST FIPS 204) |

### 5.2 Activation

PQ signatures are negotiated via a new INIT field `auth_pq_algorithm` (Phase 4).
Nodes that do not support PQ remain conformant — PQ is additive, not breaking.

When PQ is active, the `X-IICP-Signature` header format changes from HMAC-SHA256
to the PQ algorithm's binary signature encoded as base64url.

---

## 6. Extension Compatibility Matrix

| Extension | Phase | Breaking? | Requires |
|-----------|-------|-----------|---------|
| Credits / billing | 3 | No — additive fields | Ledger endpoint |
| Reputation scoring | 3 | No — scoring term defaults to 0.5 | Directory upgrade |
| MCP binding | 2 | No | Sub-protocol negotiation |
| QuDAG transport | 2 | No — fallback to REST | QuDAG network |
| CIP policy fields | 5 | No | Phase 3 credits |
| Post-quantum auth | 4 | No — parallel to bearer | PQ key infrastructure |

All extensions are additive. A Phase 1 node that ignores unknown fields remains
conformant with any future version of this specification.

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-05-15 | Initial draft — collected from iicp-billing-extension.md, iicp-mcp-binding.md, ARCHITECTURE.md, and ROADMAP.md as part of S.5 spec split |

---

## Sign-off

**Protocol Steward**: iicp-extensions.md provides a single canonical reference for all
optional IICP capabilities. Extensions are additive — no Phase 1 conformance requirement
is affected. Part of S.5 spec split (issue #17). ✓
