# IICP Research Outcomes — Consolidated Reference

**Maintained by**: RESA loop (`project/resa-loop-prompt.md`), SPEC loop, and FORGE-5 ADOPTION sub-loop  
**State file**: `project/RESA_STATE.json` (RESA tracks); WORK_QUEUE.json (ADOPTION-driven tracks)  
**Last updated**: 2026-05-21 (FORGE-5 iter-370 — inbound-adapters track added)

> **Simulation-vs-live status (updated iter93)**: REP findings (F1–F16) and R1–R7 design findings derive from discrete-event simulation (Python harness, bounded network sizes 100–10,000). RS6 Phase 2 (iter93) added actual Ollama inference validation (phi3:mini vs qwen2.5:0.5b, 90 calls) — the quality-feedback loop is now partially cross-validated against real inference. Treat REP equilibrium findings as directional until REP6 full pilot completes. R4/R5/R6 routing findings are validated at simulation scale; real-pool behaviour to be confirmed by RS6 Phase 3.

> **ADOPTION research status (added iter-301, 2026-05-21)**: GAMIFICATION + COMMUNITY-PLATFORM research tracks added to address ADOPTION binding constraint (W-016 / FC-001 — no confirmed external operators, D7 score corrected from 91 to ~60). These tracks are FORGE-5 ADOPTION sub-loop deliverables, distinct from RESA simulation tracks. Both research tracks have completed all design deliverables (5/5 each); implementation gated on #260 public-launch + ADR-030 operator identity layer.

This document consolidates all research outcomes, datasets, test cases, and design
insights across the active research tracks. It is the primary reference for
spec writers, ADR authors, and implementation teams.

---

## Track Index

| Track | Issues | Status | State |
|-------|--------|--------|-------|
| **REP** — Reputation & Tiered Access | #167-#172 | Design+Pilot complete | REP1-REP5 closed; REP6 (#172) simulation pending |
| **R1R7** — Provider Selection & Multi-Path | #173-#179 | All design+simulation done | R1–R7 all closed; RS6 Phase 2 pilot complete |
| **MESH** — Consolidator / Role-Routing | #180-#184 | Design phase | MESH1-MESH4 design done; MESH5 pilot pending |
| **GAMIFICATION** — Operator Recognition (Nerd Legacy) | #267, #269 (ADR-030) | **Research COMPLETE 5/5** (iter-294..300) | Awaiting PS review + #260 public-launch gate + ADR-030 Accepted before implementation |
| **COMMUNITY-PLATFORM** — Forum / BBS choice | #268 | **Research COMPLETE 5/5** (iter-301) | Lemmy recommended; awaiting maintainer sign-off |
| **INBOUND-ADAPTERS** — LLM API compat layer | #273 | **Research COMPLETE 1/1** (iter-370) | Priority matrix done: Ollama-compat Phase A, Anthropic-compat Phase B; implementation issues to be filed |

**RESA composite**: **92.36/90.0 CONVERGED** (iter93, 2026-05-18). R-GATE-1 OPEN.

**ADOPTION-driven research**: Gamification + Community-Platform tracks complete; both gated on maintainer review + #260 public-launch decision. See sections below.

---

## REP Track

**Charter**: `research/reputation-and-tiers-charter.md`  
**ADRs**: ADR-026 (reputation as earned signal), ADR-027 (premium as paid axis)  
**Harness**: `research/simulation/rep/harness.py`

### Issue Map

| Issue | Title | Phase | Status | Findings |
|-------|-------|-------|--------|---------|
| REP1 #167 | Reputation mechanics and starting credit | Simulation | **OPEN** (ratification pending) | F1–F9, F16 — `REP1-starting-credit-recommendation-2026-05-18.md` |
| REP2 #168 | Tier structure and transition rules | Simulation | **OPEN** (ratification pending) | F1–F12 — `REP2-tier-boundaries-recommendation-2026-05-18.md` |
| REP3 #169 | Premium services taxonomy | Design-only | Closed | `REP3-premium-services-taxonomy.md` |
| REP4 #170 | Two-sided feedback collection | Design+schema | **CLOSED** iter93 | `REP4-feedback-mechanism-2026-05-18.md`, `research/rep-track/feedback-mechanism.md`, `spec/schemas/feedback-envelope.json` |
| REP5 #171 | Whitewash and adversarial scenarios | Simulation | **CLOSED** | `REP5-adversarial-modeling-2026-05-18.md` |
| REP6 #172 | Simulation harness + local pilot gate | Simulation+local | **OPEN** (simulation pending) | RS6-F1 (Phase 1 shadow), RS6-F2..F5 (Phase 2 Ollama pilot) |

### Simulation Parameters (harness defaults)

```
starting_credit     = 0.50 (recommended — REP1 design; ratification pending)
success_bump        = +0.01
quality_coeff       = +0.001 per intent_match point above 3 (REP4)
failure_penalty     = -0.05
feedback_ema        = α_fb = 0.05 (F13-validated)
decay λ             = 0.005/hr, floor=0.30, cap=200h idle (S.12 §5.1)
tier_thresholds     = silver=0.40, gold=0.65, platinum=0.85 (REP2 design; ratification pending)
identity_age_gate   = ≥720h for platinum (REP2 design; F10/F12 validated)
bootstrap_floor     = threshold=100 lifetime_jobs, session=30min, pool-guard=3 (§5.1.2; ratification pending)
steps               = 100 (standard) / 1000 (convergence) / 3000 (strategic adversary)
network_size        = 100 / 1000 / 10000 (multi-scale)
```

### Datasets

| File | Runs | Parameters | Description |
|------|------|-----------|-------------|
| `research/results/rep/*.json` | 27 | 100/1k/10k × 3 seeds × 3 scenarios | Multi-scale preliminary runs |
| `research/results/rep/sweep/*.json` | 72 | 4 sc × 3 af × 3 seeds × 2 step-counts | Adversarial sensitivity sweep |
| `research/results/rep/identity_age/*_steps1000.json` | 18 | 2 gate × 3 af × 3 seeds, 1000 steps | Identity-age gate: Archetype A baseline |
| `research/results/rep/identity_age/*_steps3000.json` | 18 | 2 gate × 3 af × 3 seeds, 3000 steps | Identity-age gate: Archetype B strategic — F10/F11/F12 |
| `research/results/rep/collusion/*_steps1000.json` | 15 | 5 scenarios × 3 seeds, 1000 steps | Coordinated collusion α_fb=0.05 — F13/F14/F15 |
| `research/results/rep/assortative/*_steps500.json` | 12 | 4 k × 3 seeds, 500 steps, size=100 | Assortative matching — F16 |
| `research/results/resa006/resa006_results.json` | 45 | 3 pool sizes × 3 seeds × 5 thresholds | Bootstrap floor threshold validation (RESA-006) |
| `research/results/rs6/rs6_phase2_results.json` | 90 | 2 models × 30 tasks × 3 seeds | RS6 Phase 2 — real Ollama inference pilot |

### Key Findings

Confidence levels: **HIGH** = simulation-validated with sound methodology; **MED** = directional with caveats; **MED-PREL** = preliminary — explicit limitation noted.

| ID | Finding | Confidence | Source | ADR Impact |
|----|---------|------------|--------|-----------|
| F1 | **Scale invariance**: Tier distributions stable across 100/1k/10k agents at 100 steps | HIGH | REP1-REP2 preliminary | None (validates design) |
| F2 | **Adversarial isolation (20%)**: Network avg_rep drops 11% but honest agents reach gold/platinum at same rates | HIGH | REP1-REP2 preliminary | None (validates design) |
| F3 | **Recovery dynamics**: Damaged nodes (rep near floor) recover to above-baseline after 100 steps of honest behavior | HIGH | REP1-REP2 preliminary | REP1: "forgiving by default" confirmed |
| F4 | **Starting credit (sc=0.5)**: New agents start at silver/gold boundary — routable but not privileged | MED — transient window not characterized | REP1-REP2 preliminary | ADR-026: sc=0.5 defensible default |
| F5 | **Demotion asymmetry validation**: 10× asymmetry produces slow honest rise, rapid non-compliant fall | MED — ratio not swept | REP1-REP2 preliminary | REP1: delta values in right range |
| F6 | **Starting credit convergence invariance (steady-state only)**: sc ∈ {0.3,0.4,0.5,0.6} all converge to same honest-agent equilibrium at 1000 steps. **Transient behavior (first 30–100 steps) not characterized.** | MED — steady-state only | Adversarial sweep | ADR-026: sc=0.5 is UX parameter, not security parameter |
| F7 | **Adversarial equilibrium fixed at ~0.318**: 30% defect rate converges near floor. E[Δ] = −0.0143/task | HIGH | Adversarial sweep | REP5: threshold ambiguity zone defined |
| F8 | **Zero whitewash (Archetype A only)**: Random defectors never reach platinum in 72 runs. Does NOT cover strategic attackers (Archetype B). | HIGH for Archetype A only | Adversarial sweep | REP1: starting_credit=0.5 safe against random defectors |
| F9 | **Adversarial fraction resilience**: Honest avg_rep drops ≤0.005 when adversarial fraction rises 10%→30% | HIGH | Adversarial sweep | REP5: threat model ceiling at 30% |
| F10 | **Identity-age gate reduces platinum whitewash 13×**: Strategic agents complete 39 whitewash cycles/3000 steps without gate; 3 with 720h gate | HIGH | Identity-age simulation | REP2: gate validated; ADR-026 updated |
| F11 | **⚠ Gate is efficiency tax, not full deterrent — defense-in-depth required**: 3 whitewash cycles remain with gate active. Required stack: penalty asymmetry + quorum gate (§T4.2) + outlier detection (§T4.3, #187) + attestation. | HIGH — **primary architectural constraint** | Identity-age simulation | No single defense mechanism is sufficient |
| F12 | **Gate eliminates adversarial presence in platinum routing pool**: Zero adversarial agents hold platinum-eligible status at simulation end (AF=10–30%) | HIGH | Identity-age simulation | REP2: key operational benefit |
| F13 | **Coordinated feedback collusion negligible at α_fb=0.05**: K=5 colluders produce <0.03 avg reputation inflation over 1000 steps | HIGH — at α_fb=0.05 only | Collusion simulation | REP4: α_fb=0.05 validated safe |
| F14 | **⚠ Latency signal IS capturable — open attack surface**: K=5 colluders bias latency EMA 48% (174ms→91ms). §T4.3 OUTLIER_WEIGHT (#187) is the required fix. **Protocol not production-safe for open networks without #187.** | HIGH — confirmed vulnerability | Collusion simulation | T4.3 must ship before open-network deployment |
| F15 | **Low-quality provider cannot self-inflate via feedback**: At α_fb=0.05, feedback inflation (+0.0005/step) dominated by penalty asymmetry 24× | HIGH | Collusion simulation | REP4: feedback cannot elevate genuinely low-quality nodes |
| F16 | **PRELIMINARY — No ossification at k=0–3 (size=100)**: Newcomers at sc=0.50 reach gold 73–100% across k=0–3. Caveat: size=100 only; k>3 not tested; Q8 objective not modeled. | MED-PREL | Assortative matching simulation | REP1/REP2: sc=0.5 defensible within k∈[0,3] |
| RESA006-F1 | **Threshold=100 is minimum that guarantees 100% Gold rate for good nodes**: Good nodes (87% success) need ≥68 actual jobs from sc=0.50. Threshold=50 achieves only 33% (variance causes failure). Threshold=100 provides sufficient buffer — 100% Gold rate across all seeds and pool sizes. | HIGH | `RESA006-bootstrap-floor-threshold-2026-05-18.md` | §5.1.2: threshold=100 validated |
| RESA006-F2 | **Without floor, good nodes NEVER reach Gold at N≥1000**: ε-greedy selection probability ≈1/N — good new nodes receive ~2 actual jobs per 2000 calendar slots. Bootstrap floor is NOT optional for networks with N>100. | HIGH | `RESA006-bootstrap-floor-threshold-2026-05-18.md` | §5.1.2: floor is mandatory at scale |
| RESA006-F3 | **Floor correctly differentiates quality — average nodes self-select out**: Nodes below break-even (63% success < 83.3% break-even) that receive floor traffic have their reputation pushed DOWN into recovery band. Correct system behavior. | MED — static quality model | `RESA006-bootstrap-floor-threshold-2026-05-18.md` | §5.1.2: floor is opportunity, not subsidy |
| RS6-F1 | **Cold-start problem acute in real 7-node pool**: ε-greedy routes 100% to dominant node in real iicp.network pool data. New nodes never bootstrap without floor mechanism. | HIGH | `RS6-shadow-pilot-real-data-2026-05-18.md` | Validates §5.1.2 necessity empirically |
| RS6-F2 | **REP4 quality feedback correctly elevates higher-quality nodes in real inference**: phi3:mini (93.2% correct) reached 0.846 avg rep vs qwen2.5:0.5b 0.508 avg rep. A beats B 3/3 seeds. 90 actual Ollama inference calls. | HIGH | `RS6-local-pilot-phase2-2026-05-18.md` | REP4 quality modifier confirmed directionally |
| RS6-F3 | **ε-greedy concentrates on leader within 5–10 tasks**: In 2/3 seeds, second node received zero tasks once first node established lead. Concentration is rapid even at N=2. | HIGH | `RS6-local-pilot-phase2-2026-05-18.md` | Confirms R4/R6 concentration findings in real inference |
| RS6-F4 | **Quality signal strength depends on task complexity**: Both models scored perfectly on simple factual tasks. REP4 differentiation is stronger on reasoning tasks. | MED | `RS6-local-pilot-phase2-2026-05-18.md` | Phase 3 should use harder tasks |
| RS6-F5 | **Bootstrap floor essential even at N=2 with equal starting credit**: Node B excluded from routing despite being capable. §5.1.2 floor mechanism validated in real inference environment. | HIGH | `RS6-local-pilot-phase2-2026-05-18.md` | §5.1.2 empirically validated |

### Open Questions

| Q | Question | Assigned | Status |
|---|---------|---------|--------|
| Q1 | Is sc=0.5 correct or should it be lower (0.4)? | REP1 | Partially answered: F6 shows sc is long-run invariant; 0.5 is correct for UX. Transient behavior open (RESA-005 pending). |
| Q2 | Does platinum gate on identity_age ≥ 30d make whitewash economically irrational? | REP2 | Partially answered: F10/F11/F12 — gate reduces 13×, eliminates persistent platinum. Combined defenses needed. |
| Q3 | At what defection rate is adversarial agent indistinguishable from noisy-honest? | REP5 | Partially answered: Archetype A (30% defect) → 0.318, clearly below silver. Strategic (Archetype B) indistinguishable until platinum attempt. |
| Q4 | Does client feedback (REP4) suppress Sybil rating farms? | REP4 | Answered by design: identity weighting + clustering detection (§5 of feedback-mechanism.md). Simulation validation deferred to REP6. |
| Q5 | Does α_fb=0.05 prevent feedback from overwhelming telemetry signal? | REP4 | **Answered — F13**: Yes. F15 shows feedback inflation 24× dominated by penalty asymmetry. |
| Q6 | Does 30-min commit-reveal window adequately prevent rating anchoring? | REP4 | Design rationale documented in feedback-mechanism.md §3. Not simulated. |
| Q7 | Does coordinated feedback ring significantly inflate reputation? | REP4+RS2 | **Answered — F13/F15**: No. α_fb=0.05 robust against K=5 colluders. |
| Q8 | What routing concentration k is optimal for network quality? | REP2 | Open — requires objective function. Not yet modeled. |
| Q9 | Under adversarial conditions, does k=3 amplify defectors? | REP2+REP5 | Open — blocked on RS3 defector equilibrium thresholds at varying k. |

### Spec Gaps Identified (REP track → ARCS)

| Gap | Spec change needed | File | Status |
|-----|-------------------|------|--------|
| Telemetry trust model | §T4 PROXY_TOKEN_AUTH + SYBIL_QUORUM + OUTLIER_WEIGHT | spec/iicp-telemetry.md | **DONE** (iter72) |
| T4.3 Outlier detection | Implement §T4.3 OUTLIER_WEIGHT — F14 confirmed latency is capturable | spec/iicp-telemetry.md | **OPEN** (#187 — ratification pending) |
| Bootstrap traffic floor | §5.1.2: 1 job/session, threshold=100, session=30min, pool-guard=3 | spec/iicp-cooperative-inference.md | **DRAFTED** v0.6.2-draft; PENDING ratification (#168) |
| Tier structure | §5.1.1: silver=0.40, gold=0.65, platinum=0.85, identity-age=720h | spec/iicp-cooperative-inference.md | **DRAFTED** v0.6.1-draft; PENDING ratification (#168) |
| Feedback endpoint | POST /v1/feedback + /v1/feedback/reveal (commit-reveal, identity weighting) | spec/iicp-semantics.md | **SCHEMA DONE** (spec/schemas/feedback-envelope.json); spec text pending REP6 |
| Priority task field | Add `priority` to task submission schema | spec/iicp-semantics.md | Open (#188) |
| SLA declaration | Add `sla_p95_ms` to heartbeat payload | spec/iicp-core.md | Open (#189) |
| Attestation receipt | Add `attestation_receipt` + `model_used` to task response | spec/iicp-semantics.md | Open (#190 — blocked on #150, #155) |
| Intent URN suffix | Define `+attested` suffix convention | spec/iicp-intents.md | Open (#191 — blocked on #190, #150) |

---

## R1R7 Track

**Charter**: `project/cc-instructions/CC-provider-selection-R1-R7-2026-05-17.md`  
**ADRs**: ADR-025 (provider selection research track)

### Issue Map

| Issue | Title | Phase | Status | Findings |
|-------|-------|-------|--------|---------|
| R1 #173 | Protocol/policy boundary | Design | **CLOSED** | `R1-protocol-policy-boundary-2026-05-18.md` — R1-F1 |
| R2 #174 | Multi-path protocol requirements + threat model | Design | **CLOSED** | `R2-multi-path-protocol-requirements-2026-05-18.md` — R2-F1 |
| R3 #175 | Discovery: centralized vs. DHT | Design | **CLOSED** | `R3-discovery-layer-2026-05-18.md` — R3-F1 |
| R4 #176 | Selection policy comparison: ε-greedy vs harmonic/UCB/etc | Simulation | **CLOSED** | `R4-selection-policy-comparison-2026-05-18.md` — R4-F1..Fn |
| R5 #177 | Adversarial robustness of selection policies | Simulation | **CLOSED** | `R5-adversarial-robustness-2026-05-18.md` — R5-F1..Fn |
| R6 #178 | Multi-path N-of-M strategies | Simulation | **CLOSED** iter90 | `R6-multi-path-execution-2026-05-18.md` — R6-F1..F6 |
| R7 #179 | SSSP reality check | Design | **CLOSED** | `research/sssp-relevance-reality-check.md` — R7-F1 |

### Key Findings

| ID | Finding | Confidence | Source |
|----|---------|------------|--------|
| R1-F1 | **Protocol carries substrate only**: 10 fields PROTOCOL-REQUIRED; scoring weights and exploration rates are CLIENT-INTERNAL. 5 protocol gaps identified: capability staleness, identity age in discover response, role field, multi-path declaration, load indicators. | HIGH | `R1-protocol-policy-boundary-2026-05-18.md` |
| R2-F1 | **Multi-path requires new protocol fields**: `multi_path` in task submission (set_id, position, size, strategy); `multi_path_fragment` in response. All N providers in a set get paid. ADR-029 proposed. | HIGH | `R2-multi-path-protocol-requirements-2026-05-18.md` |
| R3-F1 | **Stay centralized; DHT gated on 3-condition trigger**: ADR-013 federation satisfies Phase 5+ need. DHT warranted only when ≥10k nodes AND documented censorship AND distributed reputation solution exists. | HIGH | `R3-discovery-layer-2026-05-18.md` |
| R6-F1 | **Single-provider is optimal for 3/4 job types**: Single dominates for standard, low-latency, cost-sensitive tasks at all pool sizes. 2-of-3 quorum beats single only for high_value tasks at N≥1000 (nv=4.595 vs 4.255). | HIGH | `R6-multi-path-execution-2026-05-18.md` |
| R6-F2 | **Protocol routing_mode recommendation**: BEST_EFFORT=single (default), REDUNDANT=2-of-3, BYZANTINE=3-of-5. 1+verify and 2-of-2 dominated by single in all cases. | HIGH | `R6-multi-path-execution-2026-05-18.md` |
| R6-F3 | **3-of-5 is negative expected value for cost-sensitive tasks**: Byzantine strategy significantly reduces net value for cost-sensitive workloads. Use only for Byzantine threat environments. | HIGH | `R6-multi-path-execution-2026-05-18.md` |
| R7-F1 | **SSSP irrelevant at all plausible IICP scales**: Dijkstra <50µs at 10,000 nodes — 100× faster than network RTT. Defer with 3-condition trigger: ≥50k nodes + multi-hop relay + per-request path computation. | HIGH | `research/sssp-relevance-reality-check.md` |

---

## MESH Track

**Charter**: `project/cc-instructions/CC-mesh-consolidator-role-routing-MESH1-MESH5-2026-05-17.md`  
**ADRs**: ADR-028 (consolidator pattern + role-routing)

### Issue Map

| Issue | Title | Phase | Status | Findings |
|-------|-------|-------|--------|---------|
| MESH1 #180 | Role-assignment algorithm | Design | **DONE** (design phase) | `research/mesh-track/MESH1-role-assignment-algorithm-2026-05-18.md` |
| MESH2 #181 | Consolidator pool dynamics | Design | **DONE** (design phase) | Finding doc exists |
| MESH3 #182 | Load-aware selection | Simulation | **DONE** (simulation run) | Harness: `research/simulation/mesh/load_selection.py` |
| MESH4 #183 | Consolidator integration + disagreement resolution | Simulation | **DONE** (design+simulation) | Finding doc exists |
| MESH5 #184 | Local pilot + live-readiness gate | Local pilot | **OPEN** — pilot not yet run | Pending real inference environment |

### Dependencies

```
REP1/REP2 (tier thresholds ratified)  ← PENDING PS ratification #168
  └── MESH1 (role-assignment algorithm) ← DONE (design; simulation after ratification)
       ├── MESH2 (consolidator pool dynamics) ← DONE (design)
       ├── MESH3 (load-aware selection) ← DONE (simulation)
       └── MESH4 (consolidator integration) ← DONE (design+sim)
            └── MESH5 (local pilot gate) ← OPEN
```

---

## Cross-Track Insights

1. **Penalty asymmetry is the keystone (HIGH confidence)**: The 10× failure/success asymmetry (−0.05 vs +0.01) is load-bearing across F2, F7, F9, F15. F15 specifically shows feedback inflation is dominated by penalty asymmetry 24×. Do not weaken below 10× without re-running all findings.

2. **Defense-in-depth is non-negotiable — F11 is the primary architectural constraint (HIGH confidence)**: No single mechanism provides adequate reputation security. Required stack: (a) penalty asymmetry 10×, (b) quorum gate §T4.2 (live), (c) identity-age gate for platinum (F10/F12), (d) OUTLIER_WEIGHT §T4.3 (#187, not yet implemented). F14 makes the latency attack surface explicit — the protocol is not production-safe for open networks without (d).

3. **Starting credit is onboarding UX, not security (MED — transient caveat)**: F6 shows sc is long-run invariant *at steady state*. Transient behavior (first 30–100 steps) not characterized. Security against whitewash relies on the identity-age gate (REP2) and quorum gate (§T4.2).

4. **Sybil quorum gate is live — do not weaken (HIGH confidence)**: §T4.2 quorum gate (≥3 distinct proxy_node_ids, 7-day window) is production-deployed. F13's collusion-resistance result depends on this gate being active.

5. **MESH depends on REP1/REP2 resolution**: MESH1 role-assignment uses reputation thresholds. Simulation phase cannot proceed until REP1/REP2 PENDING markers are cleared (#168).

6. **ε-greedy (Algorithm B) is the validated default selection policy**: R4 simulation confirmed ε-greedy is the recommended default at all tested pool sizes. RS6-F3 confirmed its concentration behavior in real inference. RS6 Phase 2 validated that feedback correctly differentiates quality in ε-greedy routing.

---

## High-Confidence Constraints — What NOT to Do

| Constraint | Source | Reason |
|-----------|--------|--------|
| Do NOT ship a single-defense reputation system | F11 | Combined stack required; no single mechanism sufficient |
| Do NOT ship without §T4.3 OUTLIER_WEIGHT (#187) for open-network claims | F14 | 48% latency bias confirmed. No mitigation except #187. |
| Do NOT generalize F8 ("zero whitewash") to strategic attackers | F8 | F8 tests Archetype A only. Strategic attackers need identity-age gate (F10). |
| Do NOT use α_fb above 0.05 without re-testing | F13 | Collusion resistance validated at α_fb=0.05 only. |
| Do NOT use routing concentration k>3 without testing | F16 | Ossification behavior above k=3 unknown. |
| Do NOT weaken penalty asymmetry below 10× without re-testing | F2/F7/F9/F15 | Load-bearing across four key findings. |
| Do NOT claim SSSP adds value at current scale | R7 | Dijkstra <50µs at 10k nodes — 100× faster than network RTT. |
| Do NOT use multi-path REDUNDANT=2-of-2 or 1+verify | R6-F1 | Both dominated by single-provider in all tested conditions. |
| Do NOT deploy bootstrap floor without pool-size guard (≥3 Silver+ nodes) | §5.1.2, RESA006 | Guard prevents floor from firing when pool is too small to absorb it. |

---

## GAMIFICATION Track (Nerd Legacy Program)

**Issues**: #267 (research), #269 (ADR-030 Operator Identity & Anti-Sybil — prerequisite)
**Deliverables location**: `research/gamification-track/`
**Status**: Research COMPLETE (5/5 deliverables) — awaiting PS review + 8 rollout gates
**Concept doc**: `project/gamification.md` (public-facing project-level doc)

### Deliverables (all complete iter-294..300)

| # | File | Purpose | iter |
|---|------|---------|------|
| 01 | `01-design-rationale.md` | Earn-by-existing principle, multi-axis identity, prior art survey (StackOverflow / GitHub / Foldit / BOINC / Strava), constraints | 294 |
| 02 | `02-metric-mapping.md` | Rank/badge → telemetry mapping. 16/23 fully computable today; 7 partial bounded extensions; composite rank_score formula proposed | 296 |
| 03 | `03-anti-gaming.md` | 7 attack categories (sock-puppet, metric-stuffing, time-boxing, tier-surfing, identity-laundering, geographic spoofing, collusion); per-rank/badge mitigations; **hybrid operator identity proposed (→ ADR-030 candidate)**; 6 hard normative rules | 297 |
| 04 | `04-rollout-gates.md` | 8 sequential gates (G1 Identity → G2 Public-launch → G3 REACH multi-region → G4 ≥10 external operators → G5 Telemetry → G6 Spec+conformance → G7 Privacy+moderation → G8 Founding Cohort migration); 4-phase staged rollout (R1 quiet → R2 internal → R3 public → R4 first season close) | 299 |
| 05 | `05-api-surface.md` | 7 endpoints (4 public reads cacheable + 3 operator-authenticated writes); 4 tables (2 from ADR-030 + 2 new); 8 conformance test IDs (RECOG-PROF-01..PRIV-01); ~10 commits implementation estimate | 300 |

### Key research findings

- **Earn-by-existing principle**: every signal the framework rewards is already produced by normal mesh operation. No parallel metric. Same actions that make the mesh work = actions that earn recognition.
- **Multi-axis identity** (reliability, throughput, diversity, reach, conformance, tenure) prevents single-metric Goodhart gaming and creates multiple ladders to climb.
- **Temporal cohorts** (H1/H2 seasons + Class of YEAR) create urgency + renewal mechanic + permanent cohort identity without locking out late joiners (their own class).
- **Anti-Sybil requires operator identity layer** — ADR-030 surfaced as prerequisite. Hybrid model: Tier 1 pseudonymous Ed25519 (default) + Tier 2 attested (email/DID:web/federated) for operator-diversity badges.
- **Implementation is bounded**: ~10 commits over 2 weeks once gates clear. Reuses existing CF cache, throttle, auth middleware.

### Blocking

- **#260** (public-launch gate) — leaderboards of a single-operator mesh are embarrassing
- **#269** (ADR-030 Operator Identity) — operator-diversity badges undefeatable without identity layer
- **≥10 attested external operators** — quantitative threshold for safe launch (G4)

---

## COMMUNITY-PLATFORM Track (Forum / BBS Evaluation)

**Issue**: #268
**Deliverables location**: `research/community-platform/`
**Status**: Research COMPLETE (5/5 deliverables) — awaiting maintainer sign-off
**Recommendation**: **Lemmy** (Rust + Postgres + AGPL + ActivityPub native)

### Deliverables (all complete iter-301)

| # | File | Purpose |
|---|------|---------|
| 01 | `01-requirements.md` | 15 functional + 10 non-functional requirements; scale assumptions (Y1 <500 ops, Y2 5k, Y5 50k aspirational) |
| 02 | `02-candidates.md` | 8 platforms evaluated (Lemmy, Discourse, Flarum, NodeBB, Misskey, Cactus, GH Discussions, Custom); top-3 deeper dive; cost-of-life comparison |
| 03 | `03-federation-fit.md` | ActivityPub maturity per candidate; **federation promoted from NICE to MUST** (deliverable 03 amendment); Lemmy only candidate clearing the bar today |
| 04 | `04-dogfood-angle.md` | Community-on-mesh exploration — appealing long-arc story, premature today; defer until Phase 6 + ADR-030 + ≥100 attested operators |
| 05 | `05-recommendation.md` | Lemmy recommended; Discourse as fallback; 4-phase rollout plan (stand-up → federate → embed → migration) |

### Key research findings

- **Federation is a hard requirement** (deliverable 03 amendment) — IICP's federated philosophy demands a federated community venue. Centralized forum on top of federated protocol = contradiction.
- **Lemmy wins on philosophy + federation**: only candidate with mature ActivityPub support today. Rust stack aligns with iicp-node. AGPL aligns with operator-sovereign posture.
- **Discourse is fallback only**: superior mobile UX and plugin ecosystem, but federation gap blocks. Reserve for Phase 2 if Lemmy proves blocking for gamification integration.
- **Community-on-mesh deferred**: aspirational but premature. Document the path (deliverable 04) without committing to build.
- **Hosting cost**: ~$10/mo VPS (Hetzner CX22 recommended); scales to $25/mo at 5k users.

### Implementation

- Tracking issue to be filed by maintainer after sign-off.
- Suggested: "[ADOPTION] Deploy community.iicp.network (Lemmy) — Phase 1 stand-up"
- Estimated: 2-3 day standup + 1 week federation validation

### Blocking

- Maintainer sign-off on Lemmy choice
- Hosting decision (infrastructure provider)
- Initial mod team selection

---

## Maintenance Protocol

**This document is a mandatory output of multiple loops — RESA (simulation tracks) AND FORGE-5 ADOPTION (Gamification / Community-Platform / future ADOPTION research) — update every iteration that touches a research track.**

After each iteration that affects research:
1. Update "Last updated" header (date + iter number + composite score where applicable)
2. Update Track Index status row for the affected track
3. Update Issue Map row: change Status and Findings columns
4. Add new findings to the finding table (sequentially numbered within track)
5. Update dataset table when new result files are generated
6. Update open questions (mark answered, add new ones)
7. Update spec gaps table when new gaps are identified or existing ones closed
8. Update Cross-Track Insights if a new finding changes architectural understanding
9. Update High-Confidence Constraints if a finding changes a constraint
10. **For ADOPTION-driven tracks** (Gamification, Community-Platform): add a deliverable row to the track's section when a new research doc lands

**Never skip this step.** RESEARCH.md is the authoritative consolidated reference — staleness here makes it useless as a reference for ARCS, CORC, and implementation teams.

The SPEC loop bumps the spec version and deploys to iicp.network when spec files change.
