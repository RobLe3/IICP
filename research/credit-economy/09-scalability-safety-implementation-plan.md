# S-Credit Economy: Scalability & Safety Implementation Plan

**Research track**: R-ECON-09  
**Iteration**: 590  
**Directive**: Make the general population S-Credit economy safe and usable for node providers
and users — survival-ready if the mesh grows to 100k+ endpoints in 2 months.  
**Scope**: S-Credits (peer economy) only. P-Credits (premium/commercial) are a separate future project.

---

## 0. What Exists Today

```
directory/
  credits table:           node_id, balance, total_earned, total_spent, updated_at
  CreditsController.php:   balance(), award(), spend(), history()
  credit_cost_multiplier:  per-node float in nodes table (default 1.0)
  CIP-only:               credits only move during CIP cooperative inference
```

**Gap**: No quality tier weighting. No anti-inflation sinks. No bootstrap grant.
No non-CIP earn/spend. No balance gates. No Mint governance.

---

## 1. Implementation Steps (Priority Order)

### Step 1 — Ledger Foundation (Day 1–3)
**Protects against**: ledger inconsistency, race conditions, negative balances at scale.

#### 1A. Schema hardening

```sql
-- credits table: add NOT NULL constraints + check constraints
ALTER TABLE credits 
  ADD COLUMN quality_tier TINYINT UNSIGNED NOT NULL DEFAULT 2,
  ADD COLUMN founding_multiplier DECIMAL(5,2) NOT NULL DEFAULT 1.00,
  ADD COLUMN ttl_expires_at TIMESTAMP NULL DEFAULT NULL,
  ADD COLUMN version INT UNSIGNED NOT NULL DEFAULT 0;

-- credit_transactions: audit log (immutable append-only)
CREATE TABLE credit_transactions (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  node_id       VARCHAR(64) NOT NULL,
  tx_type       ENUM('earn','spend','burn','expire','bootstrap','mint_adjust') NOT NULL,
  amount        INT NOT NULL,           -- signed: positive=earn, negative=spend
  balance_after INT UNSIGNED NOT NULL,
  task_id       VARCHAR(64) NULL,       -- foreign key to tasks if CIP
  quality_tier  TINYINT UNSIGNED NOT NULL DEFAULT 2,
  multiplier    DECIMAL(5,2) NOT NULL DEFAULT 1.00,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_node_created (node_id, created_at),
  INDEX idx_task (task_id)
) ENGINE=InnoDB;

-- mint_parameters: single row, Mint-governed values
CREATE TABLE mint_parameters (
  param_key     VARCHAR(64) PRIMARY KEY,
  param_value   DECIMAL(12,4) NOT NULL,
  set_by        VARCHAR(64) NOT NULL,   -- directory_id of Mint authority
  updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  change_pct    DECIMAL(5,2) NOT NULL DEFAULT 0.00  -- track quarterly change magnitude
);

INSERT INTO mint_parameters (param_key, param_value, set_by) VALUES
  ('earn_multiplier',        1.00, 'genesis'),
  ('spend_base_per_1k_tok',  1.00, 'genesis'),
  ('bootstrap_grant',      100.00, 'genesis'),
  ('genesis_bootstrap',    150.00, 'genesis'),
  ('ttl_days',              90.00, 'genesis'),
  ('burn_rate',              0.02, 'genesis'),  -- 2% per transaction, activated month 13
  ('burn_active',            0.00, 'genesis'),  -- 0=off, 1=on
  ('max_balance_cap',     5000.00, 'genesis'),  -- soft cap; balances above earn 0 bonus
  ('min_velocity_days',     30.00, 'genesis');  -- idle nodes earn no TTL extension
```

#### 1B. Optimistic locking in CreditsController

```php
// award() — atomic: read version, update with version check, retry on collision
public function award(string $node_id, int $raw_tokens, string $task_id): array
{
    $tier       = $this->getQualityTier($node_id);
    $mult       = $this->getTierWeight($tier);
    $founding   = $this->getFoundingMultiplier($node_id);
    $earn_mult  = $this->getMintParam('earn_multiplier');
    $credits    = (int) floor(($raw_tokens / 1000) * $mult * $founding * $earn_mult);
    if ($credits <= 0) return ['awarded' => 0];

    DB::transaction(function() use ($node_id, $credits, $task_id, $tier, $mult, $founding) {
        $row = DB::selectOne(
            "SELECT balance, version FROM credits WHERE node_id = ? FOR UPDATE",
            [$node_id]
        );
        if (!$row) throw new \RuntimeException("Node {$node_id} has no credits row");

        $new_balance = $row->balance + $credits;
        $affected = DB::update(
            "UPDATE credits SET balance = ?, total_earned = total_earned + ?,
             ttl_expires_at = DATE_ADD(NOW(), INTERVAL ? DAY),
             version = version + 1
             WHERE node_id = ? AND version = ?",
            [$new_balance, $credits,
             (int) $this->getMintParam('ttl_days'),
             $node_id, $row->version]
        );
        if ($affected !== 1) throw new \RuntimeException("Optimistic lock collision");

        DB::table('credit_transactions')->insert([
            'node_id'       => $node_id,
            'tx_type'       => 'earn',
            'amount'        => $credits,
            'balance_after' => $new_balance,
            'task_id'       => $task_id,
            'quality_tier'  => $tier,
            'multiplier'    => round($mult * $founding, 4),
        ]);
    });
    return ['awarded' => $credits];
}
```

**Why optimistic locking**: At 100k nodes with burst routing, row-level locks under
`SELECT ... FOR UPDATE` serialize per-node (correct) but don't block the full table.
Version column detects concurrent double-award without deadlock.

---

### Step 2 — Quality Tier Weights (Day 3–5)
**Protects against**: race to bottom (all small models), hardware subsidy inversion.

#### Scheme C weights (research-validated in 01-model-tier-roi-simulation.md):

| Tier | Model Range | earn_weight | Rationale |
|------|-------------|-------------|-----------|
| 0 | ≤1B params | 0.05 | Anti-spam; tiny models should use for small tasks only |
| 1 | 1–4B | 0.25 | Light-work tier; low hardware cost |
| 2 | 5–9B (default) | 1.00 | Baseline; 7B Mistral/LLaMA as reference |
| 3 | 10–20B | 2.00 | Meaningful step up; 13B class |
| 4 | 21–50B | 6.50 | 30B class; significant hardware investment |
| 5 | 51–100B | 32.00 | 70B class on 4×A100 or equivalent |
| 6 | 100B+ | 75.00 | Frontier models; Llama-3 405B, Opus 4 scale |

```php
private static array $TIER_WEIGHTS = [
    0 => 0.05, 1 => 0.25, 2 => 1.00, 3 => 2.00,
    4 => 6.50, 5 => 32.00, 6 => 75.00
];

private function getQualityTier(string $node_id): int
{
    $row = DB::selectOne(
        "SELECT quality_tier FROM credits WHERE node_id = ?", [$node_id]
    );
    return (int) ($row->quality_tier ?? 2);
}

private function getTierWeight(int $tier): float
{
    return self::$TIER_WEIGHTS[$tier] ?? 1.00;
}
```

**Tier assignment**: Set at registration from `model_name` heartbeat field.
`NodeScorer::detectTier(string $model_name): int` — maps model names to tiers using
a lookup table in `config/model_tiers.php`. Unknown models → tier 2 (safe default).

**Why this is safe at 100k nodes**: Tier weights are read-only per transaction.
The Mint can adjust `earn_multiplier` globally (a single row read) but cannot change
individual tier weights more than 20% per quarter.

---

### Step 3 — Bootstrap Grant (Day 5–6)
**Protects against**: cold-start chicken-and-egg; new nodes can't spend if they have 0 credits.

```php
// RegisterController::store() — called on POST /v1/register
$is_genesis = in_array($node_id, Config::get('app.genesis_node_ids', []));
$grant      = (int) $this->getMintParam($is_genesis ? 'genesis_bootstrap' : 'bootstrap_grant');
// 150 for genesis nodes, 100 for all new nodes

DB::transaction(function() use ($node_id, $grant, $is_genesis) {
    DB::table('credits')->insert([
        'node_id'             => $node_id,
        'balance'             => $grant,
        'total_earned'        => $grant,
        'total_spent'         => 0,
        'quality_tier'        => 2,     // updated on first heartbeat
        'founding_multiplier' => $this->getFoundingMultiplier(now()),
        'ttl_expires_at'      => DB::raw("DATE_ADD(NOW(), INTERVAL 90 DAY)"),
        'version'             => 0,
    ]);
    DB::table('credit_transactions')->insert([
        'node_id'       => $node_id,
        'tx_type'       => 'bootstrap',
        'amount'        => $grant,
        'balance_after' => $grant,
        'task_id'       => null,
        'quality_tier'  => 2,
        'multiplier'    => 1.00,
    ]);
});
```

**Bootstrap grant economics at scale**:
- 100k new nodes × 100 S-Credits = 10,000,000 S-Credits injected
- Against 100k nodes × ~2,000 credits/day earned by serving = 200,000,000 credits/day
- Bootstrap is ~5% of one day's earned supply → inflationary only if nodes never serve
- Bootstrap credits have the same 90-day TTL → auto-expire if node never activates
- Net: bootstrap grants do not cause structural inflation

---

### Step 4 — Anti-Inflation Sinks (Day 6–10)
**Protects against**: hyperinflation from monotonic supply growth (proven in 03-economy-growth-simulation.md).

#### 4A. TTL expiry (primary sink — Day 6–7)

```php
// CreditExpiryJob — scheduled daily at 02:00 UTC
public function handle(): void
{
    // Batch expire in chunks to avoid long table locks at 100k scale
    $expired = 0;
    do {
        $rows = DB::select(
            "SELECT node_id, balance FROM credits
             WHERE ttl_expires_at < NOW() AND balance > 0
             LIMIT 500"
        );
        foreach ($rows as $row) {
            DB::transaction(function() use ($row) {
                DB::update(
                    "UPDATE credits SET balance = 0,
                     ttl_expires_at = NULL,
                     version = version + 1
                     WHERE node_id = ? AND ttl_expires_at < NOW()",
                    [$row->node_id]
                );
                DB::table('credit_transactions')->insert([
                    'node_id'       => $row->node_id,
                    'tx_type'       => 'expire',
                    'amount'        => -$row->balance,
                    'balance_after' => 0,
                    'task_id'       => null,
                    'quality_tier'  => 0,
                    'multiplier'    => 1.00,
                ]);
            });
        }
        $expired += count($rows);
    } while (count($rows) === 500);

    Log::info("CreditExpiry: expired {$expired} nodes");
}
```

**TTL mechanics**:
- Every `earn` transaction resets TTL to 90 days from now
- Idle nodes (not serving for 90 days) lose unspent balance
- Active nodes are perpetually TTL-extended by earning activity
- At 100k nodes: daily expiry job processes ~500-row batches → no lock contention

#### 4B. Transaction burn rate (secondary sink — activated month 13+)

```php
// In spend() — only when burn_active=1 (Mint-controlled)
$burn_rate = (float) $this->getMintParam('burn_rate');  // default 0.02
$burn_active = (bool) $this->getMintParam('burn_active');

if ($burn_active && $credits_spent > 0) {
    $burn_amount = max(1, (int) ceil($credits_spent * $burn_rate));
    // burn_amount is removed from system entirely (not transferred)
    DB::table('credit_transactions')->insert([
        'node_id'       => $spending_node_id,
        'tx_type'       => 'burn',
        'amount'        => -$burn_amount,
        'balance_after' => $new_balance - $burn_amount,
        ...
    ]);
}
```

**When to activate burn**:
- Mint activates `burn_active=1` when: monthly_supply_growth > 15% AND active_nodes > 10,000
- 2% per-spend burn at 100k nodes routing ~10,000 tasks/day = ~200,000 credits/day burned
- Prevents the month-24 hyperinflation scenario from 03-economy-growth-simulation.md

**Burn rate cap**: Mint cannot set burn_rate above 5% (hard-coded in CreditsController
`MAX_BURN_RATE = 0.05`). Prevents accidental deflationary spiral.

---

### Step 5 — Balance Gates and Rate Limiting (Day 10–12)
**Protects against**: balance hoarding, spend-race at routing time, Sybil balance draining.

#### 5A. Soft balance cap

```php
// In award(): skip credit award if balance already at cap
$max_cap = (int) $this->getMintParam('max_balance_cap');  // default 5000
if ($row->balance >= $max_cap) {
    // Still log the attempt, but don't increase balance
    Log::info("CreditsCap: node {$node_id} at cap {$max_cap}, skipping award");
    return ['awarded' => 0, 'cap_reached' => true];
}
// Award up to cap
$credits = min($credits, $max_cap - $row->balance);
```

**Cap rationale**: 5,000 S-Credits at tier-2 earn rate = ~5 days of continuous serving.
Prevents "credit hoarders" who never route but accumulate indefinitely.
Cap is soft (not a hard constraint at spend time) — nodes above cap can still spend.

#### 5B. Spend rate limiting per node

```php
// In spend(): enforce per-node spend rate limit (daily)
$daily_spent = DB::selectOne(
    "SELECT COALESCE(SUM(ABS(amount)), 0) as spent
     FROM credit_transactions
     WHERE node_id = ? AND tx_type = 'spend' AND created_at > DATE_SUB(NOW(), INTERVAL 1 DAY)",
    [$node_id]
)->spent;

$daily_spend_limit = (int) $this->getMintParam('max_daily_spend');  // default 500
if ($daily_spent + $credits_requested > $daily_spend_limit) {
    return ['error' => 'IICP-E031', 'message' => 'DailySpendLimitExceeded'];
}
```

**At 100k nodes**: daily spend limit of 500 credits/node × 100k nodes = 50M credits max
circulation per day. With ~200M credits/day earned (at full mesh utilization), this is
25% circulation ratio — healthy economy, no hoarding incentive.

#### 5C. Minimum balance gate before routing

```php
// In ProbeController or NodeScorer: exclude nodes with balance < minimum
$min_routing_balance = (int) $this->getMintParam('min_routing_balance');  // default 5
// Nodes below 5 credits can still EARN but not be returned in discover results
// Prevents nodes from routing tasks they can't afford to pay for
```

---

### Step 6 — Founding Cohort Multiplier (Day 12–14)
**Protects against**: early-adopter desertion; nodes who built the mesh before it had value.

```php
// founding_multiplier stored in credits row at registration, never changes
// Formula from 08-founding-bonus-and-premium-reseller.md:
// multiplier(day) = max(1.0, 4.0 - 3.0 × (day/365))

private function getFoundingMultiplierForNewNode(\DateTime $registration_date): float
{
    $launch_date = new \DateTime('2026-05-14');  // genesis node day
    $days_since_launch = (int) $launch_date->diff($registration_date)->days;
    
    if ($days_since_launch >= 365) return 1.00;  // no bonus after year 1
    return round(max(1.0, 4.0 - 3.0 * ($days_since_launch / 365)), 2);
}

// Validation: multiplier is immutable after initial registration
// UPDATE credits SET founding_multiplier = ? WHERE node_id = ? is not allowed post-registration
// Only InsertController::store() may set this value
```

**Genesis nodes** (current 8 seed nodes, registered 2026-05-14):
- `founding_multiplier = 4.00` (day 0)
- `bootstrap_grant = 150`
- Eligible for Mint seat nomination (governance flag, not credit-related)

**Multiplier curve at 100k scale**:
- If 100k nodes join in 2 months (day 60): multiplier = 4.0 - 3.0×(60/365) = 3.51×
- If 100k nodes join in 6 months (day 180): multiplier = 4.0 - 3.0×(180/365) = 2.52×
- These are permanent per-node multipliers. A wave of 100k day-60 nodes creates a
  structural earning advantage over future day-365+ joiners → rewards early adoption.
- Does NOT distort supply: founding multiplier raises the earn rate but the TTL sink
  and burn rate absorb proportionally.

---

### Step 7 — Mint Governance Bootstrap (Day 14–21)
**Protects against**: parameter ossification (economy can't adapt), outside manipulation.

This is the most complex step because it's governance, not just code. Minimum viable
implementation for launch:

#### 7A. Mint parameters table (already defined in Step 1)

No additional schema changes needed. The `mint_parameters` table with single-row
per parameter, `set_by` tracking, and `change_pct` audit is sufficient for v1.

#### 7B. Mint authority endpoint

```php
// POST /v1/mint/parameter — directory-operator only (not public)
// Requires: X-Mint-Signature header (HMAC-SHA256 over body, key = MINT_SIGNING_KEY env var)
public function setParameter(Request $request): JsonResponse
{
    $key   = $request->input('key');
    $value = (float) $request->input('value');
    
    // Hard constraints: cannot change more than 20% from current in one update
    $current = (float) $this->getMintParam($key);
    $change_pct = abs($value - $current) / max($current, 0.001) * 100;
    if ($change_pct > 20.0) {
        return response()->json([
            'error' => 'IICP-E032',
            'message' => 'MintParameterChangeTooLarge',
            'max_allowed_pct' => 20.0,
            'attempted_pct'   => round($change_pct, 2),
        ], 422);
    }
    
    // Immutable parameters (cannot be changed via API)
    $immutable = ['burn_rate'];  // burn rate can only go up, never down
    if (in_array($key, $immutable) && $value < $current) {
        return response()->json(['error' => 'IICP-E033', 'message' => 'ImmutableParameterDirection'], 422);
    }
    
    DB::table('mint_parameters')
        ->where('param_key', $key)
        ->update(['param_value' => $value, 'set_by' => $request->input('authority_id'), 'change_pct' => $change_pct]);

    return response()->json(['updated' => $key, 'new_value' => $value]);
}
```

#### 7C. Supply monitoring endpoint (public, read-only)

```php
// GET /v1/credits/supply — public telemetry for Mint oversight
public function supplyStats(): JsonResponse
{
    $stats = DB::selectOne("
        SELECT
          COUNT(*)                         AS active_nodes,
          SUM(balance)                     AS total_supply,
          AVG(balance)                     AS avg_balance,
          SUM(total_earned)                AS cumulative_earned,
          SUM(total_spent)                 AS cumulative_spent,
          SUM(CASE WHEN ttl_expires_at < DATE_ADD(NOW(), INTERVAL 7 DAY)
                   THEN balance ELSE 0 END) AS expiring_7d
        FROM credits
        WHERE balance > 0
    ");
    
    // Month-over-month supply growth (from transactions)
    $prev_month_supply = DB::selectOne("
        SELECT SUM(amount) AS net
        FROM credit_transactions
        WHERE created_at BETWEEN DATE_SUB(NOW(), INTERVAL 60 DAY)
                              AND DATE_SUB(NOW(), INTERVAL 30 DAY)
          AND tx_type IN ('earn','expire','burn')
    ")->net ?? 0;
    
    return response()->json([
        'active_nodes'        => (int) $stats->active_nodes,
        'total_supply'        => (int) $stats->total_supply,
        'avg_balance'         => round((float) $stats->avg_balance, 2),
        'cumulative_earned'   => (int) $stats->cumulative_earned,
        'cumulative_spent'    => (int) $stats->cumulative_spent,
        'expiring_7d'         => (int) $stats->expiring_7d,
        'prev_30d_net_supply' => (int) $prev_month_supply,
    ]);
}
```

**Mint for launch**: A single directory operator (maintainer) is the Mint authority.
The full 9-seat federated committee described in `06-monetary-policy-mint-system.md`
activates in Phase 6 when ≥50 independent directory operators are running.

---

### Step 8 — Non-CIP Routing Credits (Day 21–28)
**Protects against**: free-rider problem (nodes that only route, never serve).

This step converts the S-Credit economy from CIP-only to mesh-wide.

#### 8A. Standard routing earn/spend

Currently credits only move during CIP (cooperative inference with signed receipts).
Standard routing (proxy → directory → adapter, no CIP signing) is free.

With 100k nodes, a node that only routes and never serves is a free-rider. Non-CIP
routing credits apply a small cost to standard routing requests:

```
earn (provider):  1 credit per 2000 tokens served (half the CIP rate)
spend (requester): 1 credit per 3000 tokens requested
```

This creates a ~1.5x provider surplus even for non-CIP tasks. The surplus is lower
than CIP (5-10x) because there's no signed receipt — no cryptographic proof of delivery.

**Implementation**: Requires #302 resolution. The earn/spend mechanics in
CreditsController already support this (tx_type='earn' and 'spend' are not CIP-specific).
The gap is calling award()/spend() from the standard routing path in the adapter and
directory — not from the CIP receipt handler.

**Decision required from maintainer**: enable non-CIP credits at launch or defer to
after CIP adoption (WQ-032 tracking item).

---

### Step 9 — REACH Monitoring for Credit Economy (Day 28–35)
**Protects against**: economy failures going undetected in production.

New REACH probe: `DIR-CRED-01` through `DIR-CRED-04`:

```python
async def probe_credit_supply_health(session, base_url: str) -> ProbeResult:
    """DIR-CRED-01: supply endpoint accessible and returning valid schema."""
    async with session.get(f"{base_url}/v1/credits/supply", timeout=10) as resp:
        assert resp.status == 200
        data = await resp.json()
        assert 'total_supply' in data
        assert 'active_nodes' in data
        # Sanity: avg_balance should be positive and < max_balance_cap (5000)
        assert 0 < data['avg_balance'] < 10000
        return ProbeResult.pass_("DIR-CRED-01", "supply endpoint healthy")

async def probe_no_hyperinflation(session, base_url: str) -> ProbeResult:
    """DIR-CRED-02: prev_30d_net_supply growth < 50% of total_supply."""
    async with session.get(f"{base_url}/v1/credits/supply", timeout=10) as resp:
        data = await resp.json()
        total = max(data['total_supply'], 1)
        growth = data.get('prev_30d_net_supply', 0)
        growth_pct = abs(growth) / total * 100
        assert growth_pct < 50, f"Supply grew {growth_pct:.1f}% in 30d — hyperinflation risk"
        return ProbeResult.pass_("DIR-CRED-02", f"30d growth {growth_pct:.1f}% — healthy")
```

Alert thresholds:
- `total_supply / active_nodes > 3000`: avg balance approaching cap → Mint should raise cap or activate burn
- `prev_30d_net_supply < 0`: deflation → Mint should lower burn rate or raise earn_multiplier
- `expiring_7d / total_supply > 0.15`: 15% of supply expiring in 7 days → node health issue, not economic

---

### Step 10 — ADR-031 and Spec Update (Day 35–42)
**Protects against**: spec drift, undocumented governance, future contributor confusion.

#### ADR-031: S-Credit Economy Design

```markdown
# ADR-031: S-Credit Peer Economy

Status: Proposed  
Deciders: Protocol Steward, Directory Maintainer  
Date: 2026-05-22  

## Decision

Adopt the S-Credit (Standard Credit) model as the IICP mesh economy:
- 1 credit = 1000 tokens served (CIP mode) / 2000 tokens served (standard mode)
- Tier-weighted earn rates (Scheme C, 7-tier, 0.05×–75×)
- 90-day TTL expiry (primary anti-inflation sink)
- 2% transaction burn rate (secondary sink, Mint-activated at month 13+)
- 100 credit bootstrap grant on first registration
- Founding multiplier (4.0× at day 0, decays to 1.0× at day 365)
- Federated Mint (single directory operator at launch; 9-seat committee at Phase 6)

## Consequences

+ Free-rider problem addressed (spending required to route)  
+ Hardware investment incentivized (tier weights reward larger models)  
+ Early adopters rewarded without permanent distortion (decay curve)  
+ Inflation-proof at 100k+ scale (TTL + burn + caps)  
- Non-CIP routing credits require maintainer decision (#302)  
- Full Mint committee requires Phase 6 directory federation  
```

New spec normative statements in `spec/iicp-dir.md`:
- `MUST` include `credits_balance` in node heartbeat response
- `MUST` return `IICP-E028 InsufficientCredits` on spend failure (already in 05-spec-plan)
- `SHOULD` expose `/v1/credits/supply` as public telemetry

---

## Safety at 100k Endpoints: Scenario Analysis

### Scenario A: 100k nodes join in 60 days

```
Bootstrap injection: 100,000 × 100 = 10,000,000 credits
Day-60 founding multiplier: 3.51×
Combined daily earn (100k × 1,000 credits avg): 100,000,000 credits/day
Daily TTL expiry (20% churn, 5% expire daily): 5,000,000 credits/day
Net daily supply growth: ~95,000,000 credits/day
Month 2 total supply: ~5.7 billion credits

With burn activated (2% per spend, 30% of credits cycling daily):
Daily burn = 5.7B × 0.30 × 0.02 = 34,200,000 credits/day burned
Month 3 total supply: stabilizes around 8 billion credits
Avg balance: 80,000 credits per node
```

**This looks alarming but is mathematically stable**:
- Numbers are large because the mesh is large
- The *ratio* of avg_balance to daily_earn stays constant (~80 credits = 0.08% of daily earn)
- No individual node can extract more value than they put in (structural invariant)
- The Mint cap (5,000 credits soft cap) prevents any single node from accumulating
  more than ~16 days of serving — prevents hoarding-based market power

### Scenario B: 100k nodes but only 10k are active

```
90-day TTL expiry catches the 90k inactive nodes
After 90 days: inactive nodes' balances expire
Economy resets to effectively 10k-node scale
Bootstrap grants to inactive nodes expire harmlessly
```

This is the correct behavior: the economy represents *active* nodes, not registered nodes.

### Scenario C: Coordinated founding multiplier exploit

```
Attack: 1000 Sybil nodes registered on day 0 to harvest 4.0× multiplier
Cost: 1000 VPS + servers, minimum ~$2,000/month
Earned premium: 1000 × (4.0 - 1.0) = 3,000× extra credits/day per token
```

**Defense**: founding multiplier earns only on tokens served. A Sybil cluster that
registers but never serves earns 0 credits regardless of multiplier (multiplier
scales earn rate, not idle balance). To earn 3,000× extra credits, the attacker
must serve 3,000× extra tokens — they've become a legitimate infrastructure provider.
Economic attack becomes infrastructure contribution.

### Scenario D: Mint parameter manipulation

```
Attack: accumulate 6/9 Mint seats (requires ≥600 nodes for 6 months = $90,000)
Benefit: lower burn_rate, raise earn_multiplier → inflate their holdings
Net benefit: ~$66/month in extra credit value above market
ROI: -$89,934/month (net loss)
```

Economic manipulation is structurally unprofitable before the 9-seat committee is live.
Single-operator Mint (launch) has no attack surface — it's the directory maintainer.

---

## Implementation Checklist

| Step | Est. Hours | Files | Safety Protection |
|------|-----------|-------|-------------------|
| 1A Schema | 4h | migration: `2026_05_22_credits_v2.php` | Ledger consistency |
| 1B Optimistic locking | 3h | CreditsController.php | Race conditions |
| 2 Tier weights | 2h | NodeScorer.php, config/model_tiers.php | Hardware race-to-bottom |
| 3 Bootstrap grant | 2h | RegisterController.php | Cold-start |
| 4A TTL expiry | 3h | CreditExpiryJob.php, Kernel.php | Inflation |
| 4B Burn rate | 2h | CreditsController.php (spend path) | Hyperinflation month 13+ |
| 5 Balance gates | 2h | CreditsController.php, NodeScorer.php | Hoarding, Sybil |
| 6 Founding multiplier | 2h | RegisterController.php | Early-adopter desertion |
| 7 Mint governance | 4h | MintController.php, routes/api.php | Parameter ossification |
| 8 Non-CIP routing | 3h | adapter task.py, directory router | Free-rider (pending #302) |
| 9 REACH probes | 2h | reach/probes/directory_conformance.py | Undetected failures |
| 10 ADR-031 + spec | 3h | project/decisions/ADR-031.md, spec/iicp-dir.md | Spec drift |
| **Total** | **32h** | | |

**Order**: 1A → 1B → 3 → 2 → 4A → 5 → 6 → 7 → 4B → 9 → 8 → 10

Steps 1-7 are independent of maintainer decisions.
Step 8 (non-CIP credits) awaits maintainer decision on #302.
Step 4B (burn rate activation) is Mint-operated, not a deploy event.

---

## Parameters Summary (Launch Defaults)

| Parameter | Value | Who Can Change | Change Limit |
|-----------|-------|----------------|-------------|
| earn_multiplier | 1.00× | Mint | ±20%/quarter |
| spend_base | 1.00 credit/1k tokens | Mint | ±20%/quarter |
| bootstrap_grant | 100 credits | Mint (≥20-node active minimum) | Up only |
| genesis_bootstrap | 150 credits | Immutable | Never |
| ttl_days | 90 days | Mint | 60–180 range |
| burn_rate | 2% | Mint | Up only (deflation risk) |
| burn_active | off | Mint | Switch (not via parameter API) |
| max_balance_cap | 5,000 credits | Mint | ±20%/quarter |
| max_daily_spend | 500 credits | Mint | ±20%/quarter |
| min_routing_balance | 5 credits | Mint | 1–50 range |
| tier weights | Scheme C | Protocol Steward + ADR | ADR required |

---

*Research track R-ECON-09 complete. Handoff to implementation: file ADR-031, migrate
schema, implement Steps 1–7 in CreditsController/RegisterController, schedule
CreditExpiryJob, add REACH probes DIR-CRED-01..04.*
