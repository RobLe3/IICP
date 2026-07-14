# IICP vNext Recommendations

## Priority 1 — Normative clarifications

1. Define a complete task/stream/cancellation state machine.
2. Define retry, idempotency, partial-result and receipt/billing interactions.
3. Clarify native frame validation, size/decompression limits, unknown type and
   required-profile behavior.

## Priority 2 — Semantic profiles

1. Streaming profile: sequence, finality, cancellation, error and buffering.
2. Admission profile: deadline, provider queue/admission and capacity feedback.
3. Cooperative profile: coordinator/worker lifecycle, provenance and failure rules.

## Priority 3 — Capability fields

Standardize bounded, redacted provider-facing fields for model availability,
capacity class, stream support, profile support, and temporary unavailability.
Do not publish internal runtime topology.

## Research only

- Runtime-neutral `urn:iicp:sp:distributed-inference:v1` negotiation experiment.
- QUIC transport binding and multiplexing measurements.
- Stage-level activation transport comparison against Skippy.

## Rejected now

- Base-wire changes.
- MeshLLM-specific core semantics.
- Tensor/KV/cache/GPU topology fields in ordinary IICP capabilities.

## Classification

| Recommendation | Class |
|---|---|
| State/lifecycle tables | Normative clarification |
| Streaming/admission/cooperative profiles | New semantic profile |
| Capacity/availability fields | New capability field |
| Distributed-inference experiment | New sub-protocol |
| QUIC test binding | Transport binding enhancement |
| Fixed-header mutation | Rejected pending evidence |
