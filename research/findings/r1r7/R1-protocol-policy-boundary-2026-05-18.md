# R1 — Protocol/Policy Boundary for Provider Selection

**Track**: R1R7 — Provider Selection & Multi-Path Routing  
**Issue**: #173 (R1: Protocol/policy boundary for provider selection)  
**Date**: 2026-05-18  
**Author**: RESA loop, FORGE iter82  
**Length**: ≈1800 words (within ≤2000 limit)  
**ADR impact**: Expands ADR-025; identifies 5 follow-up gaps.

---

## 1. The Question

Before any selection algorithm is designed or simulated, we must establish what the
protocol must carry on the wire for any reasonable selection policy to function. Without
a clear boundary, there is risk of protocol-level prescriptions (hardcoded scoring weights,
mandated exploration algorithms) that would ossify the protocol and make alternative
client implementations non-viable. ADR-019 precedent: protocol carries substrate, client
carries policy.

Three dimensions:

- **PROTOCOL-REQUIRED**: Every conformant node MUST publish this; every conformant client
  MUST be able to consume it. Absence means the client cannot make a selection decision.
- **PROTOCOL-OPTIONAL-DECLARATIVE**: Nodes MAY publish this. Conformant clients MUST
  accept it if present; MAY use it in policy if present; MUST NOT require it for basic
  selection. Primarily self-reported; less trusted than PROTOCOL-REQUIRED.
- **CLIENT-INTERNAL**: Never transmitted. Purely a client implementation choice. Mandating
  this at protocol level would prevent client pluralism.

---

## 2. Classification Table

### 2.1 Capability Declarations

| # | Data Item | Classification | Rationale |
|---|-----------|---------------|-----------|
| C1 | Intent URN support list | PROTOCOL-REQUIRED | The single non-negotiable hard filter. A client cannot select a node without knowing what intents the node can handle. Without this, discovery is unusable. |
| C2 | Context window size (max tokens) | PROTOCOL-REQUIRED | Many inference intents carry context size requirements (from the intent URN's capability dimension). A node that cannot handle the required context is disqualified before scoring; client must be able to filter. |
| C3 | Model family / version | PROTOCOL-OPTIONAL-DECLARATIVE | Useful for capability matching but not universally required. Intent URNs encode required model family; the directory uses this for filtering. Self-reported, so carries lower trust than measured signals. |
| C4 | Modality support (text/image/audio) | PROTOCOL-REQUIRED | Intent URNs encode modality. Client must filter nodes that lack the declared modality. Absence makes multi-modal intents unroutable. |
| C5 | Privacy class (local-only, shared-infra, etc.) | PROTOCOL-REQUIRED | Some intents carry privacy class requirements (e.g., `privacy_class: local_only`). Client must be able to hard-filter. Without this, clients cannot enforce privacy-sensitive routing. |
| C6 | Capability proof staleness timestamp | **GAP-1** | Current spec has capability declaration fields but no attestation-freshness indicator. Stale capability declarations (node claims to support model X but hasn't been probed recently) are undetectable by clients. See §5, Gap 1. |

### 2.2 Quality and Performance Signals

| # | Data Item | Classification | Rationale |
|---|-----------|---------------|-----------|
| Q1 | Reputation score (normalized 0–1) | PROTOCOL-REQUIRED | The primary quality signal. Without it, selection degrades to random or price-only. REP track simulation (F1–F16) validates its properties. Client MUST be able to read it; selection algorithm determines how to use it. |
| Q2 | Tier classification (Bronze/Silver/Gold/Platinum) | PROTOCOL-REQUIRED | Discrete gate for routing access. Tier is not redundant with reputation score — it carries the identity-age conjunctive gate for Platinum (cannot be computed from score alone without identity age). Clients performing platinum routing MUST be able to filter by tier. |
| Q3 | Identity age (hours since first registration) | **GAP-2** | Required for client-side platinum tier verification (tier requires rep ≥ 0.85 AND identity_age ≥ 720h). Currently not in discover response. Directory tracks it; it must be published. See §5, Gap 2. |
| Q4 | Observed response latency (p50, p95 from heartbeat history) | PROTOCOL-REQUIRED | Key measured signal for both selection scoring (prefer lower latency) and load-aware selection (latency trending up signals load). Directory already tracks this from heartbeat timing. Must be published in discover response. |
| Q5 | Task completion count (historical) | PROTOCOL-OPTIONAL-DECLARATIVE | Useful proxy for experience level. Self-reported and easily inflated; lower trust than directory-tracked metrics. Directory-side: attested execution count computed from heartbeat history is more trustworthy but currently no standardized field. |
| Q6 | Task success rate | CLIENT-INTERNAL | Directory computes from heartbeat + telemetry. Currently aggregated into reputation score. Exposing raw success rate as a separate protocol field risks gaming; reputation signal is the right abstraction. |

### 2.3 Economic Signals

| # | Data Item | Classification | Rationale |
|---|-----------|---------------|-----------|
| E1 | Declared price per task (token/task/hour) | PROTOCOL-REQUIRED | Per ADR-019 — already in protocol. Client cannot respect budget constraints without it. |
| E2 | Price type identifier | PROTOCOL-REQUIRED | Per ADR-019 — already in protocol. Enables apples-to-apples budget comparison across different pricing models. |
| E3 | Currency/settlement mechanism | PROTOCOL-OPTIONAL-DECLARATIVE | ADR-019 explicitly out-of-scope for protocol. Nodes MAY declare settlement preferences; protocol does not mandate or interpret them. |

### 2.4 Availability and Load Signals

| # | Data Item | Classification | Rationale |
|---|-----------|---------------|-----------|
| A1 | Declared load / availability percentage | PROTOCOL-OPTIONAL-DECLARATIVE | Self-reported; cannot be verified by protocol. Useful as a hint for load-aware selection (MESH3) but lower trust than latency-derived load indicators. |
| A2 | Observed load indicators (latency trend, recent throughput) | PROTOCOL-REQUIRED | Measured by directory from heartbeat timings. More trustworthy than declared load. Needed for load-aware selection to prevent oscillation (MESH3 design hypothesis). Currently not in discover response as a formal field. **Covered by Gap 5.** |
| A3 | Queue depth (pending tasks) | PROTOCOL-OPTIONAL-DECLARATIVE | Self-reported. Nodes MAY expose this. Useful for load-balancing but easy to misreport. Selection policies SHOULD weight it less than observed latency. |

### 2.5 Identity and Trust Signals

| # | Data Item | Classification | Rationale |
|---|-----------|---------------|-----------|
| I1 | Node identity (public key per ADR-021) | PROTOCOL-REQUIRED | Foundation of all other signals. Without stable identity, reputation is meaningless (whitewash trivial). |
| I2 | Role assignment (general/specialist/consolidator) | **GAP-3** | Directory computes role assignments (per MESH track design). Client must be able to filter by role (consolidator pool vs. inference pool). Not currently in discover response as a formal field. See §5, Gap 3. |
| I3 | Signed capability/enrollment envelope (per ADR-024) | PROTOCOL-REQUIRED | Integrity substrate. Clients cannot verify claim provenance without signed envelopes. Already in protocol via ADR-024. |

### 2.6 Multi-Path Substrate

| # | Data Item | Classification | Rationale |
|---|-----------|---------------|-----------|
| M1 | Multi-path declaration in task submission | **GAP-4** | When the client fans out the same task to N nodes, each node should know it is in a multi-path set. This affects pricing (node may charge less for multi-path because it doesn't bear full responsibility) and behavior (node returns a fragment identifier). Currently no such field in task submission schema. See §5, Gap 4. |
| M2 | Fragment ID in task response | CLIENT-INTERNAL pending R2 | R2 (multi-path inference requirements) will determine whether fragment IDs are a protocol primitive or client-managed. Premature to classify. R2 follow-up. |

### 2.7 CLIENT-INTERNAL — Never on Wire

The following are purely client implementation choices. Mandating any of these at the
protocol level would prohibit client pluralism and ossify selection policy.

| Item | Why client-internal |
|------|---------------------|
| Scoring weights for weighted scoring policy | Policy choice; alternative clients may use different weights |
| Exploration rate ε for ε-greedy | Tuning parameter; may vary by client strategy |
| UCB confidence parameter | Tuning parameter |
| Harmonic perturbation amplitude | Tuning parameter; R4 tests this against null-noise baseline |
| Local blacklist (nodes client refuses to use) | Client policy; protocol has no opinion |
| Budget allocation across layers (inference vs. consolidation) | Client policy per intent type |
| Selection history / stateful exploration state | Per-client runtime state; not transmitted |
| Tier boundary values | Reference-client defaults (REP2 research); not mandated at protocol level |
| Reputation update formula | Reference-client defaults (REP1 research); not mandated at protocol level |

---

## 3. Alignment with R7 Finding

R7 (SSSP reality check) is complete (`research/sssp-relevance-reality-check.md`). The
finding confirms: provider selection is a flat ranked-list problem, not a graph traversal.
The client scores candidates returned by the directory; no path is computed through a
network topology graph. This reinforces C1 as the correct framing — direction discovery
gives a flat list of candidates; the client applies its policy to that list.

SSSP is not applicable at any currently classified data item. The R7 trigger condition
(≥50k nodes + multi-hop relay + per-request path) remains deferred.

---

## 4. Current Protocol Coverage

Of the PROTOCOL-REQUIRED items above:

| Item | Currently in protocol? |
|------|----------------------|
| C1: Intent URN list | ✓ (discover endpoint filters by intent) |
| C2: Context window size | ✓ (capability fields in node registration) |
| C4: Modality | ✓ (intent URN encodes modality; registration declares it) |
| C5: Privacy class | ✓ (node registration field) |
| Q1: Reputation score | ✓ (heartbeat + discover response) |
| Q2: Tier classification | Partially — PENDING REP2 ratification |
| Q4: Observed latency | ✓ (directory tracks; expose in discover response) |
| E1/E2: Price/type | ✓ (ADR-019) |
| I1: Node identity | ✓ (ADR-021) |
| I3: Signed envelope | ✓ (ADR-024) |

---

## 5. Gap List (5 items — at stop condition)

| # | Gap | Required by | Follow-up |
|---|-----|------------|-----------|
| Gap 1 | **Capability proof staleness timestamp** (C6): No field indicates when a capability proof was last attested. Stale declarations invisible to clients. | Any policy that filters by capability | Add `capability_attested_at` to heartbeat schema. No separate ADR needed — extend spec/iicp-core.md §heartbeat. |
| Gap 2 | **Identity age in discover response** (Q3): Needed for client-side platinum gate verification (identity_age ≥ 720h). Currently not published. | Platinum tier routing; anti-whitewash | Add `identity_age_hours` to discover response. Extend spec/iicp-core.md §discover. |
| Gap 3 | **Role field in discover response** (I2): Clients must be able to filter by role (consolidator vs. inference vs. specialist). Not currently a formal field. | MESH track role-based routing (MESH1–MESH4) | ADR-028 (MESH track) should specify this field. Check if ADR-028 already covers it; if not, add to ADR-028 scope. |
| Gap 4 | **Multi-path declaration in task submission** (M1): Nodes need to know if they are in a multi-path set (affects pricing and fragment behavior). | R2 (multi-path requirements) + R6 (N-of-M strategies) | R2 to specify this field. ADR-028 or new ADR if R2 deems it significant. |
| Gap 5 | **Observed load indicators in discover response** (A2): Directory tracks latency from heartbeat timings but no standardized load-indicator field in discover response. Policies must proxy via latency alone. | MESH3 (load-aware selection — oscillation prevention) | Add `observed_latency_p50_ms`, `observed_latency_p95_ms` to discover response. No separate ADR needed — extend spec/iicp-core.md §discover. Gaps 2 and 5 can be bundled. |

---

## 6. Acceptance Criteria Verification

| AC | Requirement | Status |
|----|-------------|--------|
| ADR-025 classification table with justifications | Table in §2 (C1–M2, 5 categories, 24 items) | ✓ |
| Gap list is concrete | §5: 5 gaps, each with required-by and follow-up | ✓ |
| No selection algorithm mandated at protocol level | §2.7 CLIENT-INTERNAL section; all scoring/exploration items excluded from protocol | ✓ |
| Within ≤2000 words | ≈1800 words | ✓ |
