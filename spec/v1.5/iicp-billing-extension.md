# IICP Billing Extension

**Version**: 0.3.0  
**Date**: 2026-05-17  
**Status**: draft  
**Issue**: #20, #141 (ADR-019), #145  
**Authority**: Protocol Steward  
**Relation**: ARCHITECTURE.md §Credits, ADR-007, ADR-019, Phase 3

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

A client that wishes to use billing-capable nodes includes a `billing` object in the CALL:

```json
{
  "task_id": "uuid",
  "intent": "urn:iicp:intent:llm:chat:v1",
  "payload": { "messages": [...] },
  "constraints": { "timeout_ms": 30000 },
  "billing": {
    "max_credits": 10.0,
    "max_multiplier": 3.0,
    "min_quality_score": 0.7,
    "payer_id": "client-uuid",
    "budget_policy": "abort"
  }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `max_credits` | float | MUST | Maximum credits the client will spend |
| `max_multiplier` | float\|null | MAY | Reject nodes whose `credit_cost_multiplier` exceeds this. null = no filter. (ADR-019) |
| `min_quality_score` | float\|null | MAY | Reject nodes whose ADR-008 quality score is below this. null = no filter. (ADR-019) |
| `payer_id` | string | SHOULD | Client node or user identifier |
| `budget_policy` | string | MAY | `abort` (default) or `complete` if over budget |
| `priority` | string | DEPRECATED | `standard` \| `premium`. Use `min_quality_score` instead. Accepted for backward-compat. |

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

Nodes advertising billing service include a `pricing` declaration in NODELIST (ADR-019).
The legacy `billing` block is preserved for Phase 3 backward-compatibility.

```json
{
  "node_id": "uuid",
  "endpoint": "https://node.example.com",
  "score": 0.91,
  "pricing": {
    "credit_cost_multiplier": 1.5,
    "pricing_model": "per_token",
    "currency": "credits",
    "effective_from": null,
    "effective_until": null,
    "attested": false
  },
  "billing": {
    "accepts_credits": true,
    "min_credits": 0.1,
    "free_tier_tokens": 10000
  }
}
```

**`pricing` block fields** (ADR-019):

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `credit_cost_multiplier` | float | 1.0 | Applied to base rate: `credits = ceil(tokens/1000) × multiplier` |
| `pricing_model` | string | `"per_token"` | Only `"per_token"` is defined in v1; others reserved |
| `currency` | string | `"credits"` | MUST be `"credits"` in v1 |
| `effective_from` | ISO-8601\|null | null | null = immediately effective |
| `effective_until` | ISO-8601\|null | null | null = no expiry |
| `attested` | bool | false | true if `declaration_signature` was verified at last registration |

**`billing` block fields** (Phase 3 — preserved):

| Field | Type | Notes |
|-------|------|-------|
| `accepts_credits` | bool | Whether node participates in credit system |
| `min_credits` | float | Minimum credits per task |
| `free_tier_tokens` | integer | Free tokens before billing starts |

**Deprecated**: `price_per_1k_tokens` is replaced by `credit_cost_multiplier`. Implementations SHOULD NOT generate `price_per_1k_tokens` in new code. The directory MUST treat a present `price_per_1k_tokens` value as equivalent to `credit_cost_multiplier = price_per_1k_tokens / base_rate`.

Nodes where `accepts_credits = false` MUST ignore `billing` fields in CALL messages.

### 5.1 Pricing Declaration at Registration

Nodes include a signed `pricing` block in REGISTER and HEARTBEAT payloads to bind the declaration to the node's identity:

```json
{
  "node_id": "...",
  "capabilities": { ... },
  "pricing": {
    "credit_cost_multiplier": 1.5,
    "pricing_model": "per_token",
    "currency": "credits",
    "effective_from": null,
    "effective_until": null,
    "declaration_signature": "<base64url-hmac-sha256>"
  }
}
```

The `declaration_signature` MUST be HMAC-SHA256 of the canonical pricing block JSON (fields sorted, effective_from/until as ISO-8601 or the literal string `"null"`), signed with the node's registered token. Absent or null signature = unattested; directory surfaces `attested: false` to clients.

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
  "tokens_consumed": 3200,
  "multiplier_applied": 1.5
}
Authorization: Bearer <node_token>
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `receipt_id` | string | MUST | Opaque UUID; idempotency key |
| `task_id` | string | MUST | UUID of the completed task |
| `payer_id` | string | SHOULD | Client or consumer node identifier |
| `provider_id` | string | MUST | Node ID of the executing node |
| `credits_earned` | float | MUST | `ceil(tokens_consumed / 1000) × multiplier_applied` |
| `tokens_consumed` | integer | MUST | Actual tokens reported by inference backend |
| `multiplier_applied` | float | MUST | `credit_cost_multiplier` from the node's pricing declaration at dispatch time. MUST be 1.0 if no pricing block was declared. (ADR-019) |

All ledger operations MUST be idempotent on `receipt_id`. Duplicate awards return 200
with the original receipt, not an error.

---

## 8. Credit Quote Flow (Phase 5 — CIP Pre-Flight)

Before dispatching a CIP sub-task to remote workers, a consumer proxy SHOULD query the directory for an estimated credit cost. This allows the proxy to enforce `max_credits_per_task` (see S.12 §2.2) before committing to dispatch.

### 8.1 Quote Request

```
GET /v1/credits/quote?intent=<urn>&max_tokens=<int>&nodes=<comma-separated-node-ids>
Authorization: Bearer <node_token>
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `intent` | Yes | Intent URN for the task (e.g. `urn:iicp:intent:llm:chat:v1`) |
| `max_tokens` | Yes | Maximum tokens the task may consume (used for cost upper bound) |
| `nodes` | No | Comma-separated list of candidate node IDs to quote against. If omitted, quotes against all CIP-eligible nodes in the peer list. |

### 8.2 Quote Response

```json
{
  "quote_id": "q_3f8a12bc9d7e",
  "estimated_credits": 4.32,
  "price_per_1000_tokens": 1.35,
  "nodes_quoted": 3,
  "quote_expires_at": "2026-05-17T02:10:00Z",
  "currency": "iicp_credits"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `quote_id` | string | Opaque identifier; SHOULD be sent with the task for settlement traceability |
| `estimated_credits` | float | Upper-bound credit cost for `max_tokens` at the average price of quoted nodes |
| `price_per_1000_tokens` | float | Weighted average of `credits_per_1000_tokens` across quoted nodes |
| `nodes_quoted` | integer | Number of CIP-eligible nodes included in this estimate |
| `quote_expires_at` | ISO-8601 | Quote is valid until this timestamp (MUST be ≤ 60 seconds after issuance) |
| `currency` | string | Always `"iicp_credits"` in Phase 5 |

### 8.3 Normative requirements

- A quote MUST be valid for no more than 60 seconds from issuance (`quote_expires_at`). Consumer proxies MUST NOT dispatch a CIP task against an expired quote.
- A `quote_id` SHOULD be included in the task's `trace.cip_quote_id` field for audit. The directory MAY use `quote_id` to correlate the eventual settlement receipt.
- If `estimated_credits > max_credits_per_task` (proxy config), the consumer MUST reject dispatch and execute locally — this is Gate 2 of the §2.2 consumer activation flow.
- The directory MUST return 401 if the bearer token is absent or invalid, and 422 if `intent` or `max_tokens` is missing.
- The directory SHOULD cache quote computations for identical `(intent, nodes)` tuples for up to 10 seconds to reduce load during burst dispatch windows.

### 8.4 Phase mapping update

| Feature | Phase |
|---------|-------|
| Credit quote endpoint `GET /v1/credits/quote` | Phase 5 (CIP pre-flight) |
| `quote_id` in task trace | Phase 5 |

---

## 9. Phase Mapping

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
| 0.3.0 | 2026-05-17 | ADR-019 integration (#141, #145): §3 CALL billing block — `max_multiplier` + `min_quality_score` added; `priority` deprecated in favor of `min_quality_score`. §5 NODELIST — `pricing` declaration block replaces `price_per_1k_tokens` (new fields: `credit_cost_multiplier`, `attested`, `declaration_signature`; legacy billing block preserved). §5.1 pricing declaration at REGISTER/HEARTBEAT with HMAC-SHA256 signature. §7 award request — `multiplier_applied` field added (dispatch-time multiplier lock). Closes #145. |
| 0.2.0 | 2026-05-17 | §8 Credit Quote Flow: GET /v1/credits/quote endpoint contract, QuoteResponse schema, normative MUST rules (60s expiry, quote_id traceability, Gate 2 enforcement); closes #72 |
| 0.1.0 | 2026-05-14 | Initial draft — billing fields, receipt format, ledger phases, credit formula; closes issue #20 |
| 0.1.1 | 2026-05-15 | Added Changelog section (A6 spec cleanup) |

---

## Sign-off

**Protocol Steward**: Billing extension aligns with ARCHITECTURE.md §Credits and
Priority Layer. Phase mapping avoids premature commitment to decentralization.
Closes GitHub issue #20 (draft). ✓
