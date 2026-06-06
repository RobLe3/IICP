# IICP Federated Monetary Committee (Mint) — Design and Governance

**Date**: 2026-05-22
**Status**: Research / Pre-spec
**Feeds**: ADR-031, ADR-032 (to be created), spec/iicp-dir.md §credit-governance
**Depends on**: 03-economy-growth-simulation.md (inflation analysis), 01-model-tier-roi-simulation.md (Scheme C weights)

---

## 1. The Inflation Problem and Why Static Sinks Are Insufficient

Document 03 established that the IICP credit economy is structurally inflationary.
Even with the recommended 90-day TTL expiry and 2% transaction burn, credits accumulate
faster than they are destroyed. The question this document addresses: can fixed parameters
hold the economy in a useful range as the mesh grows from 8 nodes to 500+?

### 1.1 The Stability Window for Static Parameters

With the current Scheme C weights, a fixed 2% transaction burn, and a 90-day TTL:

**Define net inflation rate** as:
```
monthly_inflation = (earn_per_month - spend_per_month - expiry_burn - tx_burn) / cumulative_balance
```

Using Phase data from document 03 (after sink):

| Phase | Nodes | Net credits added/month | Cumulative balance | Monthly inflation rate |
|-------|-------|------------------------|-------------------|------------------------|
| 1 | 8 | +300,836 | ~1.8M | 16.7% |
| 2 | 20 | +1,100,328 | ~8.4M | 13.1% |
| 3 | 50 | +3,098,862 | ~27M | 11.5% |
| 4 | 150 | +13,068,648 | ~105M | 12.4% |
| 5 | 500 | +39,953,952 | ~585M | 6.8% |

The monthly inflation rate ranges from 6.8% to 16.7% across phases — not converging.
The economy is mildly inflationary throughout, which is acceptable provided credits
retain meaningful scarcity signals. The danger zone is when credits-per-node reaches
a level where routing becomes semantically "free."

**Stability assessment by node count:**

At 50 nodes (Phase 3), average balance per node is ~540,000 credits. A 7B node can
route 540,000 requests to same-tier nodes — semantically unlimited. This is the first
inflection point where a static 2% burn is too weak.

At 500 nodes (Phase 5), average balance is ~1.17M credits per node. A 70B node could
afford 36,562 requests to other 70B nodes — equivalent to 52 days of uninterrupted
70B routing access. Credits have lost scarcity value.

**The static sink fails above ~200 nodes.** Below 50 nodes (Phase 1-2), static
parameters are adequate — the economy is small enough that absolute credit counts
do not undermine scarcity signals. Above 200 nodes, the fixed 2% burn is too weak
and the 90-day TTL must either shorten dramatically or be supplemented by a
parameter-setting body.

### 1.2 Why Parameter Adjustments Cannot Be Ad Hoc

One alternative to a governance body: the maintainer adjusts TTL and burn rate manually
as the mesh grows. The problems with this approach:

1. **Speed**: manual adjustment requires the maintainer to notice the problem, analyze
   it, and ship a configuration change. By the time any of these steps complete, the
   economy may have drifted further.

2. **Legitimacy**: nodes that registered expecting a 90-day TTL will object if the
   maintainer unilaterally reduces it to 30 days. A governance process gives operators
   advance notice and a voice in parameter changes.

3. **Alignment**: the maintainer has an interest in the protocol succeeding but also
   in individual operator satisfaction. A committee distributes the political cost of
   unpopular decisions (raising the burn rate, reducing TTL).

4. **Bus factor**: if the maintainer is unavailable for an extended period, the
   protocol needs a standing body that can respond to economic emergencies without
   waiting for a single person.

**Conclusion**: An adaptive parameter-setting body — the Federated Mint Committee —
is required to maintain economic stability above ~200 nodes.

---

## 2. The Federated Mint Committee — Structural Design

### 2.1 Eligibility Criteria

To become a Mint candidate, a directory node operator must satisfy ALL of the following:

| Criterion | Threshold | Verification source |
|-----------|-----------|---------------------|
| Node type | Full directory node (not a replica or Phase 6 federation peer) | Directory `node_type` field |
| Uptime | ≥ 99.5% rolling 90-day | REACH probes (DIR-PROBE-01, DIR-PROBE-03), NOT self-reported |
| REACH conformance | ≥ 98% pass rate across DIR-PROBE-01..DIR-FED-07 | REACH daemon `probe_pass_rate` |
| Operating duration | Continuously registered ≥ 180 days | Directory `registered_at` + no gaps > 48h in heartbeat history |
| Protocol violations | Zero IICP-E-class errors from misbehavior in last 365 days | Directory `violation_log` (distinct from timeouts/network errors) |
| Entity exclusivity | No affiliated entity currently holds another active Mint seat | Operator-declared; enforced by social layer + Mint vote |

**On "affiliated entity"**: an operator declares at registration whether their node is
operated by the same legal entity as any other registered node. Self-declaration; the
protocol cannot introspect corporate structure. Deliberate false declaration is a
protocol violation that invalidates candidacy retroactively.

**Why REACH probes, not self-reported uptime**: a node can self-report 99.9% uptime
regardless of actual availability. REACH probes (external, continuous, from multiple
origins) are the only non-gameable source of uptime data. The 99.5% threshold
corresponds to at most ~10.8 hours of downtime per 90-day window.

### 2.2 Committee Structure

**Fixed size**: 9 seats.

Nine seats were chosen for three reasons:
1. Small enough to act quickly (scheduling 9 people for a vote is tractable)
2. Large enough to represent mesh diversity (geographic, model-tier, organizational)
3. Divisible into three rotating cohorts of 3 seats each

**Rotation**: 3 seats rotate each quarter. The three longest-serving members must
vacate. New seats are filled by the highest-scoring eligible candidates not currently
seated (ranking by REACH conformance score as the tiebreaker).

**Decisions**:
- Routine parameter changes: 6/9 supermajority (67% threshold)
- Emergency actions: 9/9 unanimous vote
- Eligibility rule changes: 8/9 supermajority (89% threshold); must be ratified
  by the protocol maintainer before taking effect

**Term limit**: No single entity may hold a Mint seat for more than 6 consecutive
quarters (18 months). After 6 quarters, the member is ineligible for the next 2
quarters before re-candidacy is permitted.

**Quorum**: A vote requires all 9 members to cast ballots. Abstentions count against
a supermajority. If a member is unreachable for > 7 days during an active vote,
the Mint may declare them temporarily inactive and proceed with 8-member quorum,
but this requires a 7/8 supermajority for routine decisions and 8/8 for emergency.

### 2.3 Parameters Under Mint Control

The Mint controls the following parameters. All are bounded — the Mint cannot set
any parameter outside its allowed range, even by unanimous vote. Protocol code
enforces the bounds, not committee policy.

| Parameter | Default | Mint-settable range | Max change per quarter | Notes |
|-----------|---------|--------------------|-----------------------|-------|
| Credit supply growth target | — | 0.5%–8% per month | — | Target, not enforced; Mint monitors vs actual |
| Quality tier weights | Scheme C values | Per-tier; ±20% per quarter | ±20% per tier | See §2.3.1 for bounds computation |
| Routing cost base schedule | Scheme C weights | Per-tier; ±20% per quarter | ±20% per tier | Changes take effect next billing epoch |
| Bootstrap grant | 100 S-Credits | 10–500 S-Credits | ±50% per quarter | Applied to new registrations only |
| Credit TTL by tier | 60–365 days | 30–365 days per tier | ±30 days per quarter | Lower bound 30 days; upper bound 365 days |
| Dynamic pricing floor multiplier | 0.5× | 0.1×–1.0× | ±0.2 per quarter | Applied to base routing cost |
| Dynamic pricing ceiling multiplier | 3.0× | 1.0×–10.0× | ±1.0 per quarter | Applied to base routing cost |
| Transaction burn rate | 2% | 0%–10% | ±2% per quarter | Applied to routing spend |

**§2.3.1 — Bounding quarterly weight changes for §C weights:**

The Scheme C 70B weight is 32.0. A 20% increase gives 38.4; a 20% decrease gives 25.6.
Per-tier bounds at initial Scheme C values:

| Tier | Current weight | Min (after 20% down) | Max (after 20% up) |
|------|---------------|---------------------|-------------------|
| ≤1B | 0.05 | 0.04 | 0.06 |
| 7B | 1.0 | 0.8 | 1.2 |
| 13B | 2.0 | 1.6 | 2.4 |
| 30B | 6.5 | 5.2 | 7.8 |
| 70B | 32.0 | 25.6 | 38.4 |
| 100B+ | 75.0 | 60.0 | 90.0 |

These are the bounds for a single quarter from the Scheme C starting point. After a
change, the ±20% applies to the NEW value, not the original. This allows gradual drift
but prevents abrupt shifts.

### 2.4 What the Mint Cannot Do

The following are protocol-enforced (enforced by directory code, not Mint policy):

1. **Create credits without task-serving events.** The directory's credit-emission path
   (`POST /v1/credits/earn`) requires a valid HMAC receipt for a task completion event.
   There is no code path the Mint can invoke to mint credits from nothing.

2. **Confiscate credits already in node balances.** The `credit_transactions` table is
   append-only for existing records. The Mint can change TTL going forward; it cannot
   retroactively expire credits that were issued under a longer TTL at issuance time.

3. **Exclude eligible nodes from candidacy.** The eligibility criteria in §2.1 are
   protocol-level. The Mint cannot add new criteria (e.g., "must be in region X" or
   "must run model Y") — only the maintainer can change eligibility criteria, and only
   with 8/9 Mint ratification.

4. **Change any parameter by more than 20% per quarter.** The directory validates all
   governance action payloads against the parameter bounds table before applying them.
   A payload exceeding bounds is rejected with IICP-E031 (GovernanceParameterOutOfBounds).

5. **Override a unanimous 9/9 vote to reject an emergency action.** If a proposed
   emergency action fails to achieve 9/9 unanimous support, it does not proceed.
   There is no appeal mechanism above the Mint for emergency actions. Non-emergency
   actions need only 6/9.

---

## 3. Anti-Manipulation Design

### 3.1 Why Mint Seat Accumulation Is Not Economically Viable

An attacker who wants to control the Mint must hold 6 seats to force routine parameter
changes, or 9 seats for emergency powers. Consider the cost of accumulating 6 seats:

**Operational requirements per seat** (from §2.1 eligibility):
- Run a full directory node continuously for 180+ days before candidacy
- Maintain 99.5% uptime verified by external REACH probes
- Maintain 98%+ REACH conformance across all probe types
- Pay all infrastructure costs for a production directory node

**Estimated infrastructure cost per directory node:**
A full directory node in Phase 3+ handles registration, discovery, and credit ledger
operations. Minimum viable production stack: 2 vCPUs, 4 GB RAM, 40 GB SSD, 1 Gbps
network — approximately $40–$80/month on any major cloud provider. Add monitoring,
database backup, and operational overhead: approximately $100–$150/month per node.

**Cost to accumulate 6 seats:**
```
6 nodes × $150/month × 6+ months of waiting = $5,400+ before candidacy
After candidacy: 6 × $150/month = $900/month ongoing infrastructure cost
```

**Maximum benefit from controlling 6 seats:**
The attacker can push any single parameter by 20% per quarter. For example, they could
increase the 70B weight from 32.0 to 38.4 in one quarter. If the attacker also runs
a 70B node, this increases their daily credit earnings:

```
Before: 345,600 tokens/day × 32.0 / 1000 = 11,059 credits/day
After:  345,600 tokens/day × 38.4 / 1000 = 13,271 credits/day
Gain:   2,212 credits/day
```

At a credit value of ~$0.001 (soft anchor from document 03), this is $2.21/day in
additional routing access value — roughly $66/month.

**Return on investment:**
```
Monthly cost of 6 directory nodes: $900
Monthly gain from manipulated weights: $66
Net: -$834/month
```

Controlling 6 Mint seats to inflate a single tier weight produces a net loss of roughly
$834/month. The economic attack is not viable.

**Important caveat**: this analysis assumes the attacker's goal is to enrich themselves
via credit accumulation. If the attacker's goal is ideological (sabotage the protocol)
rather than financial, the cost-benefit analysis changes. The transparency layer (§3.2)
addresses this case — sabotage attempts are visible and addressable by the community.

### 3.2 Transparency Layer

**All Mint votes are recorded on the event ledger as `CREDIT_GOVERNANCE` events.**

The event payload (logged in the directory's event system, queryable via the spec's
event endpoint):

```json
{
  "event_type": "CREDIT_GOVERNANCE",
  "event_id": "uuid",
  "timestamp": "ISO-8601",
  "governance": {
    "vote_id": "uuid",
    "proposal": "increase_burn_rate",
    "current_value": 0.02,
    "proposed_value": 0.03,
    "effective_date": "ISO-8601",
    "votes": [
      { "member_node_id": "uuid", "position": "for", "cast_at": "ISO-8601" },
      { "member_node_id": "uuid", "position": "against", "cast_at": "ISO-8601" }
    ],
    "outcome": "passed",
    "supermajority_threshold": "6/9",
    "tally": { "for": 7, "against": 2 }
  }
}
```

Queryable by any operator:
```
GET /v1/events?type=CREDIT_GOVERNANCE
GET /v1/events?type=CREDIT_GOVERNANCE&since=2026-01-01
GET /v1/events/governance/{vote_id}
```

Votes are public: `member_node_id` is the permanent identifier of the voting node.
The node's operator identity is derivable from the directory's node registry. Anonymous
voting is not available — accountability requires attribution.

**Automated anomaly detection:**

The directory computes a `self_serving_score` for each Mint member based on vote history:

```
self_serving_score(member) =
  (votes that increased member's tier weight) /
  (total governance votes cast by member)
```

A member who consistently votes for changes that increase their own model tier's weight
relative to other tiers accumulates a high `self_serving_score`. This score is:
- Published in the `/v1/governance/members` endpoint
- Not automatically acted upon (no automatic removal or vote invalidation)
- Available to the community for social accountability

The protocol takes no autonomous action on `self_serving_score` — it is a transparency
signal, not an enforcement mechanism. The community social layer handles persistent
self-serving behavior (e.g., by not electing that member in future rotation cycles).

### 3.3 Emergency Powers

**Trigger condition for emergency session:**

If total system credit supply grows by more than 10% in any single calendar month
(double the maximum Mint-set target of 8%), the Mint may declare an economic emergency.

"System credit supply growth" is computed by the directory as:
```
monthly_supply_growth = (total_credits_issued_this_month) / (cumulative_credits_outstanding_start_of_month)
```

This uses only credits issued (not burned/expired) and measures the raw emission rate.

**Emergency session procedure:**
1. Any Mint member may call an emergency session by posting a signed proposal to the
   governance endpoint
2. All 9 members are notified immediately
3. 9/9 unanimous vote required to activate emergency parameters
4. Emergency parameters available: temporary burn rate increase (up to 10%, regardless
   of quarterly limit) or TTL reduction (down to 30 days, regardless of quarterly limit)
5. Emergency parameters expire after 30 days without renewal vote
6. Renewal requires another 9/9 vote
7. Total emergency parameter duration cannot exceed 90 days per 12-month period
   (prevents emergency powers from becoming a governance workaround)

**Emergency actions that are categorically forbidden:**
- Cannot change eligibility criteria for Mint membership
- Cannot exclude a qualified candidate from candidacy
- Cannot revoke a seated Mint member's seat
- Cannot confiscate credits from node balances
- Cannot change the protocol-enforced bounds on any parameter

These prohibitions hold even in emergency. The purpose is to prevent a captured Mint
from using "emergency" framing to lock out challengers or consolidate control.

---

## 4. The Mint's First Parameterization (Year 1)

The Mint committee does not exist during Year 1 — the mesh has fewer than 200 nodes
and static parameters are adequate. The parameters below are the **pre-Mint bootstrap
defaults** and serve as the Mint's starting point when it first convenes.

The Mint convenes when:
- Mesh has ≥ 200 active full directory nodes AND
- At least 9 nodes have met all eligibility criteria for ≥ 30 days AND
- Maintainer has authorized first Mint session

### 4.1 Bootstrap Parameters (Months 1–12)

These favor credit creation over strict control during early growth, per the
recommendation in document 03 (§7, "Launch without a sink months 1-6"):

| Parameter | Month 1–6 | Month 7–12 | Rationale |
|-----------|-----------|-----------|-----------|
| Transaction burn rate | 0% | 2% | No burn during bootstrap; activate at 20 nodes |
| Credit TTL — ≤1B | None | 60 days | No expiry in first 6 months |
| Credit TTL — 7B | None | 90 days | Activate at 20 nodes per document 03 |
| Credit TTL — 13B | None | 90 days | Same |
| Credit TTL — 30B | None | 180 days | Same |
| Credit TTL — 70B | None | 180 days | Same |
| Bootstrap grant | 100 credits | 100 credits | Maintained throughout Year 1 |
| Dynamic pricing floor | 1.0× (off) | 1.0× (off) | No dynamic pricing in Phase 1 |
| Dynamic pricing ceiling | 1.0× (off) | 1.0× (off) | Activates in Phase 6 |

### 4.2 Quality Tier Weights (From Scheme C)

The Mint's first quality tier weight table inherits directly from Scheme C (document 01 §5.3):

| Tier | Weight | Monthly HW cost | Credits/day at 50% util |
|------|--------|----------------|------------------------|
| ≤1B | 0.05× | $50 | 432 |
| 7B | 1.0× | $300 | 2,592 |
| 13B | 2.0× | $2,000 | 3,024 |
| 30B | 6.5× | $4,000 | 5,616 |
| 70B | 32.0× | $8,000 | 11,059 |
| 100B+ | 75.0× | variable | — |

These weights were derived in document 01 §5 using the parity calculation:
"1× 70B node earns ≥ 4× 7B nodes at equivalent hardware investment."

**The Mint's Year 1 mandate**: do not change these weights until the Scheme C parity
assumption is validated against real-world mesh data. At minimum 6 months of real
earning data should be collected before any weight adjustment is proposed.

### 4.3 Availability Credits (Bootstrap Phase, Months 1–12)

Per document 01 §6 (Scheme D), availability credits are active during bootstrap to
ensure early adopters of high-tier nodes receive earnings even when demand is low:

| Tier | Availability rate (credits/GPU-hour) | Notes |
|------|-------------------------------------|-------|
| ≤1B | 5.0 | Counts as 0.25 GPU-hours/hour |
| 7B | 20.0 | 1 GPU |
| 13B | 25.0 | 1 GPU |
| 30B | 35.0 | 2 GPUs |
| 70B | 34.6 | 4 GPUs |
| 100B+ | 80.0 | Variable GPU count |

Availability credits are issued hourly by the directory. They are capped at 30% of
full-load token earnings to prevent phantom node exploitation (a node that earns only
availability credits without ever serving tasks).

**Deactivation trigger**: availability credits are phased out at month 13 (or when
mesh utilization reaches 70% fleet-wide, whichever comes first). The phase-out is
gradual: rate reduced 50% at trigger, then to 0 after another 90 days.

### 4.4 Recommended Year 1 Monitoring Thresholds

The Mint (once convened) or the maintainer (prior to Mint formation) should watch for:

| Signal | Threshold | Recommended action |
|--------|-----------|-------------------|
| Credits-per-node average | > 500,000 | Reduce TTL by 30 days; increase burn rate by 1% |
| Monthly supply growth | > 8% | Call Mint review session (not emergency unless > 10%) |
| 70B/7B earn ratio (per node) | < 3.0× | Increase 70B weight; investigate if quality weights drifted |
| Bootstrap grant redemption rate | < 50% | Investigate onboarding friction; consider 1-day TTL on unused grant credits |
| Price stays at dynamic floor > 2 weeks | Any tier | Mint signal: that tier is oversupplied; reduce quality weight by 10% |
| Price stays at dynamic ceiling > 2 weeks | Any tier | Mint signal: attract more operators; increase bootstrap grant or quality weight |

---

## 5. Open Questions for Maintainer

1. **Mint formation trigger**: should the Mint form at 200 nodes (as proposed) or at
   a calendar date (e.g., 18 months post-launch)? Node-count trigger is responsive to
   actual growth; calendar-date trigger is predictable for operators planning candidacy.

2. **Genesis node Mint eligibility**: genesis nodes (registered before public beta) are
   proposed to bypass the 180-day waiting period (see document 08). Should they also
   bypass the 90-day uptime window, using the first 90 days after public launch instead?

3. **Tie-breaking in seat rotation**: when multiple candidates have identical REACH
   conformance scores, what is the secondary tiebreaker? (Options: registration date,
   model tier diversity preference, geographic diversity preference.)

4. **Cross-mint communication**: should the Mint have a formal communication channel
   (e.g., a mailing list or a governance forum)? Or are votes the only formal communication?

5. **Emergency session initiation threshold**: the current proposal allows any single
   member to call an emergency session. Should this require 3/9 members to co-sign
   the initiation request to prevent frivolous emergency calls?
