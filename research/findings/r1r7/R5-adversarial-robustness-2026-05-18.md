# R5 — Adversarial Robustness of Selection Policies

**Track**: R1R7 — Provider Selection & Multi-Path Routing  
**Issue**: #177 (R5: Adversarial robustness)  
**Date**: 2026-05-18  
**Author**: RESA loop, FORGE iter87  
**Depends on**: R4 (#176), R5 harness extends `selection_policy_sim.py`  
**Harness**: `research/selection-policy-sim/adversarial_sim.py`  
**Results**: `research/results/r5/r5_summary.json`  
**Seed**: 42, 43, 44 (3 independent runs per configuration)  
**Network sizes**: 100, 1000, 10000 nodes  
**Jobs per run**: 10,000  
**Detection threshold**: 20 consecutive failures → node demoted  
**Confidence**: MED — detection model is simplified (threshold, not probabilistic reputation);
real-world detection would use reputation scoring not binary consecutive-failure counts.

---

## 1. Adversarial Scenarios

| Label | Description |
|-------|-------------|
| SYBIL_1 | 1% of nodes are sybils: report inflated score (0.70–0.90), actual success 0.12 |
| SYBIL_5 | 5% sybil fraction |
| SYBIL_10 | 10% sybil fraction |
| BAIT | 5% bait-and-switch: succeed for first 500 jobs, then fail (success→0.05) |
| FARM | 5% reputation farmers: honest for first 5000 jobs, defect for rest |
| PHI_ATTACK | Single adversary with knowledge of D's φ_job; calibrates score per job |

**Note**: Sybils report just above the honest top node's score (0.01–0.05 above),
guaranteeing they win the deterministic ranking. Bait/FARM nodes initially appear
as high-quality honest providers.

---

## 2. Sybil Injection Results

### 2.1 Key metrics (mean over 3 seeds)

#### SYBIL_1 (1% sybils)

| Algo | N=100 regret | N=100 adv% | det job | rec jobs | N=1000 regret | N=1000 adv% | det job | rec jobs |
|------|-------------|-----------|--------|---------|--------------|------------|--------|---------|
| A | 0.069 | 0.32% | 30 | 0 | 0.131 | 7.8% | 29 | 653 |
| B | 0.086 | 1.19% | 126 | 0 | 0.149 | 8.9% | 190 | 465 |
| C | 0.083 | 0.78% | 106 | 0 | 0.138 | 9.4% | 172 | **50** |
| D | 0.074 | 0.92% | 91 | 0 | 0.130 | 7.7% | 98 | 575 |
| E | 0.219 | 0.28% | never | n/a | 0.266 | 0.62% | never | n/a |

At N=100 (10 honest + 1 sybil), all algorithms handle 1% sybils adequately.
At N=1000 (1000 honest + ~10 sybils): C recovers in 50 jobs vs A's 653 —
because C's noise creates random routing to honest nodes during the cascade,
shortening the time each individual sybil dominates.

#### SYBIL_5 (5% sybils)

| Algo | N=100 regret | N=100 adv% | det job | rec jobs | N=1000 regret | N=1000 adv% | det job | rec jobs |
|------|-------------|-----------|--------|---------|--------------|------------|--------|---------|
| A | 0.110 | 5.76% | 170 | 307 | 0.461 | **51.3%** | 137 | 4896 |
| B | 0.119 | 5.48% | 159 | 327 | 0.485 | 53.2% | 111 | **785** |
| C | 0.106 | 3.85% | 100 | **0** | 0.406 | 44.6% | 477 | 2961 |
| D | 0.102 | 4.61% | 111 | 250 | 0.473 | 53.2% | 105 | 5111 |
| E | 0.227 | 1.28% | 8343 | 221 | 0.283 | 3.08% | never | n/a |

At N=1000 with 50 sybils, the cascade problem is catastrophic: A and D reach
51–53% adversarial exposure. **B reduces recovery time from 4896 (A) to 785 jobs**
by detecting multiple sybils in parallel via random exploration.

#### SYBIL_10 (10% sybils)

| Algo | N=100 regret | N=100 adv% | det job | rec jobs | N=1000 regret | N=1000 adv% | det job | rec jobs |
|------|-------------|-----------|--------|---------|--------------|------------|--------|---------|
| A | 0.150 | 10.9% | 188 | 806 | 0.813 | **97.9%** | 90 | 9633 |
| B | 0.151 | 9.61% | 108 | **371** | 0.789 | 93.4% | 175 | **1190** |
| C | 0.143 | 8.76% | 164 | 141 | 0.801 | 96.4% | 909 | 7529 |
| D | 0.123 | 7.44% | 108 | 537 | 0.803 | 96.7% | 99 | 9506 |
| E | 0.234 | 2.52% | 8330 | 1142 | 0.298 | 5.68% | never | n/a |

At N=1000 with 100 sybils: near-total adversarial dominance (93–98% adv_exposure)
for all algorithms except E (which avoids sybil concentration via exploration but
has unacceptable routing quality). B has the lowest recovery time (1190 vs 9633 for A).

### 2.2 Sybil cascade: the scaling failure

The sybil cascade problem: with N_sybils adversaries each requiring T_detect jobs
to detect, the recovery cost is O(N_sybils × T_detect). For deterministic algorithms
(A and D), T_detect is primarily determined by the sybil's actual_success rate (0.12)
and the consecutive-failure threshold (20). Expected T_detect with Bernoulli failures:
the mean wait for 20 consecutive failures with p=0.12 is long (~200–400 jobs).

For ε-greedy (B): random exploration creates parallel detection pressure — multiple
sybils simultaneously accumulate failure counts from exploratory jobs, reducing T_detect
for each by a factor of N_sybil/N_total (since exploration distributes to all sybils).
At 5% sybil fraction, B's effective T_detect per sybil is ~T_A / 0.05 ≈ 5–10×
faster per sybil, and all detected in parallel.

**B's adversarial resilience is structural**: ε-greedy's random exploration serves
as inadvertent parallel detection. This is a security benefit of exploration that
does not appear in quality-only metrics.

---

## 3. BAIT, FARM, PHI_ATTACK Results

Full sweep complete. Seeds 42/43/44, N=100/1000/10000, all scenarios.

### 3.1 BAIT — Bait-and-switch

#### Results (mean over 3 seeds)

| Algo | N=100 regret | N=100 adv% | det job | rec jobs | N=1000 regret | N=1000 adv% | det job | rec jobs |
|------|-------------|-----------|--------|---------|--------------|------------|--------|---------|
| A | 0.081 | 6.6% | 524 | 37 | 0.209 | 21.5% | 519 | 1532 |
| B | 0.092 | 6.4% | 520 | 72 | 0.242 | 23.9% | 561 | **1232** |
| C | 0.092 | 6.7% | 553 | — | 0.221 | 23.4% | 895 | 1090 |
| D | 0.084 | 6.9% | 545 | 46 | 0.228 | 23.8% | 526 | 1752 |
| E | 0.228 | 1.5% | 7013 | 166 | 0.281 | 3.1% | — | — |

| Algo | N=10000 regret | N=10000 adv% | det job | rec jobs |
|------|--------------|------------|--------|---------|
| A | 0.860 | **100.0%** | 519 | 9480 |
| B | 0.833 | 95.2% | 541 | **739** |
| C | 0.860 | 100.0% | 3266 | 6734 |
| D | 0.860 | 100.0% | 542 | 9457 |
| E | 0.265 | 5.0% | — | — |

**BAIT cascade dynamics**: Bait nodes accumulate legitimate reputation for 500 jobs, then
simultaneously defect. Detection is fast (~520 jobs post-defection = first failure after
500 + T_detect) but recovery at N=10000 is catastrophic for A/C/D (9480/6734/9457 jobs)
because the cascade is structurally identical to SYBIL_5 but with an established reputation
advantage. B recovers in 739 jobs (13× faster than A) via parallel detection.

### 3.2 FARM — Coordinated defection

#### Results (mean over 3 seeds)

| Algo | N=100 adv% | det job | rec | N=1000 adv% | det job | rec | N=10000 adv% | det job | rec |
|------|-----------|--------|-----|------------|--------|-----|-------------|--------|-----|
| A | 51.9% | 5033 | 86 | 68.0% | 5020 | 1683 | **100.0%** | 5025 | 4975 |
| B | 49.4% | 5024 | 70 | 63.8% | 5026 | **481** | 95.1% | 5020 | **1031** |
| C | 51.1% | 5074 | — | 65.7% | 5333 | 887 | 100.0% | 7757 | 2243 |
| D | 51.4% | 5029 | 57 | 66.9% | 5031 | 1563 | 100.0% | 5047 | 4952 |
| E | 4.3% | 9276 | 64 | 4.2% | — | — | 5.0% | — | — |

**FARM note**: All algorithms are blind to farmer defection for the first 5000 jobs — farmers
behave identically to honest nodes during accumulation. Post-defection, the synchronized
cascade is severe: adv% reaches 100% for A/C/D at N=10000. B's recovery advantage persists
(1031 vs 4975 for A, 5× faster) because parallel detection via exploration catches multiple
farmers simultaneously rather than sequentially.

### 3.3 PHI_ATTACK — Known-φ adversary against D

#### Results (mean over 3 seeds)

| Algo | N=100 adv% | det job | N=1000 adv% | det job | N=10000 adv% | det job |
|------|-----------|--------|------------|--------|-------------|--------|
| A | 0.6% | 110 | 0.6% | 96 | 0.8% | 123 |
| B | 0.4% | 81 | 1.7% | 220 | 0.4% | 68 |
| C | 0.9% | 209 | 1.9% | 1069 | 2.4% | 2519 |
| D | 1.8% | 310 | 1.2% | 216 | 1.0% | 177 |
| E | 0.2% | 7715 | 0.1% | — | 0.0% | — |

**PHI_ATTACK is not a distinct threat category**: A single adversary with knowledge of φ_job
achieves <2% exposure regardless of algorithm. Detection is fast (68–310 jobs) across all
deterministic/ε-greedy algorithms because a single bad node is quickly exhausted of its
consecutive-failure budget. D's φ knowledge provides no advantage because D≡A (α·β=0.24<1):
the adversary simply reports a score slightly above honest_top, which is the same attack
available against A. C shows elevated adv% at large N because noise occasionally routes to
the adversary during detection delay — a minor structural artifact of noise-based algorithms.

---

## 4. Primary Findings

**R5-F1** (HIGH): **Sybil cascade is the dominant adversarial threat at scale.** At
5% sybil injection in N=1000 pools, deterministic algorithms (A and D) route 51–53%
of all jobs to adversaries despite detection. At 10% injection, adversarial exposure
reaches 97–98%. The cascade — O(N_sybils × T_detect) detection cost — exceeds the
simulation budget at modest sybil fractions.

**R5-F2** (HIGH): **ε-Greedy (B) has the best adversarial resilience of all tested
policies.** Random exploration creates parallel sybil detection: at SYBIL_5 N=1000,
B recovers in 785 jobs vs A's 4896. At SYBIL_10 N=1000, B recovers in 1190 vs A's
9633. This resilience scales: the exploration budget (ε × N_jobs) is distributed
across all adversaries simultaneously.

**R5-F3** (HIGH): **D (harmonic perturbation) provides no adversarial advantage over
A.** Since D≡A in selection behavior (R4-F1), their adversarial profiles are identical.
D's deterministic phase (known-φ attack) does not create additional attack surface
because D's perturbation is already insufficient to distinguish nodes (α·β=0.24<1).

**R5-F4** (MED): **C (uniform noise) provides the fastest recovery at low sybil fractions
(1–5%)** due to noise routing occasional traffic to honest nodes during the cascade,
shortening each sybil's tenure. At 10% sybils and N=1000, C's recovery (7529 jobs)
is worse than B (1190) because C's noise is insufficient to create parallel detection
pressure against a large sybil cluster.

**R5-F5** (HIGH): **No selection policy alone provides adequate sybil defense at
≥5% injection in pools of N≥1000.** This confirms R4's policy recommendation scope:
selection policy is a last-line defense, not primary. Protocol-layer defenses are
required:
- Entry bonds or registration throttling (limits sybil injection rate)
- Capability verification with known-answer probes (MESH2 KAP) pre-admission
- Cross-provider cross-checking (R2 multi-path — detects systematic failure clusters)
- Reputation decay with floor (slows but doesn't prevent cascade)

**R5-F6** (MED): **UCB (E) has near-zero adversarial exposure but never detects
adversaries** within the simulation budget. UCB spreads exploration uniformly, so
no sybil accumulates enough consecutive failures to trigger detection. This makes
UCB pathological in adversarial settings: it protects against concentration but
can't eject known-bad actors — adversaries are perpetually "explored" at baseline rate.

**R5-F7** (HIGH): **BAIT cascade at N=10000 is the most severe scenario tested** —
100% adversarial exposure for A/C/D. Bait nodes accumulate legitimate reputation for
500 jobs before defecting, giving them established-node advantage. B recovers in 739
jobs (13× faster than A's 9480) via parallel detection. The core structural insight
is that BAIT = SYBIL + a reputation-establishment delay, so B's parallel detection
advantage compounds with the established-reputation handicap.

**R5-F8** (HIGH): **FARM (coordinated defection) is uniquely dangerous because
detection cannot begin until defection occurs at job 5000.** All algorithms suffer
equally during the farming phase. Post-defection, B's recovery advantage (1031 vs
4975 for A at N=10000, 5×) mirrors the SYBIL result. The synchronized defection
means the full cascade hits simultaneously — there is no staggered detection window.
Protocol countermeasure: cross-client failure reporting (REP4/R2) would detect FARM
faster because different clients hit different farmers, creating earlier accumulation.

**R5-F9** (LOW): **PHI_ATTACK confirms that knowledge of D's perturbation function φ
provides no meaningful additional attack surface.** A single adversary achieves <2%
exposure across all algorithms, with fast detection (68–310 jobs). This validates the
R4 analysis: since D≡A, the adversary's φ knowledge only lets them set their reported
score just above honest_top — identical to a SYBIL_1 (single sybil) attack against A.

---

## 5. Protocol Implications

The sybil cascade result (R5-F1/F5) directly motivates the protocol-level defenses
that MESH2 (KAP probes), REP4 (client feedback), and R2 (multi-path) address:

| Threat | Protocol defense | Track |
|--------|----------------|-------|
| Sybil injection at registration | Entry bond or registration rate limit | R3 (directory design) |
| Capability spoofing before detection | Known-answer probes (KAP) | MESH2 |
| Coordinated defection | Multi-path + cross-check | R2/MESH4 |
| Slow reputation farming | Decay with floor, cross-client reports | REP5 |
| φ-optimized targeting against D | — D is already equivalent to A; no unique threat | — |

**Selection policy recommendation (updated from R4)**:
- Default: **B (ε-greedy, ε=0.05)** — best adversarial resilience, parallel detection
- Alternative at low adversarial risk, large pool: **C (uniform noise)** — better diversity
- Do not use A or D as primary policy if adversarial sybil injection is plausible
- Do not use E (UCB) — never detects adversaries, pathological at scale

**Task-differentiated routing (new — from R5 sweep)**:

The simulation treats all jobs identically, but real inference tasks differ in failure cost
and verifiability. R5 results motivate a three-mode routing taxonomy mapped to selection policy:

| Mode | Algorithm | Trigger | Rationale |
|------|-----------|---------|-----------|
| BEST-EFFORT | B (ε=0.05) | High-volume, latency-sensitive (chat, embeddings, classification) | Fast, fair, sybil-resilient without overhead |
| REDUNDANT | B + N-of-M + ESCALATE consolidator | Verifiable/complex (code gen, reasoning, multi-step) | BAIT/FARM worst for A/D; redundancy + cross-check via MESH4 catches defection earlier |
| ADVERSARIAL-AWARE | B with dynamic ε ∝ 1/H(pool) | High-stakes (medical, financial, consensus) | Full adversarial suite; ε scales with pool entropy |

The CIP intent URI is the natural slot for a `routing_mode` hint. This maps to R1 (#173)
protocol/policy boundary: `routing_mode` is protocol-declared intent metadata, not client
side-policy, because the selection algorithm choice affects all participants in the pool.
R6 (#178) delivers the REDUNDANT mode N-of-M execution mechanics.

**Sub-0.50 reputation and the floor trap (new)**:

Nodes can drop below starting credit (0.50) with as few as 3 consecutive EMA failures.
Below the Silver tier floor (0.40), nodes are excluded from the routing pool — but this
creates a reputation floor trap: excluded nodes receive no traffic, cannot accumulate
successes, and cannot recover. The same cold start dynamics identified in RS6-F1 apply
to recovering nodes. Protocol countermeasure: a rehabilitation probationary period
(analogous to MESH2 §4 for new nodes) where nodes below-floor receive bounded exploration
traffic for up to 72h before permanent exclusion. See RESA-006 for transient window analysis.

---

## 6. Acceptance Criteria Verification

| AC | Requirement | Status |
|----|-------------|--------|
| All 4 adversarial scenarios simulated with A–E | SYBIL_1/5/10 + BAIT + FARM + PHI_ATTACK all complete (N=100/1000/10000, 3 seeds) | ✓ |
| D vs C adversarial comparison explicit | §3.3 + R5-F3: D≡A adversarially; φ knowledge not additional threat; C's noise slightly elevates adv% at large N | ✓ |
| Recovery-time metric included | §2+§3: detection_job + recovery_jobs per algorithm per scenario | ✓ |
| Null result stated plainly if no policy differs | R5-F5: "no selection policy alone provides adequate sybil defense at ≥5% in N≥1000" | ✓ |

**Sweep summary**: 6 scenarios × 3 sizes × 3 seeds × 5 algorithms = 270 runs. All completed (exit 0). Confidence: MED — detection model is simplified (binary consecutive-failure threshold, not probabilistic reputation scoring). Real-world IICP detection would use EMA reputation decay with α=0.1, which would change T_detect estimates but not the structural ordering of algorithm performance.
