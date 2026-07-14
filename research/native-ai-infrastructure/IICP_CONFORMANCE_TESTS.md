# Native AI Infrastructure Conformance Test Plan

## New test families

| Family | Required coverage |
|---|---|
| NATIVE-FRAME | magic/version/type/flags/length, truncation, oversize, invalid deterministic CBOR, duplicate keys, compression bomb. |
| NATIVE-NEGOTIATE | version downgrade, unknown custom type, optional/required profile, sub-protocol accept/reject. |
| SERVICE-LIFECYCLE | accept/reject, timeout, duplicate call, retry/idempotency, provider/client disconnect, terminal states. |
| STREAM | sequence/finality, duplicate/out-of-order event, bounded consumer/provider buffers, cancellation and partial failure. |
| ADMISSION | capacity reject, deadline expiry in queue, backpressure visibility, no unbounded queue. |
| CIP-LIFECYCLE | worker/coordinator failure, partial results, cancellation fan-out, receipt/provenance completeness, billing retry behavior. |
| MESHLLM-ADAPTER | models/readyz/health, opaque model IDs, streaming mapping, cancellation, errors, topology redaction. |
| COMPATIBILITY | HTTP fallback, TCP, QUIC, old/new framing, unknown fields/extensions/profiles. |

## Acceptance

Every normative profile requirement gets a stable fixture plus at least two
independent implementation runs. Fuzz/property tests cover native frame parsing.
No profile may claim interoperability solely from one SDK or one runtime.
