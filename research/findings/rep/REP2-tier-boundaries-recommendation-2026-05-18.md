# REP2 — Tier Structure and Transition Rules: Recommendation

**Track**: REP (Reputation & Tiered Access)  
**Issue**: #168 (REP2: Tier structure and transition rules)  
**Date**: 2026-05-18  
**Author**: RESA loop, iter 6  
**Evidence basis**: F1 (scale invariance), F2 (adversarial isolation), F5 (demotion asymmetry), F7 (adversarial equilibrium), F10/F12 (identity-age gate validation)

---

## Recommendation

### Tier thresholds (recommended)

| Tier | Threshold | Rationale |
|------|-----------|-----------|
| **Bronze** | ≥ 0.00 | All registered nodes — baseline routing available |
| **Silver** | ≥ 0.40 | Above adversarial equilibrium zone (~0.318); new nodes start here (starting_credit=0.50) |
| **Gold** | ≥ 0.65 | Demonstrated sustained quality; eligible for QoS-preferred routing |
| **Platinum** | ≥ 0.85 | Elite tier; full routing preference; gated by identity-age (≥720h) |

These are the values used throughout the simulation harness and confirmed consistent with the
simulation findings. This document constitutes the REP2 recommendation to finalize these values.

### Identity-age conjunctive gate (recommended)

**Platinum routing eligibility** requires BOTH:
1. `reputation >= 0.85`
2. `identity_age_hours >= 720` (30 calendar days of activity)

Rationale: F10 confirms this gate reduces strategic whitewash frequency 13×. F12 confirms
it eliminates adversarial agents from the platinum routing pool. F11 confirms it is a
necessary but not sufficient defense (combined with quorum gate and outlier detection).

### Transition rules (recommended)

**Promotion** (reputation increasing):
- Occurs continuously — reputation is not a step function; tiers reflect current score
- No cooldown on promotion — a node earns its tier as it accumulates quality outcomes

**Demotion** (reputation decreasing):
- Occurs immediately when reputation crosses a threshold downward
- **Identity-age is NOT reset on demotion** — demotion is a reputation event, not an identity event
- A demoted platinum node retains its identity_age_hours; it can re-promote to platinum without
  waiting another 30 days (only whitewash resets identity_age)

**Whitewash reset** (intentional identity change):
- Reputation resets to starting_credit = 0.50
- Identity_age_hours resets to 0
- New identity must accumulate 720h before reaching platinum routing eligibility

---

## Evidence summary

### F1 — Scale invariance
Tier distributions are stable across 100/1k/10k agents at 100 steps. The tier threshold
values produce consistent routing pools at any network size. Current thresholds are confirmed
as network-scale-invariant.

### F5 — Demotion asymmetry validation
10× asymmetry (−0.05 failure vs +0.01 success): 
- Honest nodes rise slowly, never fall to floor
- Non-compliant nodes fall rapidly 
- Tier boundary at silver=0.40 sits above the adversarial equilibrium (~0.318), ensuring
  adversarial nodes self-exclude from silver routing

### F7 — Adversarial equilibrium defines the "threat exclusion zone"
Adversarial agents (Archetype A, 30% defect rate) converge to ~0.318 — well below silver=0.40.
This means the silver threshold is appropriately calibrated to exclude random defectors from
quality-routing tiers.

The silver threshold MUST be above the adversarial equilibrium. Current silver=0.40 satisfies this.
If penalty rates change (ADR-023), the silver threshold should be re-validated.

### F10/F12 — Identity-age gate validates platinum protection
Gate reduces strategic whitewash frequency 13×; eliminates persistent adversarial platinum presence.
720h (30 days) is validated as the correct gate window for the 3000-step simulation horizon.
Longer windows (90 days) are not yet tested but would reduce whitewash cycles further.

---

## Parameters to finalize in REP2 issue closure

Before #168 can be closed, the following parameters need explicit ratification:

| Parameter | Candidate value | Evidence | Status |
|-----------|----------------|---------|--------|
| `bronze_threshold` | 0.00 | All nodes | Ready |
| `silver_threshold` | 0.40 | F5, F7 | **Recommended** |
| `gold_threshold` | 0.65 | F1, harness defaults | **Recommended** |
| `platinum_threshold` | 0.85 | F10/F12 (gate tested here) | **Recommended** |
| `identity_age_gate_hours` | 720 | F10, F12 | **Recommended** |
| `starting_credit` | 0.50 (0–1 scale) | F4, F6, REP1 doc | **Recommended** (REP1) |
| `decay_lambda` | 0.005/hr | S.12 §5.1 | Ready (implement spec) |
| `decay_floor` | 0.30 | S.12 §5.1 | Ready (implement spec) |
| `idle_decay_cap` | 200h | S.12 §5.1 | Ready (implement spec) |
| `success_bump` | +0.01 | F5, harness | **Recommended** (REP1) |
| `failure_penalty` | −0.05 | F5, harness | **Recommended** (REP1) |

---

## ADR update needed

ADR-026 currently lists tier thresholds as "candidates". This REP2 recommendation upgrades them
to **recommended defaults** based on simulation evidence. The next SPEC iteration should:
1. Update ADR-026 §Decision to replace "candidate" with "recommended"
2. Add note about 90-day gate variant (not yet tested — coordinated collusion model RESA iter7)
3. Update spec/iicp-cooperative-inference.md §5 with final tier values (after REP1/REP2 formal closure)

---

## Open items for REP2 closure

- [ ] Formal Protocol Steward ratification of the above tier boundary table
- [ ] 90-day gate variant simulation (coordinated collusion — RESA iter7, RS2 gap)
- [ ] Spec update: `spec/iicp-cooperative-inference.md §5.1` — tier thresholds as normative values
- [ ] ADR-026 updated from "candidate" → "recommended" for all threshold values listed above
