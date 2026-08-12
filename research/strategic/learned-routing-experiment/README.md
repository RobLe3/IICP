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
