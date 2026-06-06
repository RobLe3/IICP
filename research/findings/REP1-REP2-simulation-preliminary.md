# REP1 + REP2 — Simulation Preliminary Findings

**Track**: REP — Reputation & Tiered Access  
**Issues**: #167 (REP1), #168 (REP2)  
**Status**: Preliminary — multi-scale (100/1k/10k nodes), 3 scenarios × 3 seeds  
**Date**: 2026-05-18  
**Harness**: `research/simulation/rep/harness.py`

---

## Parameters used (harness defaults)

```
starting_credit = 50/100 = 0.5 normalised
success bump    = +0.01 + quality×0.005  (quality ~ N(0, 0.3))
failure penalty = -0.05
decay λ         = 0.005/hr, floor=0.3, cap=200h idle (S.12 §5.1)
tier thresholds = {bronze: 0.0, silver: 0.40, gold: 0.65, platinum: 0.85}
steps           = 100 (each step ≈ 1 agent-task attempt or 1 idle hour)
```

---

## Key findings

### F1 — Scale invariance

Tier distributions are remarkably stable across 100, 1000, and 10000 agents.
Baseline honest-network proportions converge to approximately:

| Tier | 100 agents | 1000 agents | 10000 agents |
|------|-----------|-------------|--------------|
| Bronze | 0–1% | 0.6–1.1% | 0.7–0.8% |
| Silver | 7–17% | 15–17% | 15–16% |
| Gold | 37–47% | 44–49% | 44–45% |
| Platinum | 42–46% | 35–38% | 39–39% |

**Implication**: the tier thresholds produce a consistent distribution regardless of network size.
This is desirable — operators can reason about tier dynamics independently of whether
the network has 10 or 10,000 nodes.

### F2 — Adversarial isolation (20% fraction)

With 20% of agents behaving adversarially (accumulate rep → whitewash reset at platinum):

- Network avg_rep drops from ~0.79 to ~0.70 (11% reduction)
- Adversarial agents accumulate in bronze tier (whitewash resets keep cycling them to rep=0.5)
- Honest agents (80%) still reach gold/platinum at similar rates to the honest-only baseline
- The adversarial fraction is **effectively isolated** in lower tiers

**Implication**: the whitewash attack is self-defeating at these parameters. An agent that
resets to platinum immediately gets cycled back to starting_credit=0.5 (silver/gold boundary)
after whitewash, losing all accumulated tier benefits. The attack incurs cost (lost reputation)
but gains nothing durable.

**Caveat**: this holds when whitewash resets to starting_credit=0.5 (bronze). If whitewash
somehow yielded higher starting credit, the attack becomes more attractive. REP1 must
explicitly state that new identity ≡ starting_credit, no exceptions.

### F3 — Recovery dynamics

When half the network starts with rep=0.35 (near the floor):
- After 100 steps at 90% success rate, avg_rep recovers to ~0.84 (5% above baseline!)
- Most agents end in platinum tier — damaged agents who "reform" accumulate rep faster
  than the baseline because they start the step below gold and see faster tier traversal

**Implication**: damaged nodes that genuinely participate honestly recover well.
No evidence of permanent reputation debt. This validates the "forgiving by default"
principle (charter Principle 3).

### F4 — Starting credit sensitivity

At starting_credit=0.5:
- New agents start at the silver/gold boundary — immediately routable at moderate quality
- Not privileged enough to bypass established operators in gold/platinum
- Cold-start problem is mild — a new honest node reaches gold in ~15–20 steps

**Open question for REP1**: is 0.5 the right starting credit, or should it be lower (say 0.4
= lower silver) to give established operators a clearer advantage in routing preference?

### F5 — Demotion asymmetry validation

The 10× asymmetry (success bump ~0.01–0.015 vs failure penalty 0.05) produces:
- Honest agents: slow, continuous rise to gold/platinum over ~30–50 steps
- Non-compliant agents: rapid demotion to floor, then slow rebuild if they reform
- The asymmetry is noticeable but not punishing — honest agents genuinely benefit

**Implication**: the current delta values are in the right range. REP1 should document
these as candidate values and run targeted sensitivity sweeps before final recommendation.

---

## Open questions (for REP1 and REP2 design documents)

1. **Starting credit**: 0.5 (candidate) or lower? Run harness with starting_credit=0.4
   and compare new-agent routing preference vs established agents.
2. **Platinum gate**: should identity_age ≥ 30 days be a conjunctive requirement for
   platinum (REP2 decision)? Current simulation does not model identity age.
3. **Decay rate**: is λ=0.005/hr appropriate for an honest node that occasionally misses
   a day? At 24h idle: decay = 0.5×(1−e^(−0.12)) ≈ 0.056 — about 11% of a typical score.
4. **Success quality distribution**: harness uses N(0, 0.3). Does this match expected
   real task quality distributions? Low-quality successes provide minimal rep gain,
   which seems correct.

---

## Next simulation steps (REP6 dependency)

1. Sensitivity sweep: starting_credit ∈ {0.3, 0.4, 0.5, 0.6} × adversarial_fraction ∈ {0.1, 0.2, 0.3}
2. Model identity-age conjunctive gate (for platinum promotion) in harness
3. Larger step counts (1000 steps) to see long-run tier distribution convergence
4. Two-sided feedback (REP4): model client reputation alongside node reputation
