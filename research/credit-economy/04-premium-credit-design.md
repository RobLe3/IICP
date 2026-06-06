# Credit Economy — Premium Credit (P-Credit) System Design

**Date**: 2026-05-22  
**Status**: Research / Pre-spec  
**Feeds**: ADR-031, spec/iicp-dir.md §premium-providers

---

## 1. The Two-Credit System — Structural Separation

IICP operates two distinct, non-interchangeable credit systems:

| Dimension | S-Credit (Standard) | P-Credit (Premium) |
|-----------|--------------------|--------------------|
| Origin | Earned by serving inference | Purchased with hard currency |
| Purpose | Peer economy routing reciprocity | Paying commercial providers |
| Exchange | Non-fungible for P-Credits | Non-fungible for S-Credits |
| Issuer | Directory (auto, on task completion) | Directory (manual, via payment gateway) |
| Storage | `credits` table, per node | `premium_credit_balances` table, per user account |
| Expiry | TTL per tier (60–180 days) | No expiry (or configurable, e.g. 1 year) |
| Who accepts | Peer nodes (S-Credit economy) | Premium providers only |
| Who earns | Any registered IICP node | No one earns P-Credits — only purchased |

**The firewall**: S-Credits and P-Credits cannot be converted in either direction.

### 1.1 Why Non-Interchangeability is Mandatory

If you could convert S-Credits to P-Credits:
- Wealthy actors could buy S-Credits (or run many nodes to earn them) and convert to
  P-Credits, bypassing the "you give, you get" reciprocity model
- The peer economy would be flooded with artificial "contributors" who never serve
- High-tier contributors (70B operators) would find their routing access undercut by
  parties who bought their way in without contributing infrastructure

If you could convert P-Credits to S-Credits:
- Premium providers (Anthropic etc.) could dump excess P-Credits into the peer economy
- This would inflate the S-Credit supply and destroy the scarcity signal
- Small mesh operators would be crowded out by commercial liquidity

The firewall is an **economic identity boundary**: the mesh's peer economy is a distinct
system from commercial API billing. Keeping them separate is not a technical convenience;
it is a philosophical requirement of the protocol.

---

## 2. Premium Provider Node Declaration

A premium provider registers exactly like a standard node but with additional fields.

### 2.1 Registration payload addition

```json
{
  "node_id": "uuid",
  "endpoint": "https://opus-01.iicp.anthropic.com",
  "model_name": "claude-opus-4-7",
  "model_size_tier": "100B+",
  "pricing": {
    "pricing_model": "premium",
    "accept_s_credits": false,
    "accept_p_credits": true,
    "p_credit_rate": 0.075,
    "p_credit_rate_unit": "per_1000_tokens",
    "currency": "USD",
    "p_credit_usd_rate": 1.0
  },
  "premium_provider_token": "anthropic:opus-farm-01:HMAC-signed-token"
}
```

Field semantics:

| Field | Type | Meaning |
|-------|------|---------|
| `pricing_model` | enum | `"premium"` declares commercial intent |
| `accept_s_credits` | bool | MUST be `false` for premium providers |
| `accept_p_credits` | bool | MUST be `true` for premium providers |
| `p_credit_rate` | float | P-Credits consumed per 1000 output tokens |
| `p_credit_rate_unit` | string | Unit of rate: always `"per_1000_tokens"` in v1 |
| `currency` | string | Always `"USD"` in v1 — P-Credits are USD-denominated |
| `p_credit_usd_rate` | float | Exchange rate at time of registration: P-Credits per USD |
| `premium_provider_token` | string | Directory-issued credential proving whitelist membership |

### 2.2 Directory Whitelist

The `premium_provider_token` is a directory-signed JWT or HMAC credential that:
1. Identifies the provider organization (Anthropic, Mistral, etc.)
2. Certifies that the directory maintainer has verified their identity
3. Authorizes `pricing_model: "premium"` status
4. Is renewed quarterly (like a certificate)

Without a valid `premium_provider_token`, the directory MUST:
- Reject the `pricing_model: "premium"` field with IICP-E029 (UnauthorizedPremiumDeclaration)
- Register the node as a standard S-Credit node with `pricing_model: "per_token"` default

This is the primary anti-fraud mechanism: you cannot self-declare as premium.

---

## 3. Discovery Filter Extensions

The `/v1/discover` endpoint gains three new filters:

| Parameter | Value | Effect |
|-----------|-------|--------|
| `accept_p_credits` | `true` | Return only premium nodes |
| `accept_s_credits` | `true` | Return only peer S-Credit nodes (default behavior) |
| `accept_any` | `true` | Return mixed results (peer + premium) |

When no payment filter is specified, default behavior is `accept_s_credits=true` for
backward compatibility. Existing clients that do not set any payment filter continue to
see only S-Credit peer nodes.

### 3.1 NODELIST response additions for premium nodes

```json
{
  "node_id": "uuid",
  "endpoint": "https://opus-01.iicp.anthropic.com",
  "score": 0.99,
  "pricing": {
    "pricing_model": "premium",
    "accept_s_credits": false,
    "accept_p_credits": true,
    "p_credit_rate": 0.075,
    "p_credit_rate_unit": "per_1000_tokens",
    "currency": "USD",
    "p_credit_usd_rate": 1.0,
    "premium_provider_verified": true
  }
}
```

`premium_provider_verified: true` is set by the directory when the node's
`premium_provider_token` has been validated. This is the trust signal for the proxy.

---

## 4. P-Credit Purchase Flow

```
User (consumer)
    │
    ▼
iicp.network payment gateway (Stripe)
    │  → user selects amount (e.g., 10 USD → 10 P-Credits)
    │  → Stripe charge succeeds
    ▼
Directory payment webhook
    │  → verify Stripe event signature
    │  → credit user's P-Credit balance: +10.00
    ▼
premium_credit_balances table
    │  → user_account_id: xyz, balance: 10.00
    ▼
User's proxy routes to premium node
    │  → proxy checks P-Credit balance ≥ routing cost
    │  → deducts: 500 tokens × 0.075 / 1000 = 0.0375 P-Credits
    │  → records transaction in premium_credit_transactions
    ▼
Premium node receives request
    │  → serves inference
    │  → directory credits premium_provider with P-Credits earned
    │    (net of any directory commission — initially 0%, TBD)
    ▼
Premium provider settlement (monthly)
    │  → Provider requests payout of accumulated P-Credits
    │  → Directory settles at p_credit_usd_rate × P-Credits_earned
    │  → Wire transfer / ACH to provider
```

### 4.1 P-Credit Balance Storage

```sql
-- New table: premium_credit_balances
CREATE TABLE premium_credit_balances (
    id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id      BIGINT UNSIGNED NOT NULL,      -- User account, not node
    balance      DECIMAL(20,6) NOT NULL DEFAULT 0,
    currency     VARCHAR(3) NOT NULL DEFAULT 'USD',
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- New table: premium_credit_transactions
CREATE TABLE premium_credit_transactions (
    id               BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id          BIGINT UNSIGNED NOT NULL,
    node_id          UUID NOT NULL,              -- Destination premium node
    task_id          VARCHAR(255) NOT NULL,
    tokens_consumed  INT UNSIGNED NOT NULL,
    p_credits_spent  DECIMAL(20,6) NOT NULL,
    usd_equivalent   DECIMAL(20,6) NOT NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 5. The Anthropic Example — Concretely

**Scenario**: Anthropic deploys 100 × Claude Opus 4.7 nodes on IICP.

**Registration**:
- All 100 nodes registered with Anthropic's `premium_provider_token`
- `p_credit_rate = 0.075` (= $75 per million tokens → $0.075 per 1000 tokens)
- `p_credit_usd_rate = 1.0` (1 P-Credit = $1 USD at registration)
- `accept_s_credits = false`

**Consumer experience**:
```
User queries the proxy for a demanding task (e.g., "explain this 10,000-token codebase"):
  → proxy calls /v1/discover?accept_p_credits=true&intent=urn:iicp:intent:llm:chat:v1
  → directory returns list of premium nodes including Anthropic's Opus 4.7 nodes
  → proxy checks user's P-Credit balance
  → for a 2,000-token response: cost = 2 × 0.075 = 0.15 P-Credits ($0.15)
  → if balance ≥ 0.15, proxy dispatches to Anthropic node
  → Anthropic node serves the inference
  → directory deducts 0.15 P-Credits from user balance, credits Anthropic's ledger
```

**Anthropic's settlement**: Anthropic's 100 nodes collectively serve X tokens/month.
Directory settles X × 0.075 / 1000 P-Credits, converted at $1.00/P-Credit → USD payment.

**What a standard IICP peer node can do**: NOTHING. A peer node with 1 million S-Credits
cannot access Anthropic's Opus 4.7 nodes. The S-Credit balance is irrelevant for premium
routing. To access Anthropic nodes, a user must purchase P-Credits — there is no other path.

**What a user with BOTH S-Credits and P-Credits does**:
- Routine tasks → peer network (S-Credits, earned by serving or by welcome grant)
- Demanding tasks → Anthropic premium (P-Credits, purchased)
- The proxy handles both in separate routing flows based on the intent annotation

---

## 6. Firewall Edge Cases

### 6.1 What if a premium provider goes bankrupt?

**Scenario**: Anthropic (hypothetically) ceases IICP premium operations.

**Impact**:
- P-Credits in user balances designated for Anthropic nodes become unspendable
- The directory freezes Anthropic's premium_provider_token
- All 100 Anthropic nodes are delisted from discover results
- P-Credit balances are NOT automatically refunded (directory is not a financial institution)

**Recommended mitigation** (directory policy, not protocol):
1. Directory maintains an insurance reserve: a % of all premium node receipts is held
   in escrow for 30 days before settlement to providers
2. If a provider disappears, the escrow is used to refund affected user P-Credit balances
3. Users whose P-Credits are tied to a single provider should be notified if that
   provider's heartbeat goes dark for > 24 hours

**Protocol-level protection**: The spec should require that premium providers specify
a `settlement_frequency` (daily, weekly, monthly) and that providers hold a minimum
reserve with the directory (e.g., 2 weeks of average billing) as a bond.

**What the protocol cannot protect**: A premium provider who has received settlement
and then immediately disappears. The reserve helps but does not fully cover this case.

### 6.2 What if a premium provider misbehaves?

**Scenario**: A premium provider serves degraded outputs (routing "Opus 4.7" tasks to
a 7B model behind the scenes) while charging P-Credit rates.

**Current protocol gap**: There is no inference quality verification in IICP.
The protocol trusts that declared model capabilities match actual outputs.

**Mitigations available**:
1. Reputation system (existing): providers accumulate reputation scores. Quality
   complaints reduce reputation, and low-reputation premium nodes are surfaced less.
2. Directory audit: directory maintainer can spot-check premium node outputs.
3. Challenge-response: a future protocol extension (Phase 6+) where the directory
   periodically issues benchmark tasks and verifies outputs against known-good answers.
4. Consumer reporting: users can flag a task as low-quality; directory tracks flagging
   rate per premium provider.

**What the protocol cannot protect against in v1**: A sophisticated provider who serves
accurate outputs for audit probes but degrades for regular users (distinguishing probe
traffic). This is a hard problem requiring trusted hardware attestation (future work).

### 6.3 Can S-Credit nodes ever access premium nodes?

**Answer: No, by design.**

The routing path for premium nodes requires:
1. A `user_id` with a P-Credit balance (not a `node_id` with S-Credits)
2. The proxy to explicitly select a premium node via `?accept_p_credits=true` discovery
3. A P-Credit deduction before dispatch

S-Credit balances are stored on `node_id`. P-Credit balances are stored on `user_id`.
These are different database tables, different authentication paths, and different
routing flows. There is no code path that converts S-Credits to P-Credits for routing.

**Attempted circumvention**: A node operator might try to route through a local proxy
that buys P-Credits on their behalf. This is legal — they are buying P-Credits with
real currency, which is exactly what the system is designed to support. The "firewall"
is not about preventing S-Credit operators from accessing premium services — it's about
preventing S-Credits from being used AS PAYMENT for premium services.

### 6.4 What prevents a non-whitelisted node from declaring premium status?

The `premium_provider_token` validation is the gate. The directory validates:
1. Token signature (HMAC-SHA256 with directory's admin key)
2. Token expiry (max 90 days, renewable)
3. Token `node_organization` matches the registering endpoint's domain

If any validation fails, the directory returns IICP-E029 and falls back to registering
the node as a standard S-Credit peer node. The node cannot refuse this fallback — the
directory is the authority on node classification.

A malicious node that somehow obtains a valid premium_provider_token from another
provider is blocked by the domain check: Anthropic's token cannot be used to register
a non-Anthropic endpoint.

---

## 7. The "Classical IICP" Firewall — Identity Statement

The maintainer's formulation: "they should not be mistaken for the classical IICP
'you give, you get' like in well-calibrated socialism sense."

The P-Credit system is structurally separate from the S-Credit peer economy. Premium
providers are a parallel track — they participate in IICP as a distribution channel,
not as mesh peers. They do not:
- Earn S-Credits by serving
- Spend S-Credits when routing
- Participate in reputation scoring (they have their own commercial SLA)
- Affect the S-Credit supply or value

They do:
- Appear in discover results when `?accept_p_credits=true` is set
- Provide superior-quality inference to users who pay
- Create a revenue stream for the IICP directory via any commission
- Expand the mesh's effective capability ceiling without distorting peer economics

The visual metaphor: IICP S-Credits are a barter economy (work for work). P-Credits
are cash. You can bring cash to a barter market and buy things from vendors who accept
both — but you can't pay with barter tokens at the currency exchange. The markets are
adjacent, not merged.

---

## 8. P-Credit Rate Stability

**Problem**: If `p_credit_usd_rate` is fixed at registration and USD/compute prices
change, premium providers are either over- or under-compensated.

**Solution**: Premium providers update their `p_credit_rate` via heartbeat, subject to:
- Maximum 10% rate change per month (prevents predatory repricing)
- 7-day advance notice in the NODELIST response (`pricing.effective_from` field)
- Rate increases require directory acknowledgment (existing `attested` field semantics)

Users who see a rate increase coming can pre-purchase P-Credits at the old rate:
```json
{
  "pricing": {
    "p_credit_rate": 0.075,
    "effective_until": "2026-06-01T00:00:00Z",
    "p_credit_rate_next": 0.080,
    "effective_from": "2026-06-01T00:00:00Z"
  }
}
```

The directory enforces the scheduled rate change automatically at `effective_from`.

---

## 9. P-Credit Purchase UX Scenarios

**Scenario A — Individual researcher**:
User buys 5 P-Credits ($5) to access 66,667 tokens of Opus 4.7 inference
(5 / 0.075 × 1000 = 66,667 tokens). This covers roughly 133 × 500-token requests.

**Scenario B — Organization with pre-negotiated bulk rate**:
Organization buys 10,000 P-Credits ($10,000) with a 10% bulk discount applied by
the directory at purchase → 11,000 P-Credits credited. Used for high-volume
organizational AI workflows via IICP mesh.

**Scenario C — Developer bootstrapping**:
Directory issues a small P-Credit welcome grant (0.10 P-Credits = $0.10 equivalent)
to new registered users for testing premium routing. This is distinct from the S-Credit
welcome grant for new nodes.

---

## 10. Commission and Sustainability

The directory is a public good operated by the maintainer. To sustain operations,
a small commission on P-Credit transactions is appropriate:

**Recommended**: 5% directory commission on all P-Credit routing transactions.
- A user spending 0.075 P-Credits for 1000 tokens: directory retains 0.00375 P-Credits
- Premium provider receives 0.07125 P-Credits
- At $1/P-Credit: directory earns $0.00375 per 1000 tokens served by premium providers

At 100M premium tokens/month: directory earns 100,000 × $0.00375 = $375/month.
At 1B premium tokens/month: $3,750/month. At this scale it covers hosting costs.

The 5% commission is disclosed at premium provider registration and in the discover
response (`pricing.directory_commission: 0.05`). It is not extracted from S-Credit
transactions (peer economy is free of directory commission).
