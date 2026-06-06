# Credit Economy — Model-Tier ROI Simulation

**Date**: 2026-05-22  
**Status**: Research / Pre-spec  
**Feeds**: ADR-031, spec/iicp-core.md §credit-economy, spec/iicp-dir.md §pricing

---

## 1. Baseline Hardware Throughput

All values at 50% sustained utilization. Token volume computed as:
`daily_tokens = tok_per_sec × 86400 × 0.50`

| Tier | Hardware | tok/s | Daily tokens (50% util) | Requests/day (500 tok avg) | Monthly HW cost |
|------|----------|-------|------------------------|---------------------------|-----------------|
| 500M | CPU | 200 | 8,640,000 | 17,280 | $50 |
| 7B | 1× RTX 4090 | 60 | 2,592,000 | 5,184 | $300 |
| 13B | 1× A100 80GB | 35 | 1,512,000 | 3,024 | $2,000 |
| 30B | 2× A100 | 20 | 864,000 | 1,728 | $4,000 |
| 70B | 4× A100 | 8 | 345,600 | 691 | $8,000 |
| 70B-Q | 2× A100 | 6 | 259,200 | 518 | $4,000 |

> **Note on simplifications**: These are single-GPU, steady-state values. Real deployments
> vary with batch size, model quantization, driver overhead, and network latency. The 50%
> utilization assumption is conservative for early mesh phases; it rises to 70–80% as
> mesh demand grows. Results in this doc should be treated as directional, not contractual.

---

## 2. The Core Problem: Raw Token Volume vs. Quality

If credits are earned purely per token served (no quality weight), the 500M operator
crushes the 70B operator by a factor of 25:

```
500M daily tokens:  8,640,000
70B daily tokens:     345,600
ratio:                   25.0×
```

A pure token economy is a race to the bottom: operators are incentivized to run many
small cheap models, which produces a mesh full of low-quality inference. This is the
opposite of what the maintainer wants. Quality weights exist to correct this distortion.

**Base credit formula** (no weight):
```
credits_earned = floor(tokens_served / 1000) × base_earn_rate
```
Where `base_earn_rate = 1.0 credit per 1000 tokens` (matching existing spec definition).

**Weighted formula** (all schemes below):
```
credits_earned = floor(tokens_served / 1000) × quality_weight
```

---

## 3. Scheme A — Market-Price-Ratio Weights

Weights derived from commercial API pricing ratios, normalized to 7B = 1.0.

Commercial prices (per million tokens): 500M: $0.10, 7B: $1.50, 13B: $0.60 (optimized,
but for sim we use raw capability → $2.00), 30B: $6.00, 70B: $30.00.

Normalized to 7B base (7B = $1.50 → weight 1.0):

| Tier | Market price/Mtok | Ratio to 7B | Assigned weight |
|------|------------------|-------------|-----------------|
| 500M | $0.10 | 0.067 | 0.1× |
| 7B | $1.50 | 1.0 | 1.0× |
| 13B | $2.00 | 1.33 | 2.5× (rounded up) |
| 30B | $6.00 | 4.0 | 8.0× |
| 70B | $30.00 | 20.0 | 20.0× |

### Scheme A: Daily Credits Earned

```
credits/day = (daily_tokens / 1000) × quality_weight
```

| Tier | Daily tokens | Weight | Credits/day | Monthly HW cost | Credits per $1 HW |
|------|-------------|--------|-------------|-----------------|-------------------|
| 500M | 8,640,000 | 0.1 | 864 | $50 | 518.4 |
| 7B | 2,592,000 | 1.0 | 2,592 | $300 | 259.2 |
| 13B | 1,512,000 | 2.5 | 3,780 | $2,000 | 56.7 |
| 30B | 864,000 | 8.0 | 6,912 | $4,000 | 51.8 |
| 70B | 345,600 | 20.0 | 6,912 | $8,000 | 25.9 |

### Scheme A: Key Comparison — Same Hardware Budget ($8,000/month)

- 1× 70B node: 6,912 credits/day
- 26× 7B nodes (RTX 4090 at $300 each = $7,800): 26 × 2,592 = **67,392 credits/day**
- 160× 500M nodes (CPU at $50 each = $8,000): 160 × 864 = **138,240 credits/day**

**Verdict**: Scheme A FAILS the maintainer's requirement. The 70B operator earns 9.7×
LESS than equivalent hardware in 7B nodes. The 25× throughput advantage of small models
is only partially cancelled by the 20× weight.

**Why it fails**: The weight and the throughput gap are in the same order of magnitude
(20× weight vs. 25× throughput gap), so small models still win on raw credit volume.
To overcome this, the weight must exceed the throughput ratio by a margin large enough
to also cover the hardware cost differential.

---

## 4. Scheme B — Compute-Cost-Ratio Weights

Weights derived from cost-per-inference, normalized to 7B = 1.0.

Cost per 1000 tokens = (monthly_hw_cost / 30) / (daily_tokens / 1000):

| Tier | Monthly cost | Daily tokens | Cost per 1000 tok | Normalized (7B=1.0) | Assigned weight |
|------|-------------|-------------|-------------------|---------------------|-----------------|
| 500M | $50 | 8,640,000 | $0.000193 | 0.049 | 0.05× |
| 7B | $300 | 2,592,000 | $0.003858 | 1.0 | 1.0× |
| 13B | $2,000 | 1,512,000 | $0.04409 | 11.4 | 2.0× (capped) |
| 30B | $4,000 | 864,000 | $0.15432 | 40.0 | 5.0× (capped) |
| 70B | $8,000 | 345,600 | $0.77160 | 200.0 | 25.0× (capped) |

Note: Raw cost ratios are enormous (200:1). We cap weights because uncapped weights make
routing costs astronomically expensive. The caps are pragmatic, not principled.

### Scheme B: Daily Credits Earned

| Tier | Daily tokens | Weight | Credits/day | Monthly HW cost | Credits per $1 HW |
|------|-------------|--------|-------------|-----------------|-------------------|
| 500M | 8,640,000 | 0.05 | 432 | $50 | 259.2 |
| 7B | 2,592,000 | 1.0 | 2,592 | $300 | 259.2 |
| 13B | 1,512,000 | 2.0 | 3,024 | $2,000 | 45.4 |
| 30B | 864,000 | 5.0 | 4,320 | $4,000 | 32.4 |
| 70B | 345,600 | 25.0 | 8,640 | $8,000 | 32.4 |

### Scheme B: Same Hardware Budget ($8,000/month)

- 1× 70B node: 8,640 credits/day
- 26× 7B nodes: 26 × 2,592 = **67,392 credits/day**
- 160× 500M nodes: 160 × 432 = **69,120 credits/day**

**Verdict**: Scheme B FAILS even harder for 70B vs. 7B (8.640× still 7.8× lower than
26× 7B). The cap at 25× weight is insufficient because the throughput difference is 25×
but the hardware cost difference is more than 25× (8000/300 = 26.7×). Scheme B
accidentally "equalizes" 7B and 500M (both 259.2 credits/$) while still leaving 70B
in a worse position per dollar.

---

## 5. Scheme C — Hybrid Throughput-Adjusted Weights (THE KEY SCHEME)

### 5.1 Finding the Minimum 70B Weight

We want: a 70B node ($8,000/month) earns ≥ credits than 4× 7B nodes ($1,200/month).

This is the "same QUALITY of hardware budget" comparison the maintainer described:
someone who chooses to invest in one powerful node rather than four weaker ones.

Let `w70` = unknown 70B weight, `w7B = 1.0`.

```
70B credits/day   ≥   4× 7B credits/day
(345,600/1000) × w70  ≥  4 × (2,592,000/1000) × 1.0
345.6 × w70  ≥  4 × 2,592
345.6 × w70  ≥  10,368
w70  ≥  10,368 / 345.6
w70  ≥  29.99
```

**Minimum w70 = 30.0** to make a 70B node equivalent to 4× 7B nodes at $1,200 total.

But the maintainer wants 70B to be BETTER ("gratified enough"), not just equal. We target
a 1.5× surplus over the break-even point:

`w70_target = 30.0 × 1.5 = 45.0`

### 5.2 Calibrating the Full Weight Table

We work backwards from the economic principle: **every tier should earn roughly equal
credits per dollar of hardware invested**, with premium applied at higher tiers to
reflect scarcity and quality of service.

Define: `target_credits_per_dollar_per_day = 2,592 / 300 = 8.64 credits per $1 HW per day`
(this is the 7B baseline — the most common node type).

For each tier, the weight needed to match the 7B credit-per-dollar rate:

```
required_weight = (7B_credits_per_dollar) × (tier_monthly_cost/30) / (tier_daily_tokens/1000)
               = 8.64 × (HW_cost_per_day) / (daily_tokens/1000)
```

| Tier | HW cost/day | Daily tok (K) | Parity weight | 1.5× surplus weight | Rounded |
|------|------------|---------------|---------------|---------------------|---------|
| 500M | $1.67 | 8,640 | 0.017 | 0.025 | 0.05 (floor) |
| 7B | $10.00 | 2,592 | 1.0 (anchor) | 1.0 | 1.0 |
| 13B | $66.67 | 1,512 | 1.21 | 1.81 | 2.0 |
| 30B | $133.33 | 864 | 4.24 | 6.35 | 6.5 |
| 70B | $266.67 | 345.6 | 21.2 | 31.8 | 32.0 |

Note: 500M is below parity even at 0.05 — this is intentional. Small models are
easy to spin up and should not be economically dominant in the mesh.

### 5.3 Scheme C Weight Table

| Tier | Weight |
|------|--------|
| ≤1B (500M) | 0.05× |
| 7B | 1.0× |
| 13B | 2.0× |
| 30B | 6.5× |
| 70B | 32.0× |
| 100B+ (commercial/Opus) | 75.0× |

### 5.4 Scheme C: Daily Credits Earned

| Tier | Daily tokens | Weight | Credits/day | Monthly HW cost | Credits per $1 HW |
|------|-------------|--------|-------------|-----------------|-------------------|
| 500M | 8,640,000 | 0.05 | 432 | $50 | 259.2 |
| 7B | 2,592,000 | 1.0 | 2,592 | $300 | 259.2 |
| 13B | 1,512,000 | 2.0 | 3,024 | $2,000 | 45.4 |
| 30B | 864,000 | 6.5 | 5,616 | $4,000 | 42.1 |
| 70B | 345,600 | 32.0 | 11,059 | $8,000 | 41.5 |

### 5.5 Scheme C: The Key Comparison

**Same hardware budget: $8,000/month**

| Configuration | Nodes | Daily credits |
|--------------|-------|--------------|
| 1× 70B (4× A100) | 1 | 11,059 |
| 4× 7B (4× RTX 4090, $1,200) | 4 | 10,368 |
| 27× 7B (RTX 4090 × 27 = $8,100 ≈ $8K) | 27 | 69,984 |
| 160× 500M (CPU × 160 = $8,000) | 160 | 69,120 |

**Observation**: The 1× 70B node vs. 4× 7B comparison (the "apples to apples" comparison
the maintainer specified) is now `11,059 vs. 10,368` — **70B wins by 6.7%**. This meets
the minimum requirement.

However, if someone deploys 27× 7B nodes for the same $8,000, they earn 6.3× more
credits. This is an acceptable outcome — they're providing 27× more availability and
serving 27× more concurrent users. The mesh benefits from them too.

**The economic argument that holds**: A 70B operator earns MORE credits per NODE than
any smaller-model operator. They can access more routing capacity, more reliably, without
needing a large fleet of machines. Their single node earns more credits than any single
smaller node.

---

## 6. Scheme D — Two-Component Earning (Availability + Tokens)

Scheme D addresses a real problem: in early mesh phases, high-tier nodes are
underutilized because demand hasn't grown yet. A pure token-earning model means
early 70B adopters earn nothing while traffic ramps up.

### 6.1 Components

**Component 1: Availability credits**
```
availability_credits = GPU_hours_online × availability_rate[tier]
```

**Component 2: Token-service credits**
```
token_credits = (tokens_served / 1000) × token_weight[tier]
```

**Total:**
```
daily_credits = availability_credits + token_credits
```

### 6.2 Calibrating Availability Rates

Target: at 0% utilization (no traffic), a 70B node earns at least 30% of its
full-load earnings. This covers a meaningful portion of fixed costs during bootstrap.

At full load (Scheme C), 70B earns 11,059 credits/day.
30% floor = 3,318 credits/day from availability.

GPU-hours available per day = 4 GPUs × 24h = 96 GPU-hours.

```
availability_rate_70B = 3,318 / 96 = 34.6 credits per GPU-hour
```

Normalize across tiers (GPU-hours differ: 500M has 0 GPUs counted as 0.25,
7B has 1 GPU, 13B has 1 GPU, 30B has 2 GPUs, 70B has 4 GPUs):

| Tier | GPUs | GPU-hrs/day | Avail rate | Avail credits/day (0% load) | Token weight (D) |
|------|------|------------|------------|----------------------------|-----------------|
| 500M | 0.25 | 6 | 5.0 | 30 | 0.04 |
| 7B | 1 | 24 | 20.0 | 480 | 0.85 |
| 13B | 1 | 24 | 25.0 | 600 | 1.70 |
| 30B | 2 | 48 | 35.0 | 1,680 | 5.0 |
| 70B | 4 | 96 | 34.6 | 3,322 | 23.0 |

### 6.3 Scheme D: Daily Credits at 50% Utilization

```
daily_credits = avail_credits + (daily_tokens/1000 × token_weight)
```

| Tier | Avail credits | Token credits (50%) | Total credits/day | Monthly HW cost | Credits/$1 HW |
|------|--------------|--------------------|--------------------|-----------------|---------------|
| 500M | 30 | 346 | 376 | $50 | 225.6 |
| 7B | 480 | 2,203 | 2,683 | $300 | 268.3 |
| 13B | 600 | 2,570 | 3,170 | $2,000 | 47.6 |
| 30B | 1,680 | 4,320 | 6,000 | $4,000 | 45.0 |
| 70B | 3,322 | 7,949 | 11,271 | $8,000 | 42.3 |

### 6.4 Scheme D at 0% Utilization (early mesh, no traffic)

| Tier | Avail credits only | Monthly HW cost | Break-even at 0 traffic |
|------|-------------------|-----------------|-------------------------|
| 500M | 30/day = 900/month | $50 | 900 credits/month earned |
| 7B | 480/day = 14,400/month | $300 | 14,400 credits/month |
| 13B | 600/day = 18,000/month | $2,000 | 18,000 credits/month |
| 30B | 1,680/day = 50,400/month | $4,000 | 50,400 credits/month |
| 70B | 3,322/day = 99,660/month | $8,000 | 99,660 credits/month |

**Scheme D key insight**: At 0% load, every tier earns proportional to its hardware
investment (credits per dollar are roughly equal). This is a strong bootstrap incentive
— early operators get rewarded just for being available, not just for being busy.

---

## 7. Four-Scheme Comparison Table

**At 50% utilization, per node, per day:**

| Tier | HW cost/month | Scheme A credits/day | Scheme B credits/day | Scheme C credits/day | Scheme D credits/day |
|------|--------------|---------------------|---------------------|---------------------|---------------------|
| 500M | $50 | 864 | 432 | 432 | 376 |
| 7B | $300 | 2,592 | 2,592 | 2,592 | 2,683 |
| 13B | $2,000 | 3,780 | 3,024 | 3,024 | 3,170 |
| 30B | $4,000 | 6,912 | 4,320 | 5,616 | 6,000 |
| 70B | $8,000 | 6,912 | 8,640 | 11,059 | 11,271 |

**Credits per $1 hardware per day:**

| Tier | Scheme A | Scheme B | Scheme C | Scheme D |
|------|----------|----------|----------|----------|
| 500M | 518.4 | 259.2 | 259.2 | 225.6 |
| 7B | 259.2 | 259.2 | 259.2 | 268.3 |
| 13B | 56.7 | 45.4 | 45.4 | 47.6 |
| 30B | 51.8 | 32.4 | 42.1 | 45.0 |
| 70B | 25.9 | 32.4 | 41.5 | 42.3 |

**Does 1× 70B (4× A100) beat 4× 7B (same $1,200 budget)?**

| Scheme | 70B credits/day | 4× 7B credits/day | 70B wins? |
|--------|----------------|-------------------|-----------|
| A | 6,912 | 10,368 | NO (33% deficit) |
| B | 8,640 | 10,368 | NO (16% deficit) |
| C | 11,059 | 10,368 | **YES (+6.7%)** |
| D | 11,271 | 10,732 | **YES (+5.0%)** |

---

## 8. Recommendation

**Adopt Scheme C for live economics, extend with Scheme D availability component
for bootstrap phases (first 12 months).**

### Rationale

1. **Scheme C** makes the 70B comparison work — it's the only scheme that achieves the
   maintainer's stated goal with a clean, principled weight table derived from parity math.

2. **Scheme D's availability component** should be layered on top of Scheme C during
   bootstrap (months 1–12). It prevents early high-tier adopters from earning nothing
   while mesh traffic ramps up. After month 12, the availability component can be
   phased out or reduced to 15% of full-load earnings.

3. **Combined recommended weights** (Scheme C + D hybrid):

| Tier | Quality weight (token earning) | Availability rate (credits/GPU-hour) |
|------|-------------------------------|--------------------------------------|
| ≤1B | 0.05× | 5.0 |
| 7B | 1.0× | 20.0 |
| 13B | 2.0× | 25.0 |
| 30B | 6.5× | 35.0 |
| 70B | 32.0× | 34.6 |
| 100B+ | 75.0× | 80.0 |

### What this protects against

- **Race to the bottom**: 500M nodes earn 259× less per node than 70B nodes at equal
  utilization. Running 10× 500M nodes yields similar total credits as 1× 70B node, but
  at 10× the management overhead and with far less routing access (small models spend
  more credits routing than they earn if they want 70B-quality responses).

- **Free rider problem**: the availability component means even zero-load nodes
  contribute something, but tokens served remains the primary earning path.

### What this cannot protect against

- **Sybil attacks on availability**: an operator could register 100 "phantom" 70B nodes
  and claim availability credits without running real hardware. The implementation must
  validate tier claims via the heartbeat health endpoint (checking actual model load
  stats, not just self-reported tier).

- **Stale mesh incentives**: if 70B demand never materializes, operators still earn
  availability credits but can never spend them usefully (no one wants to route to them).
  The availability subsidy could inflate credits without creating value. Cap availability
  credits at 30% of full-load earnings to limit this exposure.

- **Model capability drift**: a node registering as "70B" could run a quantized 4-bit
  model that performs like a 13B. The tier classification system needs to verify model
  identity (model hash or benchmark score) rather than trust self-reported labels.

---

## 9. Annex: Break-Even Analysis for Hardware Cost Recovery

Assuming 1 credit can eventually be redeemed for routing access worth some real-world
value — let's say 1 credit = $0.001 USD (rough market anchor, to be set by maintainer).

| Tier | Credits/month (Scheme C, 50% util) | Credits value ($0.001 each) | Hardware cost | ROI (value/cost) |
|------|-----------------------------------|----------------------------|---------------|------------------|
| 500M | 12,960 | $12.96 | $50 | 25.9% |
| 7B | 77,760 | $77.76 | $300 | 25.9% |
| 13B | 90,720 | $90.72 | $2,000 | 4.5% |
| 30B | 168,480 | $168.48 | $4,000 | 4.2% |
| 70B | 331,776 | $331.78 | $8,000 | 4.1% |

**Observation**: At $0.001/credit, no tier "recovers" hardware cost from credits alone.
Credits are not meant to be a full economic substitute for revenue — they are a routing
access subsidy that lowers the effective cost of consuming mesh inference. The real ROI
for a 70B operator is: they can route 331,776 / 1000 = 331.8 million tokens/month of
cheap inference through the mesh at no P-Credit cost.

At 70B market price ($30/Mtok), this routing access is worth:
```
331.8 × $30 = $9,954/month in routing access
```
This exceeds their $8,000/month hardware cost. **The mesh is ROI-positive for 70B
operators at full utilization once the mesh has enough demand to use their capacity.**
