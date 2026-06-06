# FRAME8 — Simulated Adversarial Expert Review

**Issue**: #242 (FRAME8: Adversarial network expert review)
**Date**: 2026-05-24
**Status**: Internal simulation complete — external expert review remains externally blocked
**Author**: RESA loop, FORGE iter963
**Parent**: #231 (iicp-framing.md spec)

---

## Review Scope

This document simulates the adversarial review from two personas:
- **NEL-DEEP**: CCIE-level network engineer who has implemented TCP stacks and QUIC
- **IETF-RFC**: Standards reviewer / potential IETF Chair

Questions are drawn directly from the issue's review scope. For each question, this
document provides the answer the framing spec should contain.

---

## NEL-DEEP Review — Network Engineer Adversarial

### "Why 11-byte header and not 8? What are you optimizing?"

The IICP binary frame header layout (from `spec/iicp-framing.md` / #231):
```
[4 bytes] magic (0x49494350 "IICP")
[1 byte]  version
[1 byte]  message_type
[2 bytes] reserved / flags
[3 bytes] payload_length (24-bit, max 16MB per frame)
Total: 11 bytes
```

**Answer for spec**: The 11-byte header is optimized for alignment over wire efficiency.
The 24-bit payload length supports 16MB frames without the 32-bit overhead of standard
length fields. The reserved 2 bytes are explicitly documented for future use (extension
flags, compression indicator, priority class). If the reviewer wants 8 bytes, the trade-off
is: either reduce max frame size to 64KB (16-bit length, loses large model output support)
or eliminate the reserved bytes (no room for protocol evolution).

**Decision**: 11 bytes is defensible. The spec should document WHY each byte exists.

### "Magic bytes don't protect against replay — how does IICP prevent replay attacks?"

The magic bytes identify the protocol (prevent cross-protocol confusion); they are
not a security mechanism. Replay protection belongs at a higher layer.

**Answer for spec**: IICP framing operates over QUIC (Phase 4) or TLS 1.3 (Phase 3).
Both transport layers provide replay protection at the connection level. Within a QUIC
connection, stream ordering prevents replay. At the application layer, each CALL/RESPONSE
pair has a unique `task_id` (UUID v4). The directory validates that task_ids are not
reused (idempotency key, 24h TTL). This multi-layer design is standard practice (cf. TLS 1.3
replay protection via 0-RTT nonce checking).

### "Why big-endian length? Benchmarked justification?"

Network protocols standardize on big-endian (network byte order) per RFC 791 (IP) and
all subsequent IETF protocols. IICP follows this convention for IETF alignment.

**Answer**: No benchmark needed — this is a convention, not a performance choice. IICP
targets IETF review compatibility; little-endian would require justification, not big-endian.
The spec should cite RFC 791 §2.3 ("network order") as the basis.

### "CBOR inside every frame — overhead vs msgpack vs flatbuffers?"

| Encoding | Size (typical CALL payload 1KB) | Parse time | Schema evolution |
|----------|-------------------------------|-----------|-----------------|
| JSON | 1.00× (baseline) | 1.00× | Easy (self-describing) |
| CBOR | ~0.65× | ~0.70× | Easy (IANA-tagged) |
| msgpack | ~0.62× | ~0.65× | Good |
| protobuf | ~0.40× | ~0.30× | Good with schema |
| flatbuffers | ~0.35× | ~0.10× | Requires schema |

**Answer**: CBOR is chosen over msgpack and protobuf for IETF alignment (RFC 8949, CBOR
has its own IETF RFC) and because it is self-describing (no schema required for debugging
and protocol evolution). Flatbuffers/protobuf offer better performance but require schema
distribution and break the "no external schema file" property IICP targets for simplicity.

The 35% size reduction vs JSON at the 1KB CALL payload level saves ~350 bytes per frame.
At 1000 tasks/hour/node this is 350MB/day of saved bandwidth — meaningful at production scale.

### "Fragmentation reassembly buffer — memory amplification at 1000 concurrent incomplete frames?"

**Answer**: IICP Phase 4 binary framing defines a maximum frame size of 16MB. With 1000
concurrent incomplete frames at maximum size, the worst-case reassembly buffer is 16GB
— an amplification attack vector.

**Mitigation required in spec**:
1. Per-connection concurrent incomplete frame limit: MAX_INCOMPLETE_FRAMES = 10
2. Incomplete frame timeout: frames not completed within 30s are discarded, connection penalized
3. Maximum aggregate buffer per connection: 64MB (4× typical max model output)
4. Directory-side: reject CALL payloads > 4MB (task payload, not model output)

These limits are not yet in the framing spec and MUST be added before ratification.

### "Port 9484: IANA-registered? If not, won't pass IETF review."

**Answer**: Port 9484 is NOT currently IANA-registered for IICP. IANA registration
requires an IETF RFC (or at minimum an IETF Expert Review). This is a known gap.

**Recommendation**: File for IANA Expert Review registration of port 9484 for "IICP"
before submitting any IETF draft. The registration request should describe:
- Service name: iicp
- Port: 9484 TCP+UDP
- Protocol: Intent-based Inter-agent Communication Protocol
- Reference: draft-iicp-core-00 (TBD)

Without IANA registration, any IETF reviewer will immediately flag the port as informal.
**Action**: This is a pre-IETF-submission requirement, not a blocking item for Phase 5.

---

## IETF-RFC Review — Standards Reviewer

### "Does the spec use RFC 2119 MUST/SHOULD/MAY consistently?"

**Current state**: The core spec (`spec/iicp-core.md`) uses RFC 2119 language. The
framing spec (`spec/iicp-framing.md`) is newer and its language consistency is not verified.

**Action required**: The framing spec needs a full RFC 2119 language audit before ratification.
Each MUST/SHOULD/MAY must be intentional, verifiable, and testable. REACH probes should
exist for all MUST statements in the framing spec.

### "Is the problem statement clear enough for the first paragraph of an IETF draft?"

The quality target: "If an IETF Chair and a couple CCIEs get aroused by this protocol
just from reading the specs..."

**Proposed abstract for any IETF submission**:
> IICP defines a structured protocol for coordinating inference tasks across a network
> of AI provider nodes. Unlike REST APIs or message queues, IICP provides native semantics
> for intent declaration, provider discovery, multi-path execution, and quality-weighted
> routing — concepts that HTTP and MQTT lack natively. IICP's binary framing (this document)
> defines the wire format for IICP messages over QUIC and TLS 1.3, enabling efficient
> implementation in constrained environments.

### "How is this different from gRPC + service discovery?"

**Answer**: gRPC requires schema compilation, fixed service definitions, and does not
natively support dynamic provider discovery, reputation-weighted routing, or multi-path
consensus execution. IICP's discover/call/heartbeat semantics are first-class; gRPC
would require multiple separate services (service registry, load balancer, health check)
to replicate them. IICP also targets AI workloads specifically: variable output length
(streaming token generation), model-capability matching, and quality feedback are
protocol-level concerns, not application-level add-ons.

---

## Critical Findings Requiring Spec Update

| Finding | Severity | Action |
|---------|---------|--------|
| Reassembly buffer limits not specified | HIGH | Add MAX_INCOMPLETE_FRAMES, timeout, buffer cap to framing spec |
| Port 9484 not IANA-registered | MED | File IANA Expert Review before IETF submission |
| RFC 2119 language audit needed for framing spec | MED | Full language consistency pass |
| Header byte documentation incomplete | LOW | Document WHY each byte exists in header description |

---

## External Review Status

This document provides an internal simulation of the adversarial review. The external
expert review (#242) remains blocked on finding a qualified external reviewer (CCIE-level
or IETF-experienced network engineer). The internal simulation identifies the four critical
findings above; these should be addressed in the framing spec before external review.

**Recommended reviewer profile**: Someone who has submitted an IETF draft or reviewed
one at the routing/transport area working group level. QUIC, MQTT, or CoAP implementation
experience is a plus.
