# IICP and MeshLLM Integration Assessment

## Recommended boundary

`client/agent → IICP intent + constraints → MeshLLM OpenAI surface → MeshLLM runtime`

MeshLLM exposes model inventory, readiness, health, OpenAI-compatible requests
and streaming. It intentionally keeps model resolution, peer routing, stage
placement, activation movement, speculative decode, checkpoint/restore and
runtime recovery behind that boundary. IICP should preserve it.

## Responsibility map

| Responsibility | Classification | IICP role |
|---|---|---|
| Public API and model discovery | B: optionally use IICP | Translate advertised capabilities; do not reinterpret opaque model IDs. |
| Provider discovery/policy/routing | A: standardizable | IICP discovery, constraints, identity, trust and receipts. |
| Public request streaming/cancellation | D: extension/profile needed | Standard streaming and cancellation profile over IICP. |
| Peer discovery | C: MeshLLM-specific | No MeshLLM topology in IICP directory/public output. |
| Model placement and stage scheduling | C: MeshLLM-specific | Expose only readiness/capacity at provider boundary. |
| Activation transport and tensor dtype | C now; E for generic future | Keep internal; research generic sub-protocol only. |
| KV cache/checkpoint/restore | C: MeshLLM-specific | IICP may receive summarized failure/result evidence only. |
| Cooperative whole-task execution | A/B | CIP-compatible coordinator semantics. |
| Runtime telemetry | B/D | Redacted aggregate receipt/profile, never peer topology by default. |

## Architecture decision

| Architecture | Verdict | Reason |
|---|---|---|
| A: IICP public edge | Recommended now | Maximum interoperability, minimum coupling. |
| B: IICP public edge + peer routing | Conditional | Useful only where IICP selects logical providers; MeshLLM keeps internal peers. |
| C: negotiated distributed-inference sub-protocol | Research only | Appropriate experiment if multiple runtimes need common stage semantics. |
| D: generic CALL/RESPONSE for every stage | Rejected by default | Skippy traffic has large activations, tight decode RTT, cache state and recovery semantics not expressed by generic calls. |

## Why stage traffic is different

MeshLLM documents activation frames up to roughly MiB-scale for prefill and
per-token decode activation traffic. It also uses stage generation negotiation,
direct prediction return, bounded reply credit, dtype choices, checkpoint state
and speculative windows. Generic request/response cannot claim equivalent
performance or correctness without a dedicated negotiated protocol and direct
benchmark evidence.

## Migration stages

1. Maintain MeshLLM as a named IICP backend via its public API.
2. Add IICP streaming/cancellation/capacity profiles and adapter conformance.
3. Compare whole-task IICP routing with direct OpenAI-compatible forwarding.
4. Only then evaluate a runtime-neutral distributed-inference sub-protocol.
