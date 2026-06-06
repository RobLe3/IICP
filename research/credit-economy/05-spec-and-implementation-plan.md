# Credit Economy — Spec Changes and Implementation Plan

**Date**: 2026-05-22  
**Status**: Research / Pre-spec  
**ADR**: ADR-031 (to be created)  
**Scope**: spec/iicp-dir.md, spec/iicp-core.md, directory/ PHP, adapter/ Python, proxy/ Python

---

## 1. ADR-031 Scope

**Title**: Universal Credit Economy — Model-Tier Weights, Routing Costs, and P-Credit System

**Decision**:
- Adopt Scheme C quality weights (document 01 §5) for S-Credit earning
- Adopt Scheme D availability component for bootstrap phase (months 1–12)
- Adopt routing cost formula: `cost = ceil(tokens/1000) × tier_weight × node_multiplier`
- Adopt 90-day TTL credit expiry + 2% transaction burn as sink (activated at 20 nodes)
- Introduce P-Credit system: non-interchangeable hard-currency credits for premium providers
- Introduce `premium_provider_token` whitelist mechanism

**Supersedes**: ADR-008 §credits (extend, not replace), ADR-019 §pricing (extend)

**Deferred**:
- Benchmark-at-registration model verification (Phase 5 hard problem)
- Collusion detection heuristics (Phase 4+)
- Settlement API for premium providers (Phase 4+)

---

## 2. spec/iicp-dir.md Changes

### 2.1 New section: §4 Credit Economy (insert after §3.6 PEER_EXCHANGE)

```markdown
### 4. Credit Economy

#### 4.1 S-Credit Earning

Every successfully completed task earns S-Credits for the serving node.
Credit emission formula:

  earned = ceil(output_tokens / tokens_per_credit) × tier_weight(model_size)

Where:
  tokens_per_credit = 1000 (unchanged)
  tier_weight       = weight from the table below

| Model size tier | tier_weight |
|-----------------|-------------|
| ≤1B             | 0.05        |
| 7B              | 1.0         |
| 13B             | 2.0         |
| 30B             | 6.5         |
| 70B             | 32.0        |
| 100B+           | 75.0        |

The serving node reports task completion to the directory via POST /v1/credits/earn.
The directory validates the completion receipt (HMAC-SHA256, same as CIPWorkerReceipt)
and emits the credit.

#### 4.2 S-Credit Spending (Routing Cost)

When a node routes a task to another node, it pays:

  cost = ceil(output_tokens / tokens_per_credit) × tier_weight(destination) × destination_multiplier

The proxy MUST check the routing node's balance before dispatch. If balance < cost,
proxy MUST return HTTP 402 with error IICP-E028 (InsufficientCredits).

#### 4.3 Availability Credits (Bootstrap Phase Only, Months 1–12)

During the bootstrap phase, nodes earn availability credits regardless of load:

  avail_credits_per_hour = availability_rate[tier]

  | Tier | Rate (credits/GPU-hour) |
  |------|------------------------|
  | ≤1B  | 5.0                    |
  | 7B   | 20.0                   |
  | 13B  | 25.0                   |
  | 30B  | 35.0                   |
  | 70B  | 34.6                   |
  | 100B+| 80.0                   |

Availability credits are issued hourly by the directory based on heartbeat confirmation.
The directory tracks `gpu_count` from the heartbeat to compute GPU-hours.

#### 4.4 Credit Expiry (TTL)

All S-Credits carry a TTL from issuance:

  | Tier | TTL    |
  |------|--------|
  | ≤1B  | 60 days|
  | 7B   | 90 days|
  | 13B  | 90 days|
  | 30B  | 180 days|
  | 70B  | 180 days|
  | 100B+| 365 days|

Expired credits are burned by the directory's nightly expiry sweep.

#### 4.5 Transaction Burn

On each routing transaction, 2% of the routing cost is destroyed (not transferred).
The serving node receives 98% of the routing cost; 2% is burned.
This sink is activated when the mesh reaches 20+ active nodes.

#### 4.6 Bootstrap Grant

On first successful heartbeat, the directory issues 100 S-Credits as a bootstrap
grant to new nodes. Reason: "bootstrap_grant". These credits carry the standard TTL.

#### 4.7 Premium Providers (P-Credits)

Premium providers register with `pricing_model: "premium"` and a valid
`premium_provider_token` issued by the directory maintainer.

Premium providers:
- Set MUST accept_s_credits = false
- Set MUST accept_p_credits = true
- MUST declare p_credit_rate (P-Credits per 1000 output tokens)
- MUST hold a valid premium_provider_token

P-Credits are non-interchangeable with S-Credits.
```

### 2.2 Changes to §3.3 DISCOVER (query parameters)

Add to the parameter table:
```
| accept_p_credits | MAY | Boolean; if true, return only premium (P-Credit) nodes |
| accept_s_credits | MAY | Boolean; if true, return only S-Credit peer nodes (default true) |
| accept_any       | MAY | Boolean; if true, return both premium and peer nodes |
```

### 2.3 Changes to §3.4 NODELIST

Add to the `pricing` object fields:
```
| pricing.pricing_model          | "per_token" or "premium"        |
| pricing.accept_s_credits       | bool — true for peer nodes       |
| pricing.accept_p_credits       | bool — true for premium nodes    |
| pricing.p_credit_rate          | float, null for non-premium      |
| pricing.p_credit_rate_unit     | "per_1000_tokens"                |
| pricing.p_credit_usd_rate      | float, null for non-premium      |
| pricing.premium_provider_verified | bool — directory-verified   |
| pricing.directory_commission   | float — fraction retained by dir |
```

### 2.4 New Endpoints

#### POST /v1/credits/earn (new — replaces admin-only /credits/award for task completion)

```
POST /v1/credits/earn
Authorization: Bearer <node_token>

{
  "task_id": "uuid",
  "output_tokens": 1247,
  "model_size_tier": "7B",
  "nonce": "...",
  "expires_at": "ISO-8601",
  "signature": "HMAC-SHA256-hex"
}

Response 200:
{
  "credits_earned": 1.247,
  "new_balance": 2593.247,
  "tokens_per_credit": 1000,
  "tier_weight": 1.0
}
```

The existing `POST /v1/credits/award` remains as admin-only for manual grants.

#### POST /v1/credits/spend (new)

```
POST /v1/credits/spend
Authorization: Bearer <node_token>

{
  "task_id": "uuid",
  "destination_node_id": "uuid",
  "output_tokens": 500,
  "routing_cost": 0.5
}

Response 200:
{
  "debited": 0.5,
  "burned": 0.01,
  "destination_credited": 0.49,
  "new_balance": 2592.747
}

Response 402 (insufficient):
{
  "error": {
    "code": "IICP-E028",
    "message": "InsufficientCredits",
    "balance": 0.247,
    "required": 0.5
  }
}
```

#### GET /v1/credits/routing-cost (new — pre-flight cost estimate)

```
GET /v1/credits/routing-cost?destination_node_id=uuid&tokens=500

Response 200:
{
  "estimated_cost": 0.5,
  "tier_weight": 1.0,
  "multiplier": 1.0,
  "tokens": 500,
  "tokens_per_credit": 1000
}
```

---

## 3. spec/iicp-core.md Changes

### 3.1 New §11.4 — Universal Credit Economy Rules

Add after the existing §11 IAL section:

```markdown
#### 11.4 Universal Credit Economy

Every served task earns credits for the serving node at the completion of a task
(not at routing time). The earning trigger is task completion confirmation.

**Earn trigger**: adapter reports task completion to directory via POST /v1/credits/earn.
**Spend trigger**: proxy checks balance and calls POST /v1/credits/spend before dispatching
a routed task.

The directory is the canonical ledger. Node-local credit balances are advisory only;
the directory balance is authoritative.

**Non-CIP nodes**: Standard IICP nodes (not enrolled in CIP) earn and spend S-Credits
for all routed tasks, not only CIP tasks. This is the primary change from Phase 2
CIP-only credit model.

**Credit neutrality principle**: The sum of all credits debited from routing nodes
equals the sum of all credits emitted to serving nodes (minus the 2% burn sink).
The directory must never create credits without a corresponding task completion.

**Tier declaration**: At registration, a node MUST declare its model_size_tier. This
declaration is used to compute tier_weight. False declarations reduce routing access
when benchmark probes reveal the discrepancy (Phase 5 mechanism, not enforced in v1).
```

### 3.2 New §11.5 — P-Credit System Rules

```markdown
#### 11.5 P-Credit System

Premium Credits (P-Credits) are a separate currency for commercial inference providers.

P-Credits:
- Are denominated in USD via p_credit_usd_rate
- Are purchased by users via the directory payment gateway
- Are non-interchangeable with S-Credits in both directions
- Are tracked per user account (not per node)
- Do not expire (or expire per provider contract, minimum 1 year)

S-Credit nodes cannot accept P-Credits.
Premium nodes cannot accept S-Credits.

The directory enforces the separation at the routing layer: the proxy MUST select
routing based on the user's payment type (S-Credit balance or P-Credit balance),
not by attempting to unify both into a single credit value.

Directory commission on P-Credit transactions: 5% retained, 95% credited to provider.
```

---

## 4. Implementation Changes

### 4.1 directory/app/Http/Controllers/CreditsController.php

#### New: `earn()` method (standard task completion)

```php
/**
 * POST /v1/credits/earn — award credits on task completion.
 *
 * Any authenticated node can call this. Replaces CIP-only award flow for
 * standard (non-CIP) tasks. Validates HMAC receipt same as award().
 * Applies tier_weight from model_size_tier.
 */
public function earn(Request $request): JsonResponse
{
    $validated = $request->validate([
        'task_id'          => ['required', 'string', 'max:255'],
        'output_tokens'    => ['required', 'integer', 'min:0'],
        'model_size_tier'  => ['required', 'string', 'in:500M,7B,13B,30B,70B,100B+'],
        'nonce'            => ['required', 'string', 'min:32'],
        'expires_at'       => ['required', 'string', 'date'],
        'signature'        => ['required', 'string', 'size:64'],
    ]);

    $node = $request->get('_authenticated_node');

    // Verify HMAC (same pattern as award())
    // Compute tier_weight from $validated['model_size_tier']
    // Call $this->credits->earn($node->id, $output_tokens, $tier_weight, $task_id, $nonce, $expires_at)
    // credits->earn() must be idempotent on (node_id, task_id, nonce) — nonce lock
    // Returns new balance
}
```

#### New: `spend()` method

```php
/**
 * POST /v1/credits/spend — deduct credits for a routed task.
 *
 * Called by the proxy before dispatching a routed task. Atomically checks
 * balance, deducts routing cost, and credits destination node.
 * Returns 402 InsufficientCredits if balance < cost.
 */
public function spend(Request $request): JsonResponse
{
    $validated = $request->validate([
        'task_id'             => ['required', 'string', 'max:255'],
        'destination_node_id' => ['required', 'uuid', 'exists:nodes,id'],
        'output_tokens'       => ['required', 'integer', 'min:1'],
        'routing_cost'        => ['required', 'numeric', 'min:0.0001'],
    ]);

    $node = $request->get('_authenticated_node');
    $balance = $this->credits->balance($node->id);

    if ($balance < $validated['routing_cost']) {
        return response()->json([
            'error' => [
                'code'     => 'IICP-E028',
                'message'  => 'InsufficientCredits',
                'balance'  => $balance,
                'required' => $validated['routing_cost'],
            ],
        ], 402);
    }

    // Atomic debit + destination credit + 2% burn
    $this->credits->transfer(
        from: $node->id,
        to: $validated['destination_node_id'],
        amount: $validated['routing_cost'],
        burn_fraction: 0.02,
        task_id: $validated['task_id'],
    );

    // Return new balance
}
```

#### Modify: `award()` method

- Remove the HMAC requirement for admin-direct grants (admin-only route, no HMAC needed)
- Add `reason: "bootstrap_grant"` as a recognized reason code
- Keep CIPWorkerReceipt path for backward compatibility

### 4.2 directory/app/Http/Controllers/RegisterController.php

Add bootstrap grant issuance after successful registration + first heartbeat:

```php
// In register() or heartbeat confirmation path:
if ($node->heartbeat_count === 1 && !$node->bootstrap_grant_issued) {
    $this->credits->award(
        nodeId: $node->id,
        amount: 100.0,
        reason: 'bootstrap_grant',
        taskId: 'BOOTSTRAP-' . $node->id,
    );
    $node->bootstrap_grant_issued = true;
    $node->save();
}
```

Column to add to `nodes` table: `bootstrap_grant_issued BOOLEAN DEFAULT false`.

### 4.3 directory/app/Services/CreditService.php (new or extend existing)

Add these methods to the service (or create if it doesn't exist yet):

```php
TIER_WEIGHTS = [
    '500M' => 0.05,
    '7B'   => 1.0,
    '13B'  => 2.0,
    '30B'  => 6.5,
    '70B'  => 32.0,
    '100B+' => 75.0,
];

public function earn(string $nodeId, int $outputTokens, string $tier, string $taskId, string $nonce): float
{
    $weight  = self::TIER_WEIGHTS[$tier] ?? 1.0;
    $credits = ceil($outputTokens / 1000) * $weight;
    // Idempotency: check nonce_used table; if nonce exists, return existing balance
    // Insert credit transaction, update balance, return new balance
    return $this->credit($nodeId, $credits, 'task_completion', $taskId);
}

public function transfer(string $from, string $to, float $amount, float $burnFraction, string $taskId): void
{
    $burn        = round($amount * $burnFraction, 4);
    $toReceive   = round($amount - $burn, 4);
    // Atomic DB transaction:
    //   debit($from, $amount, 'routing_spend', $taskId)
    //   credit($to, $toReceive, 'routing_receive', $taskId)
    //   credit(BURN_SINK, $burn, 'burn', $taskId) — or just discard
}

public function expireOldCredits(): int
{
    // Called by nightly scheduled job
    // Delete/zero out credit_transactions older than tier_ttl per node
    // Recompute balance for affected nodes
}
```

### 4.4 adapter/src/adapter/handlers/task.py

After a task is completed, call the directory's new `POST /v1/credits/earn` endpoint:

```python
async def _report_task_completion_for_credits(
    task_id: str,
    output_tokens: int,
    model_size_tier: str,
    node_token: str,
    node_hmac_key: str,
    directory_url: str,
) -> None:
    """Report task completion to directory to earn S-Credits.
    
    Called after every successful task (not just CIP tasks).
    Generates HMAC receipt same as CIPWorkerReceipt pattern.
    """
    nonce = secrets.token_hex(16)
    expires_at = (datetime.utcnow() + timedelta(minutes=5)).isoformat() + "Z"
    canonical = f"{task_id}:{output_tokens}:{nonce}"
    signature = hmac.new(node_hmac_key.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    
    payload = {
        "task_id": task_id,
        "output_tokens": output_tokens,
        "model_size_tier": model_size_tier,
        "nonce": nonce,
        "expires_at": expires_at,
        "signature": signature,
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{directory_url}/v1/credits/earn",
            json=payload,
            headers={"Authorization": f"Bearer {node_token}"},
        )
        if resp.status_code != 200:
            logger.warning(
                "credit_earn_failed",
                task_id=task_id,
                status=resp.status_code,
                body=resp.text[:200],
            )
        # Non-fatal: task completion is not rolled back if credit earn fails
        # The directory can reconcile from task logs if needed
```

Where to call it: in `task.py`'s `_execute_task()` or equivalent, in the success path
after the model response is returned but before the HTTP response is sent to the caller.

### 4.5 proxy/src/proxy/openai_compat/server.py

Before dispatching a routed task, check the routing node's S-Credit balance and pre-authorize:

```python
async def _check_and_reserve_credits(
    node_id: str,
    node_token: str,
    destination_node_id: str,
    destination_tier: str,
    destination_multiplier: float,
    estimated_output_tokens: int,
    directory_url: str,
) -> float:
    """Pre-check routing credit cost. Returns estimated cost or raises InsufficientCredits.
    
    The actual deduction happens post-task via _settle_routing_credits().
    Pre-check only verifies balance is sufficient.
    """
    cost = _compute_routing_cost(estimated_output_tokens, destination_tier, destination_multiplier)
    
    async with httpx.AsyncClient(timeout=3.0) as client:
        resp = await client.get(
            f"{directory_url}/v1/credits/balance",
            headers={"Authorization": f"Bearer {node_token}"},
        )
        balance = resp.json().get("balance", 0.0)
    
    if balance < cost:
        raise InsufficientCreditsError(balance=balance, required=cost)
    
    return cost


async def _settle_routing_credits(
    node_id: str,
    node_token: str,
    destination_node_id: str,
    task_id: str,
    actual_output_tokens: int,
    destination_tier: str,
    destination_multiplier: float,
    directory_url: str,
) -> None:
    """Settle actual credit cost after task completion."""
    cost = _compute_routing_cost(actual_output_tokens, destination_tier, destination_multiplier)
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.post(
            f"{directory_url}/v1/credits/spend",
            json={
                "task_id": task_id,
                "destination_node_id": destination_node_id,
                "output_tokens": actual_output_tokens,
                "routing_cost": cost,
            },
            headers={"Authorization": f"Bearer {node_token}"},
        )


def _compute_routing_cost(tokens: int, tier: str, multiplier: float) -> float:
    TIER_WEIGHTS = {
        "500M": 0.05, "7B": 1.0, "13B": 2.0,
        "30B": 6.5, "70B": 32.0, "100B+": 75.0,
    }
    weight = TIER_WEIGHTS.get(tier, 1.0)
    return math.ceil(tokens / 1000) * weight * multiplier
```

### 4.6 New Database Migrations

#### Migration 1: Extend credit_transactions for expiry and tier tracking

```php
// 2026_05_22_100000_extend_credit_transactions.php
Schema::table('credit_transactions', function (Blueprint $table) {
    $table->string('model_size_tier', 10)->nullable()->after('reason');
    $table->timestamp('expires_at')->nullable()->after('model_size_tier');
    $table->index(['node_id', 'expires_at']); // for nightly expiry sweep
});

Schema::table('nodes', function (Blueprint $table) {
    $table->boolean('bootstrap_grant_issued')->default(false)->after('credit_cost_multiplier');
    $table->string('model_size_tier', 10)->nullable()->after('bootstrap_grant_issued');
});
```

#### Migration 2: Premium credit tables (new)

```php
// 2026_05_22_200000_create_premium_credit_tables.php
Schema::create('premium_credit_balances', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->constrained()->cascadeOnDelete();
    $table->decimal('balance', 20, 6)->default(0);
    $table->string('currency', 3)->default('USD');
    $table->timestamps();
    $table->unique('user_id');
});

Schema::create('premium_credit_transactions', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->constrained()->cascadeOnDelete();
    $table->uuid('node_id');
    $table->string('task_id', 255);
    $table->unsignedInteger('tokens_consumed');
    $table->decimal('p_credits_spent', 20, 6);
    $table->decimal('usd_equivalent', 20, 6);
    $table->decimal('directory_commission', 20, 6)->default(0);
    $table->timestamps();
    $table->index(['user_id', 'created_at']);
    $table->foreign('node_id')->references('id')->on('nodes');
});

Schema::create('premium_provider_tokens', function (Blueprint $table) {
    $table->id();
    $table->uuid('node_id')->nullable(); // null = org-level token (covers multiple nodes)
    $table->string('organization', 255);
    $table->string('token_hash', 64); // SHA-256 of the issued token
    $table->timestamp('issued_at');
    $table->timestamp('expires_at');
    $table->boolean('revoked')->default(false);
    $table->timestamps();
    $table->index(['token_hash', 'revoked']);
});
```

---

## 5. Routing Table for New Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| IICP-E028 | 402 | InsufficientCredits — routing node has insufficient S-Credit balance |
| IICP-E029 | 422 | UnauthorizedPremiumDeclaration — node attempted premium registration without valid token |
| IICP-E030 | 422 | InvalidTierClaim — declared model_size_tier does not match registered model |

---

## 6. Backward Compatibility

### 6.1 Existing CIP nodes

The existing `POST /v1/credits/award` endpoint remains. CIP nodes that use the
CIPWorkerReceipt path continue to work unchanged. The new `POST /v1/credits/earn`
is an additional path for non-CIP standard task completion.

In a future cleanup (Phase 4), both paths should be merged. For now, maintain both
to avoid breaking existing CIP adapter implementations.

### 6.2 Nodes without model_size_tier declared

Nodes that registered before ADR-031 will not have `model_size_tier` set. These nodes:
- Default to `tier_weight = 1.0` (7B equivalent)
- Are prompted to update their registration with `model_size_tier` on next heartbeat
- The heartbeat endpoint should return a `"recommended_action": "declare_model_tier"` field
  when this field is missing

### 6.3 Zero-balance routing behavior (existing nodes)

Before routing costs are enforced, all nodes have zero balances and cannot route.
The activation sequence:
1. Deploy earn endpoint and adapter changes → nodes start accumulating credits
2. Wait 7 days → all active nodes have at least one week of credits
3. Enable spend enforcement in proxy → routing costs active
4. Issue bootstrap grants to all existing nodes retroactively (one-time admin script)

This sequencing prevents a "spend cliff" where routing suddenly stops working for all nodes.

---

## 7. Open Questions for Maintainer Decision

1. **Availability credit activation**: Should availability credits require the node to
   have passed a benchmark probe, or is heartbeat sufficient? (Risk: phantom nodes earn
   availability credits without real hardware.)

2. **Bootstrap grant amount**: 100 S-Credits covers ~100 cheap requests or ~3 expensive
   requests. Is this sufficient for new operators to explore the mesh before earning?

3. **2% burn activation threshold**: Document 03 recommends activating at 20 nodes.
   Should this be time-based (month 7) or node-count-based (20 nodes)?

4. **P-Credit welcome grant**: Should new user accounts receive a small P-Credit grant
   (e.g., 0.10 P-Credits = ~10 cents) for testing premium routing? This costs the
   directory real money, so it needs a daily cap.

5. **Premium provider commission**: 5% is proposed. Should it be lower for large
   providers (Anthropic-scale) and higher for small commercial providers? A tiered
   commission model adds complexity but may be necessary for large-volume deals.

6. **model_size_tier as an enum or float**: The current design uses enum strings.
   A float (e.g., 7.0, 13.0, 70.0) would be more flexible for intermediate sizes
   (e.g., Mistral 8×7B MoE which behaves like a 47B in weight but a 12B in compute).
   Decision affects how tier_weight interpolation works for non-standard sizes.
