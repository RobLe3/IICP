# MESH2 — Consolidator Pool Dynamics and Capability Probes

**Track**: MESH — Consolidator Pattern, Role-Based Routing, Load-Aware Selection  
**Issue**: #181 (MESH2: Consolidator pool dynamics and capability probes)  
**Date**: 2026-05-18  
**Author**: RESA loop, FORGE iter83  
**Depends on**: MESH1 (#180) — role-assignment algorithm; Algorithm A (conjunctive) and
operator-diversity HARD constraint are inputs to this document.  
**Length**: ≈2000 words  
**ADR impact**: Expands ADR-028 §Open Questions (MESH2 item). Interaction with ADR-013
(signed event log for probe results) and ADR-026 (reputation as earned signal).

---

## 1. Scope and Framing

Consolidators are elevated-trust nodes performing synthesis work across multi-path
inference fragments. The pool's integrity depends on continuously verifying that each
member can actually do the work — not just that it passed an initial reputation gate.

Unlike general inference nodes (verified by client feedback on each task), consolidators
may be underutilized between multi-path jobs. A consolidator that passes initial
admission via MESH1 Algorithm A but quietly degrades (model update, hardware change,
operator misconfiguration) will not generate client feedback to trigger reputation decay
until it fails a real synthesis task — which is a costly failure mode.

Capability probes solve this: the directory (or a probe coordinator) tests consolidator
nodes on known-workload problems independently of live task routing.

---

## 2. Probe Design: Two Approaches

### Approach 1 — Known-Answer Probe (KAP)

The directory sends a synthesis task with a ground-truth verifiable answer:
- Input: N inference fragments from prior network runs (stored canonical examples)
- Expected output: a reference synthesis known in advance (human-curated or
  ensemble-agreed from N past consolidations)
- Grading: semantic similarity score ≥ threshold OR exact-match on structured outputs
  (JSON merges, code consolidation with test suite)

**Reliability characteristics**:
- Grade is deterministic — independent of which other consolidators are available today
- Requires a maintained library of canonical probe problems (directory burden)
- Vulnerable to memorization if problem set is static and large enough to leak
- Ground truth degrades if the domain evolves (code best practices, factual updates)

**Recommended probe library**: minimum 500 canonical problems, rotated quarterly.
Problem categories: code synthesis (verifiable via test run), structured data merge
(diff-verifiable), argument reconciliation (embedding similarity ≥ 0.92 against reference).

### Approach 2 — Cross-Consolidator Agreement Probe (CCAP)

The directory sends the same synthesis task to K ≥ 3 consolidators simultaneously
on a known-good canonical input. Agreement rate is the quality signal:
- If K−1 of K consolidators agree to within a semantic threshold, the outlier is flagged.
- If fewer than 2/K agree, the probe inputs or the probe task are flagged (not individual
  nodes) — the canonical input itself may be ambiguous.

**Reliability characteristics**:
- Does not require pre-computed ground truth; agreement is the standard
- Requires ≥3 consolidators to be active simultaneously (minimum pool prerequisite)
- Vulnerable to correlated failures: if all consolidators share the same base model,
  they may all fail the same way without triggering a flag
- Model-family diversity in the pool is required for CCAP to detect silent failures

### Comparison

| Property | KAP | CCAP |
|----------|-----|------|
| Ground truth source | Curated library (directory burden) | Peer agreement (network burden) |
| Detects isolated failure | Yes | Yes |
| Detects correlated failure (same model family) | Yes — ground truth independent | No — all agree on the wrong answer |
| Probe cost | 1 consolidator per probe | K consolidators per probe |
| Vulnerability | Library staleness, memorization | Model-family homogeneity |
| Minimum pool requirement | 1 | 3 |

**Recommendation**: KAP as the primary probe mechanism, with CCAP as a secondary
cross-check when pool size ≥ 5. CCAP results are used to detect correlated silent
failure across model families, not to replace KAP grades. If KAP and CCAP diverge
on the same node (KAP pass, CCAP fail), escalate to human review — this indicates
the canonical example may have drifted.

**Model-family diversity constraint** (added from CCAP analysis): the consolidator pool
SHOULD include at least two distinct model families. If all current consolidators share
one model family, the pool composition is flagged in the directory event log with a
`diversity_warning: model_family_homogeneity` entry.

---

## 3. Probe Frequency: Cost/Quality Trade-off

| Frequency | Cost per node/day | Staleness window | Risk |
|-----------|------------------|-----------------|------|
| Continuous (1 probe/hr) | 24 probes/node/day | 1 hour | High directory load |
| Hourly with sampling (1 probe/4hr) | 6 probes/node/day | 4 hours | Moderate |
| Daily | 1 probe/node/day | 24 hours | Low — misses intraday degradation |
| Event-triggered | 0 unless triggered | Variable | Only works if trigger signal exists |

**Recommendation**: Tiered probe frequency based on pool size and pool age.

- **Pool size ≤ 10 nodes**: 1 KAP per consolidator every 4 hours (6/day). Justification:
  small pools have high per-node impact; one silent failure affects a meaningful fraction.
- **Pool size 11–50 nodes**: 1 KAP per consolidator every 8 hours (3/day). Standard cadence.
- **Pool size > 50 nodes**: 1 KAP per consolidator every 24 hours + CCAP group sweep daily.
  Large pools tolerate some individual variability; CCAP catches correlated failure.
- **Post-failure re-probe**: any node that receives a probe-failure signal is re-probed
  within 30 minutes to distinguish transient vs. persistent failure (see §4).
- **New entrant**: fresh consolidator (within first 24h of assignment) receives 1 probe
  every 2 hours for the first 24h, then falls to standard frequency. This is the cold-start
  acceleration window — failure rate here is higher and the cost of discovery late is worse.

---

## 4. Probe-Failure Handling

### Single Failure (Transient Classification)

A single probe failure triggers re-probe within 30 minutes. Outcomes:
- **Re-probe passes**: transient flag recorded in event log; no role action. Accumulate
  transient flags: 3 transients in 7 days triggers a degradation alert (see multi-failure path).
- **Re-probe also fails**: advances to multi-failure path immediately.

### Multi-Failure Path (Degradation Classification)

Two consecutive probe failures (original + re-probe fail) or 3 transients in 7 days
trigger the degradation demotion protocol.

**Demotion options** (mutually exclusive based on severity):

| Condition | Action |
|-----------|--------|
| 2 consecutive failures, success rate ≥ 0.85 (last 30d) | Consolidator → Probationary (traffic weight halved, probes every 2h) |
| 2 consecutive failures, success rate < 0.85 (last 30d) | Consolidator → General inference (effective next hourly cycle) |
| 4 consecutive failures or KAP score < 0.50 | Consolidator → Suspended (removed from all routing pools, re-entry requires full re-qualification) |
| Compliance violation (ADR-024 signature failure, TC-7 trigger) | Immediate revocation regardless of probe history |

**Thresholds summary**:
- Transient threshold: 3 in 7 days → degradation alert (triggers extra probing)
- Consecutive failure threshold: 2 → demotion (probationary or general depending on success rate)
- Hard removal threshold: 4 consecutive or KAP score < 0.50 → suspension

**Suspended re-entry path**: A suspended node must:
1. Clear the compliance flag (if applicable)
2. Operate as a general inference node for ≥ 168h (7 days) with success rate ≥ 0.97
3. Pass MESH1 Algorithm A fresh qualification
4. Pass 3 consecutive KAP probes at ≥ 0.85 score

Re-entry is blocked for 30 days after compliance-triggered suspension (stricter than
reputation-triggered suspension).

---

## 5. Diversity Maintenance

The pool diversity score D is computed as a weighted aggregate across three dimensions:

```
D = 0.40 × operator_diversity + 0.35 × region_diversity + 0.25 × model_family_diversity
```

Where each component is the normalized Shannon entropy of the pool distribution:

```
operator_diversity = H({frac_op1, frac_op2, ...}) / H_max(N_pool)
region_diversity   = H({frac_eu, frac_us, frac_apac, ...}) / H_max(N_regions)
model_diversity    = H({frac_llama, frac_mistral, frac_phi, ...}) / H_max(N_families)
```

H = -Σ p_i log(p_i); H_max = log(N) for uniform distribution over N buckets.

**Diversity floor**: D must remain ≥ 0.60 while the pool has ≥ 5 members.

**Diversity maintenance actions triggered automatically**:

| Condition | Action |
|-----------|--------|
| D drops below 0.60 | New consolidator admissions temporarily restricted to nodes that increase D |
| Single operator reaches > 30% of pool | That operator's additional eligible nodes bypassed in MESH1 greedy selection |
| Single region reaches > 50% of pool | `diversity_warning: region_concentration` logged; new regional entrants preferred |
| All members share one model family | `diversity_warning: model_family_homogeneity`; CCAP probes escalated to daily |

**Node departure impact**: when a node leaves (voluntary, demotion, suspension), the
directory recomputes D immediately. If D drops below 0.60 and pool size is ≥ 5,
the admission queue is re-ordered to prioritize diversity-restoring candidates.

---

## 6. Cold-Start: Entry into Consolidator Status

MESH1 Algorithm A defines initial qualification (reputation, probe p95 latency,
success rate, opt-in, identity age, operator diversity). This section defines the
transition mechanics from "qualified" to "active consolidator in full traffic share."

**Probationary period** (mandatory for all new consolidators):

| Phase | Duration | Traffic share | Probe frequency |
|-------|----------|--------------|----------------|
| Probationary | 72h (3 days) | 25% of standard consolidator allocation | Every 2h (12/day) |
| Ramp-up | 72h after probationary | 60% | Every 4h (6/day) |
| Full | Indefinite | 100% | Standard cadence (§3) |

**Probationary pass condition**: KAP score ≥ 0.85 on ≥ 4 of 5 consecutive probes during
the probationary window. If this is not met at the end of 72h, the probationary window
extends for another 72h. Two consecutive failed probationary windows → disqualification;
the node must wait 14 days before re-entering the qualification queue.

**Traffic allocation logic**: During probationary, the node appears in directory
responses with a reduced `allocation_weight` field. Clients use this field in
load-aware selection. The allocation weight rises linearly during ramp-up.

**No full-traffic-from-day-one**: starting a new consolidator at full traffic share
and discovering a failure mode is more expensive than a controlled ramp. The probationary
period is the explicit cost the protocol pays for that safety.

---

## 7. Turnover: Pool Stability Under Churn

The minimum viable pool size is 5 distinct operators (from MESH1). The protocol must
ensure that voluntary exits, compliance demotions, and quality drops do not cause the
pool to fall below this floor.

**Pool stability invariants**:
1. `pool_size_active ≥ 5` before any multi-path task is routed through consolidators.
   If pool falls below 5, consolidator routing is disabled; tasks fall back to general
   inference routing without consolidation.
2. The qualified candidate queue is maintained continuously. When a consolidator exits,
   the next qualified candidate in the queue begins probationary entry automatically
   (no manual trigger required).

**Candidate queue maintenance**:
- The directory maintains a sorted list of nodes that pass MESH1 Algorithm A but are
  not yet admitted (because the pool is at target size or diversity constraints prevent admission).
- Queue is sorted by: (1) operator-diversity contribution, (2) role-eligibility score (MESH1).
- Queue depth target: 2× current pool size. If queue depth drops below pool size,
  a `consolidator_queue_shallow` alert is logged — this is a leading indicator of
  future pool instability.

**Voluntary exit**: a consolidator announces intent to exit via heartbeat field
`consolidator_exit_intent: true`. The directory starts admitting the next candidate
immediately (probationary phase begins). The exiting node remains active at full
traffic share until the incoming candidate completes probationary phase, then exits
cleanly. Grace window: up to 72h.

**Compliance demotion or suspension**: immediate removal (no grace period). If pool
falls below 5, the queue is consumed as fast as candidates can enter probationary
phase — up to 2 candidates can be in parallel probationary at once if pool is critically
low (pool_size < 5) and queue is non-empty.

---

## 8. Acceptance Criteria Verification

| AC | Requirement | Status |
|----|-------------|--------|
| Two probe approaches compared for reliability | §2: KAP vs CCAP with 5-property comparison table | ✓ |
| Probe-failure thresholds specified | §4: transient threshold (3/7d), consecutive threshold (2→demotion), hard removal (4 consecutive or KAP<0.50) | ✓ |
| Diversity score defined with operator/region/model dimensions | §5: D = 0.40×operator + 0.35×region + 0.25×model, Shannon entropy formula, floor ≥ 0.60 | ✓ |
| Cold-start path specified | §6: 3-phase ramp (probationary 72h/25% → ramp-up 72h/60% → full), KAP pass condition | ✓ |
| Turnover scenario: pool stays above minimum size requirement | §7: stability invariants, candidate queue maintenance, parallel probationary when critically low | ✓ |

---

## 9. Open Items for MESH3

- §3 probe frequencies are design estimates; MESH3 simulation should validate whether
  4-hour probe intervals produce acceptable staleness vs. directory load at V=10,000 nodes.
- §5 diversity weights (0.40/0.35/0.25) are not validated; MESH3 should test sensitivity
  of D to different weight allocations.
- §6 probationary duration (72h) is heuristic; MESH3 should test whether a shorter
  window (24h) provides equivalent safety at lower admission latency.
- CCAP requires pool size ≥ 3 for meaningful signal; performance below that threshold
  is entirely KAP-dependent. MESH simulation should include small-pool scenarios
  (pool size 3–5) as an explicit test condition.
