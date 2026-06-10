# IICP Billing Extension

**Version**: 0.4.1  
**Date**: 2026-06-06  
**Status**: draft  
**Issue**: #20, #141 (ADR-019), #145, #305 (rate calibration), #316 (retention)  
**Authority**: Protocol Steward  
**Relation**: ARCHITECTURE.md §Credits, ADR-007, ADR-019, ADR-035 (retention), Phase 3/5

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
1 credit = ceil(output_tokens / tokens_per_credit) at the reference tier (7B)
tokens_per_credit = 1000   (directory-published; the unit definition)
```

Credits are floating-point values. The conversion factor (`tokens_per_credit`) and the
full earn/spend schedule (§10) are published by the directory at `GET /v1/credits/balance`
(echoes `tokens_per_credit`) and in `GET /v1/stats → credit_schedule`. Clients SHOULD cache
the schedule for no more than 60 seconds and MUST NOT hard-code tier weights — the directory
is the sole authority on the unit and the schedule.

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

| Code | Numeric | HTTP | Meaning |
|------|---------|------|---------|
| `billing_limit_exceeded` | — | 422 | Task would exceed `max_credits`; aborted |
| `insufficient_credits` | `IICP-E036` | 402 | Payer/consumer S-Credit balance below the computed routing cost (§10.1). The proxy MUST run this pre-check before dispatching. |
| `billing_unavailable` | — | 422 | Node does not support billing |
| `receipt_conflict` | — | 409 | Duplicate `receipt_id` detected |

> **Code-collision note (v0.4.0).** The rate-calibration research
> (`research/credit-rate-calibration/01 §5`) and `research/credit-economy/09 §10`
> drafted the insufficient-credits pre-check under `IICP-E028`. `IICP-E028` is already
> the **shipped, conformance-tested** code for *invalid CIP field value*
> (`cip.policy`/`cip.replicas`/`cip.quorum`/`cip_role`/`cip_parent_task_id`; iicp-core §7,
> iicp-cooperative-inference §4.1/§4.2, conformance `CIP-V01..V08`). To avoid overloading
> one code with two unrelated meanings, **InsufficientCredits is assigned the distinct new
> code `IICP-E036`** (registered in iicp-core §7). `IICP-E028` is unchanged.

---

## 7. Central Ledger API (Phase 3)

The directory exposes a ledger API:

```
POST /api/v1/credits/award     — provider reports completed task + credits earned
POST /api/v1/credits/debit     — client pre-authorizes credit spend
GET  /api/v1/credits/balance   — check balance
GET  /api/v1/credits/summary   — lifetime earned/spent/balance + reconcile flag + operator_wallet
GET  /api/v1/credits/receipts  — audit trail
```

**Operator wallet (v0.3.1, #463/#466).** Credits are held per node (`node_id`), but an operator running
several nodes sees them rolled up. The node-authenticated `GET /v1/credits/summary` response includes an
`operator_wallet` object aggregating the operator's holdings by `operator_pubkey`:

```json
"operator_wallet": { "total_balance": 18.0, "node_count": 2 }
```

- `total_balance` = SUM(`credit_balance`) over the operator's **non-archived** nodes; `node_count` = how
  many. Resolved via the verified ADR-045 operator binding (iicp-dir §3.1).
- `null` when the requesting node is not operator-bound. The `operator_pubkey` is **never** returned —
  only the aggregate totals.
- v1 is a **read-side rollup** (the authoritative balance stays per-node); pooled cross-node spend is a
  tracked v2 (#466).

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

## 10. Credit Schedule & Economy (S-Credits)

The **S-Credit** (Standard Credit) economy is the mesh's peer reciprocity unit. This
section folds in the rate-calibration findings (#305) and the scalability/safety plan
(`research/credit-economy/09`). P-Credits (premium/commercial) are a separate future
concern and are out of scope here.

### 10.1 Routing cost formula

```
routing_cost = ceil(output_tokens / tokens_per_credit) × tier_weight × credit_cost_multiplier
tokens_per_credit = 1000
```

`tier_weight` is the **destination** node's declared model-size tier (§10.2).
`credit_cost_multiplier` is the destination's ADR-019 per-node pricing multiplier
(default 1.0). The proxy MUST compute `routing_cost` and verify
`consumer_balance ≥ routing_cost` **before** dispatching to a remote node. If the balance
is insufficient, the proxy MUST NOT silently dispatch an unaffordable task; instead it
MUST, in order:

1. **Fall back to local execution** if the consumer has a local provider for the intent
   (local-first) — remote dispatch is skipped, the task runs locally, no error is returned;
2. otherwise **return `IICP-E036`** (InsufficientCredits, §6) to the originating client.

(Rationale, decision B-A: local-first is the better UX — a consumer with a local model
should keep working when it can't afford remote inference — while a consumer with no local
fallback gets an explicit, actionable `IICP-E036` rather than a silent failure.)

### 10.2 Tier-weight schedule

The earn/spend weight scales with the destination model's parameter tier
(Scheme C, validated in `research/credit-economy/01`):

| Tier | Model range | `tier_weight` | Credits / 1000 tok |
|------|-------------|---------------|--------------------|
| 0 | ≤1B (`sub_1b`) | 0.05 | 0.05 |
| 1 | 1–4B | 0.25 | 0.25 |
| 2 | 5–9B (`7b`, **reference**) | 1.00 | 1.00 |
| 3 | 10–20B (`13b`) | 2.00 | 2.00 |
| 4 | 21–50B (`30b`) | 6.50 | 6.50 |
| 5 | 51–100B (`70b`) | 32.0 | 32.0 |
| 6 | 100B+ (`100b_plus`) | 75.0 | 75.0 |

The 7B tier is the **reference rate** (1 credit / 1000 tokens); all other tiers scale
from it by quality weight. Unknown models default to tier 2. The directory publishes the
active schedule in `GET /v1/stats → credit_schedule`; tier weights are directory-defined
and read-only (operators cannot inject values). Per-tier weights MUST NOT change by more
than 20% per governance quarter (ADR required to change the scheme itself).

```json
"credit_schedule": {
  "formula": "ceil(output_tokens / tokens_per_credit) × tier_weight × node_multiplier",
  "tokens_per_credit": 1000,
  "tier_weights": { "sub_1b": 0.05, "7b": 1.0, "13b": 2.0, "30b": 6.5, "70b": 32.0, "100b_plus": 75.0 },
  "evaluation_grant": { "credits": 5, "interval_seconds": 21600 },
  "burn_rate_pct": 2.0
}
```

### 10.3 CIP parity — no rate premium

CIP (Cooperative Inference) tasks cost the **same** per token as standard routed tasks —
there is **no CIP rate premium** (#305). CIP's HMAC signing and credit-settlement
verification are protocol overhead (<1 ms directory-side), not routing cost; a premium
would break the credit-neutrality invariant (§10.5) and create an incentive to fake CIP
compliance. CIP providers compete on **reputation and capability, not price**. (Operators
MAY still set a higher `credit_cost_multiplier` per ADR-019 as market positioning — that
is a node-declared price, not a protocol-level CIP differential.) This requirement is
mirrored normatively in `iicp-cooperative-inference.md §7`.

### 10.4 Evaluation grant (free tier)

The directory MUST grant **5 credits per 6-hour period** to any registered node with a
zero balance (the free evaluation tier; normative rules in
`iicp-cooperative-inference.md §7.1`). At the 7B reference rate this is ~20,000 tokens/day
— enough to evaluate the mesh, not enough to sustain a production consumer.

### 10.5 Anti-inflation sinks

The S-Credit supply grows monotonically from earning; two sinks keep it stable
(`research/credit-economy/03`, `/09`):

1. **90-day TTL expiry (primary)** — see §11. Every `earn` resets a node's credit TTL to
   +90 days; a node that does not earn for 90 days forfeits its unspent balance. This is
   the dominant sink and is always active.
2. **2% transaction burn (secondary)** — `burn_amount = max(1, ceil(spend × 0.02))`,
   removed from the system on each spend. The burn is **governance-activated and inactive
   until month 13+** (activation condition: monthly supply growth > 15% AND active nodes
   > 10,000). The burn rate is capped at 5% (hard limit) and may only be revised upward
   (no deflationary spiral by accident).

**Credit-neutrality invariant**: `Σ(debits) == Σ(earnings) − burn − expiry`. No node can
extract more value than it contributes (structural invariant — see §10.3 rationale).

---

## 11. Ledger Retention (ADR-035)

`credit_transactions` is the dominant directory storage cost at scale. Retention is
**pinned to the economy's TTL** (`credit_economy.TTL_days`, currently **90**) so that the
retention window and the credit-expiry window are one parameter, not two
(ADR-035). The operator MUST NOT set retention independently of the economy TTL.

### 11.1 Transaction-type taxonomy

Every ledger row carries a logical transaction type:

| `tx_type` | Sign | Meaning |
|-----------|------|---------|
| `earn` | + | Credits awarded for tokens served (sets `expires_at = now + TTL_days`) |
| `spend` | − | Credits debited to route/consume a task |
| `bootstrap` | + | One-time cold-start grant on first registration |
| `expire` | − | TTL sweep removed an idle node's unspent balance (§11.3) |
| `burn` | − | 2% transaction burn (§10.5, month 13+) |

> **Reference encoding (PHP directory).** The shipped reference directory stores the row
> type as `type ∈ {credit, debit}` plus a `reason` string; the logical `tx_type` above
> maps onto that pair (`earn`/`bootstrap` → `credit`; `spend`/`expire`/`burn` → `debit`
> with `reason ∈ {task, ttl_expire, burn}`). This preserves the `reconciles` integrity
> invariant (`balance == Σcredit − Σdebit`). The Rust directory SHOULD adopt the explicit
> `tx_type` enum for parity. Either encoding is conformant provided the five logical types
> are distinguishable from a row.

### 11.2 `expires_at` and the retention tiers

| Tier | What | Retention |
|------|------|-----------|
| **Hot** | `credit_transactions` — full per-task detail | `credit_economy.TTL_days` (90d) |
| **Cold** | `credit_summary_monthly` — one row per (node, year-month) of totals | Forever (~12 rows/node/yr) |
| **Crypto** | V5 Merkle chain of `CREDIT_AWARD` events | Per ADR-038 chain tiering |

`credit_transactions` gains an `expires_at` column (indexed). On each `earn` the directory
MUST set `expires_at = now + TTL_days` for the awarding node. A nightly summary job MUST
compute the previous month's per-node aggregates into `credit_summary_monthly` **before**
the TTL sweep prunes those rows, so summaries are never lost. Aggregate queries for
windows > 90 days MUST fall back to `credit_summary_monthly`.

### 11.3 TTL expiry sweep (the sink)

A nightly, **idempotent** sweep enforces the primary sink:

- A node is **idle** if its newest `earn` row's `expires_at` is in the past
  (`MAX(expires_at) < now`) and it still holds a positive balance.
- The sweep MUST zero an idle node's balance and write one `expire` row for the swept
  amount (`balance_after = 0`).
- Re-running the sweep with no new earns MUST be a no-op (balance already 0). A fresh
  `earn` resets the node's TTL forward, removing it from the idle set.

The reference implementation is the `iicp:expire-credits` artisan command (PHP directory),
scheduled nightly and complementary to the live 2% burn.

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.4.1 | 2026-06-06 | §10.1 insufficient-balance behavior (decision B-A): the proxy MUST fall back to LOCAL execution when a local provider exists, else return `IICP-E036` — never silently dispatch an unaffordable task. (Was an unconditional "MUST return IICP-E036"; reconciled with the proxy's local-first design.) Implemented in proxy `decide_dispatch` Gate 2c. |
| 0.4.0 | 2026-06-06 | §10 Credit Schedule & Economy folded in (#305, credit-economy/09): routing-cost formula, Scheme-C tier-weight schedule (`sub_1b` 0.05 … `100b_plus` 75.0), `tokens_per_credit=1000`, **CIP = no rate premium** (mirrors iicp-cooperative-inference §7), evaluation grant, anti-inflation sinks (90d TTL primary + 2% burn secondary, burn governance-activated month 13+, capped 5%). §11 Ledger Retention (ADR-035): `tx_type` taxonomy {earn,spend,bootstrap,expire,burn} with PHP `type`+`reason` encoding note, `expires_at` hot tier + `credit_summary_monthly` cold tier, idempotent TTL expiry sweep. §6: **`IICP-E036` InsufficientCredits** assigned (resolves the research E028 collision; E028 stays invalid-CIP-field). §2 unit definition references the published schedule. |
| 0.3.0 | 2026-05-17 | ADR-019 integration (#141, #145): §3 CALL billing block — `max_multiplier` + `min_quality_score` added; `priority` deprecated in favor of `min_quality_score`. §5 NODELIST — `pricing` declaration block replaces `price_per_1k_tokens` (new fields: `credit_cost_multiplier`, `attested`, `declaration_signature`; legacy billing block preserved). §5.1 pricing declaration at REGISTER/HEARTBEAT with HMAC-SHA256 signature. §7 award request — `multiplier_applied` field added (dispatch-time multiplier lock). Closes #145. |
| 0.2.0 | 2026-05-17 | §8 Credit Quote Flow: GET /v1/credits/quote endpoint contract, QuoteResponse schema, normative MUST rules (60s expiry, quote_id traceability, Gate 2 enforcement); closes #72 |
| 0.1.0 | 2026-05-14 | Initial draft — billing fields, receipt format, ledger phases, credit formula; closes issue #20 |
| 0.1.1 | 2026-05-15 | Added Changelog section (A6 spec cleanup) |

---

## Sign-off

**Protocol Steward**: Billing extension aligns with ARCHITECTURE.md §Credits and
Priority Layer. Phase mapping avoids premature commitment to decentralization.
Closes GitHub issue #20 (draft). ✓
