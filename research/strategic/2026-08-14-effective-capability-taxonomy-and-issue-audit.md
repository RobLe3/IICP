# Effective capability taxonomy and issue audit

**Date:** 2026-08-14

**Status:** implementation-neutral research and first fixture; no wire, runtime,
directory, SDK, release, or deployment change.

## Decision

The proposal is applicable and aligned with IICP's long-term direction. It does
not justify a new intent hierarchy or an immediate ecosystem-wide field rollout.
IICP already has the right broad architecture: stable intent URNs, per-intent
capability objects, policy and evidence layers, negotiated profiles, versioned
fixtures, and client-side eligibility. The missing part is a precise definition
of an **effective service capability** and a vocabulary that does not confuse
modalities, model features, runtime actions, limits, policy, bindings, identity,
observations, or quality.

The canonical rule should be:

> An advertised capability is usable through the complete model, template,
> runtime, provider API, and IICP adapter path for the advertised intent.

The first implementation in this change is deliberately non-wire: it adds this
rule to the existing pre-normative registry profile and adds a research fixture
that makes the class boundaries and negative implications executable. IICP #156
owns the remaining semantic and schema work. IICP #55 remains the ratification
gate and is now explicitly blocked on #156.

## Sources inspected

The audit used current default branches rather than issue summaries alone.

| Component | Commit inspected | Relevant authority or behavior |
|---|---:|---|
| IICP specification | `9cdcba5cf0c2` | Core, directory, semantics, node capability format, MCP binding, Registry 1.4, profile fixtures |
| Python SDK | `2990a529cbd3` | capability construction, modality/intent inference, MCP gateway registration |
| TypeScript SDK | `e9297b0f6e3e` | equivalent capability construction and MCP gateway behavior |
| Rust SDK | `60433388d0e5` | equivalent capability construction, provider registration and profile advertisement |
| PHP directory | `19c5a96339fc` | registration validation, persistence, discovery and node-detail projection, OpenAPI |
| Rust directory | `a9ae62dc77d9` | registration persistence, schema contract, discovery and federation projection |
| Browser node | `025867e9a348` | browser-provider capability advertisement |

The issue audit covered IICP #1, #3, #4, #54-#56, #89, #98-#99, #104,
#135-#136 and historical iicp.network #408, #414, #619-#620, #623, #697 and
#714. Repository-wide searches found no existing issue that owns effective
capability semantics, tool-calling versus tool-execution semantics, or the
confirmed capability-preservation contradiction.

External implementation evidence was checked against current primary sources:

- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
  exposes model-generated tool requests, but application code remains responsible
  for executing a tool and returning its result.
- [vLLM's OpenAI-compatible server](https://docs.vllm.ai/en/stable/serving/openai_compatible_server/)
  supports different endpoint families and makes chat behavior depend on model
  type and chat-template availability.
- [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
  exposes multimodal input, constrained JSON, tool use, reasoning parsing and
  streaming through separately enabled templates and server features.
- [Apple Foundation Models](https://developer.apple.com/documentation/foundationmodels/)
  exposes guided generation and tool calling as framework features rather than
  as a universal property of every model invocation.
- [MCP tools](https://modelcontextprotocol.io/specification/draft/server/tools)
  describe executable tools and their schemas. MCP is a binding and execution
  surface, not proof that an inference model can generate tool calls.

These implementations support the effective-path rule. A model label alone
does not establish what a particular serving path can accept or return.

## What already works

The current ecosystem already provides much of the needed foundation:

- `registry/intents.json` is a validated Registry 1.4 vocabulary with stable
  URNs, lifecycle, schemas, digests, fixtures, compatibility and released
  implementation evidence.
- `capabilities[].input_modalities` describes text, image, audio and video input.
  Vision in chat is already a modality of `llm:chat:v1`, not a second generic
  vision intent.
- `capabilities[].supported_profiles` carries explicit negotiated profiles. The
  service-lifecycle profile already owns streaming, partial responses,
  cancellation and terminal behavior.
- policy fields, including `allow_tool_execution`, remain separate from
  capability advertisement.
- the MCP binding defines MCP tool execution separately from ordinary LLM chat.
- the layered registry proposal already has entry kinds for intent, capability,
  policy, evidence, binding and subprotocol declarations. Extending that model
  avoids a second registry architecture.
- shared fixtures already enforce required versus optional extension behavior:
  required unknown extensions fail closed; optional unknown extensions do not
  weaken compatibility.

These are reasons to extend the current profile, not replace it.

## Confirmed gaps and contradictions

### Capability cardinality

`node-capability-format.md §7` says each intent may appear at most once in a
capability array. `iicp-dir.md §3.1` allows multiple entries for one intent with
different modalities. Python, TypeScript and Rust group advertisements by
`(intent, input_modalities)`, and both directory schemas permit duplicate intent
rows. The specification currently gives two incompatible answers.

The foundation must define whether a capability object is one intent-wide
aggregate or one effective service variant. It should not encode a uniqueness
rule until the variant identity is explicit.

### Inference fields are treated as universal fields

`iicp-core.md §2.1`, PHP registration validation and PHP OpenAPI require
`models` and `max_tokens` for every capability. The canonical capability
document defines MCP, batch and retrieval examples without those fields. The
official MCP gateways work around this by advertising synthetic values such as
`models=["mcp:<tool>"]` and `max_tokens=65536`.

The base object should contain fields shared by every capability. Model and
token fields should be conditional on an inference capability, not invented for
tool or data services.

### Capability preservation is promised but not implemented

`node-capability-format.md §8` requires capability objects and unknown fields to
be returned without modification. The PHP directory stores a fixed set of
columns and its node-detail response returns only intent, models, max tokens,
modalities and profiles. The Rust directory also stores and projects a bounded
subset. Documented fields such as context length, legacy streaming support,
hardware and MCP-specific attributes do not survive the directory path.

The protocol must choose and test one of two honest contracts: preserve a
bounded extension object, or define explicit supported fields and stop promising
lossless propagation. Silent loss is not forward compatibility.

### Current modality claims are heuristic

All three SDKs infer embedding intent and input modalities from model-name
substrings such as `embed`, `-vl-`, `vision`, `llava`, `audio`, `voxtral` and
`omni`. The parity is intentional, but the result can over-advertise a model
whose active template, runtime or provider API does not expose the feature.
It can also miss a capable model with an unfamiliar name.

Heuristics can remain a compatibility fallback if they are labelled as such.
Operators and adapters need a path to report authoritative runtime/provider
metadata or a conformance-probed result. A heuristic must not be presented as
verified evidence.

### Missing feature vocabulary

IICP cannot currently ask whether a chat provider supports structured output or
model-generated tool calls. Both properties have routing value and can be
defined without depending on a vendor. Neither implies that tools will be
executed. The protocol also lacks precise agentic terms, but a generic
`agent=true` flag would make the ambiguity worse.

The smallest useful initial vocabulary is:

- input modality, using the existing field;
- structured or constrained output as an effective inference feature;
- model-generated tool calls as an effective inference feature;
- tool execution as a separate execution capability controlled by policy;
- service-lifecycle support as an existing negotiated profile;
- quantitative context and output limits as numbers, not booleans.

State, delegation, resumability and agentic-loop ownership should remain
separate candidate declarations until each has a testable contract.

### Matching is narrow

Directory discovery supports one required `modality` plus model, reputation,
region, cost and profile negotiation. It does not provide a general contract for
several required features, advisory preferences and quantitative thresholds.
This is a genuine future discovery requirement, but it must reuse existing
eligibility and constraint machinery. It should not become another scoring or
policy engine.

## Semantic model

| Axis | Question | Example | Must remain separate from |
|---|---|---|---|
| Intent | What operation is requested? | `urn:iicp:intent:llm:chat:v1` | natural-language payload and features |
| Modality | What media can the operation accept or produce? | image input | a generic vision intent |
| Capability feature | What behavior does this service path expose? | structured output, tool-call generation | tool execution and quality |
| Execution capability | What surrounding runtime action is available? | tool execution, delegation | model generation |
| Quantitative limit | What bound applies? | context tokens, batch size | boolean support and quality |
| Policy/permission | May this caller use it? | shell execution denied | capability absence |
| Binding/profile | How is it invoked or negotiated? | MCP, service lifecycle | semantic intent |
| Identity | What implementation is serving? | model/runtime/provider revision | capability truth |
| Observation | How is it performing now? | latency, availability | semantic quality |
| Evidence/provenance | Why should the claim be believed? | runtime introspection, probe | the claim itself |

An intent is best described as a stable operation address. Calling it a
"capability address" in the current core text is understandable historically,
but it blurs the distinction now required by per-intent feature declarations.
This can be clarified without changing any URN or payload.

## Negative semantics

The foundation must state what each capability does **not** imply:

- image input does not imply tool calls, execution or an agentic loop;
- tool-call generation does not imply tool execution, MCP, shell access or
  network access;
- MCP tool execution does not imply model-generated tool calls or unrestricted
  execution;
- structured output does not imply semantic correctness;
- a reasoning-interface declaration does not expose hidden chain of thought and
  does not imply higher quality;
- a context limit does not imply availability or quality;
- capability availability does not override caller-specific policy denial.

The new research fixture records these cases so later schema and implementation
work has a stable semantic target.

## Registry and versioning decision

Do not create another intent registry. Extend the existing layered registry
profile under #55 so a capability declaration can define:

- stable identifier and lifecycle;
- canonical meaning and applicable intent classes;
- representation and quantitative parameters;
- dependencies, incompatibilities and negative implications;
- evidence/provenance requirements;
- conformance fixtures;
- introduced, deprecated and replacement versions.

The fixture in this change intentionally uses conceptual property names. It is
not a wire schema and does not pre-empt the identifier or representation review.
Stable intent versions and capability-vocabulary versions remain separate.

## Issue audit and disposition

| Issue | Action | Reason |
|---|---|---|
| IICP #54 | Keep closed | The layered substrate coordination is complete; this work follows its boundary. |
| IICP #55 | Update and block on #156 | The registry ratification gate lacks the effective capability semantics needed for promotion. |
| IICP #3 | Keep closed | Service lifecycle already owns negotiated streaming; do not create a duplicate boolean contract. |
| IICP #4 | Keep closed | Provider admission and capacity remain separate and reusable. |
| IICP #56 | Keep open, no scope merge | Policy and data handling decide permission, not capability meaning. |
| IICP #98 | Keep closed | Its observation provenance is reusable, but semantic capability is not a performance observation. |
| IICP #135 | Keep closed | Semantic quality remains evaluator-specific and outside this taxonomy. |
| IICP #136 | Keep open, no scope merge | Execution privacy may later use a capability/evidence profile; fresh attestation remains point-to-point. |
| iicp.network #408 and #414 | Keep closed | They correctly established modalities and task-specific intents; name heuristics become fallback evidence rather than final truth. |
| IICP #156 | New canonical owner | Owns effective capability semantics, schema/cardinality reconciliation, matching and provenance. |

No SDK or directory child issue was opened. Opening six implementation issues
before the semantic/schema decision would invite feature drift and duplicated
field design. #156 requires a reviewed shared fixture before those children are
created together.

## Dependency order

```text
IICP #156 semantic decision
        |
        v
existing registry/profile representation under #55
        |
        v
shared positive/negative capability fixtures
        |
        +--------------------+
        |                    |
        v                    v
directory persistence   SDK/adapter effective advertisement
PHP + Rust              Python + TypeScript + Rust + browser
        |                    |
        +----------+---------+
                   v
       required/preferred/limit matching
                   |
                   v
       cross-implementation conformance
                   |
                   v
       independent evidence and #55 decision
```

This order prevents a Rust-first experiment from becoming protocol behavior
before Python, TypeScript, browser and both directory implementations have the
same observable contract.

## Feasibility and scope

The semantic foundation is feasible without changing the base wire format.
Existing additive capability objects, profile negotiation, unknown-field rules
and client-side eligibility provide the required extension points. The costly
part is not adding JSON keys; it is making the claim accurate across serving
paths and preserving it across directories and SDKs.

The first downstream implementation should therefore prove one narrow path,
likely explicit modality override plus structured-output/tool-calling probes,
against at least two different runtime families. It must retain the current
name heuristic only as a labelled fallback and must ship through the coordinated
cross-SDK parity gate. Output modalities, broad agentic execution, batch,
determinism and resumability can wait for demonstrated routing use cases.

## Alignment with long-term goals

This work supports IICP's core question: which service can satisfy an intent
under declared capability, policy, trust, quality, cost, locality and
availability constraints? It increases interoperability across local runtimes,
cloud providers, browser nodes, tool servers and agent harnesses without making
any one of them the protocol model.

It also preserves the project's established boundaries:

- directories remain payload-free control planes;
- clients retain eligibility and dispatch authority;
- MCP and other protocols are bound rather than reimplemented;
- semantic quality stays evaluator-specific;
- runtime health and performance stay observational;
- policy does not become capability truth;
- model identity does not become a capability score.

The result is an incremental completion of the existing layered design, not a
reinvention of model serving, MCP, agent frameworks or provider APIs.

## Validation record

The repository checks executed for this slice are recorded in the pull request.
At minimum they cover JSON parsing, fixture semantics, profile-fixture manifest
validation, intent-registry validation, specification release integrity and the
repository's profile-fixture workflow equivalent. No runtime, registry version,
package version, release or deployment changes are part of this work.
