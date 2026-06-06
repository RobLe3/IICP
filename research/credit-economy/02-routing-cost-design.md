# Credit Economy — Routing Cost Design

**Date**: 2026-05-22  
**Status**: Research / Pre-spec  
**Feeds**: ADR-031, spec/iicp-core.md §routing-costs, proxy spend logic

---

## 1. The Routing Cost Principle

When a node routes a task to another node (consuming that node's inference capacity),
it pays S-Credits from its balance. This creates two forces:

1. **Demand signal**: nodes that want high-quality inference must earn it by serving
2. **Scarcity signal**: better models charge more, reflecting their lower throughput
   and higher hardware cost

The formula proposed:
```
routing_cost = ceil(tokens_routed / 1000) × tier_weight × spend_multiplier
```

Where `tier_weight` is the same quality weight table from document 01, and
`spend_multiplier` is a scaling constant that controls the earn/spend ratio.

---

## 2. Provider Surplus Target

The maintainer's "you give, you get" model requires providers to earn more than they
spend on routing. Otherwise the mesh collapses: nodes can't afford to consume the
inference they want.

**Target: providers earn 2–3× what they spend.**

Define:
- **Provider surplus ratio** = credits_earned_per_day / credits_spent_per_day

A provider who serves inference earns credits and, on the same day, consumes inference
from other nodes (spending credits). A healthy mesh has:
```
surplus_ratio = earn / spend ≥ 2.0
```

---

## 3. Deriving the Spend Denominator

The earn formula (Scheme C from document 01):
```
earn_per_day = (daily_tokens / 1000) × earn_weight
```

A provider who ALSO routes tasks back into the mesh to serve its own users spends:
```
spend_per_day = (routed_tokens / 1000) × tier_weight × spend_multiplier
```

We assume a "typical" operator uses the mesh to route 20% of its SERVED volume
back out (they serve 80% locally, route 20% to other nodes for tasks their model
can't handle or for load balancing). This is a conservative assumption.

For a 7B node serving 2,592,000 tokens/day:
- Served tokens: 2,592,000
- Routed tokens (20% of served): 518,400
- Routed to a mix of nodes (mostly 7B, occasional 13B/30B)

Assuming routing destination mix: 70% to same tier (7B→7B), 20% to 13B, 10% to 30B:
```
spend_per_day_7B = (518,400/1000) × [0.70×1.0 + 0.20×2.0 + 0.10×6.5] × spend_multiplier
                 = 518.4 × [0.70 + 0.40 + 0.65] × spend_multiplier
                 = 518.4 × 1.75 × spend_multiplier
                 = 907.2 × spend_multiplier
```

For surplus ratio = 2.5 (midpoint of target):
```
earn_per_day_7B = 2,592
surplus_target  = earn / spend = 2.5
spend_target    = 2,592 / 2.5 = 1,036.8
907.2 × spend_multiplier = 1,036.8
spend_multiplier = 1.143
```

Round to `spend_multiplier = 1.0` for simplicity (the 2.5× target is not a hard
contract — it's a design target). At `spend_multiplier = 1.0`:

```
surplus_ratio_7B = 2,592 / (907.2 × 1.0) = 2.86×
```

This is comfortably within the 2–3× target without any tuning.

---

## 4. Full Routing Cost Schedule

**Formula**: `routing_cost = ceil(tokens / 1000) × tier_weight`
Where `tier_weight` is the DESTINATION node's tier weight (you pay for what you use).

| Destination tier | Tier weight | Cost per 1000 tokens | Cost per 500-token request |
|-----------------|-------------|----------------------|---------------------------|
| ≤1B | 0.05 | 0.05 credits | 0.025 credits |
| 7B | 1.0 | 1.0 credits | 0.5 credits |
| 13B | 2.0 | 2.0 credits | 1.0 credits |
| 30B | 6.5 | 6.5 credits | 3.25 credits |
| 70B | 32.0 | 32.0 credits | 16.0 credits |
| 100B+ | 75.0 | 75.0 credits | 37.5 credits |

---

## 5. Provider Surplus Verification — All Tiers

Routing destination mix assumption (same for all providers):
- 60% to same tier, 25% to one tier below, 15% to one tier above

| Provider tier | Earn/day | Routed tokens/day (20% of served) | Effective spend weight | Spend/day | Surplus ratio |
|--------------|----------|----------------------------------|----------------------|-----------|---------------|
| 500M | 432 | 1,728,000 | 0.05 | 86.4 | **5.0×** |
| 7B | 2,592 | 518,400 | ~1.0 (blended) | 518.4 | **5.0×** |
| 13B | 3,024 | 302,400 | ~1.8 (blended) | 544.3 | **5.6×** |
| 30B | 5,616 | 172,800 | ~4.5 (blended) | 777.6 | **7.2×** |
| 70B | 11,059 | 69,120 | ~16.0 (blended) | 1,105.9 | **10.0×** |

**Observation**: Surplus ratios are 5–10×, not 2–3×. This is actually fine — it means
the economy is not credit-deflationary during growth. As the mesh grows and more routing
happens, the spend side will increase and ratios will converge toward 2–3×.

**Critical insight**: The 70B node has a 10× surplus because it earns enormously from
its high-weight tokens but routes rarely (low throughput means fewer tasks to route out).
This large surplus is what lets 70B nodes afford rare luxury: routing to other 70B nodes
for tasks that need multiple perspectives, or routing to specialized models.

---

## 6. Routing Cost Edge Cases

### 6.1 A 7B node accessing 70B inference

Cost for one 500-token request to a 70B node:
```
routing_cost = ceil(500/1000) × 32.0 = 1 × 32.0 = 32 credits
```

A 7B node earns 2,592 credits/day, so it can afford:
```
2,592 / 32 = 81 requests to 70B per day
```
That's roughly 6.7% of its daily request volume (1,244 requests/day for a 7B node). This
is realistic for a provider who occasionally needs GPT-4-tier quality for complex tasks
while handling most work locally.

A 7B node does NOT go bankrupt accessing 70B inference — it simply must budget for it.

### 6.2 A 70B node using its credits for cheap inference

A 70B node earns 11,059 credits/day. It can route to 7B nodes:
```
11,059 / 1.0 = 11,059 cheap requests/day (at 1000 tokens each)
```
Or to 500M nodes:
```
11,059 / 0.05 = 221,180 tiny requests/day
```

The 70B operator can effectively use their earned credits to run a high-volume cheap
inference workload (scraping, summarization, classification) through the mesh's smaller
nodes — which is exactly the asymmetry the maintainer wants.

### 6.3 Bootstrap period — zero-credit new nodes

New nodes have zero credits on registration. They cannot route until they serve.

**Bootstrap grant**: on successful registration + first heartbeat, award 100 credits as
a welcome grant. This allows a new node to route ~100 requests at 7B tier or ~3 requests
at 70B tier to explore the mesh before it has earned credits.

The welcome grant is covered by the overall credit surplus (see document 03). It is not
inflationary in meaningful amounts: 100 credits × 5 nodes/month = 500 credits/month
against a mesh generating millions of credits.

### 6.4 Credit floor — preventing zero-balance deadlock

If a node's balance hits zero, it can still SERVE (earning credits) but cannot ROUTE
(spending credits). This is intentional: the mesh never fully locks out a node — it
just restricts routing until the balance is restored.

Implementation: proxy balance check before routing. If `balance < routing_cost`,
return `insufficient_credits` error (HTTP 402 with a body explaining the deficit).

### 6.5 Credit ceiling — preventing runaway accumulation

Nodes with very large balances (> 10,000,000 credits, approximately 100 days of full
70B earning) should be subject to review. Extremely large balances suggest one of:
- A node that earns but never routes (credit hoarder — reduces mesh liquidity)
- An accounting bug
- A node being used as a credit sink for future premium access

No hard ceiling is imposed in v1, but balances > 1M credits should trigger a flag
in the directory admin dashboard. Cap per document 03's recommendation.

---

## 7. node_credit_cost_multiplier Interaction

The existing `credit_cost_multiplier` in the spec and `PricingConfig` allows a node
to charge a premium above the base rate. Under the new model:

```
routing_cost = ceil(tokens/1000) × tier_weight × node_credit_cost_multiplier
```

A 7B node with `multiplier = 2.0` charges 2.0 credits per 1000 tokens instead of 1.0.
Its EARN rate does not change (earning is based on what it SERVES, not what it charges).

**Market effect**: A node with a high multiplier will be discovered less often
(the `?max_multiplier=` filter lets consumers exclude expensive nodes). This creates
natural price competition — nodes that charge too much get no traffic and no earnings.

The existing multiplier caps (directory enforces `multiplier ≤ max_multiplier` from
the discover filter) remain valid. For S-Credit nodes, recommend `max_multiplier ≤ 5.0`
as a soft directory default (configurable, not hard-coded).

---

## 8. Routing Cost Formula — Final Spec Language

```
S-Credit routing cost for a routed task:

  cost = ceil(output_tokens / tokens_per_credit)
         × tier_weight(destination_model_size)
         × destination_node.credit_cost_multiplier

  where:
    tokens_per_credit = 1000                   (unchanged from existing spec)
    tier_weight       = weight table §2.3      (new in ADR-031)
    multiplier        = node-declared pricing  (existing ADR-019)
    
  The proxy MUST check the routing node's S-Credit balance ≥ cost before
  dispatching the request. If balance < cost, the proxy MUST return
  HTTP 402 with IICP-E028 (InsufficientCredits) rather than forwarding.

  The directory MUST deduct cost atomically from the routing node's balance
  and credit it to the destination node's earn ledger.
```

---

## 9. What This Design Protects Against

| Threat | Protection mechanism |
|--------|---------------------|
| Free-riding (routing without serving) | Credits required to route; zero-balance nodes cannot route |
| Sybil farming (many tiny nodes earning more) | Low weights on small models; quality weight calibrated to hardware cost |
| Premium gaming (self-declaring high tier) | Tier weight set by directory based on model registration, not node claim |
| Credit inflation (earning >> spending) | Availability caps, transaction burn option (see doc 03) |
| 70B marginalization (small models crowd out big ones) | Weights calibrated so 70B earns > 4× 7B per node |

## 10. What This Cannot Protect Against

| Gap | Honest assessment |
|-----|------------------|
| Model capability fraud | A node registering as 7B but running a 500M model. The directory cannot introspect the model — it trusts self-reported tier. Mitigation: benchmark-at-registration probe (future work). |
| Token inflation | A provider could pad responses with whitespace to earn more credits. Mitigation: output_tokens should be measured at the proxy (receiver), not reported by the serving node. |
| Collusion | Two nodes could round-trip tasks to each other to inflate both balances. Mitigation: the directory should flag balance growth with zero reputation increase as suspicious (audit flag, not automatic action). |
