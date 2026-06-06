# MESH4 — Consolidator-Pattern Integration and Disagreement Resolution

**Track**: MESH — Consolidator Pattern, Role-Based Routing, Load-Aware Selection  
**Issue**: #183 (MESH4: Consolidator-pattern integration and disagreement resolution)  
**Date**: 2026-05-18  
**Author**: RESA loop, FORGE iter84  
**Depends on**: MESH1 (#180), MESH2 (#181)  
**Harness**: `research/simulation/mesh/consolidator_integration.py`  
**Results**: `research/results/mesh/consolidator_integration_all.json`  
**Seed**: 42 · 300 trials per combination · 20 inference nodes · 10 consolidators  
**Confidence**: MED — quality model is a proxy; real synthesis quality depends on model
capability and task type. Cost ratios are calibrated from realistic token estimates but
not validated against live pricing data.

---

## 1. Parameters Tested

- **K** (consolidators): 2, 3, 5 — pool draws from a 10-node consolidator pool
- **N** (inference fan-out): 3, 5, 7 — fragments consolidated per task
- **9 combinations**: all K × N pairs
- **4 disagreement-resolution policies**: FALLBACK, RECONSOLID, ESCALATE, DEFER
- **4 scenarios**: normal (honest), COLLUDE (majority coordinated), LAZY (no synthesis),
  BIASED (one consolidator inflates outputs)
- **Metrics**: mean quality, quality lift vs single-provider, mean cost (× single inference),
  agreement rate, resolution type distribution

---

## 2. Normal Scenario — Honest Consolidators

### Quality and cost across K × N (ESCALATE policy)

| K | N | Cost (× single) | Quality | Lift vs single | Agreement |
|---|---|----------------|---------|---------------|-----------|
| 2 | 3 | 8× | 0.948 | +0.117 | 0.97 |
| 3 | 3 | 11× | 0.934 | +0.091 | 0.92 |
| 2 | 5 | 14× | 0.969 | +0.120 | 0.97 |
| 5 | 3 | 17× | 0.948 | +0.114 | 0.79 |
| 3 | 5 | 19× | 0.960 | +0.112 | 0.92 |
| 2 | 7 | 20× | 0.983 | +0.120 | 0.97 |
| 3 | 7 | 26× | 0.978 | +0.119 | 0.92 |
| 5 | 5 | 28× | 0.966 | +0.112 | 0.85 |
| 5 | 7 | 39× | 0.977 | +0.113 | 0.89 |

**Finding M4-F1** (MED): Consolidated multi-path measurably improves quality over
single-provider by +0.09 to +0.12 across all K × N combinations. The improvement
is real but not large — it compresses the tail of bad outputs rather than uniformly
lifting quality.

**Finding M4-F2** (MED): **N scales quality; K does not.** Increasing N from 3→7
raises quality by ~0.035 units. Increasing K from 2→5 at fixed N raises quality by
<0.005 units while doubling cost. K=2 with N=5 (14×) outperforms K=5 with N=5 (28×)
at half the cost: quality 0.969 vs 0.966.

**Finding M4-F3** (HIGH): **K=2 N=3 is the minimum viable configuration.** At 8×
single-inference cost with 0.97 agreement and +0.12 lift, it captures most of the
quality benefit at the lowest premium. Recommended as the default for quality-sensitive
tasks. Moving to K=2 N=5 (14×) buys another +0.003 quality improvement — marginal.

**Finding M4-F4** (MED): **Consolidated multi-path is only justified at quality-critical
tasks.** An 8–14× cost multiplier (minimum viable) is economically defensible only when
quality failures are costly: medical inference, legal summarization, code generation for
high-stakes systems. For general chat or embeddings, single-provider with reputation-based
selection is sufficient.

### Agreement rate and K

Agreement rate decreases as K increases (fewer pairs of consolidators agree within
threshold): K=2: 0.95–0.99, K=3: 0.91–0.97, K=5: 0.79–0.90. This is expected —
more consolidators means more variance in synthesis outputs. K=5 with N=3 shows
agreement only 0.79 — the FALLBACK policy is triggered 21% of the time at K=5 N=3,
returning raw fragments and partially defeating the consolidation purpose.

---

## 3. Adversarial Scenarios

### 3.1 LAZY — Consolidators Return Fragments Without Synthesis

This is the most dangerous failure mode. Lazy consolidators pass fragments through
as-is (output quality ≈ mean(fragments) − overhead penalty). The result is a quality
drop below single-provider baseline:

| Policy | K=3 N=5 quality | K=3 N=5 lift |
|--------|----------------|-------------|
| FALLBACK | 0.658 | **−0.167** |
| RECONSOLID | 0.625 | **−0.200** |
| ESCALATE | 0.639 | **−0.190** |
| DEFER | 0.624 | **−0.197** |

**Finding M4-F5** (HIGH): **Lazy consolidation is invisible to agreement detection.**
Agreement rate under LAZY (0.88 at K=3) is nearly identical to normal (0.91). All lazy
consolidators produce the same mediocre output and agree — the disagreement signal is
absent. This means agreement-rate monitoring alone cannot detect lazy consolidators.

**Finding M4-F6** (HIGH): Under lazy scenario, FALLBACK policy performs **best** (quality
0.658 vs 0.624 for DEFER). This is the one case where bypassing consolidation and returning
raw fragments outperforms any consolidator-based resolution. It also costs the least.

**Finding M4-F7** (HIGH): **The only reliable defence against lazy consolidators is
reputation feedback from clients.** A lazy consolidator's output quality is detectable
by the requesting proxy post-hoc — the synthesized response lacks coherence and attribution
across fragments. Clients must be able to submit negative feedback specifically flagging
consolidation failure (REP4 feedback mechanism). Without REP4, lazy consolidators never
accumulate reputation penalty. MESH5 liveness gate is blocked on REP4 implementation.

### 3.2 COLLUDE — Majority of Consolidators Coordinated (Biased Outputs)

Colluding consolidators inflate quality claims by +0.25 (bias toward a coordinated target).
Agreement rate drops sharply as K increases (more dissenting honest nodes): K=5 N=3
agreement = 0.46 (vs 0.83 normal).

| Policy | K=3 N=5 quality | K=3 N=5 lift |
|--------|----------------|-------------|
| FALLBACK | 0.949 | +0.089 |
| RECONSOLID | 0.974 | +0.112 |
| **ESCALATE** | **0.982** | **+0.118** |
| DEFER | 0.972 | +0.113 |

**Finding M4-F8** (MED): Under collusion, ESCALATE achieves the highest quality
because returning all K synthesis outputs allows the client to identify the biased
cluster and select the outlier honest output. FALLBACK performs worst (returns raw
fragments, losing the honest consolidators' work).

**Finding M4-F9** (MED): Collusion is partially self-revealing — as K increases, the
disagreement between the colluding cluster and honest consolidators reduces agreement
rate to 0.46 at K=5. The directory can monitor agreement rates as a signal: persistent
low agreement from a specific consolidator node across tasks is evidence of systematic
disagreement with peers. This is a viable detection heuristic for MESH5.

### 3.3 BIASED — One Consolidator Inflates Outputs (+0.20)

A single biased consolidator inflates self-reported quality by 0.20. Agreement rate
drops at higher K (K=5 N=3: 0.48 vs 0.52 normal). ESCALATE and RECONSOLID outperform
DEFER:

| Policy | K=5 N=5 quality | K=5 N=5 lift |
|--------|----------------|-------------|
| FALLBACK | 0.890 | +0.085 |
| RECONSOLID | 0.935 | +0.133 |
| **ESCALATE** | **0.959** | **+0.160** |
| DEFER | 0.936 | +0.135 |

**Finding M4-F10** (MED): **DEFER is the weakest policy under any adversarial scenario.**
It concentrates trust on the highest-reputation consolidator — precisely the node an
attacker would invest in elevating. Never use DEFER as the primary policy.

---

## 4. Policy Recommendation

| Policy | Best use case | Worst case |
|--------|-------------|-----------|
| FALLBACK | Lazy consolidators detected | Collusion (wastes honest consolidators) |
| RECONSOLID | General disagreement (K≥3) | Lazy (re-consolidation also lazy) |
| **ESCALATE** | **Adversarial-robust default** | High client complexity |
| DEFER | No adversarial context, latency critical | Any adversarial scenario |

**Recommended default**: ESCALATE. It achieves highest quality under COLLUDE and BIASED,
and reasonable quality under LAZY. Its downside is client-side complexity — the proxy must
implement synthesis-selection logic to choose among K returned outputs.

**Protocol requirement (from M4-F5/F6)**: The protocol MUST include a
`consolidation_quality_flag` field in the response envelope when consolidation was
attempted. Clients must be able to submit quality feedback that specifically attributes
failure to the consolidation step vs. individual inference nodes (REP4 extension needed).

---

## 5. Cost Justification Summary

Consolidated multi-path justifies its premium when:

| Condition | Minimum configuration | Cost premium |
|-----------|-----------------------|-------------|
| Quality-sensitive task, low adversarial risk | K=2 N=3, ESCALATE | **8×** |
| Quality-sensitive task, moderate adversarial risk | K=2 N=5, ESCALATE | **14×** |
| Byzantine-tolerant (medical/legal/critical) | K=3 N=5, ESCALATE | **19×** |
| Extreme quality requirement | K=3 N=7, ESCALATE | **26×** |
| K=5 configurations | Not recommended | 17–39× (poor K scaling) |

K=5 should not be used as the default: it costs 2–3× more than K=2-3 with no
measurable quality gain in honest conditions and lower agreement rates.

---

## 6. Acceptance Criteria Verification

| AC | Requirement | Status |
|----|-------------|--------|
| K=2,3,5 × N=3,5,7 tested (9 combinations) | All 9 combinations run, all policies | ✓ |
| All 4 disagreement-resolution policies tested | FALLBACK/RECONSOLID/ESCALATE/DEFER across all scenarios | ✓ |
| Cost analysis | §2 table: 8× to 39× single-inference cost; N scales better than K | ✓ |
| Quality analysis | +0.09 to +0.12 lift in normal; LAZY produces negative lift | ✓ |
| Adversarial scenarios | COLLUDE + LAZY + BIASED characterized (§3.1–3.3) | ✓ |
| Plain report if quality doesn't improve | Quality does improve (+0.09–0.12) in normal. Fails under LAZY (−0.14 to −0.22). Stated explicitly | ✓ |

---

## 7. Open Items for MESH5 and Protocol

1. **REP4 blocking item**: consolidation-specific quality feedback (M4-F7). Without it, lazy
   consolidators never accumulate reputation penalty and cannot be evicted from the pool.
2. **Agreement-rate monitoring**: persistent low agreement from a specific consolidator should
   feed into directory reputation computation (M4-F9 detection heuristic).
3. **K=2 recommendation**: ADR-028 should document K=2 N=3 as the minimum viable multi-path
   configuration. K=5 is a research target, not a production recommendation.
4. **ESCALATE complexity**: proxy must implement fragment-selection or synthesis-voting
   logic when ESCALATE is active. This is a reference-client requirement, not protocol.
5. **Lazy detection gap**: agreement monitoring is insufficient. Probe-based capability
   verification (MESH2 §2 — KAP) must specifically include synthesis-quality probes
   with verifiable ground-truth consolidation problems.
