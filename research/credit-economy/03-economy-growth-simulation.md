# Credit Economy — 36-Month Growth Simulation

**Date**: 2026-05-22  
**Status**: Research / Pre-spec  
**Feeds**: ADR-031, economic viability assessment

---

## 1. Simulation Parameters

**Credit earning formula** (Scheme C from document 01):
```
earn_per_day = (daily_tokens / 1000) × tier_weight
```

**Credit spending formula** (from document 02):
```
spend_per_day = (routed_tokens / 1000) × destination_tier_weight
```

**Routing ratio assumption**: 20% of served tokens are routed out by each node
(conservative; likely rises to 30–35% as mesh matures).

**Destination tier mix for routing** (blended effective weight):
- Phase 1–2 (small mesh): mostly same-tier routing → blended weight ≈ tier_weight × 0.8
- Phase 3+ (diverse mesh): mixed routing → blended weight ≈ 1.5 (floor-tier dominance)

**Utilization ramp**: 50% months 1-6, 65% months 7-18, 80% months 19-36.

---

## 2. Node Fleet Definitions by Phase

### Phase 1 (Months 1–6): Bootstrap
8 seed nodes: 6× 7B, 2× 13B

| Node type | Count | Earn/day each | Total earn/day |
|-----------|-------|---------------|---------------|
| 7B | 6 | 2,592 | 15,552 |
| 13B | 2 | 3,024 | 6,048 |
| **Fleet total** | **8** | | **21,600** |

### Phase 2 (Months 7–12): Early Growth
20 nodes: 15× 7B, 3× 13B, 2× 30B
Utilization: 65%

| Node type | Count | Earn/day (65%) | Total earn/day |
|-----------|-------|----------------|---------------|
| 7B | 15 | 3,370 | 50,544 |
| 13B | 3 | 3,931 | 11,794 |
| 30B | 2 | 7,301 | 14,602 |
| **Fleet total** | **20** | | **76,940** |

### Phase 3 (Months 13–18): Ecosystem Emergence
50 nodes: 30× 7B, 10× 13B, 5× 30B, 3× 70B, 2× 500M
Utilization: 65%

| Node type | Count | Earn/day (65%) | Total earn/day |
|-----------|-------|----------------|---------------|
| 500M | 2 | 562 | 1,123 |
| 7B | 30 | 3,370 | 101,088 |
| 13B | 10 | 3,931 | 39,312 |
| 30B | 5 | 7,301 | 36,506 |
| 70B | 3 | 14,377 | 43,130 |
| **Fleet total** | **50** | | **221,159** |

### Phase 4 (Months 19–24): Scale
150 nodes: 80× 7B, 30× 13B, 20× 30B, 12× 70B, 5× 500M, 3× 70B-Q
Utilization: 80%

| Node type | Count | Earn/day (80%) | Total earn/day |
|-----------|-------|----------------|---------------|
| 500M | 5 | 691 | 3,456 |
| 7B | 80 | 4,147 | 331,776 |
| 13B | 30 | 4,838 | 145,152 |
| 30B | 20 | 8,986 | 179,712 |
| 70B | 12 | 17,694 | 212,327 |
| 70B-Q | 3 | 13,271 | 39,813 |
| **Fleet total** | **150** | | **912,236** |

### Phase 5 (Months 25–36): Maturity + Commercial
500 nodes + 2 commercial premium providers (Anthropic tier, 100B+)
Note: Commercial/premium providers earn P-Credits, not S-Credits (see document 04).
S-Credit economy from peer nodes only.

S-Credit peer nodes: 300× 7B, 80× 13B, 60× 30B, 40× 70B, 15× 500M, 5× 70B-Q
Utilization: 80%

| Node type | Count | Earn/day (80%) | Total earn/day |
|-----------|-------|----------------|---------------|
| 500M | 15 | 691 | 10,368 |
| 7B | 300 | 4,147 | 1,244,160 |
| 13B | 80 | 4,838 | 387,072 |
| 30B | 60 | 8,986 | 539,136 |
| 70B | 40 | 17,694 | 707,573 |
| 70B-Q | 5 | 13,271 | 66,355 |
| **Fleet total** | **500** | | **2,954,664** |

---

## 3. Routing Spend by Phase

Routing spend = 20% of served tokens, routed at blended effective weight.

**Blended spend weight** (all routing is at destination tier weight, mixed):

| Phase | Blended spend weight | Notes |
|-------|---------------------|-------|
| 1 | 0.85 | Mostly 7B→7B routing |
| 2 | 1.10 | Some 30B demand emerging |
| 3 | 1.50 | Diverse mesh, routing to 30B/70B |
| 4 | 2.00 | Mature routing mix |
| 5 | 2.50 | Heavy 70B demand from consumers |

**Daily routing spend formula**:
```
spend_per_day = (total_tokens_served × 0.20 / 1000) × blended_spend_weight
```

Total tokens served per day = sum of all nodes' daily token throughput:

| Phase | Total daily tokens (fleet) | Routing spend/day |
|-------|--------------------------|-------------------|
| 1 | 8× avg 2.5M = 17.6M | 17,600 × 0.20 × 0.85 = 2,992 |
| 2 | 20× avg 2.2M = 44M | 44,000 × 0.20 × 1.10 = 9,680 |
| 3 | 50× avg 2.0M = 100M | 100,000 × 0.20 × 1.50 = 30,000 |
| 4 | 150× avg 1.9M = 285M | 285,000 × 0.20 × 2.00 = 114,000 |
| 5 | 500× avg 1.8M = 900M | 900,000 × 0.20 × 2.50 = 450,000 |

---

## 4. Net Credit Balance — Phase-by-Phase

| Phase | Earn/day | Spend/day | Net/day | Net/month | Cumulative end |
|-------|----------|-----------|---------|-----------|---------------|
| Phase 1 (mo 1-6) | 21,600 | 2,992 | +18,608 | +558,240 | +3,349,440 |
| Phase 2 (mo 7-12) | 76,940 | 9,680 | +67,260 | +2,017,800 | +15,456,240 |
| Phase 3 (mo 13-18) | 221,159 | 30,000 | +191,159 | +5,734,770 | +49,865,060 |
| Phase 4 (mo 19-24) | 912,236 | 114,000 | +798,236 | +23,946,000 | +193,641,060 |
| Phase 5 (mo 25-36) | 2,954,664 | 450,000 | +2,504,664 | +75,139,920 | +1,094,939,100 |

**Critical finding**: The economy is strongly **inflationary** by design. Credits
accumulate because the mesh earns far more than it spends. By month 36, the system
has issued over 1 billion S-Credits against a much smaller spend volume.

This is not immediately harmful — credits have no exchange rate in Phase 1. But without
a credit sink, the system eventually produces credits that are worthless (too abundant
to be a meaningful routing signal). The credit sink is mandatory.

---

## 5. Inflation/Deflation Analysis

### 5.1 Earn/Spend Ratio by Phase

| Phase | Earn/Spend ratio | Economy state |
|-------|-----------------|---------------|
| 1 | 7.2× | Mildly inflationary (healthy for bootstrap) |
| 2 | 7.9× | Inflationary (acceptable — mesh is small) |
| 3 | 7.4× | Inflationary (credit value starts declining) |
| 4 | 8.0× | Strongly inflationary (sink urgently needed) |
| 5 | 6.6× | Inflationary (even with more routing demand) |

The earn/spend ratio does not converge to 1 naturally. The fundamental reason: routing
spend scales with TRAFFIC, but earning scales with AVAILABILITY × UTILIZATION.
As more nodes join, both sides grow, but earning grows faster because new nodes
immediately start earning credits (serving) while routing demand builds more slowly.

**Equilibrium point**: The system would reach earn = spend only if:
```
routing_fraction × blended_weight = earn_weight_per_tier
```
For 7B: routing_fraction × blended_weight = 1.0
At blended_weight = 2.0: routing_fraction = 50% of served tokens must be routed.

A 50% routing fraction is unrealistically high — it would mean every node routes
out half of all requests. Real routing fractions are 10–30%. Therefore natural
equilibrium is not achievable without an artificial sink.

### 5.2 Consequences of No Sink

Without a sink, by month 24 the average node balance is:
```
193,641,060 total credits / 150 nodes = 1,290,940 credits per node
```

A 7B node earns 2,592/day and has a balance of 1.3M credits. It can afford
1,290,940 / 1.0 = 1.3M cheap requests to same-tier nodes — essentially unlimited
routing. Credits cease to function as a scarcity signal.

By month 36 (500 nodes, ~2M credits/node average):
```
2 million credits / 32.0 = 62,500 requests to 70B per node
```

A single node with a 2M credit balance could route 62,500 requests to 70B nodes —
equivalent to 43 days of continuous 70B access. Credits at this scale provide no
meaningful incentive signal.

---

## 6. Credit Sink Options — Analysis

### Option A: Credits Expire After 90 Days

**Mechanics**: Credits issued with a 90-day TTL. Unclaimed credits are burned by the
directory on a nightly sweep.

**Effect at Phase 4** (earn 23.9M credits/month, spend 3.4M/month):
- Net monthly addition: 20.5M credits
- After 90 days, a node's 90-day accumulation = 2,592/day × 90 = 233,280 credits max
- With a 90-day cap, the total float in the system is bounded:
  ```
  max_float = nodes × daily_earn × 90
  Phase 4: 150 × avg_earn × 90 ≈ 150 × 6,082 × 90 = 82.1M credits maximum
  Phase 5: 500 × avg_earn × 90 ≈ 500 × 5,909 × 90 = 266M credits maximum
  ```

**Pros**:
- Simple to implement (TTL column on credit_transactions table)
- Strong signal: use your credits or lose them → encourages active routing
- Naturally limits total float without complex market mechanisms

**Cons**:
- Punishes operators who run infrastructure but have no need to route (e.g., dedicated
  providers who use P-Credits for their own consumption)
- Creates periodic "rush to spend" behavior near expiry → spiky routing load
- Complicates the ledger: every balance check must filter expired credits

**Net burn at Phase 5 with 90-day expiry**:
```
Credits burned/month = max(0, earn - spend × 90-day_cap_adjustment)
≈ (2,954,664 - 450,000) × 30 × adjustment_factor
```
Effective: roughly 40–50% of earned credits expire unused in a healthy mesh.
This is acceptable — the burned credits were "speculative earning" by idle capacity.

### Option B: 5% Transaction Fee Burned on Each Routing Transaction

**Mechanics**: When a node spends credits routing, 5% of the routing cost is burned
(destroyed), not transferred to the destination node.

**Effect**:
```
burn_per_routing_tx = 0.05 × routing_cost
```

At Phase 4 (spend 114,000 credits/day routing):
```
burn_per_day = 0.05 × 114,000 = 5,700 credits/day burned
earn_per_day = 912,236
```

Burn rate: 5,700 / 912,236 = 0.625% of daily earnings burned.

This is far too small to control inflation. To burn 50% of net earnings (20,500/day after
spend), the fee would need to be:
```
fee_rate = 20,500 / 114,000 = 18%
```
An 18% transaction fee would severely discourage routing — the opposite of the goal.

**Verdict**: Option B is insufficient as a primary sink. It could work as a minor
supplement (2%) but cannot control the inflationary dynamics alone.

### Option C: No Sink — Market Self-Regulation

**Mechanics**: Credits are issued infinitely. Market participants decide their value.

**Theoretical argument**: If credits become abundant, their value drops. Nodes will
demand more credits per routing transaction (i.e., voluntarily raise their multiplier).
This re-establishes scarcity via price discovery.

**Reality check**: This requires:
1. Nodes to have perfect information about credit supply
2. Nodes to coordinate on pricing (they don't — each sets their own multiplier independently)
3. The directory to allow multiplier increases (it does, but it's per-node, not mesh-wide)

In practice, credit abundance leads to nodes lowering their multiplier (wanting more
traffic, happy to accept cheap credits). This creates a race to the bottom: credit value
drops, routing becomes "free," the mesh loses its economic signal. This is the
Venezuela problem — hyperinflation destroys the monetary system's utility.

**Verdict**: Option C is not viable as a sole mechanism.

---

## 7. Recommendation: Option A (90-Day Expiry) as Primary Sink

**Reasoning**:

1. **Simplest to implement**: TTL on credit_transactions, nightly expiry sweep.
2. **Strongest economic signal**: "use it or lose it" creates real routing demand.
3. **Bounded float**: total credit supply is capped at `nodes × daily_earn × 90`.
4. **Aligns with mesh goal**: providers who earn must consume — this reinforces
   the "you give, you get" philosophy. Passive accumulators lose out.

**Modified recommendation**: 90-day expiry for tier ≤ 13B, 180-day expiry for
tier ≥ 30B. Rationale: high-tier operators have lower throughput and may legitimately
accumulate credits more slowly. They shouldn't be penalized for serving fewer
(but more expensive) requests.

| Tier | Credit TTL |
|------|-----------|
| ≤1B | 60 days |
| 7B | 90 days |
| 13B | 90 days |
| 30B | 180 days |
| 70B | 180 days |
| 100B+ (S-Credit, if any) | 365 days |

**Supplement with Option B at 2%** on routing transactions to create a small deflationary
pressure independent of the TTL cycle. The 2% fee is small enough to not deter routing
but adds a meaningful sink proportional to usage:

At Phase 5: 2% × 450,000 credits/day = 9,000 credits/day burned.
Over a 30-day month: 270,000 credits burned. Against a monthly earn of 88.6M, this
is minimal but directionally correct. As mesh volume grows, the burn grows proportionally.

---

## 8. Corrected Economy Simulation with Sink

**Assumptions**:
- 90-day expiry: 40% of earned credits expire before use (conservative)
- 2% transaction burn: 2% × routing spend burned

**Effective credit addition per month**:
```
effective_addition = earn - (earn × 0.40 expiry) - spend - (spend × 0.02 burn)
```

| Phase | Raw earn/month | After expiry (40%) | Spend/month | After burn (2%) | Net/month |
|-------|---------------|-------------------|-------------|-----------------|-----------|
| 1 | 648,000 | 388,800 | 89,760 | 87,964 | +300,836 |
| 2 | 2,308,200 | 1,384,920 | 290,400 | 284,592 | +1,100,328 |
| 3 | 6,634,770 | 3,980,862 | 900,000 | 882,000 | +3,098,862 |
| 4 | 27,367,080 | 16,420,248 | 3,420,000 | 3,351,600 | +13,068,648 |
| 5 | 88,639,920 | 53,183,952 | 13,500,000 | 13,230,000 | +39,953,952 |

**Even with the sink, the system accumulates significant credits.** The key metric is
whether the credits-per-node remains a meaningful scarcity signal:

| Phase | Net credits in system (cumulative, with sink) | Average per node | 70B routing access (requests) |
|-------|----------------------------------------------|-----------------|-------------------------------|
| End of Phase 1 | 1,804,800 | 225,600 | 14,100 |
| End of Phase 2 | 8,407,800 | 420,390 | 26,274 |
| End of Phase 3 | 27,002,000 | 540,040 | 33,752 |
| End of Phase 4 | 105,414,000 | 702,760 | 43,922 |
| End of Phase 5 | 585,460,000 | 1,170,920 | 73,182 |

**Interpretation**: By Phase 5, a typical node can afford 73,182 requests to 70B nodes.
This is large but represents 105 days of 70B access at 700 requests/day — reasonable
for an established mesh participant who has been earning for months.

The economy is **mildly inflationary but under control**. Credits don't become worthless;
they become gradually more abundant, which is expected as the mesh grows. The equilibrium
that emerges: operators with large balances become price-sensitive (they want good value
from routing) while operators with small balances are incentivized to serve more.

---

## 9. Credit Pricing Anchor

To prevent credits from becoming semantically meaningless numbers, the directory should
maintain a soft exchange-rate anchor between S-Credits and P-Credits:

```
1 S-Credit ≈ equivalent to 1000 tokens of 7B inference
```

This is already encoded in the spec (`tokens_per_credit = 1000` at base tier). The anchor
is descriptive, not exchangeable — you cannot swap S-Credits for P-Credits. But it gives
operators a mental model: "I have 10,000 credits → I can access 10 million tokens of
7B-equivalent inference."

---

## 10. Summary

| Metric | Phase 1 | Phase 3 | Phase 5 |
|--------|---------|---------|---------|
| Nodes | 8 | 50 | 500 |
| Daily credits earned | 21,600 | 221,159 | 2,954,664 |
| Daily credits spent | 2,992 | 30,000 | 450,000 |
| Earn/Spend ratio | 7.2× | 7.4× | 6.6× |
| Economy state | Inflationary | Inflationary | Controlled |
| Recommended sink | None needed | TTL expiry begins | TTL + 2% burn |

**Final recommendation**: Launch without a sink (months 1–6) to maximize bootstrap
incentives. Activate the 90-day TTL expiry at month 7 when the fleet reaches 20 nodes.
Activate the 2% transaction burn at month 13 when the fleet reaches 50 nodes. Review
at month 24 — if credits-per-node exceeds 500,000, reduce TTL to 60 days and raise
burn fee to 3%.
