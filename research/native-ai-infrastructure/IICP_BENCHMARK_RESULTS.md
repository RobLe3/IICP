# IICP Native AI Infrastructure Benchmark Results

## Scope and status

This is a **local encoding baseline**, not an end-to-end protocol performance
claim. It measures in-process JSON and deterministic-CBOR serialization of the
same synthetic invocation-shaped value. It does **not** compare HTTP/1.1,
HTTP/2, HTTP/3, gRPC, TCP, QUIC, or MeshLLM/Skippy transport, and it reports no
throughput, allocation, copy, WAN, streaming, or inference claim.

Raw local artifact: `iicp-protocol-lab/results/encoding-baseline-2026-07-14.jsonl`
(the lab deliberately ignores generated result artifacts). The table below is a
verbatim transcription of that artifact.

## Environment

| Field | Value |
|---|---|
| Timestamp | 2026-07-14T10:13:03Z |
| Host | Apple M3 Max, arm64 |
| Memory | 128 GiB unified memory |
| OS | Darwin 25.5.0 |
| Rust | rustc/cargo 1.96.1 |
| Lab | `iicp-protocol-lab` local baseline, unoptimised `cargo run` |
| Encoding samples | 100 sequential encodes per payload and codec; median reported |
| Frame assumption | 12-byte experimental IICP envelope added to CBOR encoded size |

The synthetic map contains a UUID-like task ID, `urn:iicp:intent:llm:chat:v1`,
a repeated text payload, and a timeout constraint. This is a size/serialization
probe only; it is not a complete protocol message or a normative wire vector.

## Results

| Payload bytes | JSON bytes | CBOR bytes | CBOR + 12-byte envelope | JSON median encode ns | CBOR median encode ns |
|---:|---:|---:|---:|---:|---:|
| 64 | 201 | 184 | 196 | 14,792 | 3,083 |
| 256 | 393 | 377 | 389 | 26,750 | 3,208 |
| 1,024 | 1,161 | 1,145 | 1,157 | 102,084 | 4,833 |
| 4,096 | 4,233 | 4,217 | 4,229 | 180,000 | 2,708 |
| 32,768 | 32,905 | 32,889 | 32,901 | 758,416 | 1,750 |
| 131,072 | 131,209 | 131,195 | 131,207 | 2,767,750 | 2,917 |
| 1,048,576 | 1,048,713 | 1,048,699 | 1,048,711 | 22,298,208 | 28,500 |

## Interpretation

For this repetitive, text-heavy synthetic shape, deterministic CBOR was 16–17
bytes smaller than JSON before the experimental 12-byte native envelope. The
local timings suggest serialization deserves further measurement, but they do
**not** establish wire-level latency, server efficiency, QUIC behavior, or a
benefit over established RPC stacks. Results are sensitive to payload shape,
compiler optimization, allocator, CPU, and benchmark design.

The evidence supports retaining the current default position: keep the fixed
frame small; evaluate semantics, profiles, and negotiated sub-protocols before
considering a base-frame change.

## Implemented lab checks

The lab currently verifies:

- deterministic fixed-envelope round trip and malformed-frame rejection;
- a bounded reference stream with terminal cancellation;
- a loopback QUIC endpoint can bind a UDP socket;
- MeshLLM public-edge readiness/model discovery, filtering of the experimental
  `mesh` virtual model, and refusal of a selected model not in the inventory.

These checks do **not** yet prove QUIC stream multiplexing, end-to-end
cancellation propagation, or MeshLLM streaming translation.

## Required next benchmark phases

1. Add release-mode repeated benchmarks with allocation/copy instrumentation.
2. Compare HTTP/1.1, HTTP/2, HTTP/3, gRPC, IICP/TCP and IICP/QUIC under the
   same local and shaped-WAN harness.
3. Add token-stream fairness, cancellation delay, provider overload and
   connection-migration scenarios.
4. Run a MeshLLM whole-task benchmark only through its public API boundary.
5. Treat Skippy activation/checkpoint traffic as a separate, opt-in
   sub-protocol experiment; compare it directly with existing Skippy transport
   before making any standardization or performance claim.
