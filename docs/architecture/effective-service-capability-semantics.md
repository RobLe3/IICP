# Architecture decision: effective service capabilities

**Status:** Accepted additive pre-normative Profile contract; ecosystem adoption remains parity-gated
**Recorded:** 2026-08-14  
**Machine-readable contract:**
[`effective-service-capability-v1.json`](effective-service-capability-v1.json)  
**Related work:** IICP #55, #56, #98, #135 and #156

## Decision

An IICP capability describes behavior usable through the complete advertised
service path for an intent. The model, template, runtime, provider interface and
IICP adapter must all expose the behavior. A model label or theoretical model
feature alone is not an effective capability.

The following axes remain separate:

| Axis | Meaning | Example |
|---|---|---|
| Intent | Requested semantic operation | `urn:iicp:intent:llm:chat:v1` |
| Modality | Media accepted or produced | image input |
| Feature | Behavior exposed by the service path | structured output, tool-call generation |
| Execution capability | Action performed by the surrounding runtime | tool execution, delegation |
| Limit | Numeric bound | context tokens, batch size |
| Policy | Whether this caller may use available behavior | tool execution denied |
| Profile or Binding | Negotiated behavior or invocation mapping | service lifecycle, MCP |
| Identity and evidence | What served and why a claim is believed | runtime revision, conformance probe |
| Observation and quality | Current fitness or evaluator-specific outcome | latency, task evaluation |

Capability existence does not imply reachability, availability, authorization,
quality or selection.

## Capability variants

A node may advertise more than one effective variant for one intent when the
serving paths expose different modalities, Profiles, features or limits. This
matches the official SDKs' existing `(intent, input_modalities)` variants.

`variant_id` is an optional, node-scoped opaque identifier for a stable variant.
When present, `(intent, variant_id)` must be unique within one advertisement.
Without it, exact duplicate objects are invalid, but distinct objects for the
same intent remain valid. A Directory indexes all variants by intent and must
evaluate requirements against one complete variant; it must not combine
unrelated fields from several variants into a capability that no path offers.

## Base and conditional fields

Every capability object requires only `intent`. `version`, `phase`,
`variant_id`, modalities, features, limits, Profiles, claim provenance and
extensions are additive shared fields.

`models` is required only when the advertised path is model-backed and model
selection or identity is part of that intent's contract. `max_tokens` is
required only when an output-token limit is meaningful. Tool, batch, retrieval,
sensor and deterministic-service capabilities must not invent model names or
token limits to satisfy the base object.

The additive contract is published as
[`effective-capability-advertisement-v1.json`](../../schemas/effective-capability-advertisement-v1.json).
Current directories and SDKs keep accepting their legacy flattened
representation while the coordinated rollout adopts this conditional schema.
Existing registrations remain valid. Synthetic MCP model names are
compatibility data, not capability semantics, and may be removed only through
that rollout.

## Extension preservation

The previous promise that a Directory returns every unknown top-level field
unchanged is replaced by an implementable contract:

- registered base and capability-vocabulary fields are preserved semantically;
- optional future data uses a namespaced `extensions` object;
- each extension states whether it is required;
- an unknown required extension makes the candidate ineligible;
- an unknown optional extension may be ignored by a consumer, but a Directory
  that accepts it must preserve and return it;
- a Directory may reject an extension that exceeds documented resource limits;
  it must not accept and silently discard it.

Unknown unnamespaced top-level fields may be ignored for legacy compatibility
and must never be treated as support. Extension identifiers and lifecycle use
the existing registry/profile architecture under #55; this decision creates no
second registry.

## Initial vocabulary boundaries

- Image, audio, text and video input are modalities of the active intent.
- `structured_output` means the path accepts a declared structured-output
  contract and constrains machine-readable output accordingly. It does not
  promise semantic correctness.
- `tool_calling` means the inference path accepts tool definitions and can emit
  machine-readable tool requests. It does not imply execution, MCP, shell or
  network access, or an agentic loop.
- `tool_execution` is a separate runtime capability and remains subject to
  authentication, authorization, policy and sandboxing.
- Streaming remains owned by the negotiated service-lifecycle Profile. A
  boolean cannot replace that negotiation or change buffered `call()` behavior.
- `agent` is not a valid composite feature. Future agentic behavior must use
  separately testable declarations such as loop ownership, stateful session,
  tool execution, delegation and resumability.

## Matching

A capability-aware discovery request has three independent inputs:

- `requires`: every understood requirement must be present on one effective
  variant;
- `prefers`: missing or unknown preferences do not make a candidate ineligible;
- `limits`: quantitative comparisons use the named operator and unit.

Portable refusal classes are `required_capability_unknown`,
`required_capability_unsupported`, `required_capability_stale`,
`capability_limit_unsatisfied` and `capability_policy_denied`. Unknown required
declarations fail closed. Policy denial remains distinct from capability
absence, and preferences influence ranking only after eligibility.

The binding-neutral request and refusal shapes are published as
[`capability-requirements-v1.json`](../../schemas/capability-requirements-v1.json)
and
[`capability-refusal-v1.json`](../../schemas/capability-refusal-v1.json).
The shared fixture is
[`effective-capability-v1.json`](../../research/pre-normative-profiles/fixtures/effective-capability-v1.json).
It is the parity contract for complete-variant matching, unknown required and
preferred declarations, typed limits, stale evidence, policy denial and
extension preservation.

These schemas do not define a new HTTP endpoint. Existing `?modality=` behavior
remains unchanged until a binding adopts the general requirements object.

## Claim provenance and freshness

Capability claims use bounded provenance: `heuristic_fallback`,
`operator_assertion`, `provider_metadata`, `runtime_introspection` or
`conformance_probe`. A claim may include `observed_at`, `valid_until` and a
content-free evidence reference. Expired evidence is stale; absent provenance
is unknown. Heuristic and operator claims may inform compatibility behavior but
must not be labelled verified.

Provenance does not disclose credentials, private routes, hardware fingerprints
or backend topology. Hardware attestation is not required for ordinary claims.

## Compatibility and non-goals

The new schemas are additive and opt-in. Implementations that have not adopted
the Profile continue using the current request, registration and discovery
shapes. The contract preserves existing intents, modality filtering, Profile
negotiation and buffered execution. It does not create a vision intent, model
ontology, global quality score, monitoring framework, agent framework or
vendor-specific vocabulary. Downstream support must ship as one parity-gated
chain across both directories, Python, TypeScript, Rust and browser surfaces.

Adoption and rollback follow these rules:

- a producer emits the Profile fields only when its implementation has enabled
  this contract and can supply a complete effective-path claim;
- a Directory either preserves accepted Profile data or rejects the
  registration; it must not accept a required declaration and discard it;
- a consumer that does not request the Profile keeps the current discovery and
  selection behavior;
- disabling the Profile stops new capability-aware requirements and
  advertisements without rewriting legacy capability records;
- rollback uses the existing registration and `?modality=` paths. It does not
  require a protocol downgrade, version rewrite or changed buffered call.
