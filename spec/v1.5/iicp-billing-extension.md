# IICP Billing Extension

**Version**: 0.1.0  
**Date**: 2026-05-14  
**Status**: draft  
**Issue**: #20  
**Authority**: Protocol Steward  
**Relation**: ARCHITECTURE.md §Credits, ADR-007, Phase 3

---

## 1. Purpose

This document specifies the billing fields added to IICP CALL and RESPONSE messages
when a node operates in premium mode. Billing is an optional extension — non-billing
nodes ignore these fields transparently.

The billing protocol uses a **central ledger** at `iicp.network` in Phase 3.
Decentralized accounting (signed receipts, on-chain ledger) is a Phase 4+ concern.

---

## 2. Credit Unit

```
1 credit ≈ 1000 tokens (output tokens; tunable via directory config)
```

Credits are floating-point values. The exchange rate is published by the directory
and SHOULD be cached by clients for no more than 60 seconds.

---

## 3. CALL Message Billing Fields

A client that wishes to use premium nodes includes a `billing` object in the CALL:

```json
{
  "task_id": "uuid",
  "intent": "urn:iicp:intent:llm:chat:v1",
  "payload": { "messages": [...] },
  "constraints": { "timeout_ms": 30000 },
  "billing": {
    "max_credits": 10.0,
    "priority": "premium",
    "payer_id": "client-uuid",
    "budget_policy": "abort"
  }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `max_credits` | float | MUST | Maximum credits the client will spend |
| `priority` | string | MUST | `standard` \| `premium` |
| `payer_id` | string | SHOULD | Client node or user identifier |
| `budget_policy` | string | MAY | `abort` (default) or `complete` if over budget |

**`budget_policy`**:
- `abort` — node MUST stop and return `billing_limit_exceeded` error if cost would exceed `max_credits`
- `complete` — node MAY complete and report actual credits used (client pre-authorized overage)

---

## 4. RESPONSE Message Billing Fields

The node returns actual credits consumed:

```json
{
  "task_id": "uuid",
  "status": "success",
  "result": { "content": "..." },
  "billing": {
    "credits_used": 3.2,
    "tokens_consumed": 3200,
    "rate": 1.0,
    "receipt_id": "uuid",
    "node_id": "provider-uuid"
  }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `credits_used` | float | MUST (if billing active) | Actual credits deducted |
| `tokens_consumed` | integer | MUST | Total tokens (input + output) |
| `rate` | float | SHOULD | Credits-per-1000-tokens used for this task |
| `receipt_id` | string | SHOULD | Opaque receipt for audit trail |
| `node_id` | string | SHOULD | Provider node that executed the task |

---

## 5. NODELIST Billing Fields

Nodes advertising premium service include pricing in NODELIST:

```json
{
  "node_id": "uuid",
  "endpoint": "https://node.example.com",
  "score": 0.91,
  "billing": {
    "price_per_1k_tokens": 0.5,
    "accepts_credits": true,
    "min_credits": 0.1,
    "free_tier_tokens": 10000
  }
}
```

| Field | Type | Notes |
|-------|------|-------|
| `price_per_1k_tokens` | float | Credits charged per 1000 tokens |
| `accepts_credits` | bool | Whether node participates in credit system |
| `min_credits` | float | Minimum credits per task |
| `free_tier_tokens` | integer | Free tokens before billing starts |

Nodes where `accepts_credits = false` MUST ignore `billing` fields in CALL messages.

---

## 6. Error Codes

| Code | Meaning |
|------|---------|
| `billing_limit_exceeded` | Task would exceed `max_credits`; aborted |
| `insufficient_credits` | Payer balance below `max_credits` |
| `billing_unavailable` | Node does not support billing |
| `receipt_conflict` | Duplicate `receipt_id` detected |

---

## 7. Central Ledger API (Phase 3)

The directory exposes a ledger API:

```
POST /api/v1/credits/award     — provider reports completed task + credits earned
POST /api/v1/credits/debit     — client pre-authorizes credit spend
GET  /api/v1/credits/balance   — check balance
GET  /api/v1/credits/receipts  — audit trail
```

**Award request** (node → directory after task completion):

```json
{
  "receipt_id": "uuid",
  "task_id": "uuid",
  "payer_id": "client-uuid",
  "provider_id": "node-uuid",
  "credits_earned": 3.2,
  "tokens_consumed": 3200
}
Authorization: Bearer <node_token>
```

All ledger operations MUST be idempotent on `receipt_id`. Duplicate awards return 200
with the original receipt, not an error.

---

## 8. Phase Mapping

| Feature | Phase |
|---------|-------|
| Billing fields in CALL/RESPONSE (optional, ignored) | Phase 1 (reserved) |
| Central ledger at iicp.network | Phase 3 |
| Node pricing in NODELIST | Phase 3 |
| Signed receipts (tamper-evident audit trail) | Phase 3 |
| Decentralized on-chain accounting | Phase 4+ |

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.0 | 2026-05-14 | Initial draft — billing fields, receipt format, ledger phases, credit formula; closes issue #20 |
| 0.1.1 | 2026-05-15 | Added Changelog section (A6 spec cleanup) |

---

## Sign-off

**Protocol Steward**: Billing extension aligns with ARCHITECTURE.md §Credits and
Priority Layer. Phase mapping avoids premature commitment to decentralization.
Closes GitHub issue #20 (draft). ✓
