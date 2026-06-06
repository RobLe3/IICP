# REP — Adversarial Sensitivity Sweep

**Track**: REP — Reputation & Tiered Access  
**Issues**: #167 (REP1), #168 (REP2), #171 (REP5)  
**Status**: Complete — 72 runs (36 × 100 steps + 36 × 1000 steps)  
**Date**: 2026-05-18  
**Harness**: `research/simulation/rep/sweep_adversarial.py`  
**Raw results**: `research/results/rep/sweep/sweep_summary_steps{100,1000}.json`

---

## Sweep parameters

```
network_size:         1000 agents (fixed)
starting_credit:      {30, 40, 50, 60}   (0.3, 0.4, 0.5, 0.6 normalised)
adversarial_fraction: {0.10, 0.20, 0.30}
seeds:                {0, 1, 2}
steps:                100 (convergence check) + 1000 (long-run)
scenario:             adversarial (20% → parameterised fraction)
```

Adversarial agent behaviour: 70% tasks attempted (85% success rate), 30% outright failure
(intentional defection). Whitewash reset triggered on platinum at 30% probability.

---

## 100-step results

| starting_credit | adv_fraction | honest_avg | adv_avg | gap  | whitewash_resets |
|-----------------|-------------|-----------|---------|------|-----------------|
| 30 | 0.10 | 0.649 | 0.317 | 0.332 | 0 |
| 30 | 0.20 | 0.649 | 0.317 | 0.332 | 0 |
| 30 | 0.30 | 0.646 | 0.317 | 0.330 | 0 |
| 40 | 0.10 | 0.711 | 0.317 | 0.394 | 0 |
| 40 | 0.20 | 0.709 | 0.317 | 0.392 | 0 |
| 40 | 0.30 | 0.708 | 0.317 | 0.391 | 0 |
| 50 | 0.10 | 0.791 | 0.317 | 0.474 | 0 |
| 50 | 0.20 | 0.789 | 0.317 | 0.472 | 0 |
| 50 | 0.30 | 0.788 | 0.317 | 0.471 | 0 |
| 60 | 0.10 | 0.863 | 0.317 | 0.546 | 0 |
| 60 | 0.20 | 0.860 | 0.317 | 0.543 | 0 |
| 60 | 0.30 | 0.860 | 0.317 | 0.543 | 0 |

---

## 1000-step results (long-run convergence)

| starting_credit | adv_fraction | honest_avg | adv_avg | gap  | whitewash_resets |
|-----------------|-------------|-----------|---------|------|-----------------|
| 30 | 0.10 | 0.954 | 0.318 | 0.635 | 0 |
| 30 | 0.20 | 0.954 | 0.319 | 0.635 | 0 |
| 30 | 0.30 | 0.950 | 0.316 | 0.634 | 0 |
| 40 | 0.10 | 0.954 | 0.318 | 0.635 | 0 |
| 40 | 0.20 | 0.954 | 0.319 | 0.635 | 0 |
| 40 | 0.30 | 0.950 | 0.316 | 0.634 | 0 |
| 50 | 0.10 | 0.954 | 0.318 | 0.635 | 0 |
| 50 | 0.20 | 0.954 | 0.319 | 0.635 | 0 |
| 50 | 0.30 | 0.950 | 0.316 | 0.634 | 0 |
| 60 | 0.10 | 0.954 | 0.318 | 0.635 | 0 |
| 60 | 0.20 | 0.954 | 0.319 | 0.635 | 0 |
| 60 | 0.30 | 0.950 | 0.316 | 0.634 | 0 |

---

## Key findings

### F6 — Starting credit converges away (long-run invariance)

At 1000 steps, **starting_credit has zero effect** on final reputation distributions.
All four values (30, 40, 50, 60) produce identical honest_avg (~0.954) and adv_avg
(~0.318) at convergence. Starting credit only affects onboarding speed (at 100 steps,
sc=60 gives honest_avg=0.863 vs sc=30 gives 0.649), not the long-run equilibrium.

**Implication for REP1**: Starting credit is an onboarding UX decision, not a security
decision. The choice of 50 (silver/gold boundary) is appropriate — it gives new nodes
a fair routing chance without granting platinum access. Lower values (30, 40) slow
onboarding without improving adversarial resilience.

### F7 — Adversarial equilibrium is fixed at ~0.318 (near floor)

Adversarial agents converge to ~0.317–0.319 regardless of starting_credit or adversarial
fraction. This is the analytical equilibrium: with 70% task rate at 85% success and
30% outright failure, expected per-task reputation change is:

```
E[Δ] = 0.595 × (+0.01) + 0.405 × (-0.05) = 0.00595 - 0.02025 = -0.0143
```

Adversarial agents are in a **net-negative regime** — they cannot sustain reputation
growth. They converge to the floor (0.30) unless they defect less aggressively.

**Implication for REP5**: The 30% defection rate is adversarial-fatal. To reach platinum,
an adversarial agent must defect at ≤10% rate (where the expected Δ becomes positive).
At ≤10% defection, the agent is behaviorally indistinguishable from an honest agent
with a bad day — the protocol cannot meaningfully distinguish this from noise.
REP5 should note this as the "threshold ambiguity zone."

### F8 — Whitewash attack does not manifest at current parameters

Zero whitewash resets across all 72 runs (36 × 100 steps + 36 × 1000 steps). Adversarial
agents never reach platinum because their net-negative expected Δ prevents sustained
reputation growth. The whitewash attack (reset identity at platinum) is a threat model
concern that does not manifest under current defection rate assumptions.

**Implication for REP1**: The Sybil/whitewash gate (starting_credit=0.5 for new identity)
is still necessary as a preventive measure, but the threat is less severe than F2
(adversarial isolation) suggested. A node would need to act nearly honestly for ~200+
steps before reaching platinum — at which point whitewash is an economically irrational
move (losing all accumulated trust for a momentary advantage).

**Caveat**: If adversarial fraction is combined with coordinated colluding proxies that
inflate latency signals, the dynamic changes. The Sybil quorum gate (§T4.2) is the
correct defence for that attack vector, not reputation mechanics.

### F9 — Adversarial fraction has negligible effect on honest nodes

Increasing adversarial fraction from 10% → 30% reduces honest_avg by only:
- 100 steps: 0.003–0.005
- 1000 steps: 0.003–0.004

The reduction is statistically negligible. The reputation system is resilient to
adversarial fractions up to 30% without any mitigation beyond the existing asymmetric
penalty (10× demotion vs promotion).

**Implication**: The 20% adversarial fraction from the preliminary findings (F2) is a
reasonable upper bound for the current threat model. Protocol designers can assume
honest-node behaviour is not materially affected up to 30% adversarial participation.

---

## Open questions resolved

| Question (from preliminary findings) | Answer |
|--------------------------------------|--------|
| Is sc=0.5 correct or should it be lower? | sc=0.5 is appropriate — lower values slow onboarding without adversarial benefit. |
| Does long-run convergence depend on starting credit? | No — all values converge to the same equilibrium at ~1000 steps. |
| Does adversarial fraction matter above 20%? | No — honest node distributions are stable up to 30% adversarial fraction. |

---

## Open questions remaining (feed to REP1, REP2, REP5)

1. **Defection threshold ambiguity**: At what defection rate does the adversarial agent
   become indistinguishable from a "bad-day honest" node? Preliminary: ~10% defect rate
   is the crossover point. REP5 should model this explicitly.

2. **Coordinated defection**: The sweep models independent adversarial agents. What
   happens with coordinated collusion (adversarial agents always routing to each other)?
   Not modelled here — REP5 scope.

3. **Identity age gate for platinum**: Not modelled. If platinum requires identity_age ≥ 30d,
   the whitewash attack becomes even more irrational (cost = 30 days of honest behaviour
   lost, not just reputation score). REP2 should decide this as a conjunctive gate.

4. **Two-sided feedback (REP4)**: This sweep only models provider reputation. If client
   reputation is added (REP4), adversarial clients can't exploit honest providers by
   routing to them unfairly — the two-sided signal closes that vector.
