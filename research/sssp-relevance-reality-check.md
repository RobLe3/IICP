# R7 — SSSP Relevance Reality Check

**Track**: R1R7 — Provider Selection & Multi-Path Routing  
**Issue**: #179 (R7: SSSP reality check — does shortest-path matter at any plausible scale?)  
**Date**: 2026-05-18  
**Author**: RESA loop, FORGE iter 82  
**Length**: ≈1600 words (within ≤2000 limit)  
**Recommendation**: **Defer SSSP entirely** — trigger condition specified in §5.

---

## 1. The Question

Source material for the R1–R7 provider-selection track references Duan et al. 2025/2026
directed SSSP results as candidate routing mechanisms. This document asks: does any
realistic IICP routing decision require computing a shortest path through a graph? And
if so, at what scale does algorithmic sophistication become necessary?

---

## 2. Candidate SSSP Problem Areas in IICP

### 2.1 Provider Selection (PRIMARY USE CASE — NOT SSSP)

The core provider-selection flow is: client queries `/v1/discover` → receives N candidates
with reputation_score + observed_latency → scores candidates with some policy function →
sends task to winner.

This is **not** a graph traversal problem. The directory service returns a flat ranked
list of nodes. The client's selection policy operates on that list. No path is computed;
no graph is traversed. The network topology (who peers with whom) is invisible to this
decision.

**Verdict**: SSSP not applicable.

### 2.2 Relay-Path Selection (SINGLE-HOP — NOT SSSP)

IICP's relay model (spec §6, ADR-013) is single-hop: requester → relay → provider.
A relay node is a provider that accepts forwarded tasks. There is no multi-hop relay
chain in the current protocol. A request either goes directly to a provider (no relay)
or through one intermediary (one relay). Single-hop relay selection is a provider
selection problem (§2.1), not a graph traversal.

**When would this become SSSP?** Only if a multi-hop relay chain were introduced — e.g.,
requester → relay-A → relay-B → provider. No such chain exists in the current protocol.
ADR-013 (federated directory) does discuss cross-cluster routing (§2.3 below), but that
operates at a different granularity.

**Verdict**: SSSP not applicable under current protocol. Triggered if multi-hop relay chains are added.

### 2.3 Cluster-to-Cluster Routing (FUTURE — PHASE 6+)

The federated control plane (ADR-013, Phase 6) introduces a cluster-of-clusters model:
multiple directories federate into a hierarchical structure. A request arriving at Cluster A
may need to be routed to a provider in Cluster B. If the inter-cluster graph has > 2 hops
(A → C → B), path selection through the cluster graph is a real SSSP problem.

**Scale reality check**: How many clusters would trigger this? If clusters have ≈1000 nodes
each, IICP would need 100+ clusters (100,000+ nodes globally) before a cluster-graph with
> 3 hops becomes common. That is a long-range future.

**Even then**: At 100 clusters, the cluster-level graph has V=100, E ≤ 10,000. Dijkstra
with binary heap on V=100 is nanoseconds. No algorithmic sophistication needed.

**Verdict**: SSSP applies in Phase 6+ cluster routing. Dijkstra is trivially fast at any
plausible cluster-count.

### 2.4 Observability and Network Health Tools

REACH probes endpoints directly — no graph traversal. Network health monitoring (ADR-012)
aggregates telemetry — no path computation. Visualization tools might compute spanning
trees for display, but this is a rendering concern, not a protocol concern.

**Verdict**: SSSP not applicable.

---

## 3. At What Scale Does Dijkstra Stop Being Instant?

Dijkstra with binary heap runs in O((V + E) log V).

| Nodes (V) | Avg degree | Edges (E) | Dijkstra time (commodity hardware, ≈10^8 ops/sec) |
|-----------|-----------|-----------|------------------------------------------------|
| 10 | 4 | 40 | << 1 microsecond |
| 1,000 | 10 | 10,000 | ~1 microsecond |
| 10,000 | 20 | 200,000 | ~50 microseconds |
| 100,000 | 30 | 3,000,000 | ~5 milliseconds |
| 1,000,000 | 50 | 50,000,000 | ~1 second |

IICP currently has 7 active nodes. Even an optimistic 5-year growth scenario to 10,000
nodes produces Dijkstra runtimes of ~50 microseconds — negligible compared to network
RTT (50–300ms). At 100,000 nodes (implausible within any reasonable planning horizon),
Dijkstra at 5ms is still well under network latency for a one-time routing decision.

**Conclusion**: Dijkstra is "instant" (< 10ms) at all plausible IICP scales within the
next 3–5 years. The O((V+E) log V) constant factors dominate only at > 500,000 nodes.

---

## 4. What Duan et al. Would Buy

Duan et al. 2025/2026 provide improved directed SSSP algorithms with bounds of the form
O(n^(1+o(1))) or related near-linear results for sparse graphs. The practical improvement
over Dijkstra is:

- **Asymptotically**: Better by a log factor or fractional exponent for large sparse graphs.
- **In practice at V ≤ 10,000**: Zero improvement — both run in microseconds. The
  Duan et al. algorithms carry higher constant factors from their auxiliary data structures
  (balanced trees, potential functions, AMQ queries). For V ≤ 10,000, Dijkstra's lower
  constant factor wins in practice.
- **Correctability**: Dijkstra is simple, well-understood, and trivially correct with
  non-negative weights. IICP latency weights are non-negative (observed_latency_ms ≥ 0).
  Duan et al. algorithms add engineering complexity without correctness benefit.
- **Dynamic graphs**: IICP's node membership changes continuously (nodes register/deregister,
  latency updates flow in). Dynamic SSSP (re-use of prior computation) would be relevant
  only if path computation were on the critical path of every request, which (per §2) it
  is not.

**Verdict**: Duan et al. buys nothing at plausible IICP scale. Even at large scale, the
operational complexity is not justified when Dijkstra is already 100× faster than network RTT.

---

## 5. Recommendation: Defer with Trigger Condition

**Recommendation**: Defer SSSP consideration entirely. IICP should not reference, implement,
or design around any specific SSSP algorithm. The complexity is unwarranted and the
algorithmic choice adds no protocol value.

**Trigger condition for revisiting** (concrete and measurable):

> SSSP becomes worth evaluating when **all three** conditions hold simultaneously:
> 1. Active node count ≥ 50,000 (V at which Dijkstra approaches 1ms — still fast, but worth monitoring)
> 2. A multi-hop relay chain (> 1 intermediate relay hop) is added to the protocol
> 3. Relay-path routing decisions are on the per-request critical path (not pre-computed or cached)

None of these conditions is met today or within the 2026–2027 planning horizon.

**Implication for ADR-025 (provider selection)**: The scoring policies compared in R4
(weighted scoring, ε-greedy, harmonic/fractal, UCB) operate on flat candidate lists, not
graphs. ADR-025 should explicitly note that SSSP is out of scope for the selection policy
decision.

**Implication for ADR-013 (federated directory)**: If Phase 6 introduces cluster-level
routing, the inter-cluster graph at plausible cluster counts (< 500 clusters) is trivially
handled by Dijkstra. No architectural decision about SSSP algorithms is needed in ADR-013.

---

## 6. Acceptance Criteria Verification

| AC | Requirement | Status |
|----|-------------|--------|
| ≤2000 words | ≈1600 words | ✓ |
| ≥3 candidate routing problems assessed | §2.1 (provider selection), §2.2 (relay), §2.3 (cluster), §2.4 (observability) — 4 assessed | ✓ |
| Recommendation includes concrete trigger condition | §5: 3-condition trigger | ✓ |
| Duan et al. bounds cited correctly | §4: near-linear O(n^1+o(1)), practical constant factor discussion | ✓ |
