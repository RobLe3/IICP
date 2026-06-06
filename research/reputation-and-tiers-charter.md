# REP Track Charter: Reputation, Tiered Access, and Premium Services

**Issued**: 2026-05-17  
**Status**: Active — issues filed, execution queued

---

## Purpose

The REP track exists to design, simulate, locally test, and eventually live-pilot a reputation-and-tier system for IICP. S.12 §5.1 already specifies reputation decay mechanics (λ=0.005/hr, floor=0.3, 200h idle cap), but the *inputs* to that decay — what moves reputation up, by how much, under what rules, and how reputation maps to tiers — remain unspecified. This track fills that gap.

Reputation in IICP is a behavior signal: it reflects what a node or client has actually done over its lifetime. This is its load-bearing property. If reputation can be purchased, transferred, or shortcut by payment, it stops being a useful signal and becomes a class indicator. The design must preserve the signal's independence from payment.

Premium services form a distinct, orthogonal axis. Some nodes or clients may offer or consume paid services. Credits buy access to those services. Payment does not change reputation. High reputation does not exempt a participant from paying for premium. These two axes — reputation earned, premium paid — are independent dimensions of the protocol, and the research track's designs must keep them cleanly separated.

## Scope

**In scope**: reputation mechanics (starting credit, update rules per outcome type, decay dynamics, score range), tier structure (discretization, transition rules, promotion/demotion asymmetry), premium-service taxonomy (candidate services, pricing models, gaming surfaces), two-sided feedback (client→node quality feedback, node→client compliance feedback, commit-reveal blinding), anti-whitewash design (identity-age conjunctive gates, durable identity binding), demotion-promotion asymmetry (fast for compliance violations, forgiving for quality), testing program (simulation → local dogfooding → live pilot).

**Out of scope**: implementing the system in production code (separate work after research converges); choosing the specific number of tiers (the research decides); defining specific premium services beyond a taxonomy (the research decides what catches on); cryptographic countermeasures beyond what the feedback mechanism requires; penetration testing the live network.

## Principles

**Principle 1 — Reputation is earned, never purchased.** Reputation reflects behavior. It cannot be bought, transferred, or shortcut by payment. This is the load-bearing property that makes reputation a useful signal. Any design that allows reputation to be purchased breaks the signal and turns it into a class indicator.

**Principle 2 — Premium services are paid, never reputation-substituting.** A separate, orthogonal axis. Credits buy access to specific paid services that some nodes or clients offer. Paying does not change reputation. High reputation does not exempt you from paying for premium. These are two independent dimensions of the protocol.

**Principle 3 — Forgiving by default, decisive on protocol violations.** Promotion is readier than demotion for quality signals. Demotion is fast and decisive for compliance violations (failure to honor declared price per ADR-019, signature mismatch, refusal to serve under valid intent, payment-protocol violation). The asymmetry is intentional: quality is noisy and forgiving demotion preserves cooperation; compliance is testable against the spec and decisive demotion preserves protocol integrity.

**Principle 4 — Two-sided and symmetric.** Same mechanics apply to nodes and to clients. Both have reputation. Both have tiers. Both can be demoted for compliance failures. The compliance axes are different per side (clients can't violate node-side rules and vice versa), but the system structure is symmetric.

**Principle 5 — Cold-start without ossification.** New identities (node or client) enter with a known starting credit (initial value to test, candidate default 50/100). They are immediately routable, just at moderate confidence. The system must not require established reputation to participate, but it must reward established reputation enough that whitewash attacks via identity reset are unattractive.

**Principle 6 — Measure before shipping.** The design is validated by simulation, then local tests against the actual dogfooding mesh, then a small live pilot. Live behavior change to the production network only happens after simulation and local converge on a design and the maintainer reviews findings.

## Tracks

| Issue | Title | Phase |
|-------|-------|-------|
| REP1 | Reputation mechanics and starting credit | simulation |
| REP2 | Tier structure and transition rules | simulation |
| REP3 | Premium services taxonomy | design only |
| REP4 | Two-sided feedback collection | design + local-test stub |
| REP5 | Whitewash and adversarial scenarios — modeling | simulation |
| REP6 | Simulation harness, local pilot, and live-readiness gate | simulation + local |

## Cross-references

- **Provider-selection track (R1-R7)**: protocol/policy boundary, multi-path execution, adversarial robustness. REP1 cross-references R1 (protocol/policy boundary). REP5 cross-references R5 (adversarial robustness). REP6 cross-references R4/R5/R6 (simulation harness, adversarial scenarios, multi-path execution).
- **ADR-019**: declarative pricing — premium services declare their prices the same way nodes declare any price. REP3 (premium services taxonomy) must not require protocol fields beyond ADR-019.
- **ADR-013**: federated control plane trust tiers — the REP tier system extends to individual identities; ADR-013 covered directory operator tiers. REP2 explicitly distinguishes individual identity tiers from directory operator trust tiers.
- **ADR-026** (this instruction): two-sided reputation as earned signal — the normative anchor for Principles 1 and 4.
- **ADR-027** (this instruction): premium services as paid axis — the normative anchor for Principle 2.
- **S.12 §5.1**: existing reputation decay model — REP track designs the inputs and the tier-mapping that sit above the decay model.
- **ADR-021**: identity slot — whitewash defense depends on durable identity binding (REP2 conjunctive transition rule includes identity_age).

## Testing program

Each REP issue identifies its testing phase:

1. **Simulation** (REP1, REP2, REP5, REP6): Python harness building on the provider-selection track's R4/R5 simulation harness. Network sizes: 100, 1000, 10000. Three independent seeds per scenario. Results report mean and spread.
2. **Local dogfooding** (REP6): Shadow mode against the 7-node dogfooding mesh. Record what the reputation system *would* do given observed job outcomes without changing live behavior. Compare shadow decisions to current behavior.
3. **Live pilot**: Maintainer-gated. Only after simulation and local converge on a design with no catastrophic adversarial failures and the maintainer signs off.

## Status

Charter created 2026-05-17. Issues REP1 through REP6 filed. ADR-026 (two-sided reputation) and ADR-027 (premium services axis) created as stubs. Execution order: maintainer triages.

**Context anchor**: STATE.md commit `a7fd2bf`, FORGE-5 C4_CONVERGED (composite 93.62, iter 57), Sentrux 7151, active_nodes=7, S.12 v0.6.0 normative (§5.1 reputation decay), ADR-013 Draft (federated control plane, hybrid trust), ADR-019 Accepted (declarative pricing).
