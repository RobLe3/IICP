# Heterogeneous model quality and learned-routing boundary

**Assessment date:** 2026-08-12<br>
**Native-integration eligibility checkpoint:** 2026-08-13<br>
**Decision status:** retain the opt-in client-local experiment; no wire change, default-routing change, deployment, MetaHarness dependency or upstream MetaHarness PR is authorized

> **Experiment update:** the bounded reproduction and v0 eligible-candidate
> projection are published under
> [`learned-routing-experiment/`](learned-routing-experiment/README.md). On the
> pinned 20-row DRACO dataset, leave-one-out MetaHarness k-NN improved mean
> quality and threshold success over the post-hoc best fixed model while using
> a lower mean price input. The sample is too small and domain-specific for
> normative promotion; it justifies a Rust client experiment behind the hard
> eligibility boundary.

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
| Heterogeneous semantic-quality boundary | **OPENED [IICP #135](https://github.com/RobLe3/IICP/issues/135)** | No existing issue owned evaluator-specific semantic prediction, backend continuity and the policy-safe selector boundary together. |
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

## Native MetaHarness integration eligibility checkpoint (2026-08-13)

This checkpoint assesses the later proposal to prepare a native MetaHarness ×
IICP integration and submit one upstream MetaHarness pull request. The proposal
has the right separation of responsibilities, but its implementation sequence is
not yet eligible.

### Current evidence

- The inspected MetaHarness source remains commit
  [`68402755f017`](https://github.com/ruvnet/metaharness/tree/68402755f017e0df5f493c6ee608218420540d17),
  the same revision used by the original experiment. No IICP issue or pull
  request exists in that repository.
- `@metaharness/router` 0.4.0 is a local model-quality router over caller-defined
  candidate IDs, costs and labelled embedding outcomes. It does not own dynamic
  discovery, IICP eligibility, authorization or dispatch.
- MetaHarness host adapters describe agent runtimes such as Codex, Claude Code
  and Hermes. IICP is an execution substrate, not one of those hosts. An IICP
  integration therefore does not belong in a host-adapter package.
- Basic request compatibility already exists wherever a MetaHarness execution
  path accepts a configurable OpenAI-compatible base URL and is pointed at the
  IICP local proxy. That path delegates execution through IICP but does not
  expose IICP's dynamic, already-eligible candidate set to the learned router.
- The official IICP clients now share the non-wire `candidate-ranker-v0`
  contract. Rust publishes that seam in 0.7.103. Python and TypeScript implement
  it on `main`, but their current 0.7.102 registry releases predate the feature.
  A cross-project adapter cannot claim a coordinated public SDK contract until
  the next authorized parity release publishes those two implementations.
- The 90-task heterogeneous benchmark did not establish a production promotion
  case. Learned routing reached 70.0% task success, below the fixed Phi baseline
  at 75.6%; threshold-plus-cost reached 64.4%. The oracle gap shows potential,
  not a sufficiently calibrated general improvement.

### Architectural ownership

| Concern | Authority |
|---|---|
| Discovery, hard eligibility, policy, identity, authentication, confidentiality and execution-privacy requirements | IICP |
| Availability, route revalidation, retry boundaries, ticketing, transport and dispatch | IICP |
| Query embedding, evaluator-specific quality prediction, calibration and learned history | MetaHarness or another optional local evaluator |
| Cost or latency preference | Caller policy; a ranker may optimize only within the supplied eligible set and declared preference |
| Semantic outcome labels | Evaluator-owned storage, correlated through content-free references |

The integration seam remains:

```text
IICP eligible candidates
  -> versioned redacted candidate evidence
  -> optional local adapter into @metaharness/router
  -> SELECT(supplied candidate_ref) or DECLINE
  -> IICP revalidation, ticketing and dispatch
```

The existing IICP contract already enforces the important safety rules. A ranker
sees only eligible candidates, cannot add a candidate, and can decline to the
built-in order. An unknown reference or ranker error fails before dispatch.
IICP keeps retry and fallback authority.

The current seam still has limitations that an upstream integration must not
hide. Rust and Python ranker calls are synchronous and the TypeScript call has no
SDK-enforced timeout. Bounded latency and cancellation must therefore be supplied
by an adapter or added as a separately reviewed, cross-SDK semantic change. The
MetaHarness router also picks a best-effort candidate when no model clears the
quality bar; an IICP adapter must translate insufficient or uncalibrated evidence
to `DECLINE` instead of presenting that fallback as threshold satisfaction.

### Identity and privacy

MetaHarness may index history by IICP's request-local opaque `candidate_ref` only
for the current selection. Longer-lived quality continuity should use the
research-only `execution_profile_ref`: an evaluator-local, rotation-sensitive
commitment that changes when the model revision, quantization, fine-tune, runtime
or other quality-relevant configuration changes. It must not expose a full node
identifier, endpoint, hardware serial, prompt, response, embedding or stable
cross-service fingerprint. This remains an experimental evaluator concern, not a
directory field or protocol identity.

### Eligibility decision

| Proposed action | Decision | Reason |
|---|---|---|
| Reuse IICP's candidate-ranker seam | **Eligible now for local experiments** | Cross-SDK source parity and adversarial fixture coverage exist. |
| Add a MetaHarness dependency to IICP | **Reject** | It would couple protocol clients to one evaluator and package ecosystem. |
| Implement IICP as a MetaHarness host | **Reject** | IICP is not an agent host under MetaHarness's host contract. |
| Add an IICP-specific provider that dispatches directly | **Reject** | It would duplicate or bypass IICP dispatch authority. |
| Create a thin optional adapter | **Eligible after gates** | This is the smallest composable boundary if repeated evidence demonstrates value. |
| Submit an upstream MetaHarness PR now | **Not eligible** | The Python/TypeScript seam is not yet released, benchmark promotion evidence is insufficient, and upstream ownership has not been agreed. |
| Reopen Edge-Net or QuDAG work | **No action** | This checkpoint produced no new connection beyond the existing observation/algorithm boundary. |
| Change the wire protocol or directory schema | **Not eligible** | The current experiment needs no normative or public directory field. |

### Promotion gates and next sequence

1. **Release parity, without a special release.** Include the existing Python and
   TypeScript ranker seam in the next authorized coordinated SDK release. Verify
   that Rust, Python and TypeScript package artifacts expose the same fixture
   semantics. Do not publish solely for this experiment.
2. **Strengthen the experiment.** Use a larger, multi-domain and preferably
   multi-operator corpus. Compare learned routing against strong fixed and simple
   metadata baselines using predeclared quality, cost and calibration criteria.
   Include cold start, sparse history, backend revision, poisoned observations,
   ranker timeout and deliberate decline.
3. **Require a promotion result.** A native adapter advances only if it improves
   the declared quality/cost objective out of sample, preserves IICP eligibility,
   and declines safely when confidence is inadequate. Oracle headroom alone is
   not a pass.
4. **Open an upstream design issue before code.** If the evidence passes, ask the
   MetaHarness maintainers whether the adapter belongs in a new optional package
   or remains application glue around `@metaharness/router`. It should not be
   placed in a host adapter. Record any required ADR before implementation.
5. **Submit one bounded pull request only after acceptance.** The pull request may
   add a thin optional adapter and tests for dynamic candidate sets, stale
   execution profiles, decline, timeout and IICP fallback. It must not add IICP
   policy, transport or dispatch logic to MetaHarness.

No new IICP or Edge-Net issue is justified by this checkpoint. The closed IICP
issue [#135](https://github.com/RobLe3/IICP/issues/135) and its executable
fixtures remain the authoritative project record. A new implementation issue is
warranted only when the evidence and upstream-ownership gates pass.
