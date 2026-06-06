# REP5 — Adversarial Modeling and Whitewash Attack Surface

**Track**: REP (Reputation & Tiered Access)  
**Issue**: #171 (REP5: Whitewash and adversarial scenarios — modeling)  
**Date**: 2026-05-18  
**Author**: RESA loop, iter 5  
**Related findings**: F7 (adversarial equilibrium), F8 (zero whitewash resets), F9 (adversarial fraction resilience)  
**Simulation**: `research/simulation/rep/identity_age_gate.py`, 3000 steps, size=200

---

## 1. Attack taxonomy

This document characterizes two distinct adversarial agent archetypes discovered
through RESA simulation:

### Archetype A — Random Defector (modeled in F7/F8/F9)

Defects with probability p_defect regardless of reputation tier. Interleaves honest
and defecting behaviour uniformly.

- **Parameters**: 30% defect rate, 85% success rate on honest tasks
- **E[Δ]** per task: −0.0143 (net negative — drives toward reputation floor)
- **Equilibrium**: ~0.318 (near floor, silver/bronze boundary)
- **Whitewash behaviour**: Whitewashes from floor/silver, never from platinum
- **Threat level**: LOW — self-defeating design; the attack cannot sustain above silver

### Archetype B — Strategic Defector (modeled in this document — F10/F11/F12)

Acts fully honest until routing-eligible platinum tier, then exploits platinum routing
priority. Whitewashes when reputation begins to fall. This is the threat model that
the identity-age gate (REP2 §gate) is designed to counter.

- **Parameters**: 92% success rate (fully honest build phase), exploit at platinum
- **E[Δ] (build phase)**: positive — can reach platinum in ~350-400 steps
- **Whitewash behaviour**: Whitewashes from platinum after exploiting
- **Threat level**: MEDIUM — reaches platinum reliably without gate; gate is the primary defense

---

## 2. Findings

### F10 — Identity-Age Gate Reduces Platinum Whitewash Frequency 13×

**Source**: `identity_age_gate.py`, 3000 steps, size=200, seeds 0-2  
**ADR impact**: REP2: identity-age gate is validated as the primary defense against strategic defectors

| Condition | AF=0.10 | AF=0.20 | AF=0.30 |
|-----------|---------|---------|---------|
| Without gate — whitewash cycles / agent | 39 | 39 | 39 |
| With gate (720h) — whitewash cycles / agent | 3 | 3 | 3 |
| **Reduction factor** | **13×** | **13×** | **13×** |

The reduction factor is independent of adversarial fraction — it is determined solely
by the ratio of total steps to gate threshold (3000 / 720 ≈ 4.2 cycles max).

### F11 — Gate Is Efficiency Tax, Not Full Deterrent (at current step count)

**Source**: same simulation  
**ADR impact**: REP2: gate requires validation against real time horizons

At 3000 simulated steps, a strategic adversarial agent completes ~3 whitewash cycles:

1. Build reputation to platinum (≈350 steps)  
2. Build identity age to ≥720h (≈370 more steps)  
3. Exploit platinum routing for 1-2 tasks, then whitewash  
4. Repeat

The gate does not make the attack economically irrational — it taxes the attacker's time
but does not eliminate the strategy. Extended gate windows (e.g., 90d instead of 30d)
or combination with other defenses (quorum gate, attestation) reduce feasibility further.

**Design implication**: The identity-age gate (720h) is necessary but not sufficient.
It should be combined with:
- Sybil quorum gate (T4.2, ≥3 distinct proxies) — limits rapid reputation inflation
- Reputation decay (§5.1) — idle identity costs reputation
- Rate limiting on new node registrations — raises Sybil creation cost

### F12 — Gate Eliminates Adversarial Presence in Platinum Routing Pool

**Source**: same simulation  

At all adversarial fractions tested (10–30%), zero adversarial agents remain
routing-eligible at platinum tier at simulation end with the gate active
(`adv_platinum_eligible_final = 0`).

Without the gate: 1 adversarial agent in platinum routing pool at end (AF=0.20, 0.30).

This is the key operational benefit: the gate prevents adversarial nodes from holding
platinum routing status persistently. Even when an adversarial agent reaches platinum,
it whitewashes immediately — yielding platinum status for only ≈1-2 steps before reset.

---

## 3. Threshold ambiguity zone

From F7: adversarial agents (Archetype A) equilibrate at ~0.318 — above the floor (0.30)
but below the silver threshold (0.40). This creates a **threshold ambiguity zone**
between 0.30 and 0.40:

```
floor (0.30) ─────── ambiguity zone ─────── silver (0.40)
                 adversarial equilibrium
                       ~0.318
```

Nodes in this zone:
- Are not routing-eligible at silver or above
- Receive tasks only if directories route to bronze nodes
- Cannot improve reliably due to negative E[Δ] (further defections push toward floor)

Design implication: the tier thresholds in REP2 SHOULD place the silver/gold boundary
above the expected adversarial equilibrium. Current candidate (silver=0.40) is correct —
Archetype A adversarial nodes naturally self-exclude from silver routing.

---

## 4. Open questions resolved by this document

| Q | Question | Resolution |
|---|---------|-----------|
| Q2 | Does platinum gate on identity_age ≥ 30d make whitewash economically irrational? | Partially (F10, F11). Gate reduces frequency 13× and eliminates persistent platinum presence (F12). Not fully irrational — attacker completes 3 cycles/3000 steps. Combination with quorum gate and decay is recommended. |
| Q3 | At what defection rate does adversarial agent become indistinguishable from noisy-honest? | Archetype A at 30% defect rate equilibrates at ~0.318 — below silver, clearly distinguishable. Archetype B (strategic) is indistinguishable until platinum attempt. |

---

## 5. ADR impact

**REP2 (tier structure and transition rules)**:
- Identity-age gate should be set to ≥720h (30 days) — validated as reducing whitewash frequency 13×
- Gate is a necessary but not sufficient defense — must be combined with T4.2 quorum gate and T4.3 outlier detection (#187)
- Tier boundary silver=0.40 is validated — sits above adversarial equilibrium zone (~0.318)

**REP5 (#171)**:
- Archetype A (random defector) is self-defeating at current parameters
- Archetype B (strategic defector) is the primary threat; identity-age gate is the primary defense
- Combined defense stack: identity-age gate + quorum gate + decay + attestation receipt (#190)

---

## 6. Datasets

| File | Runs | Parameters | Description |
|------|------|-----------|-------------|
| `research/results/rep/identity_age/identity_age_gate_summary_steps1000.json` | 18 | 2 gate × 3 af × 3 seeds, 1000 steps, size=200 | Baseline (Archetype A) — no platinum whitewash events |
| `research/results/rep/identity_age/identity_age_gate_summary_steps3000.json` | 18 | 2 gate × 3 af × 3 seeds, 3000 steps, size=200 | Strategic adversarial (Archetype B) — confirms F10/F11/F12 |
