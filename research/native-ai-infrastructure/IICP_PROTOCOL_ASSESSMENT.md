# IICP Protocol Assessment: Native AI Service and Coordination

## Executive conclusion

IICP v1.9 is **AI-native in semantic direction and capability model**, but it is
not yet a complete universal native service interface in the operational sense.
Its strongest current boundary is whole-task invocation, discovery, provider
selection, policy-aware routing, confidential transport where keys exist, and
coordinator/worker cooperation. Native framing is a draft and implementations
currently provide partial, divergent lifecycle coverage.

The protocol should evolve by semantic profiles and negotiated sub-protocols,
not by broadening the fixed frame to encode runtime-specific inference internals.

## Strengths

| Area | Evidence | Assessment |
|---|---|---|
| Intent-first invocation | Core/semantics/URN grammar | Strong reusable service abstraction. |
| Capability discovery | Node capability envelope and IICP-DIR | Strong foundation; dynamic capacity semantics need tightening. |
| Whole-task routing | CALL/RESPONSE, HTTP fallback, native transport implementations | Suitable as a service boundary. |
| Cooperative work | CIP coordinator/worker modes and receipts | Useful foundation; lifecycle and aggregation semantics are uneven. |
| Privacy/security slots | CX, identity slot, signed-envelope direction | Sound direction; deployment/conformance coverage remains incomplete. |
| Extensibility | custom range, sub-protocol negotiation, unknown-field rules | Correct architectural escape hatch. |

## Material gaps

| Area | Current condition | Required action |
|---|---|---|
| Streaming | OBSERVE exists, but token event, ordering, finality, resumption and backpressure are not one interoperable profile. | Define `streaming` semantic profile and conformance vectors. |
| Cancellation | No complete state machine across queued, running, streaming and cooperative calls. | Normative lifecycle clarification before new frame type. |
| Flow control | Transport capacity, provider admission and workload limits are mixed. | Separate connection/stream flow control from provider admission profile. |
| Retry/idempotency | Fields exist, but partial-result and billing retry behavior lacks one binding table. | Normative retry matrix and receipt rules. |
| Native parity | Framing draft, TCP implementations and relay framing contain historical shape differences. | Canonical wire vectors and cross-SDK conformance gate. |
| Version/extension negotiation | Core algorithm exists, but profiles and sub-protocol compatibility outcomes are underspecified. | Negotiation registry and negative test cases. |
| Observability | Trace fields exist but standard queue/inference/network/failure-origin fields are incomplete. | Redacted execution telemetry profile. |

## Layer boundary findings

IICP should own transport binding, framing, request lifecycle, intent semantics,
capability advertisement, policy, routing evidence, identity, receipts and
safe telemetry. Model placement, tensor representation, KV-cache state, stage
scheduling, activation lanes and runtime-local recovery remain runtime-specific.

## Readiness

- **General AI service protocol:** conditional; suitable for controlled
  HTTP/OpenAI-adapter and whole-task deployments, not yet universally specified.
- **Provider/agent interoperability:** credible foundation; requires profile and
  lifecycle conformance before broad interoperability claims.
- **Distributed inference coordination:** suitable at coordinator/worker level
  after CIP lifecycle hardening.
- **Stage-level distributed inference:** not a base-protocol readiness claim.

## Required answers

1. IICP is genuinely AI-native conceptually and semantically.
2. It is not yet a fully specified universal AI service interface.
3. It can become a provider/agent interoperability layer with profile work.
4. It is suitable for MeshLLM whole-model routing through the public API.
5. It is not suitable for generic Skippy stage traffic without a specialized
   negotiated protocol and measurements.
