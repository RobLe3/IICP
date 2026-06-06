# Founding Cohort Bonus and Premium Credit Reseller Model

**Date**: 2026-05-22
**Status**: Research / Pre-spec
**Feeds**: ADR-031, ADR-032, spec/iicp-dir.md §registration, project/FOUNDING_COHORT_MIGRATION.md
**Depends on**: 01-model-tier-roi-simulation.md (Scheme C weights), 04-premium-credit-design.md (P-Credit system), 06-monetary-policy-mint-system.md (Mint structure)

---

## Section 1: Founding Cohort Early-Bird Bonus

### 1.1 The Founding Multiplier

Nodes that register earlier take more risk. The protocol is unproven; there are no
precedents for credit values, no established community, and no guarantees that the mesh
will reach the scale necessary for credits to be meaningful. Early adopters provide
the initial liquidity and reputation that make later adoption possible.

The founding multiplier compensates for this risk. It is a permanent, per-node
coefficient applied to all S-Credits earned from task serving:

```
founding_multiplier(registration_day) = max(1.0, 4.0 - 3.0 × (registration_day / 365))
```

Where `registration_day = 0` is the public launch date. The multiplier decreases
linearly from 4.0× at launch to 1.0× at day 365. After day 365 all new registrations
receive a permanent multiplier of 1.0×.

**Computed values by registration day:**

| Registration day | Multiplier (formula) | Rounded |
|-----------------|---------------------|---------|
| 0 (launch) | 4.0 - 3.0 × 0 = 4.0× | 4.0× |
| 30 | 4.0 - 3.0 × 0.082 = 3.75× | 3.75× |
| 60 | 4.0 - 3.0 × 0.164 = 3.51× | 3.5× |
| 90 | 4.0 - 3.0 × 0.247 = 3.26× | 3.25× |
| 120 | 4.0 - 3.0 × 0.329 = 3.01× | 3.0× |
| 180 | 4.0 - 3.0 × 0.493 = 2.52× | 2.5× |
| 240 | 4.0 - 3.0 × 0.658 = 2.03× | 2.0× |
| 300 | 4.0 - 3.0 × 0.822 = 1.53× | 1.5× |
| 365 | max(1.0, 4.0 - 3.0 × 1.0) = 1.0× | 1.0× |
| 365+ | max(1.0, ...) = 1.0× | 1.0× |

**The multiplier is set once at registration and never changes.** A node that registers
on day 90 locks in a 3.25× multiplier for its entire lifetime in the protocol, regardless
of how many times it re-registers, restarts, or changes its endpoint.

The locked multiplier is stored as a column in the `nodes` table. It is not re-computed
on re-registration or heartbeat. It can only be cleared by the directory maintainer via
an administrative action (e.g., if a node is found to have obtained its multiplier by
fraudulent means).

### 1.2 Credit Earning With the Founding Multiplier

The base earning formula from document 01 (Scheme C) extended with the founding multiplier:

```
credits_earned = ceil(output_tokens / 1000) × tier_weight × founding_multiplier
```

**Example — 7B node registered on day 60 (3.5× multiplier):**
```
Task serves 2,000 tokens
tokens_per_credit = 1000
tier_weight_7B = 1.0
founding_multiplier = 3.5

credits_earned = ceil(2000/1000) × 1.0 × 3.5 = 2 × 3.5 = 7.0 credits
```

Compared to a day-365 registrant (1.0× multiplier):
```
credits_earned = ceil(2000/1000) × 1.0 × 1.0 = 2.0 credits
```

The early adopter earns 3.5× more credits for the same task. Over a full day at 50%
utilization (2,592,000 tokens/day for a 7B node):

| Founding multiplier | Credits/day | Monthly credits |
|--------------------|-----------|--------------:|
| 4.0× (day 0) | 10,368 | 311,040 |
| 3.5× (day 60) | 9,072 | 272,160 |
| 3.0× (day 120) | 7,776 | 233,280 |
| 2.5× (day 180) | 6,480 | 194,400 |
| 2.0× (day 240) | 5,184 | 155,520 |
| 1.5× (day 300) | 3,888 | 116,640 |
| 1.0× (day 365+) | 2,592 | 77,760 |

### 1.3 Why This Does Not Enable Credit Farming

A common concern: operators register early to secure a high multiplier, then idle their
node (doing nothing) and earn credits passively via the multiplier.

This is not possible because:

**The founding multiplier applies only to task-serving credits (token earning).**
It does not multiply availability credits (document 01 §6 Scheme D). An idle node
earns only availability credits, which are not scaled by `founding_multiplier`.

Specifically:
```
# Token earning (scaled by founding_multiplier):
credits_earned = ceil(output_tokens / 1000) × tier_weight × founding_multiplier

# Availability earning (NOT scaled by founding_multiplier):
avail_credits_per_hour = availability_rate[tier]   ← fixed, no multiplier
```

A node that registers on day 1 and serves zero tasks earns zero founding-multiplier
credits. It earns only the base availability rate, which is the same for all nodes
regardless of registration date.

**The multiplier only compounds real contribution.** A node must serve actual tasks —
confirmed by HMAC receipt and directory ledger — to benefit from the founding multiplier.
There is no passive income from holding the multiplier alone.

Additionally, serving tasks to earn founding-multiplier credits requires real hardware:
a 7B node running on an RTX 4090 at $300/month. The economic cost of participation
is real. The multiplier compensates for the risk of that cost, not for showing up
and doing nothing.

### 1.4 Implementation

The `founding_multiplier` is stored in the `nodes` table:

```sql
ALTER TABLE nodes
ADD COLUMN founding_multiplier DECIMAL(5,2) NOT NULL DEFAULT 1.00
    COMMENT 'Set once at registration. Formula: max(1.0, 4.0 - 3.0 * (days_since_launch / 365)).',
ADD COLUMN founding_multiplier_locked_at TIMESTAMP NULL
    COMMENT 'When the multiplier was sealed. Null if node predates the founding bonus.';
```

Registration logic (PHP, in `RegisterController.php`):

```php
private function computeFoundingMultiplier(\DateTimeImmutable $launchDate): float
{
    $registrationDay = (new \DateTimeImmutable())->diff($launchDate)->days;
    $multiplier = 4.0 - 3.0 * ($registrationDay / 365);
    return (float) number_format(max(1.0, $multiplier), 2, '.', '');
}

// In register():
$node->founding_multiplier = $this->computeFoundingMultiplier($this->launchDate);
$node->founding_multiplier_locked_at = now();
$node->save();
```

Applied in `CreditService::earn()`:

```php
public function earn(string $nodeId, int $outputTokens, string $tier, string $taskId, string $nonce): float
{
    $weight     = self::TIER_WEIGHTS[$tier] ?? 1.0;
    $node       = Node::find($nodeId);
    $multiplier = $node->founding_multiplier ?? 1.0;
    $credits    = ceil($outputTokens / 1000) * $weight * $multiplier;
    // ... idempotency check, insert, balance update ...
    return $this->credit($nodeId, $credits, 'task_completion', $taskId);
}
```

**Link to FOUNDING_COHORT_MIGRATION.md**: migration of the 8 current seed nodes to
the founding cohort status is covered in `project/FOUNDING_COHORT_MIGRATION.md`.
All 8 seed nodes should receive `founding_multiplier = 4.0` at migration time (they
registered before public launch and are treated as Day 0 registrants).

---

## Section 2: Genesis Cohort Distinction

### 2.1 Definition

Nodes registered before the public beta launch date are the Genesis Cohort. Currently
8 nodes exist in this category (the seed nodes). They are distinct from all other
founding cohort nodes in three ways:

1. **Founding multiplier**: `founding_multiplier = 4.0` (the maximum, same as Day 0 launch)
2. **Genesis status badge**: permanent `genesis_node = true` flag in the directory
3. **Mint eligibility bypass**: Genesis nodes are eligible for Mint membership starting
   on Day 1 of Mint formation, bypassing the 180-day operating duration requirement
   (document 06 §2.1), provided uptime and conformance criteria are met

### 2.2 Genesis Node Registry Display

In the `/nodes` public registry and `/v1/discover` responses, Genesis nodes receive
an additional field:

```json
{
  "node_id": "uuid",
  "endpoint": "https://node01.example.com",
  "genesis_node": true,
  "founding_multiplier": 4.0,
  "model_size_tier": "7B",
  "score": 0.98
}
```

The `genesis_node: true` field is set by the directory at migration and cannot be
self-declared by nodes. It is a directory-attested field.

### 2.3 Enhanced Bootstrap Grant

Genesis nodes receive a one-time enhanced bootstrap credit grant:

```
Standard bootstrap grant: 100 S-Credits (document 02 §6.3)
Genesis bootstrap grant:  150 S-Credits (50% higher)
```

The additional 50 credits are issued as a second `reason: "genesis_grant"` transaction,
separate from the standard `reason: "bootstrap_grant"`. This separation allows the
ledger to distinguish genesis grants from standard bootstrap grants for accounting purposes.

### 2.4 Mint Eligibility Bypass — Rationale

The 180-day operating duration requirement (document 06 §2.1) exists to ensure Mint
members have demonstrated sustained commitment before gaining governance power. Genesis
nodes have already demonstrated this: the seed nodes have been running since before
public launch, which in most cases means more than 180 days of actual operation.

The bypass is conditional: uptime (99.5% rolling 90-day) and REACH conformance (98%+)
must still be met. The bypass covers only the operating duration criterion, not the
quality criteria. A Genesis node that has poor uptime cannot bypass the requirement.

**Database field:**

```sql
ALTER TABLE nodes
ADD COLUMN genesis_node BOOLEAN NOT NULL DEFAULT FALSE
    COMMENT 'Set to true for nodes registered before public beta launch. Directory-only write.',
ADD COLUMN genesis_grant_issued BOOLEAN NOT NULL DEFAULT FALSE;
```

---

## Section 3: Premium Credit Reseller Model

### 3.1 The Foundation as Wholesale Buyer and Retail Seller

The IICP foundation (operated by the maintainer) occupies the intermediary position
in the premium inference supply chain:

```
Anthropic / OpenAI / Mistral (enterprise API providers)
        ↓  wholesale tokens (pre-committed volume, discounted rate)
IICP Foundation (wholesale buyer)
        ↓  P-Credits at retail price
IICP end users / operators (retail buyers)
        ↓  P-Credits spent at routing time
Premium provider nodes (settlement target)
        ↓  revenue to Anthropic / OpenAI / Mistral
```

**Why the foundation takes this position:**

Direct billing (user → Anthropic) is simpler but loses the IICP protocol's value:
- The protocol cannot enforce quality standards on direct-billed inference
- Users must manage separate billing relationships with each provider
- REACH probes cannot monitor nodes that aren't registered in the IICP directory
- The S-Credit economy and P-Credit economy would be entirely disconnected

By acting as the reseller, the foundation:
1. Provides a single billing relationship (user → foundation, not user → 5 providers)
2. Keeps premium nodes registered and monitored within IICP's directory
3. Earns a margin that funds directory infrastructure, REACH probes, and Mint governance
4. Takes the risk of pre-committed wholesale contracts (absorbing volume risk)

### 3.2 The Wholesale Layer

The foundation signs enterprise agreements with each premium provider. These agreements
typically provide:

| Benefit | Typical structure | Example |
|---------|-------------------|---------|
| Volume discount | 20–40% below pay-as-you-go | $20/Mtok vs $30/Mtok pay-as-you-go |
| Pre-committed volume | Monthly minimum spend commitment | 1 billion tokens/month guaranteed |
| SLA guarantees | Uptime and latency contractual floor | 99.9% uptime, p95 latency < 2s |
| Rate lock period | Fixed pricing for a contract term | 12-month rate lock |

The foundation pays for pre-committed tokens in advance, regardless of whether users
consume them. This is the **inventory risk** the foundation absorbs. If a month has
lower-than-expected P-Credit redemptions, the foundation has over-purchased.

**Risk mitigation for inventory risk:**
- Stagger contract terms (some providers on 6-month, some on 12-month terms)
- Maintain a rolling reserve (see §3.6, Open Question 3)
- Build P-Credit expiry into the terms to drive consumption (see §3.6, Open Question 1)
- Start with conservative committed volumes in Year 1; increase as P-Credit demand is established

### 3.3 The Retail Layer — P-Credit Tiers

P-Credit tiers are priced to cover wholesale cost plus a margin that funds foundation
operations. Margins are higher on small purchases (to cover payment processing overhead)
and thin on enterprise purchases (to attract high-volume buyers with competitive pricing).

**Hardware and wholesale cost basis:**

Wholesale cost is expressed as fraction of retail P-Credit price. At $1 P-Credit = $1 USD:

| Provider | Pay-as-you-go | Estimated wholesale (30% discount) | Foundation cost per P-Credit |
|----------|--------------|-----------------------------------|------------------------------|
| Anthropic Opus-class | $30/Mtok | ~$21/Mtok | $0.021 per P-Credit (at 0.075 P-Credits/1000 tok) |
| Anthropic Sonnet-class | $15/Mtok | ~$10.50/Mtok | ~$0.011 per P-Credit |
| OpenAI GPT-4o class | $10/Mtok | ~$7.00/Mtok | ~$0.007 per P-Credit |

Note: These are illustrative estimates. Actual wholesale rates are negotiated and
non-public. The foundation's actual margins depend on negotiated rates, which will
vary by provider and volume.

**P-Credit pricing tiers:**

| Tier | P-Credits | Price (USD) | Per P-Credit | Foundation cost (est.) | Gross margin (est.) |
|------|-----------|-------------|--------------|----------------------|---------------------|
| Starter | 1 | $1.50 | $1.50 | $0.90 | 40% |
| Small | 10 | $12.00 | $1.20 | $0.85 | 29% |
| Medium | 100 | $90.00 | $0.90 | $0.80 | 11% |
| Large | 1,000 | $700.00 | $0.70 | $0.65 | 7% |
| Enterprise | 10,000 | $5,500.00 | $0.55 | $0.50 | 9% |

**Margin analysis:**

The Starter tier's 40% margin covers Stripe's payment processing fee (~2.9% + $0.30):
```
Stripe fee on $1.50 = 2.9% × $1.50 + $0.30 = $0.04 + $0.30 = $0.34
Net after Stripe: $1.50 - $0.34 = $1.16
Foundation cost: $0.90
Contribution margin: $1.16 - $0.90 = $0.26 (17% effective margin after payment processing)
```

The Large tier:
```
Stripe fee on $700.00 = 2.9% × $700 + $0.30 = $20.30 + $0.30 = $20.60
Net after Stripe: $700.00 - $20.60 = $679.40
Foundation cost: 1000 × $0.65 = $650.00
Contribution margin: $679.40 - $650.00 = $29.40 (4.3% effective margin after processing)
```

The Enterprise tier uses ACH or wire transfer (no Stripe fee), so the full 9% gross
margin translates to effectively the same net margin.

**Why enterprise pricing is near cost:**

Enterprise buyers generate the volume that justifies pre-committed wholesale contracts.
If the foundation charges enterprise buyers significantly above cost, they will negotiate
directly with Anthropic/OpenAI and bypass IICP entirely. Near-cost pricing retains their
volume within the protocol, which provides: (a) reliable committed volume to fulfill
wholesale contracts, (b) REACH monitoring of their traffic, and (c) protocol data
for quality improvements.

### 3.4 How P-Credits Work at the Technical Level

P-Credit flow from purchase to settlement (detailed from document 04 §4):

```
Step 1: User selects tier and pays via iicp.network/buy (Stripe payment gateway)
Step 2: Stripe webhook fires → directory verifies event signature (STRIPE_WEBHOOK_SECRET)
Step 3: Directory credits user's premium_credit_balances row:
        UPDATE premium_credit_balances
        SET balance = balance + <p_credits_purchased>
        WHERE user_id = <user_id>
Step 4: User's proxy selects a premium node via /v1/discover?accept_p_credits=true
Step 5: Proxy fetches current P-Credit rate for the selected node from NODELIST response
Step 6: Proxy calls directory to pre-authorize the spend (balance check)
Step 7: Task is dispatched to the premium node
Step 8: Premium node serves inference and returns result
Step 9: Proxy reports actual token count to directory
Step 10: Directory deducts P-Credits:
         p_credits_deducted = actual_tokens / 1000 × node.p_credit_rate
         directory_commission = p_credits_deducted × 0.05
         provider_credited = p_credits_deducted - directory_commission
Step 11: Monthly settlement: provider requests payout; directory settles at
         provider_credited × p_credit_usd_rate via wire/ACH
```

**Database tables involved** (from document 04 §4.1):
- `premium_credit_balances` — user P-Credit balances
- `premium_credit_transactions` — per-task deduction log
- `premium_provider_tokens` — provider authorization

### 3.5 The Firewall Between S-Credits and P-Credits

The two credit systems are separated at every level. Quoting and extending document 04 §1:

**Database separation:**
- S-Credits: stored in `credit_transactions` table, keyed by `node_id`
- P-Credits: stored in `premium_credit_balances` table, keyed by `user_id`
- No foreign key or join path connects these tables in credit-related operations

**Authentication separation:**
- S-Credit operations: authenticated via `node_token` (Bearer token issued at node registration)
- P-Credit operations: authenticated via `user_token` (Bearer token issued at user account registration)
- No endpoint accepts both token types for the same operation

**Routing path separation:**
- S-Credit routing: proxy calls `/v1/discover` (default: S-Credit nodes only) → selects peer node → calls `/v1/credits/spend`
- P-Credit routing: proxy calls `/v1/discover?accept_p_credits=true` → selects premium node → calls `/v1/premium-credits/spend`
- These are distinct endpoint trees with distinct authentication requirements

**Conversion prohibition:**
- No endpoint exists to convert S-Credits to P-Credits or vice versa
- The directory code has no function `convert_s_to_p()` or equivalent
- Adding such a function would require modifying the spec, the directory, and the proxy — a non-trivial change that would be visible in a code review

**What this does and does not prevent:**

The firewall prevents S-Credits from being used as payment for premium inference.
It does not prevent an S-Credit operator from also purchasing P-Credits using hard
currency. An operator can simultaneously:
- Run a 7B node, earn S-Credits, and use them for peer routing (S-Credit economy)
- Purchase P-Credits at the Starter tier to access Opus-class inference for demanding tasks (P-Credit economy)

This is explicitly allowed — the two economies are parallel, not exclusive. An operator
who participates in both contributes infrastructure (via their node) AND funds premium
provider access (via P-Credit purchases). Neither activity affects the other.

### 3.6 Why P-Credits Are Not Speculative or Harmful

Five properties prevent P-Credits from becoming a speculative instrument:

1. **Non-transferable between users.** P-Credits purchased by User A cannot be sent
   to User B. The `premium_credit_balances` table has a `UNIQUE` constraint on `user_id`.
   There is no transfer endpoint. P-Credits are like gift cards — useful only to the holder.

2. **No appreciation mechanism.** P-Credits are priced in USD at the time of purchase.
   1 P-Credit purchased today for $1.50 is worth $1.50 of inference access today and
   $1.50 of inference access in 6 months (unless the provider changes their rate, which
   is bounded at 10% per month per document 04 §8). P-Credits cannot appreciate.

3. **No secondary market.** Because P-Credits are non-transferable, there is no
   exchange on which to sell them. You cannot buy low and sell high — there is no
   "high" to sell to.

4. **No supply scarcity.** The foundation replenishes P-Credit supply by purchasing
   more tokens from providers (subject to wholesale contract terms). A buyer cannot
   corner the market because the foundation creates supply on demand. The only limit
   is the foundation's wholesale contract volume, which is a negotiated floor, not
   a ceiling.

5. **Foundation has no incentive for price inflation.** The foundation earns margin on
   P-Credit sales, but the margin is fixed at the retail tier pricing table. If the
   foundation raises P-Credit prices, it directly loses enterprise buyers to direct
   provider billing. Price increases hurt, not help, the foundation's revenue at scale.

### 3.7 The Reseller Profit Model at Scale

The foundation's P-Credit economics at three illustrative scales:

**Scale: 100 users each buying 100 P-Credits (Medium tier)**
```
Revenue: 100 × $90.00 = $9,000
Stripe fees: 100 × (2.9% × $90 + $0.30) = 100 × ($2.61 + $0.30) = $291
Net after Stripe: $9,000 - $291 = $8,709
Foundation wholesale cost: 100 × 100 × $0.80 = $8,000
Gross profit: $8,709 - $8,000 = $709 (7.9% net margin)
```

**Scale: 50 users each buying 1,000 P-Credits (Large tier)**
```
Revenue: 50 × $700.00 = $35,000
Stripe fees: 50 × (2.9% × $700 + $0.30) = 50 × ($20.30 + $0.30) = $1,030
Net after Stripe: $35,000 - $1,030 = $33,970
Foundation wholesale cost: 50 × 1,000 × $0.65 = $32,500
Gross profit: $33,970 - $32,500 = $1,470 (4.2% net margin)
```

**Scale: 5 enterprise buyers each buying 10,000 P-Credits (Enterprise tier, wire)**
```
Revenue: 5 × $5,500.00 = $27,500
Wire fees: ~$25 flat per transfer × 5 = $125
Net after fees: $27,500 - $125 = $27,375
Foundation wholesale cost: 5 × 10,000 × $0.50 = $25,000
Gross profit: $27,375 - $25,000 = $2,375 (8.6% net margin)
```

**What the profit funds:**

At Phase 4 scale (document 03, 150 nodes), estimated P-Credit revenue at medium-scale
buyer mix:
- REACH infrastructure: ~$150/month (4 probe origins × $37.50/month server)
- Directory hosting: ~$80/month
- Mint governance overhead (tooling, communications): ~$50/month
- Development hours: variable

If P-Credit gross profit covers these fixed costs, the protocol is self-sustaining
without relying on grants or investor funding.

### 3.8 Future Provider Expansion

When additional premium providers join (e.g., Google Gemini, Mistral, Meta
LLaMA-Commercial, Cohere, AI21 Labs):

**Standard expansion path:**
1. Provider applies for `premium_provider_token` from the directory maintainer
2. Maintainer verifies provider identity and capability claims
3. Foundation negotiates wholesale agreement (or starts with pay-as-you-go if volume is unknown)
4. Provider registers nodes with their `premium_provider_token`
5. Discover results include provider nodes when `?accept_p_credits=true` is set
6. Users' P-Credits work with all verified premium providers (foundation is the single billing entity)

**Provider-specific P-Credits (optional future feature):**

Users who want guaranteed routing to a specific provider can request "provider-tagged"
P-Credits:
```
Anthropic P-Credits: usable only at Anthropic nodes
OpenAI P-Credits: usable only at OpenAI nodes
Universal P-Credits: usable at any verified premium node (default)
```

Provider-tagged P-Credits allow users to lock in a specific provider's rate for future
use. This is analogous to buying airline miles on a specific airline vs. a flexible
points currency. Implementing this requires:
- Additional `provider_tag` column in `premium_credit_balances`
- Modified balance check in routing path (filter by `provider_tag`)
- Separate purchase flows per provider

This is a Phase 5+ feature — not planned for Phase 3-4 implementation.

---

## Section 4: Open Questions for Maintainer

1. **Should P-Credits expire?**

   The airline miles model: credits expire after 18 months of account inactivity.
   Benefits: reduces unclaimed liability on the foundation's books; incentivizes
   consumption; reduces the "over-purchased" risk.
   Costs: user trust — expiring credits feel punitive, especially to occasional users.

   **Proposed compromise**: P-Credits expire after 24 months of zero redemption activity
   (any P-Credit redemption, regardless of amount, resets the clock). This is generous
   enough to not punish occasional users while still providing an expiry mechanism.

2. **Should there be a P-Credit discovery trial?**

   New IICP registrations receive 1 free P-Credit to experience premium inference.
   Benefits: strong onboarding hook; reduces friction to first premium task; builds
   immediate understanding of the S/P credit distinction.
   Costs: real money ($1.50 cost per new registration at Starter tier wholesale rate ≈ $0.90).
   At 100 new registrations/month: $90/month. At 1,000 new registrations/month: $900/month.

   **Proposed gate**: activate the P-Credit trial only when monthly P-Credit gross
   profit exceeds $500 (self-funding threshold). Before that threshold, the S-Credit
   bootstrap grant (100 credits) is sufficient for onboarding.

3. **What is the foundation's reserve policy?**

   Recommended: maintain a reserve equal to 30 days of estimated wholesale token cost
   to cover pre-commitment risk if user demand drops unexpectedly.

   ```
   If monthly wholesale commitment = $10,000
   Reserve target = $10,000 (30 days = 1 month)
   ```

   The reserve is funded by retaining a portion of each month's P-Credit gross profit
   until the reserve target is met. After target is met, full profit is available for
   operations and development.

   Open question: should the reserve be disclosed publicly (builds trust) or kept
   private (avoids speculation about foundation's financial health)?

4. **Should the foundation take a commission on Mint governance decisions that change earn rates?**

   **Answer: No.**

   If the foundation earns revenue when the Mint raises earn rates (because more
   S-Credit earning attracts more operators → more P-Credit purchases), the foundation
   has a financial interest in governance outcomes. This compromises the independence
   of the Mint and the integrity of the governance process.

   Governance must be structurally free from the foundation's revenue incentives.
   The foundation participates in the Mint only through operating directory nodes
   that meet eligibility criteria (and then only one seat, subject to entity
   exclusivity rules in document 06 §2.1).

5. **Wholesale contract risk allocation:**

   If a wholesale provider (e.g., Anthropic) increases its enterprise pricing by 30%
   at contract renewal, should the foundation pass the increase to users (via P-Credit
   price adjustment) or absorb it temporarily (maintaining current prices from reserve)?

   **Proposed policy**: announce price changes 30 days before they take effect. Users
   who pre-purchase P-Credits at the current price before the effective date lock in
   that rate. The foundation absorbs the cost difference on pre-purchased inventory
   from the reserve. This is a pro-user policy that reduces the sting of price increases.
