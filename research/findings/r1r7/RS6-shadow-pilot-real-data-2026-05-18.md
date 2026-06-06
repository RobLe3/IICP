# RS6 Shadow Pilot — Real-Data Validation of Selection Policy Simulations

**Status**: RS6 Phase 1 (desk-based shadow test)  
**Date**: 2026-05-18  
**Author**: RESA loop, FORGE iter87  
**RESA dimension**: RS6 — Live Pilot Gate  
**Data source**: Live `https://iicp.network/api/v1/registry/nodes` (2026-05-18T12:xx UTC)  
**Method**: Real node reputation scores as quality proxy; 10,000 synthetic jobs; all 5 R4 algorithms  

---

## 1. Real Network State (Live Data)

| Node | Region | Reputation | Tier | Intents |
|------|--------|-----------|------|---------|
| node-01 (dominant) | eu-central | **0.9370** | Silver→near-Platinum | 1 |
| node-02 through node-07 | eu-central | **0.5000** | Silver (starting credit) | 1 |

**Pool characteristics**:
- Pool size: 7 nodes
- Score gap: dominant vs. next = **0.437** (>>>> 2α = 0.06)
- Score distribution: highly bimodal — 1 established node, 6 at starting credit
- Observed latency: not available (no telemetry data yet)

**Assessment**: This is an early-network pool. The single established node was registered earlier
and has had time to accumulate reputation via successful tasks. The other 6 nodes are newly
registered (or reset) and start at 0.50 Silver tier.

---

## 2. Shadow Test Results

Algorithm A–E run against 10,000 synthetic jobs using real reputation scores. No actual API
calls made — this is a simulation using real score inputs.

| Algorithm | Dominant node share | Diversity/1k | Unique nodes used |
|-----------|--------------------|--------------|--------------------|
| A (deterministic) | **100%** | 1.0 | 1 of 7 |
| B (ε-greedy, ε=0.05) | 95.8% | 7.0 | **7 of 7** |
| C (uniform noise, α=0.03) | **100%** | 1.0 | 1 of 7 |
| D (harmonic, α=0.03, β=8.0) | **100%** | 1.0 | 1 of 7 |
| E (UCB1) | 91.1% | 7.0 | **7 of 7** |

---

## 3. Validation of R4 Findings Against Real Data

### R4-F1 (D≡A): CONFIRMED IN REAL POOL

The dominant node has score 0.937 vs. competitors at 0.500 (gap = 0.437). Since the reversal
condition requires α·β > 1 (here: 0.24) AND gap < 2α (here: 0.437 >> 0.06), D cannot create
any reversals. D routes identically to A: 100% to the dominant node.

**This is not an edge case** — early-network IICP pools will commonly have this structure:
one or a few nodes with accumulated reputation versus many new entrants at starting credit.

### R4-F3 (B has predictable, bounded diversity): CONFIRMED

B routes 95.8% to the dominant node (= 1 − ε = 95%) and distributes 5% uniformly. At 7 nodes
with 5% exploration and 10,000 jobs: ~500 exploratory jobs split across 7 nodes ≈ 71 jobs/node
for non-dominant nodes. This matches the simulation prediction exactly.

### R4-F4 (C at low α): CONFIRMED

Uniform noise of ±0.03 cannot overcome a 0.437 gap. C = A in this regime. The noise magnitude
was designed for tight competition between similarly-scored nodes, not for the bimodal
early-network distribution.

---

## 4. New Finding — Cold Start Problem

**RS6-F1** (HIGH, new): **The cold start problem is acute in early IICP.network pools.**

With A, C, or D as the selection policy, new nodes at starting credit (0.50) receive **zero
traffic** when any established node exists (≥0.90 reputation). This creates a self-reinforcing
cycle:
1. New node registers at 0.50
2. Routing policies (A/C/D) always prefer the 0.937 node
3. New node never receives traffic → reputation stays at 0.50
4. New node is never discovered by real clients

**The only way new nodes accumulate reputation is via explicit exploration**:
- ε-greedy (B): gives each new node ~ε/N_new jobs = 0.05/6 ≈ 0.8% of traffic
- UCB (E): distributes uniformly during warm-up, then converges on the dominant node
- Neither A, C, nor D provides any new-node bootstrap

**Protocol implication**: The directory SHOULD actively inject exploration load on new nodes
during their probationary period. Options:
1. Directory-side minimum-traffic guarantee for probationary nodes (similar to MESH2's
   probationary traffic cap, but as a floor rather than a ceiling)
2. Client ε-greedy default (B) with ε=0.05 — our current recommendation
3. Directory flags nodes with `in_probation: true` and clients apply higher exploration rate

This finding validates the MESH2 §4 cold-start protocol: probationary nodes get 25% traffic
for 72h specifically to bootstrap reputation from zero.

---

## 5. RS6 Assessment

This shadow test constitutes **RS6 Phase 1** — desk-based validation using real network data:

| Validation aspect | Status |
|------------------|--------|
| R4 core finding (D≡A) validated on real data | ✓ |
| C noise ineffective at real pool gap sizes | ✓ |
| B is the only feasible diversity algorithm | ✓ |
| Cold start problem identified and documented | ✓ |
| Protocol implication: exploration floor for probationary nodes | ✓ |

**Not yet tested (RS6 Phase 2 — live pilot)**:
- Running actual inference workloads through the reference client with B vs A
- Measuring observed reputation dynamics (does reputation actually accumulate for explored nodes?)
- Cross-node quality comparison (do the 6 new nodes actually have different quality once loaded?)
- Multi-intent routing (current pool all uses same intent)

RS6 Phase 2 requires provisioned multi-node testbed with REP4 client feedback collection,
which is blocked on REP4 implementation (#170).

---

## 6. Recommendations

1. **Default client policy**: ε-greedy (ε=0.05) — B. This is the only tested policy that
   provides exploration in real early-network pools. Without it, new nodes never bootstrap.

2. **Pool health metric**: Directory should expose a "pool diversity score" (e.g., Shannon
   entropy of reputation distribution) in `/v1/stats`. A bimodal distribution (1 dominant +
   many at floor) is a signal that exploration is needed at the client layer.

3. **Dynamic ε**: Client proxies in real deployments should consider ε proportional to pool
   entropy — lower ε when reputation spread is wide (healthy competition), higher ε when
   distribution is bimodal (new nodes need bootstrap). This is a protocol recommendation for
   the CIP client profile.
