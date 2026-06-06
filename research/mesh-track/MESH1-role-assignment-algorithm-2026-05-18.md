# MESH1 — Role-Assignment Algorithm Design

**Track**: MESH — Consolidator Pattern, Role-Based Routing, Load-Aware Selection  
**Issue**: #180 (MESH1: Role-assignment algorithm for general, specialist, and consolidator roles)  
**Date**: 2026-05-18  
**Author**: RESA loop, FORGE iter82  
**Depends on**: REP1 (#167), REP2 (#168) — thresholds informative; design proceeds without ratified values  
**Length**: ≈1900 words (within ≤2000 limit)  
**ADR impact**: Expands ADR-028; specifies event-log format for ADR-013 compatibility.

---

## 1. Roles and Their Properties

Three mutually exclusive roles (per architecture §7):

| Role | Population target | Eligibility basis | Primary work |
|------|------------------|------------------|--------------|
| **General inference** | Majority of nodes | Any node meeting minimum reputation threshold | Broad intent types |
| **Specialist inference** | Small pool per specialty | Demonstrated superiority in specific intent type | High-match-intent tasks only |
| **Consolidator** | Small curated pool | Top reputation + high capacity + diversity constraints | Multi-path synthesis |

Role assignment is performed by the directory, not by node-to-node election. A node
cannot claim a role; it earns assignment through measurable behavior verified by the
directory's observable data.

---

## 2. Inputs to Role Assignment

The directory has access to the following observable data per node:

| Input | Source | Trustworthiness |
|-------|--------|----------------|
| Reputation score (time-windowed: 24h, 7d, 30d) | Directory from heartbeats + telemetry | HIGH — measured, signed |
| Capability probe results (latency distribution per intent type) | REACH-style probes | HIGH — externally measured |
| Declared opt-in to specialist/consolidator eligibility | Node registration field | LOW — self-reported |
| Declared capacity (max_concurrent_tasks) | Heartbeat field | LOW — self-reported |
| Observed throughput (tasks/hour from heartbeat history) | Directory computed | HIGH — measured |
| Observed task success rate (from telemetry) | Directory from TelemetryController | HIGH — measured, proxy-quorum-gated |
| Identity age (hours since first registration) | Directory from registration timestamp | HIGH — directory-controlled |
| Tier classification (Bronze/Silver/Gold/Platinum) | Derived from reputation + identity age | HIGH — derived from HIGH sources |
| Compliance history (TC violations, if any) | Directory event log | HIGH — signed events |

**Principle from R1**: measured data outweighs self-reported data. Opt-in and declared
capacity are necessary inputs (nodes must consent to specialist/consolidator roles) but
cannot be the decisive factor. The algorithm always weights observed data above declared.

---

## 3. Algorithm Proposals

Two alternative algorithms are specified here for simulation comparison. The simulation
goal (MESH2, MESH3) is to determine which produces better network quality outcomes.

### Algorithm A — Conjunctive Threshold (Conservative)

A node qualifies for a role only if it meets **all** requirements simultaneously across
**all** time windows. No single excellent time window compensates for a poor one.

**General inference** (default for all qualifying nodes):
- Reputation ≥ bronze threshold (≥ 0.00) at all time windows
- No active compliance violation in last 30d

**Specialist inference** (per intent type T):
- Reputation ≥ gold threshold (≥ 0.65) at **all** time windows (24h, 7d, 30d)
- Capability probe p95 latency for intent T ≤ 1.5× network median for T (measured)
- Task success rate for intent T ≥ 0.92 over last 7d
- Tier: Gold or Platinum
- Opt-in declared for specialist eligibility

**Consolidator**:
- Reputation ≥ platinum threshold (≥ 0.85) at **all** time windows (24h, 7d, 30d)
- Identity age ≥ 720h (conjunctive gate — same as platinum tier)
- Observed throughput capacity ≥ N×Kmax tasks/hour (where K is max consolidation set size)
- Task success rate ≥ 0.97 over last 30d
- Tier: Platinum
- Opt-in declared for consolidator eligibility
- Not from an operator already providing ≥1 consolidator in the same pool

**Properties of Algorithm A**:
- Stable: hard to game because all windows must pass simultaneously
- Conservative: transient performance dips (noise) can disqualify a node even if long-term excellent
- Resistant to gaming: no single "burst" of good behavior qualifies a node
- Disadvantage: may reduce pool size if requirements are strict; newcomers effectively excluded

### Algorithm B — Weighted Aggregate with Role-Specific Cutoffs (Flexible)

A node's role-eligibility score is a weighted sum across time windows and metrics.
Role assignment happens when the aggregate score exceeds a role-specific cutoff.

**Score formula** (for consolidator eligibility):

```
score = 0.50 × rep_30d
      + 0.30 × rep_7d
      + 0.20 × rep_24h
      + 0.10 × (success_rate_30d × 10 - 8.0)   # bonus for >0.90 success
      + 0.10 × (throughput_pct)                  # bonus for high capacity
      - 0.50 × (compliance_violations_30d > 0)   # hard penalty for violations
```

Consolidator cutoff: aggregate score ≥ 0.85.
Specialist cutoff (per intent type): aggregate score ≥ 0.72 + (capability_probe_percentile × 0.1).

**Properties of Algorithm B**:
- Flexible: transient dips don't disqualify if long-run is excellent
- Responsive: recent performance (24h) gets real signal weight
- Higher gaming risk: a node that scores 30d well can tolerate short-term underperformance
- Harder to audit: a node's score requires explanation of all 5 components

### Comparison Framework for Simulation (MESH2)

| Property | Algorithm A | Algorithm B |
|----------|-------------|-------------|
| Gaming resistance | HIGH | MEDIUM |
| Newcomer access to specialist | Slow (all windows must qualify) | Moderate (recent performance weighted) |
| Stability under network churn | HIGH — pool membership stable | MEDIUM — pool shifts with short-term scores |
| Consolidator pool size | Smaller (conjunctive requirements) | Larger (weighted relaxation) |
| Adversarial robustness | HIGH — hard gates resist manipulation | MEDIUM — weighted score can be partially gamed |
| Auditability | Simple (all criteria visible) | Complex (requires score decomposition) |

**Initial recommendation**: Algorithm A for consolidator role (security-critical — smaller
but more adversarially robust pool). Algorithm B for specialist role (less security-critical,
responsiveness to emerging capabilities more valuable). Final decision deferred to MESH2 simulation.

---

## 4. Time-Window Conjunction vs Disjunction

Algorithm A uses conjunction (all windows must qualify). Algorithm B uses weighted
combination (equivalent to soft disjunction). The key research question:

**Conjunction (AND)**: node must qualify on 24h, 7d, AND 30d windows simultaneously.
- Pro: no burst gaming; stable long-run requirement
- Con: a single bad day removes consolidator eligibility even with 30d perfect record

**Disjunction (OR)**: node qualifies if any single window meets threshold.
- Pro: captures emerging excellence; responsive to improvement
- Con: trivially gameable — sustained burst qualifies immediately

**Recommendation**: Pure disjunction is ruled out for consolidator role. Algorithm A's
conjunction is the minimum acceptable bar for consolidator. Algorithm B's weighted
average is an acceptable intermediate for specialist roles. No simulated evidence exists
yet to choose between A-conj and B-weighted for specialist — MESH2 deliverable.

---

## 5. Tie-Breaking and Operator Diversity

When the eligible pool is larger than the target pool size (e.g., 50 nodes qualify for
a consolidator pool of 10), tie-breaking determines which nodes are selected.

**Diversity-maximizing selection** (recommended over random subset):

1. Sort eligible nodes by consolidated role-eligibility score (descending).
2. Greedily add nodes to the pool, skipping any node whose operator key shard is already
   present in the pool (operator-diversity constraint).
3. Within the same operator's node set, allow at most 1 node in the pool.
4. After operator-diversity filter, fill remaining slots with next-highest-score nodes.

**Operator-diversity enforcement strength**: HARD (no exceptions). A second node from the
same operator is never admitted to the consolidator pool, regardless of score. The pool
size is reduced before this constraint is relaxed. This is the mitigation for Threat 4.3
from R2 (multi-path document): Sybil provider pool corruption.

**Pool size floor**: consolidator pool must have ≥ 5 distinct operators before
multi-path tasks are routed through consolidators. Below 5-operator diversity, the
consolidator pattern is disabled (fall back to general inference).

---

## 6. Assignment Frequency

**Options evaluated:**

| Frequency | Pros | Cons |
|-----------|------|------|
| Real-time (per task) | Always current | Directory load O(N×task_rate); latency on critical path |
| Periodic — hourly | Low directory load; stable pool | Pool may be stale for 60 min |
| Periodic — daily | Minimal load | Too stale for dynamic networks |
| Hybrid: hourly re-evaluation with real-time emergency demotion | Stable baseline + instant compliance response | Implementation complexity |

**Recommendation**: Hybrid. Role assignments are computed hourly (background job, not
on request path). Compliance violations trigger immediate role revocation (real-time
emergency path). Reputation-based demotion waits for the next hourly cycle.

**Flag for maintainer review**: real-time role re-evaluation on every discover request
would be directory-load-intensive at scale (V=10,000 nodes, 1,000 req/s = 10M eval/s).
Hourly batch is the correct default. If the directory moves to a Replica architecture
(ADR-013), each Replica can independently compute and verify role assignments from
the same inputs, removing the single-point-of-failure concern.

---

## 7. Transitions and Auditability

### 7.1 Graceful Drain at Role-Cycle Boundary

When a node's assignment changes (e.g., Specialist → General because probe score dropped),
in-flight tasks must complete before the transition takes effect.

- Role transitions are announced at the start of the next hourly cycle.
- Nodes retaining old role complete in-flight tasks with old role semantics.
- New discover requests use the new role assignment from cycle start + 1 minute grace.

Emergency revocation (compliance violation): immediate, no grace period. In-flight tasks
carry a protocol flag allowing the client to treat the response as lower-trust.

### 7.2 Signed Event Log (ADR-013 Compatibility)

Every role transition must produce a signed event entry per ADR-013's immutable event log:

```json
{
  "event_type": "role_assignment",
  "node_id": "<identity key hash>",
  "previous_role": "general",
  "new_role": "specialist",
  "intent_type": "urn:iicp:intent:llm:code:v1",
  "effective_at": "2026-05-18T15:00:00Z",
  "algorithm": "A",
  "score_snapshot": {
    "rep_30d": 0.91,
    "rep_7d": 0.94,
    "rep_24h": 0.89,
    "capability_probe_p95_ms": 187,
    "success_rate_30d": 0.967
  },
  "signed_by": "<directory_key_hash>",
  "signature": "<ADR-024 envelope signature>"
}
```

The `score_snapshot` field provides auditability: any participant can verify the
assignment from the same observable data, independent of trusting the directory's
output. This satisfies ADR-013's verifiability requirement for role assignments.

---

## 8. Acceptance Criteria Verification

| AC | Requirement | Status |
|----|-------------|--------|
| ≥2 algorithm proposals with enough detail to simulate | §3: Algorithm A (conjunctive) + B (weighted aggregate) | ✓ |
| Time-window conjunction vs disjunction compared | §4 | ✓ |
| Auditability: signed-event format | §7.2 with JSON schema | ✓ |
| Operator-diversity enforcement | §5: HARD constraint, ≥5 operators for consolidator pool | ✓ |
| Real-time vs periodic frequency trade-off | §6: hybrid recommended; real-time flagged as load concern | ✓ |
