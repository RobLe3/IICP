# IICP Validation Methodology Disclosure

**Version**: 1.0.2
**Date**: 2026-06-29
**Status**: accepted
**Issue**: #16
**Authority**: Protocol Steward + Security Architect

---

## 1. Purpose

This document discloses the validation methodology underlying performance claims in
IICP v1.4.2 and corrects how those claims should be interpreted. It is required reading
before citing IICP performance figures in any public-facing context.

---

## 2. What v1.4.2 Claims

Section 14 of IICP v1.4.2 states:
- "99.98% success rate (validated via neural network simulation)"
- "6.25M messages/second peak capacity"
- "< 50ms average routing latency"

Section 15 discloses the methodology:
- Neural network simulation with stochastic modelling
- Multi-layer feedforward networks model agent behaviour

---

## 3. What These Claims Actually Mean

These figures are **simulation-backed feasibility estimates**, not empirical measurements.

| What is claimed | What it actually is |
|----------------|---------------------|
| "99.98% success rate" | Predicted by a simulation model, not measured on a deployed network |
| "6.25M messages/second" | Theoretical peak from a stochastic simulation, not a load test result |
| "< 50ms routing latency" | Model prediction; no real-world measurement exists |

The simulation modelled agent behaviour and network topology using neural networks trained
on synthetic data. The methodology produces **plausibility arguments**, not production
benchmarks.

---

## 4. How to Use These Figures

### Permitted use

- "IICP's simulation model predicts < 50ms routing latency at moderate load"
- "Feasibility analysis suggests the protocol can scale to millions of messages/second"
- "Simulation results indicate high reliability is achievable with the defined retry policy"

### Prohibited use

- Citing these as measured production performance
- Using them as SLO baselines without empirical validation
- Presenting them as proof of production readiness

### Website policy (iicp.network)

The landing page and `/spec` page MUST NOT present these figures as empirical.
Any mention of performance estimates MUST link to `/research` and include the disclaimer:
*"These figures are derived from neural network simulation, not production measurement."*

---

## 5. Empirical Baseline (iicp.network PoC)

As the iicp.network reference implementation matures, actual measurements will be
documented here. The following baseline targets are set for Milestone 1:

| Metric | Target | How measured |
|--------|--------|-------------|
| `GET /v1/discover` p95 latency | < 100ms | k6 load test, 100 concurrent users |
| `POST /v1/heartbeat` p95 latency | < 50ms | k6 load test |
| Task submission overhead | < 20ms | pytest benchmark (excluding inference time) |
| Node expiry time | < 90s after last heartbeat | Integration test |

These will be measured against the Docker Compose stack before Milestone 1 gate closes.

---

## 6. Required v1.5 Changes

The following changes are required in the v1.5 spec draft to address this issue:

1. Rename Section 14 to "Simulation-Backed Performance Estimates (Non-Normative)"
2. Add to Section 14 header: *"The following results are derived from neural network
   simulation with stochastic modelling, not from empirical measurement of a deployed
   implementation. They represent feasibility estimates."*
3. Move performance claims to a clearly-labelled non-normative appendix.
4. Separate normative protocol sections from illustrative performance sections.

---

## 7. 2026-06-29 Research Evidence Addendum

The same evidence discipline now applies beyond the original v1.4.2 performance
claims. IICP research must label whether a statement is backed by design
rationale, simulation, controlled implementation tests, or live-network
observation. Public pages must not collapse those categories into a single
marketing claim.

Current research clarifications:

1. Reachability evidence MUST distinguish self-attested routes,
   directory-observed probes, and external signed probe receipts. In particular,
   IPv6 reachability is not directory-observed unless the probing runtime has
   verified IPv6 egress or a signed IPv6-capable worker supplies the evidence.
2. Relay research MUST distinguish accountless bootstrap tunnels from stable
   operator-controlled production endpoints. Accountless Quick Tunnel style
   endpoints are a low-friction fallback, not a production availability promise.
3. Reputation and trust tiers MUST be described as evidence signals. Minimum
   observation gates reduce overclaiming, but verified receipts and
   anti-self-dealing controls are still required before reputation can be
   treated as strong economic integrity proof.
4. Privacy claims MUST remain transitional when live key coverage is incomplete.
   Key-ready encrypted payload routing is not the same as universal
   confidentiality, and executing providers can still read prompts they execute.
5. Browser-native serving research MUST separate relay-backed provider mode
   from future WebRTC self-addressing. WebRTC requires a signaling contract
   before it can be treated as an implementation-ready transport.
6. Federation and Phase 6 claims MUST remain gated until Phase 5 security,
   relay, reachability, SDK adoption and privacy evidence are stable.

The public `/research` page should summarize these distinctions in plain
language and link detailed reports for expert readers.

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-05-14 | Initial draft — performance validation methodology, simulation vs. empirical distinction, disclosure requirements; closes issue #16 |
| 1.0.1 | 2026-05-15 | Added Changelog section (A6 spec cleanup) |
| 1.0.2 | 2026-06-29 | Added research evidence addendum for reachability, relay, reputation, privacy, browser serving and Phase 6 public-claim discipline |

---

## Sign-off

**Protocol Steward**: Disclosure required before any public mention of IICP performance
figures. v1.5 spec changes required per §6. ✓
**Security Architect**: Misleading performance claims create implementation risk.
Disclosure is a security-adjacent concern (false trust). ✓

Closes GitHub issue #16.
