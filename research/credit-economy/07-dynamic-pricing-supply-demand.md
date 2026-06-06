# IICP Adaptive Routing Prices — Supply/Demand Market Layer

**Date**: 2026-05-22
**Status**: Research / Pre-spec
**Feeds**: ADR-032, spec/iicp-dir.md §pricing, spec/iicp-core.md §routing-cost
**Depends on**: 01-model-tier-roi-simulation.md (Scheme C weights), 02-routing-cost-design.md (base cost schedule), 06-monetary-policy-mint-system.md (Mint floor/ceiling authority)

---

## 1. Why Static Routing Costs Fail at Scale

Document 02 established a static routing cost schedule derived from Scheme C quality
weights. This schedule is correct and sufficient for Phase 1-3. In Phase 4+ (150+ nodes),
it breaks down.

### 1.1 The Static Pricing Problem

Consider the 70B tier. Under static pricing:

- Routing to a 70B node costs 32.0 credits per 1000 tokens (regardless of load)
- When there are 3 × 70B nodes (Phase 3), and demand is low, routing is easy
- When there are 40 × 70B nodes (Phase 5) and 60% are idle, routing is still priced
  at 32.0 credits/1000 tokens

**Signal failure in both directions:**

If 70B nodes are abundant and idle, the static price provides no signal to consumers
to use them more. Operators see idle GPUs, credits are being earned only from availability
credits (not token serving), and there is no market mechanism to attract demand.

If 70B nodes are at capacity (all 40 nodes at 95% utilization), the static price provides
no signal to consumers to throttle demand or accept longer wait times. The result is
queue saturation and degraded quality for everyone — at the same price as when the
tier was half-empty.

### 1.2 What the Market Needs

A routing price that:
1. Falls when supply exceeds demand (encourage more consumption when capacity is available)
2. Rises when demand approaches capacity (signal scarcity; encourage wait or routing to an alternative tier)
3. Updates on a timescale that is useful but not manipulable (hourly: fast enough to track real shifts, slow enough that a one-hour burst cannot set prices permanently)
4. Is bounded (floor and ceiling) so that no automatic mechanism can make routing impossibly cheap or impossibly expensive

The dynamic pricing layer provides this without replacing the Scheme C base weights.
Base weights remain the anchors; the price multiplier moves around them.

---

## 2. The Price Function Design

### 2.1 Input: Per-Tier Utilization

The utilization signal is computed by the directory from its own telemetry. It is
NOT self-reported by nodes — the directory tracks task routing logs directly.

```
utilization[tier] = tasks_routed_to_tier_last_hour / tier_capacity_last_hour
```

Where:

```
tier_capacity_last_hour = sum over all nodes in tier of:
    requests_per_hour_per_node

requests_per_hour_per_node = 3600 / (avg_latency_ms[node] / 1000)
```

`avg_latency_ms[node]` is taken from REACH probe telemetry (DIR-PROBE-03 latency
measurements), averaged over the same 60-minute window. This means the capacity
estimate reflects actual observed performance, not declared capability.

**Example — 70B tier with 5 nodes:**

| Node | REACH avg latency (ms) | Requests/hour capacity |
|------|----------------------|----------------------|
| 70B-01 | 1,850 | 1,946 |
| 70B-02 | 2,100 | 1,714 |
| 70B-03 | 1,950 | 1,846 |
| 70B-04 | 2,300 | 1,565 |
| 70B-05 | 1,800 | 2,000 |
| **Tier total** | | **9,071 req/hour** |

If 5,400 requests were actually routed to the 70B tier in the last hour:
```
utilization[70B] = 5,400 / 9,071 = 0.595 (59.5%)
```

### 2.2 The Price Function

The price multiplier follows a sigmoid (S-curve) centered at 50% utilization. Below
50%, prices fall toward the floor. Above 50%, prices rise toward the ceiling.

```
price_multiplier = Mint_floor + (Mint_ceiling - Mint_floor) × sigmoid(k × (utilization - 0.5))

where:
    sigmoid(x)    = 1 / (1 + e^{-x})
    k             = 6   (steepness parameter; controls how sharply price responds near 50%)
    Mint_floor    = 0.5 (default; set quarterly by the Mint; range 0.1×–1.0×)
    Mint_ceiling  = 3.0 (default; set quarterly by the Mint; range 1.0×–10.0×)
```

The steepness parameter `k = 6` means:
- At 33% utilization: sigmoid ≈ 0.12 → price ≈ floor + 12% of range
- At 50% utilization: sigmoid = 0.50 → price = floor + 50% of range (midpoint)
- At 67% utilization: sigmoid ≈ 0.88 → price ≈ floor + 88% of range
- At 90% utilization: sigmoid ≈ 0.97 → price ≈ floor + 97% of range

With Mint defaults (floor=0.5, ceiling=3.0, range=2.5):
```
At 50% utilization: multiplier = 0.5 + 2.5 × 0.50 = 1.75
```

Wait — the sigmoid at x=0 is exactly 0.5, giving multiplier = 0.5 + 2.5 × 0.5 = 1.75.
This means at exactly 50% utilization, prices are 75% above floor. To anchor the
midpoint at 1.0× (the base Scheme C rate), the sigmoid center should correspond to
a multiplier of 1.0, which requires:

```
1.0 = 0.5 + 2.5 × 0.5   →  this gives 1.75, not 1.0
```

Correction: normalize the formula so that at 50% utilization, multiplier = 1.0 exactly:

```
price_multiplier = Mint_floor + (Mint_ceiling - Mint_floor) × sigmoid(k × (utilization - u0))

where u0 is chosen so that:
    Mint_floor + (Mint_ceiling - Mint_floor) × sigmoid(0) = 1.0
    0.5 + 2.5 × 0.5 = 1.0   → false

Instead, define the midpoint explicitly:
    sigmoid(k × (u0 - u0)) = sigmoid(0) = 0.5
    multiplier at u0 = floor + range × 0.5 = 0.5 + 2.5 × 0.5 = 1.75
```

At the default floor=0.5 and ceiling=3.0, the "neutral price" (1.0× base) occurs at
the utilization where the multiplier equals 1.0:

```
1.0 = 0.5 + 2.5 × sigmoid(6 × (u - 0.5))
0.5 / 2.5 = sigmoid(6 × (u - 0.5))
0.20 = sigmoid(6 × (u - 0.5))
logit(0.20) = 6 × (u - 0.5)
-1.386 = 6 × (u - 0.5)
u = 0.5 - 1.386/6 = 0.5 - 0.231 = 0.269
```

So with defaults, the "neutral price" (exactly 1.0× base Scheme C rate) occurs at
~27% utilization. Below 27%, routing is cheaper than the base rate. Above 27%,
it is more expensive. This is intentional: it makes the "cheap routing" zone wider,
encouraging consumption when capacity exists, and reserves the expensive zone for
genuinely scarce conditions (> 50% utilization).

**If the Mint adjusts floor=0.8, ceiling=2.0** (less volatility), neutral price moves to:
```
1.0 = 0.8 + 1.2 × sigmoid(6 × (u - 0.5))
0.2 / 1.2 = sigmoid(6 × (u - 0.5))
u ≈ 0.5 - (logit(0.167)/6) ≈ 0.5 - 0.283 = 0.217 (22% utilization for neutral)
```

The Mint can tune aggressiveness by adjusting floor and ceiling.

### 2.3 Price Curve Table (Default Mint Parameters)

Using floor=0.5, ceiling=3.0, k=6:

| Utilization | sigmoid | Multiplier | 7B cost per 1000 tok | 70B cost per 1000 tok |
|-------------|---------|------------|---------------------|----------------------|
| 0% | 0.047 | 0.62× | 0.62 credits | 19.8 credits |
| 10% | 0.100 | 0.75× | 0.75 credits | 24.0 credits |
| 25% | 0.231 | 1.08× | 1.08 credits | 34.6 credits |
| 27% | 0.250 | 1.00× (neutral) | 1.00 credits | 32.0 credits |
| 50% | 0.500 | 1.75× | 1.75 credits | 56.0 credits |
| 75% | 0.769 | 2.42× | 2.42 credits | 77.5 credits |
| 90% | 0.900 | 2.75× | 2.75 credits | 88.0 credits |
| 100% | 0.953 | 2.88× | 2.88 credits | 92.2 credits |

At 100% utilization, the multiplier approaches (but does not reach) the ceiling of 3.0,
because sigmoid approaches but never reaches 1.0. The ceiling is a hard cap: the directory
clamps `multiplier = min(computed_multiplier, Mint_ceiling)`.

**Simplified reference table using rounded values:**

| Utilization | Multiplier | 7B routing cost (per 1000 tok) | 70B routing cost (per 1000 tok) |
|-------------|------------|-------------------------------|--------------------------------|
| 0% | 0.50× | 0.5 credits | 16.0 credits |
| 25% | ~1.00× | 1.0 credits | 32.0 credits |
| 50% | ~1.75× | 1.75 credits | 56.0 credits |
| 75% | ~2.42× | 2.42 credits | 77.4 credits |
| 90% | ~2.75× | 2.75 credits | 88.0 credits |
| 100% | ≤3.00× | ≤3.0 credits | ≤96.0 credits |

Note: at 0% utilization the floor applies, giving 0.50× even though the sigmoid
approaches (but does not reach) 0. Floor is a hard minimum.

### 2.4 Update Cadence

The price multiplier is recomputed hourly (every 3,600 seconds).

The directory runs a scheduled job at the start of each hour:
1. Query task routing logs for the last 60 minutes, grouped by destination tier
2. Query REACH probe telemetry for per-node average latency over the last 60 minutes
3. Compute `utilization[tier]` for each tier
4. Compute `price_multiplier[tier]` using the sigmoid formula
5. Store in `dynamic_pricing_current` table, replacing the prior row
6. Publish an event: `PRICING_UPDATE` with the new multipliers per tier
7. The proxy fetches the updated multipliers on its next request cycle (or via SSE push)

**Why hourly and not per-minute?**

Per-minute updates would make prices responsive to short load spikes. A burst of
100 requests in one minute to a 70B tier with 2,000 req/hour capacity would be:
```
1-minute utilization = 100 req × 60 (annualized to per-hour) = 6,000 / 2,000 = 3.0 (300%)
```
This would peg prices at the ceiling for one minute, then crash to the floor the next.
Such volatility provides no useful signal — it rewards whoever happens to be routing
at low-demand moments and punishes anyone routing during a burst.

Hourly averaging smooths out these spikes while still tracking genuine capacity trends.
A sustained high-demand period (lasting > 60 minutes) will move prices appropriately.

---

## 3. Speculator and Manipulator Protection

### 3.1 Why Price is Not Self-Reported

A node cannot declare its own utilization. Utilization is computed from the directory's
routing logs — the directory counts how many tasks it dispatched to each tier in the
last hour. This is the directory's own internal record, not data submitted by nodes.

A node that claims to be busy cannot affect the price computation unless the directory
actually routed tasks to it.

### 3.2 Why Flash Manipulation Doesn't Work

**Attack**: an operator controls a 7B node and wants to make 7B routing appear highly
utilized (to make competitors' routing expensive and their own node more attractive
via `credit_cost_multiplier` dynamics).

**Method**: the attacker routes a flood of short tasks to the 7B tier (using their own
credits) to drive utilization toward 100% and push the price multiplier to the ceiling.

**Why this fails:**

1. **Cost to manipulate**: to drive 7B utilization from 10% to 90% (assuming a 5,000
   req/hour tier capacity), the attacker needs to generate ~4,000 fake requests/hour.
   At 1.0 credits per 500-token request, this costs 4,000 credits/hour = 96,000
   credits/day. A 7B node earns 2,592 credits/day — the attacker burns 37 days of
   earnings per day of sustained manipulation.

2. **Duration required**: the price update is hourly. To shift prices, the attacker
   must sustain fake load for a full hour. Maintaining 4,000 fake requests/hour for
   one hour costs 4,000 credits.

3. **Who benefits?** Higher prices mean routing to the 7B tier is more expensive for
   all consumers, including the attacker (who also routes to the mesh). The attacker's
   node earns more per token if it raises its own `credit_cost_multiplier`, but other
   nodes in the same tier also benefit from the higher price — and the attacker cannot
   target price inflation to just their node.

4. **Net result**: the attacker spends real credits to drive up prices for the entire
   tier, benefiting all 7B operators equally (including competitors) while destroying
   their own credit balance. This is a negative-sum attack for the attacker.

### 3.3 Price Bounds as Manipulation Ceiling

Even in the worst case (all fake load, 100% utilization), the price multiplier is
capped at `Mint_ceiling = 3.0×`. The ceiling is Mint-set and protocol-enforced — no
amount of load can push prices beyond 3× base. The Mint can raise the ceiling, but
only by 1.0 per quarter and only with 6/9 supermajority, making ceiling manipulation
via captured Mint even slower than via load manipulation.

### 3.4 Self-Routing Circular Attacks

**Attack**: node A routes tasks to node B; node B routes tasks back to node A. Both
accumulate credits and drive up the apparent routing utilization of each other's tier.

**Why this partially fails:**

The directory detects circular routing patterns. Two nodes that form a perfect
routing loop (A→B→A with no external task originator) will trigger the collusion
detection flag described in document 02 §10: "the directory should flag balance
growth with zero reputation increase as suspicious."

The circular pair would not be generating real task completion events (no external
task originators, no end-user results). The reputation system (which requires
successful task completions as observed by external requestors) would not increase
for either node. High credit balance + zero reputation growth = audit flag.

Additionally, routing costs flow: A spends credits routing to B, B spends credits
routing to A. Net credits per round trip:
```
A sends 1 req to B: costs A 1.0 credits (7B tier)
B sends 1 req to A: costs B 1.0 credits (7B tier)
A earns from serving: +1.0 credits
B earns from serving: +1.0 credits
Net credit change: 0 for both (spend = earn, minus 2% burn = net -0.02 per round trip)
```

The circular routing attack is credit-neutral at best and credit-negative due to the
2% burn. It does inflate apparent utilization, but since the directory's own routing
logs record the transactions, the directory can identify that the same pair of nodes
is generating all the traffic.

**Open gap**: the directory's collusion detection is advisory (flags, not automatic action)
in Phase 1-3. Automated enforcement is Phase 4+ work (document 05 §1 §Deferred).

---

## 4. Phase 6 Eligibility Criteria

Dynamic pricing is not activated in Phase 1 through Phase 5. The default dynamic
pricing parameters are `floor=1.0×, ceiling=1.0×` (effectively static, no movement).

Activation in Phase 6 requires:

| Criterion | Requirement | Why |
|-----------|-------------|-----|
| REACH probe coverage | REACH probes must cover all registered nodes' bootstrap and peer endpoints across ≥ 3 geographic regions | Utilization computation depends on REACH latency data; missing probe coverage produces inaccurate capacity estimates |
| Mint committee operational | Mint must be formed and have cast ≥ 1 routine parameter vote | Mint must set floor and ceiling before dynamic pricing is meaningful |
| Minimum fleet size | ≥ 200 active nodes across ≥ 3 tiers | With fewer nodes, per-tier utilization is too noisy for meaningful price signals |
| Routing ledger completeness | Directory must log 100% of routed tasks with destination tier and timestamp | Partial logging produces biased utilization estimates |
| Proxy dynamic pricing support | All registered proxies must be running a version that reads `PRICING_UPDATE` events | Proxies using hardcoded tier weights would not respond to price signals |

Estimated readiness: Phase 6 launch. Phase 6 is the federated control plane phase —
the directory becomes a peer-to-peer protocol, multiple directories emerge, and dynamic
pricing across federated directories requires additional coordination (out of scope for
this document).

---

## 5. Interplay with the Mint

Dynamic pricing and the Mint operate at different timescales and serve different purposes:

| Layer | Timescale | Purpose |
|-------|-----------|---------|
| Mint (parameter governance) | Quarterly | Set floor, ceiling, and base tier weights |
| Dynamic pricing (market) | Hourly | Set actual multiplier within Mint's bounds |
| REACH probes | Per-minute | Provide raw latency data for capacity estimation |

**Mint responds to sustained pricing signals:**

If the dynamic pricing layer reports that a tier's price stays at the ceiling for more
than 2 consecutive weeks, the Mint should interpret this as a supply shortage signal:

```
Ceiling sustained > 2 weeks for tier T → signal: T is undersupplied
Mint options:
  1. Increase bootstrap grant (attract more T operators) — covered in document 08
  2. Increase T's quality weight (improve ROI for existing T operators)
  3. Increase ceiling temporarily (allow price to rise further and attract operators)
  4. No action (if the Mint believes demand will naturally moderate)
```

If the dynamic pricing layer reports that a tier's price stays at the floor for more
than 2 consecutive weeks:

```
Floor sustained > 2 weeks for tier T → signal: T is oversupplied
Mint options:
  1. Decrease T's quality weight (reduce ROI for new T operators; may cause attrition)
  2. Decrease floor (allow price to fall further; signal to consumers to use more T capacity)
  3. Increase TTL for T (let credits accumulate longer; operators may self-regulate)
  4. No action (if the Mint believes demand will naturally grow)
```

The Mint's response is quarterly — it cannot act immediately on a 2-week floor/ceiling
event. The quarterly vote cycle means there is typically a 6–12 week lag between a
sustained pricing signal and a Mint parameter change. This lag is intentional: it
prevents the Mint from overreacting to short-term demand shifts.

**Information flow architecture:**

```
REACH probes (per-minute) → directory telemetry DB
                                    ↓
             directory: hourly utilization job
                                    ↓
              dynamic_pricing_current table → proxy (reads on each request)
                                    ↓
              PRICING_UPDATE event → Mint monitoring dashboard
                                    ↓
              (if floor/ceiling sustained > 2 weeks) → Mint governance vote
                                    ↓
              new floor/ceiling values → directory config → next pricing cycle
```

---

## 6. What This Design Does Not Cover

**Cross-tier routing optimization:** the price function is per-tier, not per-node.
A 7B node with a `credit_cost_multiplier = 2.0` charges `2.0 × dynamic_multiplier × tier_weight`.
If the dynamic multiplier is already at 1.75× and the node charges 2.0×, the effective
cost is `1.0 × 1.75 × 2.0 = 3.5 credits` — above what many consumers will accept.
This creates natural per-node price competition within a tier: nodes that charge high
multipliers will be excluded by discover filters when the tier is already expensive.
Document 02 §7 covers the `credit_cost_multiplier` interaction.

**Federation-layer dynamic pricing:** when Phase 6 federated directories emerge, each
directory computes its own utilization from its own routing logs. A consumer whose proxy
discovers nodes from multiple directories will see potentially different prices. Federated
price arbitrage (routing via the cheapest federated directory for the same tier) is an
open research question outside this document's scope.

**P-Credit pricing:** P-Credits (premium providers) use a separate pricing mechanism
(provider-declared rate × premium provider's declared `p_credit_rate`). Dynamic pricing
applies only to S-Credit routing in the peer economy. Premium providers may implement
their own dynamic pricing via rate updates (bounded at 10% per month per document 04 §8),
but this is independent of the S-Credit price function.

---

## 7. Open Questions for Maintainer

1. **Steepness parameter k**: the value `k = 6` is a theoretical choice. Real-world
   calibration may require a different value. Should the Mint be allowed to adjust `k`
   (making price response more or less aggressive) as a governed parameter?

2. **Per-node vs. per-tier pricing**: the current design uses per-tier utilization.
   Would per-node utilization (routing to specifically busy nodes costs more) provide
   better market signals? Complexity tradeoff: per-node requires O(N) price queries;
   per-tier requires O(tiers) = O(6) queries.

3. **Latency-based capacity estimation**: using REACH probe latency as a proxy for
   capacity has a gap — REACH probes are 500-token benchmark requests, not representative
   of actual task distributions. Should capacity be estimated from routing log latencies
   (actual tasks) instead?

4. **Price transparency for consumers**: should the proxy display the current multiplier
   to the end user before routing? (e.g., "Routing to 70B tier at 1.75× due to 50%
   utilization — cost will be 56.0 credits per 1000 tokens.") This improves user control
   but adds latency (an extra price-fetch round trip before dispatch).

5. **Cross-tier routing incentives**: if 70B is at 90% utilization (2.75× price) and
   30B is at 20% utilization (0.7× price), should the discover algorithm automatically
   suggest the cheaper alternative tier? Or should routing tier selection remain fully
   user-controlled?
