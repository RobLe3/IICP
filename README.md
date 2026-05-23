# IICP — Intent-based Inter-agent Communication Protocol

![IICP Logo](IICP_Logo.webp)

*Building the HTTP for the Age of Generative AI*

**Current version**: v1.6.0  
**Reference implementation**: [iicp.network](https://github.com/RobLe3/iicp.network)  
**Status**: Active development — Phase 5 (Cooperative Inference Protocol)

---

## What Is IICP?

IICP is an open protocol that lets AI agents discover each other, negotiate capabilities, and route tasks across a distributed network — without any central broker owning the compute or controlling the data.

```
Agent A  ──CALL──▶  IICP Node B  ──▶  LLM Backend
              ▲
              │  discovery
         iicp.network
         (directory only —
          no payload passes through)
```

The directory (`iicp.network`) is **bootstrap and discovery only**. Task payloads route directly between nodes, peer-to-peer. No central party can see, throttle, or monetise your AI traffic.

### The core idea

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440001",
  "intent":  "urn:iicp:intent:llm:chat:v1",
  "payload": { "messages": [{ "role": "user", "content": "Summarise this doc." }] },
  "constraints": { "timeout_ms": 5000, "qos": "interactive" }
}
```

An **intent URN** expresses what you want, not which model or endpoint to call. The network finds the best available node that can serve that intent, routes the task, and returns a structured response.

---

## Specification Documents

### Core (read these first)

| Document | What it covers | Normative level |
|----------|---------------|-----------------|
| [iicp-core.md](spec/v1.5/iicp-core.md) | Wire format, 14 message types, required fields, error codes, security minimums | **MUST** |
| [iicp-semantics.md](spec/v1.5/iicp-semantics.md) | Intent routing, QoS tiers, node scoring, retry policy, circuit breaker | SHOULD / MAY |
| [iicp-extensions.md](spec/v1.5/iicp-extensions.md) | Billing, reputation, MCP binding, Cooperative Inference, post-quantum | MAY / future |

### Sub-protocols

| Document | What it covers |
|----------|---------------|
| [iicp-dir.md](spec/v1.5/iicp-dir.md) | IICP-DIR: directory registration, heartbeat, discovery, peer exchange |
| [iicp-mcp-binding.md](spec/v1.5/iicp-mcp-binding.md) | MCP ↔ IICP translation rules |
| [node-capability-format.md](spec/v1.5/node-capability-format.md) | Capability object schema: intents, models, limits, availability |
| [iicp-billing-extension.md](spec/v1.5/iicp-billing-extension.md) | Credits, billing fields, receipt protocol |
| [iicp-cbor-wire.md](spec/v1.5/iicp-cbor-wire.md) | Optional CBOR wire encoding (Phase 3, `application/iicp+cbor`) |

### Conformance and governance

| Document | What it covers |
|----------|---------------|
| [IICP-core-phase1-profile.md](spec/v1.5/IICP-core-phase1-profile.md) | Phase 1 field subset — the minimum viable implementation |
| [conformance-test-suite.md](spec/v1.5/conformance-test-suite.md) | 40 machine-verifiable test IDs (DIR-REG, PROXY-ROUTE, SEC-*, etc.) |
| [validation-methodology.md](spec/v1.5/validation-methodology.md) | How to validate implementations; performance claim disclosure |
| [iicp-v1.5-overview.md](spec/v1.5/iicp-v1.5-overview.md) | What changed in v1.5; migration guide from v1.4.2 |

### Supporting assets

| Path | Contents |
|------|---------|
| [schemas/task.json](schemas/task.json) | JSON Schema 2020-12 for `IicpTask` |
| [schemas/nodelist.json](schemas/nodelist.json) | JSON Schema 2020-12 for `NodeListResponse` |
| [registry/intents.json](registry/intents.json) | Official intent URN registry |

### Previous version

| Path | Contents |
|------|---------|
| [spec/v1.4/IICP_draft_1.4.2.txt](spec/v1.4/IICP_draft_1.4.2.txt) | Original monolithic Internet-Draft (archived) |

---

## Quick Start: Implement IICP

Read [IICP-core-phase1-profile.md](spec/v1.5/IICP-core-phase1-profile.md) for the minimum field subset. A Phase 1 node must:

1. **Register** — `POST /v1/register` with `{endpoint, region, capabilities[], limits}`
2. **Heartbeat** — `POST /v1/heartbeat` every 30 s with `{load, active_jobs}`
3. **Accept tasks** — `POST /v1/task` — validate UUID-v4 `task_id`, intent URN, `timeout_ms` bounds
4. **Discover peers** — `GET /v1/discover?intent=urn:iicp:intent:llm:chat:v1`
5. **Return structured errors** — never raw exceptions; always `{"error": {"code": "IICP-Exxx", ...}}`

### Conformance levels

| Level | Documents to satisfy | Typical implementer |
|-------|---------------------|---------------------|
| **Core** | iicp-core.md MUSTs only | Minimal node, embedded device |
| **Phase 1** | Core + IICP-core-phase1-profile.md | Reference implementation |
| **Phase 2** | Phase 1 + iicp-dir.md §3.6 (peers) | Mesh node |
| **Phase 3+** | Phase 2 + billing/reputation extensions | Full CIP node |

---

## Intent URN Registry

Intent URNs identify *what* is being requested, independent of model or backend:

```
urn:iicp:intent:<domain>:<action>:v<version>
```

Examples from [`registry/intents.json`](registry/intents.json):

| URN | Purpose |
|-----|---------|
| `urn:iicp:intent:llm:chat:v1` | Conversational LLM completion |
| `urn:iicp:intent:llm:embedding:v1` | Text embedding / vector |
| `urn:iicp:intent:llm:summarise:v1` | Document summarisation |
| `urn:iicp:intent:vision:describe:v1` | Image-to-text description |
| `urn:iicp:intent:audio:transcribe:v1` | Speech-to-text |

To propose a new intent, open an issue with the URN, domain justification, and example payload.

---

## Node Discovery and Scoring

The directory scores nodes server-side at query time. Clients receive a pre-sorted list and may only filter (remove `available=false` nodes or those with open circuit breakers).

**Phase 3 scoring formula** (currently deployed):

```
score = 0.35 × availability_factor
      + 0.28 × (1 − normalized_load)
      + 0.18 × capacity_ratio
      + 0.09 × region_match
      + 0.10 × reputation_score
```

See [iicp-semantics.md](spec/v1.5/iicp-semantics.md) for full term definitions.

---

## Security Baseline

All IICP implementations MUST:

- Use **TLS 1.3 minimum** for all inter-node communication
- Validate `task_id` as **UUID v4**
- Validate `intent` against `urn:iicp:intent:[a-z0-9:]+:v[1-9][0-9]*`
- Validate `timeout_ms` in range **[100, 300 000]**
- Never log or expose `payload` content
- Return **structured errors only** — no stack traces, no filesystem paths

See [conformance-test-suite.md](spec/v1.5/conformance-test-suite.md) SEC-* test IDs for machine-verifiable checks.

---

## Development Status

**Phase 5 — Cooperative Inference Protocol (active)**

The reference implementation at [iicp.network](https://iicp.network) is live. Nodes can register, serve tasks, and earn credits today.

| Feature area | Status | Notes |
|---|---|---|
| Core protocol — register / discover / route | ✅ Live | 37 conformance probes green continuously |
| CIP coordinator (multi-node dispatch) | ✅ Implemented | Credit receipts, response integrity verification |
| Rust node runtime (`iicp-node`) | ✅ Working | `curl -L https://iicp.network/install.sh \| sh` |
| Reputation scoring | 🟡 Spec-complete | REP1/REP2 pending Protocol Steward ratification |
| Operator identity (anti-Sybil) | 🔴 Design phase | ADR-030 — Ed25519 key pair, multi-node ownership |
| Published SDKs (Python / TypeScript / Rust) | 🔴 Not yet | PyPI / npm / crates.io publication pending |

**Estimated progress toward closed beta: ~60%**

The mesh works end-to-end. The main gap before closed beta is a portable operator identity system (so node operators have a persistent, recoverable identity across machines) and published SDK packages for easy client integration.

To run a node today: `curl -L https://iicp.network/install.sh | sh`

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| **v1.6.0** | 2026-05-23 | CIP receipt response integrity (TC-9c `response_hash`); framing spec stubs (CBOR/QUIC); 12 additional sub-protocol docs |
| v1.5.0-draft | 2026-05-15 | Spec split (core/semantics/extensions); 7 sub-protocol docs; 40 conformance test IDs; CBOR wire format |
| v1.4.2 | 2024 | Original monolithic Internet-Draft |

v1.5+ is **wire-compatible with v1.4.2** — no message opcodes, field names, or error codes changed.

---

## Reference Implementation

The reference implementation lives at **[RobLe3/iicp.network](https://github.com/RobLe3/iicp.network)**:

| Component | Language | Purpose |
|-----------|----------|---------|
| `directory/` | PHP 8.3 + Laravel | Control plane — registration, discovery, scoring |
| `adapter/` | Python 3.11 + FastAPI | Execution plane — task acceptance, backend dispatch |
| `proxy/` | Python 3.11 | Client plane — discovery, routing, retry, fallback |
| `iicp-node/` | Rust 2021 + tokio | High-performance node runtime |

---

## Contributing

- **Bug reports / clarifications**: Open an issue
- **New intent URNs**: Open an issue with URN, domain, and example payload
- **Protocol proposals**: Open an issue tagged `protocol-change`
- **Conformance tests**: PRs to `spec/v1.5/conformance-test-suite.md` welcome

All normative language follows RFC 2119 / BCP 14.

---

## Tools

| File | Purpose |
|------|---------|
| [tools/protocol_integrity_analysis.py](tools/protocol_integrity_analysis.py) | Analyses a spec file for internal consistency |
| [tools/quick_validation.py](tools/quick_validation.py) | Quick syntax + field validation against v1.4.2 |
