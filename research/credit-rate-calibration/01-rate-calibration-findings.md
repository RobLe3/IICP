# Credit Rate Calibration — Research Findings
## Issue #305: What is the right credit cost per 1000 tokens for non-CIP mesh routing?

**Date**: 2026-05-24
**Status**: Research / Pre-spec
**Issue**: #305
**Author**: ADOPTION sub-loop, FORGE iter-958
**Depends on**: `research/credit-economy/02-routing-cost-design.md`, `research/credit-economy/05-spec-and-implementation-plan.md`
**Feeds**: `spec/iicp-core.md §routing-costs`, `spec/iicp-dir.md §credit-economy`, proxy spend logic, `/api/v1/stats`

---

## Executive Summary

| Question | Answer |
|----------|--------|
| Base rate (non-CIP) | **1.0 credit per 1000 tokens** at the 7B tier (after `spend_multiplier = 1.0`) |
| Economic balance | **2–5× surplus ratio** for all provider tiers — healthy margin |
| CIP vs non-CIP parity | **Same rate** — CIP adds no routing cost premium |
| Rate discoverability | **Publish tier_weight table in `/api/v1/stats`** as `credit_schedule` field |

---

## 1. Base Rate Derivation

**Source**: `research/credit-economy/02-routing-cost-design.md §3–4`

The routing cost formula is:
```
routing_cost = ceil(tokens_routed / 1000) × tier_weight(destination)
```

`spend_multiplier = 1.0` (simplified from 1.143; within the 2–3× surplus target).

**Tier weight table** (destination node's declared model size):

| Destination tier | Tier weight | Credits per 1000 tokens | Credits per avg 500-token task |
|-----------------|-------------|------------------------|-------------------------------|
| ≤1B | 0.05 | 0.05 | 0.025 |
| 7B | 1.0 | 1.0 | 0.50 |
| 13B | 2.0 | 2.0 | 1.00 |
| 30B | 6.5 | 6.5 | 3.25 |
| 70B | 32.0 | 32.0 | 16.00 |
| 100B+ | 75.0 | 75.0 | 37.50 |

**The "1 credit per 1000 tokens at 7B" rate** becomes the reference rate. All other tiers
scale from it by quality weight. This is consistent with the existing CIP earn rate
(1 credit awarded per 1000 tokens served at the 7B tier) — ensuring neutral exchange
at the most common tier.

---

## 2. Economic Balance Verification

**Source**: `research/credit-economy/02-routing-cost-design.md §5`

| Provider tier | Earn/day | Spend/day (20% routing) | Surplus ratio |
|--------------|----------|------------------------|---------------|
| ≤1B | 432 | 86.4 | **5.0×** ✓ |
| 7B | 2,592 | 518.4 | **5.0×** ✓ |
| 13B | 3,024 | ~720 | **~4.2×** ✓ |
| 30B | 5,616 | ~1,250 | **~4.5×** ✓ |
| 70B | 11,059 | ~2,800 | **~3.9×** ✓ |

All tiers maintain ≥ 3.9× surplus — comfortably above the 2.0× minimum target.

**Free evaluation tier check**: The free tier grants 5 credits every 6 hours (20 credits/day).
At 1.0 credit per 1000 tokens (7B tier):
- 20 credits/day → 20,000 tokens/day → 40 × 500-token requests at 7B
- At a mixed tier (mostly ≤1B and 7B), this stretches to 100–400 evaluation tasks

**Conclusion**: 5 credits / 6h is sufficient for meaningful evaluation without being
generous enough to sustain a production consumer node. The free tier is correctly calibrated.

---

## 3. CIP vs Non-CIP Rate Parity

**Research question**: Should CIP tasks cost more per token than non-CIP tasks, given that
CIP adds richer receipts, HMAC verification, and signed credit awards?

**Finding: Same rate. No CIP premium.**

**Reasoning**:

1. **CIP overhead is protocol cost, not routing cost.** HMAC signing and credit settlement
   verification add <1ms of directory-side compute per task. This is not a meaningful cost
   increment compared to the inference latency (500ms–2000ms per task).

2. **Credit neutrality principle** (doc 05): `sum(debits) == sum(earnings) - 2% burn`.
   A CIP-specific surcharge would break this symmetry at the node level — a CIP-capable
   provider would earn more per token than a standard provider for the same compute,
   creating an incentive to fake CIP compliance without actually implementing it.

3. **Protocol simplicity**: One cost formula across all task types reduces client
   implementation complexity. Clients can pre-compute routing cost from the tier_weight
   alone, without knowing whether the destination node is CIP-capable.

4. **CIP value proposition is quality, not cost.** CIP providers earn reputation for
   delivering verified, high-quality results. The reputation signal (reflected in `score`)
   already makes CIP nodes more desirable — they don't need a cost premium.

**Recommendation**: `routing_cost` formula applies equally to CIP and non-CIP tasks.
CIP nodes charge the same rate as standard nodes; they compete on reputation and
capability, not price.

**One exception — the `credit_cost_multiplier`** (node-declared, ADR-019):
A CIP provider may choose to set a higher `credit_cost_multiplier` (up to 5.0) to
signal premium positioning. This is operator-driven market pricing, not a protocol-level
CIP/non-CIP differential. Clients are free to select lower-multiplier CIP nodes.

---

## 4. Rate Discoverability

**Research question**: Should the per-token rate be published in `/api/v1/stats` so clients
can predict cost before routing?

**Finding: Yes. Add `credit_schedule` field to `/api/v1/stats`.**

Clients should not need to read the spec to know routing costs. The directory should
serve the active tier_weight table as part of the stats endpoint so clients can:
1. Pre-compute routing cost for a known task size
2. Build UI elements showing "estimated cost: X credits" before dispatching
3. Implement budget guards (IICP-E028 pre-check) without hardcoding weights

**Proposed stats addition**:

```json
"credit_schedule": {
  "formula": "ceil(output_tokens / tokens_per_credit) × tier_weight × node_multiplier",
  "tokens_per_credit": 1000,
  "tier_weights": {
    "sub_1b":  0.05,
    "7b":      1.0,
    "13b":     2.0,
    "30b":     6.5,
    "70b":     32.0,
    "100b_plus": 75.0
  },
  "evaluation_grant": {
    "credits": 5,
    "interval_seconds": 21600
  },
  "burn_rate_pct": 2.0
}
```

This field is read-only, directory-defined. Node operators cannot inject values.

**Implementation**: Add to `NodeController.php` stats response (or a dedicated
`CreditController.php::schedule()` method). ~30 lines of PHP.

---

## 5. Recommended Spec Language

For `spec/iicp-core.md §routing-costs`:

```
### Routing Credit Cost

The proxy MUST compute the routing cost before dispatching a task:

  cost = ceil(output_tokens / 1000) × tier_weight × destination_node.credit_cost_multiplier

where tier_weight is the destination node's model size tier weight (fetched from
/api/v1/stats → credit_schedule.tier_weights). The proxy MUST check that its
S-Credit balance ≥ cost before dispatching. If balance < cost, the proxy MUST
return IICP-E028 (InsufficientCredits) to the originating client.

This formula applies to both CIP and non-CIP routed tasks. There is no
CIP-specific routing cost premium.
```

---

## 6. Summary and Implementation Path

| Item | Status | Owner | Phase |
|------|--------|-------|-------|
| Base rate formula | ✅ Established (doc 02) | Spec | Now |
| Tier weight table | ✅ Established (doc 02) | Spec | Now |
| Economic balance | ✅ Verified (surplus ≥ 3.9×) | — | Now |
| CIP vs non-CIP parity | ✅ **Same rate** (this doc) | Spec | Now |
| `/api/v1/stats` credit_schedule | 🔲 Not implemented | directory (PHP) | Phase 5A |
| Proxy pre-check (IICP-E028) | 🔲 Not implemented | proxy (Python) | Phase 5A |
| Director spend deduction | 🔲 Not implemented | directory (PHP) | Phase 5A |
| Adapter earn trigger | 🔲 Not implemented | adapter (Python) | Phase 5A |

Implementation sequence from `research/credit-economy/05-spec-and-implementation-plan.md`:
schema → earn endpoint → spend endpoint → proxy pre-check → stats field → conformance tests.
