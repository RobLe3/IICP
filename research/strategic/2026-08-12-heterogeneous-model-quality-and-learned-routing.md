# Heterogeneous model quality and learned-routing boundary

**Assessment date:** 2026-08-12  
**Decision status:** research recommendation; no wire change, default-routing change, deployment or MetaHarness dependency is authorized

## Sources and method

This assessment compared the current IICP specification and official implementations with MetaHarness at fixed source revisions. It also checked the existing Edge-Net/QuDAG assessment rather than repeating that work.

| Source | Inspected revision | Relevant surface |
|---|---:|---|
| IICP specification | `fbc30489dff7` | core capability metadata, selection and receipt profiles, provider admission, prior routing research |
| Rust SDK/node | `f7a67b16b702` (`0.7.102`) | discovery projection, policy eligibility, selection strategies, route tickets and receipts |
| Python SDK/node | `72d82096fdfc` (`0.7.102`) | parity check for routing and receipts |
| TypeScript SDK/node | `8527d3f04f4a` (`0.7.102`) | parity check for routing and receipts |
| Rust directory | `57483563c68c` (`0.1.11`) | stored capability metadata, live model state and discovery projection |
| MetaHarness | [`68402755f017`](https://github.com/ruvnet/metaharness/tree/68402755f017e0df5f493c6ee608218420540d17) | `@metaharness/router` 0.4.0, DRACO, calibration and routing ADRs |

The Rust directory release was verified independently: GitHub release `v0.1.11` and crates.io package `iicp-directory-rs` both report `0.1.11`. It remains an operator preview; publication does not make it Genesis authority.

## Executive decision

IICP has a real but contained gap. It can determine whether a provider is eligible and currently usable, but it does not expose a stable, privacy-bounded interface for an optional selector to estimate whether a particular backend is likely to satisfy this particular request.

That gap should not be filled with a directory-owned quality score. The right boundary is:

```text
request
  -> IICP discovery
  -> mandatory policy and capability eligibility
  -> versioned candidate evidence
  -> optional local semantic-quality ranker
  -> IICP-controlled selection, ticket acquisition and dispatch
  -> execution
  -> redacted routing receipt and operational metrics
  -> evaluator-owned semantic outcome
  -> local learned history
```

MetaHarness is useful prior art and a possible experimental adapter. It should not become an IICP dependency or a protocol authority.

## Current IICP state

### The boundaries that already work

The official SDKs apply hard eligibility before probabilistic selection. The Rust implementation in `src/routing_policy.rs` rejects candidates that fail intent, encryption, region, risk, retention, operator-identity, reachability or profile requirements. `client.rs` then selects within the eligible set and retains control of route-ticket acquisition and dispatch.

The current selection profiles already provide:

- deterministic selection for diagnostics;
- epsilon exploration, currently the default;
- opt-in `softmax_top_k` and `weighted_v1` behavior;
- a canonical inverse-load fixture for `weighted_v1`;
- redacted routing receipts that identify the selection profile, eligible-candidate count and selected-node prefix.

The directory already accepts useful advisory evidence:

- model identifiers;
- quantization;
- inference engine;
- maximum tokens and concurrency;
- modalities and supported profiles;
- live `health_models` from heartbeat observations;
- load, availability, capacity, region, reachability, latency and reputation evidence.

These fields are evidence, not proof of semantic quality. That distinction is correct and should remain.

### The concrete gaps

1. **No external ranking seam.** The SDK selection code is closed over built-in strategies. There is no generic callback or trait that receives an already eligible candidate set and returns a permitted candidate.
2. **No stable candidate projection.** The Rust `Node` type does not currently preserve all directory capability details, including quantization, inference engine and supported profiles. An external selector would otherwise depend on an internal directory response shape that may drift.
3. **No backend-quality continuity identifier.** A node can change model revision, quantization, fine-tune, runtime or material serving configuration while keeping the same node and marketed model name. Old semantic observations can therefore be applied to a materially different backend.
4. **Receipts do not explain selection purpose.** Current receipts do not distinguish ordinary selection, intentional exploration and fallback, nor do they correlate an execution with a stable backend revision or evaluator-owned outcome record.
5. **Operational metrics are too coarse for the experiment.** The common task result covers overall latency and tokens, but no versioned cross-SDK projection yet standardizes queue time, time to first token, generation duration, throughput, retry/fallback class or evidence freshness.

None of these gaps justifies a universal `quality` field.

## Existing work that must remain authoritative

| Topic | Existing IICP work | Disposition |
|---|---|---|
| Eligibility, capability and extension layering | Issues #54 and #55; layered substrate report | Reuse; do not create a second capability system. |
| Runtime fitness and public measurement | Provider-admission profile and issue #98 | Reuse; semantic evaluation is not node health. |
| Selection profiles | `selection-profile-v1.md`, shared fixture and official SDK implementations | Extend experimentally; do not replace current defaults. |
| Dispatch authorization and receipts | Issue #58 and route-ticket/receipt profile | Reuse; an external ranker must not dispatch directly. |
| Distributed inference | Issue #6 | Separate. Whole-task backend choice is not stage-level tensor or KV-cache transport. |
| Edge-Net and QuDAG | 2026-08-09 boundary assessment | No new work. Its recommendation already keeps observations portable and learning algorithms local. |
| MeshLLM | `iicp.network` #631 | Separate ensemble-backend experiment, not a general selector contract. |

The prior Edge-Net/QuDAG conclusion remains sufficient: protocol-visible observations may be portable, while adaptive algorithms remain implementation-specific. **No new Edge-Net or QuDAG issue is warranted.**

## What MetaHarness contributes

At the inspected commit, `@metaharness/router` 0.4.0 accepts candidate IDs, per-million-token cost and labelled examples that map query embeddings to candidate-specific quality. Its basic router uses k-nearest neighbors; its trained path uses cosine-kernel ridge regression with leave-one-out selection of the regularization parameter. It chooses the cheapest candidate predicted to clear a caller-supplied threshold, otherwise the highest predicted candidate. Its calibration module reports Brier score, reliability bins and expected calibration error.

The DRACO evidence is useful but small. ADR-043 reports 20 questions: the best fixed strategy scored `0.6960`, k-NN `0.7048`, KRR `0.6964` and the per-query oracle `0.7682`. This supports an experiment, not a protocol claim or production default. MetaHarness itself notes the data ceiling and the need for more observations.

MetaHarness does **not** provide IICP eligibility, policy, identity, trust, capability freshness, verified dispatch or receipt semantics. Its candidate identifier is application-defined and does not solve backend revision continuity. That makes it complementary to IICP when placed after eligibility and before IICP-controlled dispatch.

## Required separation of concerns

| Dimension | Owner | Meaning |
|---|---|---|
| Protocol and policy eligibility | IICP directory evidence plus client policy | May the candidate receive this task? |
| Runtime fitness | IICP observations and provider admission | Can it execute effectively now? |
| Predicted semantic capability | Optional evaluator/ranker | Is it likely to satisfy this request's evaluator-specific requirement? |
| Economic and user preference | Client policy | Which sufficient candidate best fits cost, latency, locality or operator preference? |
| Dispatch authorization | IICP | Is the selected eligible route authorized and evidenced? |

The directory may carry evidence used by these dimensions, but it must not collapse them into one unexplained score.

## Minimal candidate-evidence contract

A learned selector needs a small, versioned and read-only projection rather than the entire internal `Node` structure. The first experiment should reuse existing values wherever possible.

| Evidence | Current status | Recommendation |
|---|---|---|
| opaque candidate reference, node ID and intent | present | Include. |
| models, modalities, context/token limits and profiles | present in directory capability data | Normalize into the experimental projection. |
| quantization and inference engine | present as advisory directory fields | Preserve as optional priors. Never treat them as quality truth. |
| live availability, load, reachability and latency | present | Include with freshness and provenance where available. |
| trust/reputation and cost/credits | present | Keep as separate evidence groups. |
| model revision, fine-tune and material runtime configuration | incomplete | Research one privacy-safe continuity field. |
| prompt, response, embeddings or private topology | deliberately absent | Keep absent. Query embeddings and evaluator data stay local to the selector. |

The continuity field is justified by a specific failure mode, but its design is not settled. A value such as `execution_profile_id` could be an opaque, rotation-sensitive commitment over a bounded configuration profile. It must not expose raw hardware identity, exact host configuration or a stable cross-service fingerprint. It should change when historical semantic observations cease to be comparable.

## Minimal selector interface

The client-side experiment should establish behavior, not a final API name. A conforming seam must:

1. receive only candidates that already passed mandatory eligibility;
2. receive a versioned, redacted evidence projection;
3. return one candidate reference from that same set, or decline;
4. never modify directory evidence or synthesize a directory score;
5. leave ticket acquisition, route verification, retries and dispatch in the IICP client;
6. fall back to the declared existing selection profile when the ranker is absent or declines;
7. fail closed if it returns an unknown or ineligible candidate;
8. preserve buffered and streaming execution semantics;
9. remain usable with a simple heuristic, MetaHarness or another evaluator.

This can eventually look like a `CandidateRanker` or `SelectionPolicy` trait, but naming and ownership should follow the Rust SDK's established API conventions after the experiment is specified.

## Receipts and learning evidence

The routing receipt should remain content-free. The experiment should determine whether the following additive fields are necessary:

- candidate-evidence schema version;
- opaque execution-profile reference;
- selection purpose: normal, exploration or fallback;
- selector profile identifier and version, not proprietary weights;
- operational outcome references and bounded timing fields.

Semantic evaluations should live in an evaluator-owned store keyed to a receipt/task correlation value. IICP should not record a universal semantic score, prompt embedding, prompt or response. Different evaluators must be able to disagree.

## Cold start and exploration

Cold-start inputs such as model family, declared specialization, quantization, approximate parameter class and trusted conformance evidence are priors only. Predictions should carry sample count and calibration evidence. Missing history must never be represented as high confidence.

The existing epsilon and weighted/top-k strategies are enough to run an exploration experiment. A new exploration subsystem is not justified. A receipt annotation may be useful because intentionally sampled traffic must not be mistaken for an ordinary best estimate when training later selectors.

## Security and abuse constraints

The experiment must cover:

- false model and specialization claims;
- node-stable but backend-changing identities;
- stale and poisoned observations;
- Sybil amplification and selective benchmark behavior;
- evaluator manipulation and benchmark gaming;
- routing capture by a single operator;
- privacy leakage through embeddings, stable fingerprints or small cohorts;
- a ranker attempting to return a candidate that eligibility rejected;
- dominance by the largest model despite a smaller specialist meeting the threshold.

Parameter count is never a quality score. A smaller or specialist model remains preferable whenever evidence predicts that it can satisfy the task more efficiently.

## Small experiment

The first useful experiment belongs in the client/research layer and requires no normative field.

1. Freeze a versioned task set and evaluator definitions.
2. Use heterogeneous backends: small, mid-sized, large and at least one specialist where available.
3. Record exact model/runtime configuration privately and derive an opaque experimental execution-profile reference.
4. Compare default IICP selection, fixed backend, metadata heuristic, MetaHarness k-NN/KRR, threshold-plus-cost, and an offline oracle.
5. Report semantic outcome, task success, latency, time to first token, throughput, cost and routing regret independently.
6. Run cold-start, backend-revision change, stale-evidence, malicious-advertisement and insufficient-sample cases.
7. Confirm that every choice remains inside the IICP-eligible set and that IICP still acquires and verifies the route ticket.

Success means a repeatable improvement over the current selector with calibrated uncertainty and no policy bypass. It does not mean one benchmark's quality scale becomes normative.

## Issue disposition

| Area | Action | Reason |
|---|---|---|
| Heterogeneous semantic-quality boundary | **OPEN one focused IICP research issue** | No existing issue owns evaluator-specific semantic prediction, backend continuity and the policy-safe selector boundary together. |
| Layered substrate (#54) | **UPDATE** | Link the new research owner and keep eligibility, evidence, ranking and dispatch separated. |
| Registry profile (#55) | **UPDATE** | Candidate evidence and any continuity reference must be additive, versioned and privacy-bounded. |
| Route tickets and receipts (#58) | **UPDATE** | Track only evidence required to correlate selection purpose/backend continuity; no universal quality score. |
| Public measurement (#98) | **UPDATE** | Clarify that public operational observation is not semantic evaluation. |
| Rust selector implementation | **DEFER** | Open an SDK implementation issue only after the research issue fixes the experimental projection and acceptance test. |
| Specification change | **AFTER EVIDENCE** | Standardize only fields or hooks shown to be stable and generally useful. |
| Edge-Net/QuDAG | **NO ACTION** | Existing research already covers the only relevant observation/algorithm boundary. |
| Distributed inference (#6) | **NO ACTION** | Stage-level execution is not required for whole-task quality-aware selection. |

## Recommended sequence

### Now: bounded 0.7.x research experiment

- establish the focused research issue;
- define the experimental candidate projection and backend-continuity test;
- implement the Rust-only policy-safe ranker seam only after that contract is reviewed;
- run the heterogeneous benchmark with MetaHarness as one optional adapter.

### After evidence: cross-SDK and profile decision

- decide whether the seam and evidence projection are generally useful;
- add cross-SDK semantics and fixtures only if the experiment succeeds;
- decide which receipt additions are required for reproducibility;
- decide whether any additive registry field warrants pre-normative profile work.

### Later

- external evaluation portability;
- larger multi-operator benchmarks;
- standardized evaluator-correlation vocabularies only if independent implementations converge.

### Reject

- MetaHarness as a core dependency;
- parameter count as quality;
- a directory-owned universal quality score;
- an external selector that bypasses IICP eligibility or ticketed dispatch;
- prompt, response or embedding material in directory records or routing receipts.

## Final answer

IICP can support radically heterogeneous backends without changing its role. It should expose a small, versioned view of already eligible candidates to an optional local ranker, retain verified dispatch, and correlate operational outcomes without owning semantic judgments. MetaHarness is a strong experimental adapter for that seam. It is not a protocol layer.

