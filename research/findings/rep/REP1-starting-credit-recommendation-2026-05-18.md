# REP1 — Starting Credit Recommendation

**Track**: REP (Reputation & Tiered Access)  
**Issue**: #167 (REP1: Reputation mechanics and starting credit)  
**Date**: 2026-05-18  
**Author**: RESA loop, iter 5  
**Evidence basis**: F4 (silver/gold boundary positioning), F6 (convergence invariance)  
**Simulation**: `research/simulation/rep/harness.py` preliminary runs (iter69) + adversarial sweep (iter73)

---

## Recommendation

**Starting credit = 50/100 = 0.50 (normalised)**

This is the value that SHOULD be used as the default reputation for newly registered nodes.

---

## Evidence

### F4 — Positioning at silver/gold boundary (onboarding UX)

New agents starting at 0.50 begin between the silver threshold (0.40) and the gold
threshold (0.65):

```
bronze (0.0) ──── silver (0.40) ──── new node (0.50) ──── gold (0.65) ──── platinum (0.85)
```

This means a new node is immediately routing-eligible at silver tier upon registration.
It is not privileged (not gold or platinum), but it is not in the penalty zone (below silver).

This gives new operators a meaningful starting position — their node can receive tasks
immediately — while requiring them to earn gold and platinum through demonstrated quality.

### F6 — Convergence invariance (security)

Adversarial sweep across starting_credit ∈ {0.30, 0.40, 0.50, 0.60}:
- At 1000 steps, all starting credits converge to the same equilibrium (~0.954 honest avg)
- Long-run reputation distribution is independent of starting_credit
- This means the choice of starting credit is a UX decision, not a security decision

Implication: a lower starting credit (e.g., 0.40 = silver floor) would not provide
meaningfully better security — long-run adversarial resilience is determined by the
penalty asymmetry (−0.05 vs +0.01), not by the starting position.

### Cross-track: F8/F10 confirm starting_credit does not enable whitewash

- F8 (Archetype A, random defector): adversarial agents starting at 0.50 never reach platinum
- F10 (Archetype B, strategic defector): adversarial agents can reach platinum but
  only through sustained honest behaviour — the starting credit is irrelevant since they
  would reach the same state from any starting_credit after enough steps

The identity-age gate (#187, REP2) is the defence against strategic defectors —
not a lower starting_credit.

---

## Decision

| Parameter | Value | Rationale |
|-----------|-------|----------|
| `starting_credit` | 50 / 100 = 0.50 | Silver routing from day 1; F6 confirms invariance; F8/F10 confirm it doesn't enable attacks |
| Tier at start | Silver (0.40–0.65 range) | Useful enough to receive tasks, not privileged |
| Security role | None | Security is handled by identity-age gate, quorum gate, penalty asymmetry |

---

## Open items for REP1 close

Before issue #167 can be closed, REP1 also requires:

1. **Delta values** (±bumps): currently +0.01/success, −0.05/failure — confirmed in F5
   (demotion asymmetry validation). These values are specified in `harness.py` and
   `directory/app/Models/Node.php` (`delta_success`, `delta_failure` constants).
   REP1 should formally ratify these values and record them in a spec note.

2. **Decay parameters**: λ=0.005/hr, floor=0.30, cap=200h idle — from S.12 §5.1.
   These should be confirmed as the normative defaults or documented as implementation-defined.

3. **First-task grace period**: Current design has no grace period — new nodes start
   immediately participating. Consider whether a "probation period" (e.g., first 10 tasks
   are shadow-rated only) is needed. REP2 should weigh in on this.

---

## ADR update (ADR-026)

ADR-026 currently states:
> "starting_credit = 50/100 is the candidate value, pending REP1 decision"

This document constitutes the REP1 recommendation. ADR-026 should be updated from
"candidate" to "recommended default" with this document as evidence.

Spec note for `spec/iicp-cooperative-inference.md` §5.1:
> `starting_credit = 0.50` — default for new nodes. Implementations MAY allow
> operators to configure a higher starting credit for nodes with off-protocol
> trust relationships, but MUST NOT exceed 0.75 (below gold threshold) without
> explicit governance approval.
