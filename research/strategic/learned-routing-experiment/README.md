# Learned-routing boundary experiment

This experiment tests one narrow question from IICP issue #135: can an
evaluator-owned ranker improve task-specific model choice after IICP has already
removed ineligible providers? It does not change discovery, routing defaults,
route tickets, receipts or the wire protocol.

## Experimental candidate projection

`candidate-evidence-v0.schema.json` separates four concerns:

- `eligibility` records that IICP completed mandatory filtering and retains
  ticketed dispatch;
- `semantic_prior` carries optional model evidence without calling it quality;
- `runtime_fitness` carries current operational evidence;
- `economic_evidence` carries preferences such as cost.

Candidate and execution-profile references are evaluator-local opaque values.
The projection excludes endpoints, full node identifiers, keys, credentials,
prompts, responses and task content. A ranker may return only one supplied
candidate reference or decline. IICP must reject an unknown reference and keeps
control of ticket acquisition and dispatch.

`execution_profile_ref` is justified only as an optional continuity boundary:
it changes when model revision, quantization, fine-tune, runtime or another
material serving property makes old semantic observations incomparable. It is
not a hardware identifier and must not expose private topology.

This v0 projection is a research artifact, not a directory response or
normative schema. Current SDK `Node` projections do not yet carry every field.

## Cross-SDK candidate-ranker contract

`candidate-ranker-v0.json` is the implementation-neutral client contract used
by the Rust, Python and TypeScript experiments. It does not define a directory
or wire payload. Each SDK evaluates an exact byte-for-byte copy in its test
suite.

The contract fixes only observable safety semantics: the ranker sees candidates
after hard eligibility, may select one supplied opaque reference or decline,
and cannot perform dispatch. Decline preserves the built-in order. Ranker
errors, invalid policy identifiers and unknown candidate references fail closed
under `IICP-CANDIDATE-RANKER-REFUSED`. Receipt evidence records a bounded policy
and `normal`, `exploration` or `fallback` mode without semantic scores or task
content. With no ranker attached, existing routing behavior is unchanged.

The complete task request may be made available to an in-process adapter. The
SDK never serializes or transmits it automatically; any out-of-process adapter
creates a separate privacy and trust boundary owned by the application.

## Reproduce the MetaHarness result

The benchmark uses the MetaHarness DRACO routing dataset without copying its
prompts or embeddings into IICP. Pin the external repository and verify the
dataset digest before running:

```bash
git clone https://github.com/ruvnet/metaharness.git
git -C metaharness checkout 68402755f017e0df5f493c6ee608218420540d17

cd research/strategic/learned-routing-experiment
npm ci
node run-metaharness.mjs \
  --dataset /path/to/metaharness/packages/bench/draco/runs/routing-dataset.json \
  --output reproduced.json
cmp reproduced.json result-draco-20-v0.json
npm test
```

The script refuses any dataset other than SHA-256
`8cfbedb6120b69d229919f9bfd453a01e36ad88cbb2af9e1c47378728c4adc9e`.
It uses leave-one-out evaluation, so a held-out row is never used to predict
itself. Each candidate is treated as already eligible.

## Result and disposition

On these 20 rows, the k-NN learned-best policy improved mean quality from
`0.69595` for the post-hoc best fixed model to `0.70478`, lowered the mean
price input from `45` to `32.55` per million tokens, and raised the 0.70
threshold success rate from `0.50` to `0.60`. The threshold-plus-cost policy
cost less again, but its quality and threshold success did not beat the fixed
baseline. The oracle gap remains large.

This is enough to justify a bounded Rust client experiment with a generic,
optional selector seam. It is not enough to standardize semantic quality,
change default routing, or promote the candidate projection. The next test must
use an IICP-specific, versioned heterogeneous task set with operational timing,
realized token cost, cold start, backend revision changes and adversarial
advertisements. Quality remains evaluator-specific and stays out of directory
reputation and routing receipts.

## IICP-specific heterogeneous benchmark

The follow-up benchmark uses 90 deterministic synthetic tasks: 30 structured
output tasks, 30 stable factual questions and 30 multi-step reasoning tasks.
Each task ran once against three local Ollama backends, producing 270
observations. The backends span approximately 0.5B, 1.2B and 3.8B parameters.
Every request used temperature zero, seed 42 and a one-field JSON answer
contract. Exact-match scoring, first-token latency, total latency, throughput
and opaque execution-profile continuity references are recorded in
`observations-local-ollama-v1.json`.

| Strategy | Success | Relative compute weight | Mean latency | Mean TTFT |
| --- | ---: | ---: | ---: | ---: |
| Fixed Phi-3 Mini 3.8B | 75.6% | 3.80 | 191.7 ms | 73.7 ms |
| MetaHarness learned | 70.0% | 2.81 | 201.7 ms | 100.2 ms |
| MetaHarness threshold + cost | 64.4% | 2.07 | 206.7 ms | 118.6 ms |
| Offline cheapest-success oracle | 80.0% | 1.30 | 200.6 ms | 129.2 ms |

The learned selector reduced the declared compute preference relative to the
best fixed backend, but it did not match that backend's success rate. The
threshold-plus-cost selector reduced the preference weight further and lost
more quality. The oracle gap shows that task-specific selection could still be
valuable, but this dataset and feature projection do not justify a normative
quality profile or a default-routing change.

The benchmark also executes ten cold-start and abuse dispositions covering
unknown or ineligible candidates, stale history, execution-profile changes,
missing continuity, insufficient samples, malformed scores, evaluator errors,
exploration and fallback. `candidate-ranker-benchmark-replay-v1.json` carries
ten content-free decisions into byte-identical Python, TypeScript and Rust SDK
tests. Those tests prove that the external decisions remain inside the supplied
eligible set and retain IICP-controlled receipt and fallback behavior.

Reproduce the local run after installing the three declared Ollama models:

```bash
cd research/strategic/learned-routing-experiment
npm ci
python3 generate-iicp-tasks.py
node run-iicp-heterogeneous.mjs \
  --tasks iicp-heterogeneous-tasks-v1.json \
  --backends backends-local-ollama-v1.json \
  --output observations-local-ollama-v1.json \
  --result result-local-ollama-v1.json
npm test
```

Pinned artifact digests are:

- task fixture: `sha256:91c7823e03a77f1d9ec1951c3393ba7a7ffec9eac11f3ab5b041e70bec01276a`;
- observations: `sha256:417eb78d290066c3255dc59ae6139fead371e3550eaed82e75b57b903ddd1409`;
- evaluated result: `sha256:1bb4dfec32d6bba6d6ea9ec6cb105dbe880e0a8cd64d71424be88c4f847c0639`;
- SDK replay fixture: `sha256:279baf4c6fb6b4c20f4b599a438bb85768da10726d84af7ebac8e5f9c9c95f85`.

### Disposition

Retain the generic candidate-ranker seam as an opt-in, client-local experiment.
Defer any protocol or directory profile. `execution_profile_ref` is justified
only as evaluator-local continuity evidence and rotates when model revision,
quantization, runtime or material serving configuration changes. Semantic
outcomes remain evaluator-owned; the IICP receipt carries only bounded policy,
selection-mode and existing task correlation. No MetaHarness dependency,
quality score, prompt, response or embedding enters IICP core or the directory.
