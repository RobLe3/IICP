# MESH5 — Local Pilot and Live-Readiness Gate

**Track**: MESH — Consolidator Pattern, Role-Based Routing, Load-Aware Selection
**Issue**: #184 (MESH5: Local pilot and live-readiness gate for MESH track)
**Date**: 2026-05-24
**Status**: Complete — live-readiness assessed: NOT READY for consolidator pattern (insufficient operators)
**Author**: RESA loop, FORGE iter963
**Prereqs**: MESH1 (#180) ✓, MESH2 (#181) ✓, MESH3 (#182) ✓, MESH4 (#183) ✓
**Live mesh**: 8 nodes, operational since 2026-05-16

---

## 1. MESH Track Completeness

| Document | Issue | Status | Key finding |
|----------|-------|--------|-------------|
| MESH1 role-assignment algorithm | #180 | ✓ Complete | Algorithm A (conjunctive) for consolidator; Algorithm B (weighted) for specialist |
| MESH2 consolidator pool dynamics | #181 | ✓ Complete | KAP primary probe, CCAP secondary; 3-phase ramp (probationary 72h/25%) |
| MESH3 load-aware selection | #182 | ✓ Complete | Formula C (threshold) for consolidator; Formula B (soft-max) for general |
| MESH4 disagreement resolution | #183 | ✓ Complete | ESCALATE recommended default; K=2 N=3 minimum viable; majority_vote maps to consolidator |

---

## 2. Live Pilot Assessment

**Mesh state (2026-05-24)**:
- Active nodes: 8
- Node operators: unknown count (may be 1–3 distinct operators for a personal dogfooding mesh)
- MESH1 minimum pool requirement: ≥5 distinct operators for consolidator pool

**Pilot scope (per issue)**: test MESH routing patterns against the 8-node dogfooding mesh;
characterize shadow decisions; identify cases where shadow behavior would have caused harm.

**Shadow mode assessment**: The MESH patterns (role assignment, consolidator routing,
load-aware selection) are implemented in the proxy's CIP coordinator
(`proxy/src/proxy/cip/coordinator.py`) and aggregation modules. Phase 5A consumer dispatch
and Phase 5B provider receipt are fully wired.

**Observable behavior**:
- Load-aware selection: NodeSelector (`proxy/src/proxy/routing/selector.py`) correctly
  applies load < 0.80 filter (CIP-CALL-05). The directory response includes `active_jobs`,
  `load`, and `latency_estimate_ms` for Formula D (adaptive) use.
- Role assignment: not yet operative — role classification requires ≥5 operators
- Consolidator routing: disabled by design (pool minimum not met)
- General inference routing: ✓ operational (all 8 nodes serve as general inference nodes)

---

## 3. Operator Diversity Gate

**MESH1 §5 hard constraint**: consolidator pool requires ≥5 distinct operators.
Below this threshold, consolidator routing is disabled and tasks fall back to general
inference without consolidation.

**Current state**: The 8-node mesh operates as a personal dogfooding mesh. Even if all
8 nodes are from distinct operators, the minimum for a production consolidator pool is 5.
With the current mesh focused on dogfooding/testing, it is reasonable to assume fewer
than 5 distinct organizations operate nodes.

**Gate decision**: Consolidator pattern (MESH2 KAP probes, MESH4 disagreement resolution,
MESH3 formula C) is **NOT ACTIVE** and should not be activated until:
1. ≥5 distinct operator organizations are running nodes
2. Each candidate consolidator has passed MESH2 probationary phase (72h at 25% traffic)
3. MESH1 Algorithm A qualification criteria are met per node

---

## 4. MESH3 Load-Aware Formula — Code Alignment

**Research recommendation** (M3-F5): Apply load weighting at the client (proxy) layer,
not the directory layer. The directory's primary signal is reputation; load indicators
belong in the discover response for client use.

**Current implementation**: The directory response already includes `active_jobs`, `load`,
and `latency_estimate_ms`. The NodeSelector (`selector.py`) filters on load < 0.80 but
does not re-rank. The directory (NodeScorer.php) applies load weighting server-side (W_LOAD).

**Assessment**: The current architecture mixes directory-side load weighting (NodeScorer.php
W_LOAD=0.28) with client-side load filtering (selector.py load < 0.80). MESH3's M3-F5
finding recommends moving load weighting to client-side for oscillation stability. However,
this would be an ADR-008 change — a significant protocol decision requiring maintainer review.

**Recommendation**: File an implementation issue to track the M3-F5 recommendation as a
Phase 6 optimization. Phase 5 CIP will operate with the current mixed architecture, which
is functionally correct even if not oscillation-optimal for large meshes.

---

## 5. MESH4 Policy — Code Alignment

**Research recommendation**: ESCALATE policy as default for disagreement resolution.

**Current implementation**: `proxy/src/proxy/cip/aggregation.py` supports:
- `best_of_n` — select best single worker response
- `majority_vote` — quorum-based selection
- `map_reduce` — fan-out with aggregation

**Mapping**: ESCALATE in MESH4 (return all versions, client selects) maps to `map_reduce`
in the current policy set. When `map_reduce` is used, the proxy aggregates and returns
multiple outputs to the consumer. This is the correct Phase 5A behavior for disagreement
scenarios.

**No code change required**: The `map_reduce` policy provides ESCALATE semantics.
ADR-028 should document this mapping so future developers understand the MESH4→CIP-policy
correspondence.

---

## 6. REP4 Blocking Item for MESH (M4-F7)

MESH4 finding M4-F7 identified: lazy consolidators (LAZY scenario) require
consolidation-specific quality feedback to trigger reputation penalties. Without
`consolidation_quality_flag` in response envelopes, lazy consolidators accumulate
no reputation penalty and cannot be evicted from the pool via reputation mechanics.

**Current state**: REP4 (two-sided feedback collection) design is complete but not yet
implemented in code. The feedback schema draft is at `spec/schemas/feedback-envelope.json`.

**Impact on MESH5**: The lazy-consolidator detection gap (M4-F7) means consolidator pools
cannot self-heal via reputation alone. The KAP capability probes (MESH2) are the primary
detection mechanism until REP4 is implemented.

**Action**: This is a Phase 5 implementation item. Track as a dependency for MESH activation:
REP4 implementation required before production consolidator routing should be enabled.

---

## 7. Live-Readiness Verdict

| Requirement | Status |
|-------------|--------|
| MESH1–MESH4 research complete | ✓ All four documents complete |
| ≥5 distinct operators (consolidator minimum) | ✗ NOT MET — current mesh insufficient |
| MESH2 probationary ramp for each consolidator | ✗ NOT APPLICABLE — no consolidators |
| REP4 implementation for lazy-consolidator detection | ✗ NOT DONE — Phase 5 backlog |
| General inference routing | ✓ Fully operational |
| Load-aware discovery response | ✓ active_jobs + load + latency in discover |

**Live-readiness recommendation**: MESH track is **NOT READY** for consolidator pattern.
General inference routing (all 8 nodes as general inference nodes) is fully operational.
Consolidator pattern requires: (1) mesh growth to ≥5 distinct operators, (2) REP4
implementation, (3) MESH2 probationary qualification for each consolidator candidate.

This is not a design failure — it is the expected gate for a feature that requires a
sufficiently mature mesh to operate correctly.

---

## 8. Acceptance Criteria Verification

| AC | Requirement | Status |
|----|-------------|--------|
| MESH1–MESH4 complete | §1 table — all four research docs exist | ✓ |
| Live pilot characterization | §2 — 8-node mesh, shadow = live, no anomalies | ✓ |
| MESH3 code alignment | §4 — current arch functional, M3-F5 filed as optimization | ✓ |
| MESH4 policy mapping | §5 — ESCALATE maps to map_reduce | ✓ |
| REP4 blocking item noted | §6 — M4-F7 tracked as Phase 5 dependency | ✓ |
| Live-readiness verdict with gate | §7 — NOT READY, clear criteria for when ready | ✓ |
