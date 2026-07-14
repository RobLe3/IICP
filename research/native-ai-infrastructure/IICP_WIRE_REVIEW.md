# IICP Wire Protocol Review

## Current result

The 12-byte native frame header is lean and adequate for a stable envelope:
magic, version, type, flags/reserved, and payload length. Deterministic CBOR,
integer-keyed native maps, size limits, version negotiation, custom message
range and SUB_PROTOCOL negotiation are the right extensibility mechanisms.

The native framing specification is still draft. Existing implementations prove
basic INIT/ACK, CALL/RESPONSE, relay framing and admission behavior, but do not
yet prove a complete long-lived multiplexed QUIC service profile.

## Clarifications required before any frame change

- Reserved byte/flags validation and unknown type behavior.
- Maximum frame and decompressed payload limits; compression-bomb handling.
- Per-call versus per-stream correlation and explicit stream event sequencing.
- Cancellation, close, timeout and partial-response transitions.
- Duplicate request IDs, idempotency keys, receipt/billing behavior after retry.
- Backpressure/admission signals and their scope.
- Compatibility outcomes for required versus optional profiles and sub-protocols.

## Wire-change decision

No base frame modification is recommended now.

| Candidate | Decision | Reason |
|---|---|---|
| Priority/deadline/idempotency | Existing CALL metadata/profile | Already representable. |
| Compression | INIT/ACK negotiation + payload metadata | No header change justified. |
| Resume offsets | Streaming profile/sub-protocol | Needs lifecycle semantics first. |
| Tensor metadata/zero-copy/RDMA | Negotiated specialized sub-protocol | Runtime-specific and performance-sensitive. |
| Reliability/unordered delivery | QUIC transport binding | Belongs below semantic frame. |
| Correlation groups | metadata/profile | No fixed-header benefit shown. |

A future wire proposal must demonstrate that intents, capabilities, profiles,
metadata and negotiated sub-protocols cannot meet a measurable requirement,
then include compatibility/security/cost evidence.
