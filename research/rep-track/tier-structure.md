# REP2 — Tier Structure Design

**Track**: REP (Reputation & Tiered Access)  
**Issue**: #168 (REP2: Tier structure and transition rules)  
**Date**: 2026-05-18  
**Status**: Design complete — pending Protocol Steward ratification  
**Author**: RESA loop, iter8  
**Simulation evidence**: `research/simulation/rep/harness.py`, identity_age_gate.py, F1–F16  
**Findings**: `research/findings/rep/REP2-tier-boundaries-recommendation-2026-05-18.md`

---

## 1. Recommended Tier Design

**Decision: 4 tiers (Bronze/Silver/Gold/Platinum)**

| Tier | Reputation threshold | Routing access | Notes |
|------|---------------------|----------------|-------|
| Bronze | ≥ 0.00 | Limited | Default for new nodes |
| Silver | ≥ 0.40 | Standard | Starting credit 0.50 places new nodes here |
| Gold | ≥ 0.65 | Full | Reachable in ~39 honest steps from start |
| Platinum | ≥ 0.85 AND identity_age ≥ 720h | Premium | Conjunctive gate prevents whitewash |

**Starting credit 0.50 placement**: New nodes start at the silver/gold boundary
(above silver threshold 0.40, below gold threshold 0.65). They receive routing
access from step 1 but must earn gold through honest work.

---

## 2. Platinum Identity-Age Conjunctive Gate

The platinum routing tier requires BOTH conditions to hold simultaneously:
1. `reputation_score ≥ 0.85`
2. `identity_age_hours ≥ 720` (30 calendar days)

**Rationale**: Reputation alone is insufficient for platinum because it can be
accumulated quickly (≈37 steps at max task rate). The 720h clock creates a time
lock that cannot be accelerated by task volume.

**Key property**: Demotion does NOT reset `identity_age_hours`. Identity age is a
monotonically increasing clock tied to the identity credential, not to tier status.
A node demoted from platinum retains its age; it just loses the routing tier label
until reputation recovers.

**Whitewash**: Resetting identity (creating a new credential) resets `identity_age_hours`
to 0. A whitewashed node cannot access platinum routing for 720h regardless of
reputation score.

**Evidence (F10/F11/F12)**:
- F10: Gate reduces whitewash cycles 13× (39 → 3 cycles per agent per 3000 steps)
- F11: Gate is an efficiency tax, not a full deterrent (3 cycles remain). Combined
  defenses required: gate + quorum + attestation.
- F12: Gate eliminates adversarial presence in the platinum routing pool at simulation
  end — zero adversarial agents hold routing-eligible platinum status with gate active.

---

## 3. Candidate Tier Count Justification

**Why not 2 tiers (provisional/established)**:
- Insufficient routing granularity for the REP3 premium services taxonomy
- Loses the silver intermediate state that new nodes naturally occupy

**Why not 5+ tiers**:
- Simulation (F1) shows 4 tiers produces stable distributions at 100/1k/10k scale
- More tiers increase threshold-gaming risk (Goodhart's law)
- ADR-027 premium taxonomy fits naturally into the gold/platinum distinction

**Why 4 is right**: Bronze (new/low), Silver (active/reliable), Gold (established/trusted),
Platinum (premium/high-trust). The gold/platinum distinction supports premium service
routing (REP3) without over-engineering.

---

## 4. Tier Transition Rules

### Promotion (upward)

Promotion is **continuous and automatic** — no explicit trigger. When
`reputation_score` crosses the threshold, the tier label updates in the next
heartbeat evaluation. For platinum, both conditions (reputation + age) must hold.

**Speed**: A node at sc=0.50 can reach gold (0.65) in approximately 39 honest steps
at 85% task rate / 90% success rate. At the standard one step per hour cadence, this
is ≈1.6 days.

**No promotion ceremony**: Avoid explicit "promotion request" flows — they create
threshold-gaming opportunities and add protocol complexity.

### Demotion (downward)

Demotion is **immediate** — when `reputation_score` drops below a tier threshold,
the tier label changes at the next heartbeat evaluation.

**Identity age is NOT reset on demotion**: A node demoted from platinum retains its
720h identity age. Reputation recovery (typically 2–5 steps of honest work from a
−0.05 penalty) can restore the node to platinum without re-waiting the 720h clock.

**Asymmetry**: Demotion is faster than promotion (−0.05/failure vs +0.01/success).
This prevents tier levels from being treated as "banked safety margin." Nodes near
a tier boundary must maintain consistent quality.

---

## 5. Threshold Values — Evidence and Calibration

| Threshold | Value | Calibration notes |
|-----------|-------|------------------|
| Silver lower bound | ≥ 0.40 | E[rep at floor+decay] ≈ 0.318 for 30% defectors (F7); adversarial nodes equilibrate below 0.40, confirming this as the minimal honest threshold |
| Gold lower bound | ≥ 0.65 | Starting credit 0.50 + ≈39 steps of honest work; at this level, nodes have demonstrated consistent task completion |
| Platinum lower bound | ≥ 0.85 | High-trust threshold; 0.954 avg for fully honest network, so 0.85 ≈ P30 of honest equilibrium distribution |
| Identity-age gate | ≥ 720h | ~30 days; 13× whitewash frequency reduction at this value (F10). A 90-day gate further reduces but was not simulated |
| Decay floor | ≥ 0.30 | Matches S.12 §5.1; nodes cannot decay below bronze through idle alone |

---

## 6. Adversarial Equilibrium Reference Points

| Archetype | Equilibrium rep | Tier | Notes |
|-----------|----------------|------|-------|
| Random defector (30% defect rate) | ~0.318 | Bronze | E[Δ]=−0.0143/task (F7) — clearly below silver |
| Strategic defector (honest until platinum) | ≥ 0.85 | Platinum (gated) | Identity-age gate prevents sustained platinum access (F12) |
| Honest node | ~0.954 | Platinum | Long-run equilibrium |

**Threshold ambiguity zone**: Nodes with defect rate 10–15% may equilibrate near the
silver/gold boundary (0.50–0.65 range). These are indistinguishable from noisy-honest
nodes at moderate observation windows. Not a design failure — quorum gate and outlier
detection (§T4.3) provide additional signals.

---

## 7. Cross-reference to ADR-013 (Federated Trust Tiers)

ADR-013 defines trust tiers for directory operators: Seed → Replica → Gossip. These
are distinct from REP2 node tiers but share the same principle: tiers are earned
through demonstrated behavior, not purchased or assigned. The two systems do not
interfere — a node's reputation tier (REP2) is orthogonal to the directory
operator's trust tier (ADR-013).

---

## 8. Validation Summary

| Criterion | Evidence | Status |
|-----------|---------|--------|
| Candidate tier counts evaluated | §3 (2/3/5 analyzed; 4 recommended) | ✓ |
| Tier boundaries documented with calibration | §5 table | ✓ |
| Transition rules: promotion continuous, demotion immediate | §4 | ✓ |
| Identity-age conjunctive gate for platinum | §2, F10/F11/F12 | ✓ |
| Demotion asymmetry | §4 (immediate vs slow rise) | ✓ |
| Cross-reference to ADR-013 | §7 | ✓ |
| Adversarial equilibrium reference points | §6, F7 | ✓ |
| Scale invariance validated (F1) | F1 | ✓ |

**Remaining for Protocol Steward ratification**: formal adoption of threshold values
(silver=0.40, gold=0.65, platinum=0.85, age-gate=720h) as normative defaults in
spec/iicp-cooperative-inference.md §5.1.1. Current state: PENDING markers in spec.
Remove PENDING markers only after Protocol Steward approves these values.
