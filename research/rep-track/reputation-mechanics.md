# REP1 — Reputation Mechanics Design

**Track**: REP (Reputation & Tiered Access)  
**Issue**: #167 (REP1: Reputation mechanics and starting credit)  
**Date**: 2026-05-18  
**Status**: Design complete — pending Protocol Steward ratification  
**Author**: RESA loop, iter8  
**Simulation evidence**: `research/simulation/rep/harness.py`, F1–F9, F16  
**Findings**: `research/findings/rep/REP1-starting-credit-recommendation-2026-05-18.md`

---

## 1. Starting Credit

**Decision**: `starting_credit = 0.50` (recommended default)

New nodes receive a normalised starting reputation of 0.50. This places them at the
silver/gold boundary — accessible to routing but not privileged over established nodes.

**Evidence**:
- F4: New agents at sc=0.50 start near the silver/gold boundary, receiving tasks
  without being excluded. Routing is possible immediately.
- F6: At 1000 steps, sc ∈ {0.3, 0.4, 0.5, 0.6} all converge to the same equilibrium
  (~0.954 avg among honest agents). Starting credit is long-run invariant — it affects
  onboarding experience, not final equilibrium.
- F16: Under routing concentration k=0–3, newcomers at sc=0.50 reach gold tier 73–100%
  of the time within 300 steps — no ossification.

**Security note**: Starting credit is NOT a security parameter. Whitewash defense relies
on the identity-age gate (§5 below), quorum gate (§T4.2), and penalty asymmetry (§3).

---

## 2. Score Range and Convention

- Range: [0.0, 1.0] normalised floating point
- Starting credit: 0.50 (new node)
- Compliance floor: 0.30 (hard floor — reputation cannot drop below this through task
  outcomes alone; compliance violations may additionally gate routing access)
- Ceiling: 1.00 (hard cap)
- The REP score IS the S.12 §5.1 reputation score — same variable, no separate track.
  REP1 defines the update rules for task-outcome events; S.12 §5.1 defines the idle decay.

---

## 3. Outcome Type → Reputation Delta Table

| Outcome type | Delta | Notes |
|-------------|-------|-------|
| Successful task (neutral quality) | +0.01 | Base success increment |
| Successful task (quality=q > 0) | +0.01 + q×0.005 | quality ~ N(0, 0.3); max contribution ≈ +0.015 |
| Task failure | −0.05 | Decisive, not catastrophic |
| Idle step (no task) | −reputation × (1−e^(−λ)) | S.12 decay, λ=0.005/hr, floor=0.30 |

**Compliance violations** (non-payment, fraud, blacklist): handled by directory policy
outside the task-outcome path — potential routing suspension independent of score.

**Parameters**:
```
success_bump     = +0.01
quality_coeff    = 0.005
failure_penalty  = -0.05
decay_lambda     = 0.005 (per hour idle)
decay_floor      = 0.30
```

---

## 4. Demotion/Promotion Asymmetry

**Asymmetry ratio**: 5× (failure penalty −0.05 vs success bump +0.01 base).

**Justification (Principle 3: "Forgiving by default, decisive on compliance violations")**:

- Slow honest rise: E[Δ] per honest step = 0.85 × (0.90 × 0.01 + 0.10 × (−0.05)) = +0.0038
  At this rate, a node goes from 0.50 → 0.65 (gold) in ≈39 steps. Attainable for
  legitimate nodes within hours of operation.
- Rapid non-compliant fall: An adversarial agent defecting 30% of the time converges to
  equilibrium 0.318 (near floor). E[Δ] = −0.0143/task (F7). This keeps adversarial
  nodes clearly below silver (≥0.40) without forcing them to floor immediately.
- Recovery: Damaged nodes (near floor) recover to above-baseline within 100 honest steps
  (F3). The system is forgiving but not exploitable.

**Validation (F5)**: The 10× ratio in the simulation (−0.05 vs +0.01) produces the
intended asymmetric behavior. The ratio is bounded; arbitrary increases would harm
new-entrant mobility.

---

## 5. Decay Formula (S.12 §5.1 alignment)

```
new_rep = max(floor, rep - rep × (1 - exp(-λ × idle_hours)))
```

Where:
- λ = 0.005/hr (decay rate constant)
- floor = 0.30 (minimum reputation from idle decay)
- idle_hours: hours since last task assignment
- Cap: max idle hours before decay hits floor = 200h (≈8 days)

**Relationship to S.12**: REP track uses S.12 §5.1's decay formula directly — the
reputation score in REP IS the S.12 reputation score. No separate signal.

---

## 6. Whitewash Defense

**Why identity reset is unattractive at sc=0.50**:

1. An adversarial agent reaching platinum (≥0.85) must then reset to 0.50 (bronze/silver
   boundary). The reset costs 0.35 reputation points — recovering to platinum requires
   ≈37 additional steps of honest work even at maximum task rate.
2. The identity-age conjunctive gate (REP2 §5) requires platinum nodes to have
   identity_age_hours ≥ 720 (30 days). Resetting the identity resets the age counter
   to zero. A new identity cannot access platinum routing regardless of reputation score
   until 720h have elapsed.
3. F8: In 72 runs (1000 steps), no adversarial agent ever reaches platinum via whitewash
   at current parameters. Random defectors self-defeat at E[Δ] = −0.0143/task.
4. F10: Strategic defectors (honest until platinum, then exploit) complete 39 whitewash
   cycles/3000 steps WITHOUT the gate; 3 cycles WITH the gate — 13× reduction.

**Combined defense stack**: identity-age gate (REP2) + quorum gate (§T4.2) + penalty
asymmetry (§4) + attestation receipt (#190).

---

## 7. Privacy

| Signal | Visible to | Notes |
|--------|-----------|-------|
| `reputation_score` | Requester (via /v1/discover) | Rounded to 2 decimal places |
| `tier` | Requester | Derived from score; routing tier may differ from actual tier (identity-age gate) |
| Raw task outcomes | Directory only | Not exposed via API |
| identity_age_hours | Directory only | Used for gate computation; not exposed |
| Feedback submissions | Commit-reveal; not exposed after reveal | REP4 design doc |

---

## 8. Validation Summary

| Criterion | Evidence | Status |
|-----------|---------|--------|
| Starting credit 0.50 documented with rationale | F4+F6, §1 | ✓ |
| Delta table (4 outcome types) | §3 table | ✓ |
| Demotion/promotion asymmetry justified | §4, F5, F7 | ✓ |
| Decay formula verified vs S.12 §5.1 | §5 | ✓ |
| Score range documented ([0.3, 1.0]) | §2 | ✓ |
| Whitewash defense explained | §6, F8, F10 | ✓ |
| Simulation validation (scale-invariant, adversarial) | F1-F9 | ✓ |

**Remaining for Protocol Steward ratification**: formal adoption of delta values
(+0.01/success, −0.05/failure, λ=0.005/hr, floor=0.30) as normative defaults in
spec/iicp-cooperative-inference.md §5.1. Current state: PENDING markers in spec.
