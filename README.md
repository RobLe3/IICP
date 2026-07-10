# IICP — Intent-based Inter-agent Communication Protocol

![IICP Logo](IICP_Logo.webp)

*Building the HTTP for the Age of Generative AI*

**Current version**: v1.9.0  
**Reference implementation**: [iicp.network](https://iicp.network)  
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

The directory (`iicp.network`) is **bootstrap and discovery only** and does not receive task
payloads. Tasks route to the selected execution node, whose operator can read the work it executes.
Current IICP-CX clients encrypt requests across the network and relays when a provider advertises
`cx_public_key`; this is transport confidentiality, not executor-blind inference or anonymity.

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
| [iicp-core.md](spec/v1.9/iicp-core.md) | Wire format, 14 message types, required fields, error codes, security minimums | **MUST** |
| [iicp-semantics.md](spec/v1.9/iicp-semantics.md) | Intent routing, QoS tiers, node scoring, retry policy, circuit breaker | SHOULD / MAY |
| [iicp-extensions.md](spec/v1.9/iicp-extensions.md) | Billing, reputation, MCP binding, Cooperative Inference, post-quantum | MAY / future |

### Sub-protocols

| Document | What it covers |
|----------|---------------|
| [iicp-dir.md](spec/v1.9/iicp-dir.md) | IICP-DIR: directory registration, heartbeat, discovery, peer exchange |
| [iicp-mcp-binding.md](spec/v1.9/iicp-mcp-binding.md) | MCP ↔ IICP translation rules |
| [node-capability-format.md](spec/v1.9/node-capability-format.md) | Capability object schema: intents, models, limits, availability |
| [iicp-billing-extension.md](spec/v1.9/iicp-billing-extension.md) | Credits, billing fields, receipt protocol |
| [iicp-cbor-wire.md](spec/v1.9/iicp-cbor-wire.md) | Optional CBOR wire encoding (Phase 3, `application/iicp+cbor`) |

### Conformance and governance

| Document | What it covers |
|----------|---------------|
| [IICP-core-phase1-profile.md](spec/v1.9/IICP-core-phase1-profile.md) | Phase 1 field subset — the minimum viable implementation |
| [conformance-test-suite.md](spec/v1.9/conformance-test-suite.md) | 200+ machine-verifiable test IDs (DIR-*, PROXY-*, SEC-*, CIP-*, DIR-FED-*) mapped to REACH probes |
| [validation-methodology.md](spec/v1.9/validation-methodology.md) | How to validate implementations; performance claim disclosure |
| [iicp-v1.5-overview.md](spec/v1.9/iicp-v1.5-overview.md) | What changed in v1.5; migration guide from v1.4.2 |

### Supporting assets

| Path | Contents |
|------|---------|
| [schemas/task.json](schemas/task.json) | JSON Schema 2020-12 for `IicpTask` |
| [schemas/nodelist.json](schemas/nodelist.json) | JSON Schema 2020-12 for `NodeListResponse` |
| [registry/intents.json](registry/intents.json) | Official intent URN registry |
| [spec/intent-risk-taxonomy.json](spec/intent-risk-taxonomy.json) | Shared prohibited/high-risk/transparency/minimal intent classification fixture |
| [spec/mcp-tool-risk-taxonomy.json](spec/mcp-tool-risk-taxonomy.json) | Shared MCP tool-risk and default-gating fixture |

### Archived

| Path | Contents |
|------|---------|
| [spec/archived/IICP_draft_1.4.2.txt](spec/archived/IICP_draft_1.4.2.txt) | Original monolithic Internet-Draft (archived) |

---

## Quick Start: Implement IICP

Read [IICP-core-phase1-profile.md](spec/v1.9/IICP-core-phase1-profile.md) for the minimum field subset. A Phase 1 node must:

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

## Client SDKs

Three official client SDKs (current release: **v0.7.85**) implement
both sides of the protocol — the consumer (discovery, routing, retry, fallback, CIP
consumer) and the provider (`iicp-node` runtime with backend auto-detection, NAT
escalation, relay worker/server modes, and a built-in MCP gateway). All are open-source
and published:

| Language | Install | Package registry | Source repository |
|----------|---------|------------------|-------------------|
| Python | `pip install iicp-client` | [PyPI: iicp-client](https://pypi.org/project/iicp-client/) | [github.com/RobLe3/iicp-client-python](https://github.com/RobLe3/iicp-client-python) |
| TypeScript | `npm install @iicp/client` | [npm: @iicp/client](https://www.npmjs.com/package/@iicp/client) | [github.com/RobLe3/iicp-client-typescript](https://github.com/RobLe3/iicp-client-typescript) |
| Rust | `cargo add iicp-client` | [crates.io: iicp-client](https://crates.io/crates/iicp-client) | [github.com/RobLe3/iicp-client-rust](https://github.com/RobLe3/iicp-client-rust) |

**No install at all?** [iicp.network/browser-node](https://iicp.network/browser-node)
runs a real model in your browser (WebGPU) and queries the live mesh as an IICP
consumer — with a connection console that shows every discover/dispatch wire step.

The SDKs are conformant reference clients — a good starting point for understanding the
wire format in practice. Bug reports and PRs are welcome on each repository.

### Reachability: the automatic NAT ladder

A provider node should become reachable without router surgery. The SDKs escalate
automatically: **direct** endpoint → **UPnP** pinhole → **IPv6** GUA → **relay**
auto-election from the directory (outbound bind; `transport_method=turn_relay`) →
**Quick Tunnel** (zero-account `cloudflared`; `transport_method=external_tunnel`) —
each rung tried only when the previous fails, each surfaced honestly in the node's
`exposure_mode` so discovery and scoring can see how a node is reached.

---

## Research

The protocol's normative choices are backed by simulation and analysis. The full research
record — credit economy & rate calibration, reputation/tier modelling, adversarial robustness
(FRAME8, REP, MESH), routing/multi-path selection, cryptographic trustworthiness, portable
operator identity, gamification anti-gaming, NAT traversal, and more — lives under
[`research/`](research/), indexed in [`research/RESEARCH.md`](research/RESEARCH.md).

These notes are published so the spec's decisions are **externally verifiable**: each major
parameter (tier weights, credit schedule, decay floors, EMA α, etc.) traces back to a documented
simulation or analysis. Found a flaw or have a better method? The research is meant to be
challenged — open an issue.

The live reference implementation also keeps a public research summary at
[iicp.network/research](https://iicp.network/research). Treat live-network
evidence, controlled validation, simulation and future research as different
confidence levels; do not cite simulations as production measurements.

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

See [iicp-semantics.md](spec/v1.9/iicp-semantics.md) for full term definitions.

---

## Security Baseline

All IICP implementations MUST:

- Use **TLS 1.3 minimum** for all inter-node communication
- Validate `task_id` as **UUID v4**
- Validate `intent` against `urn:iicp:intent:[a-z0-9:]+:v[1-9][0-9]*`
- Validate `timeout_ms` in range **[100, 300 000]**
- Never log or expose `payload` content
- Return **structured errors only** — no stack traces, no filesystem paths

See [conformance-test-suite.md](spec/v1.9/conformance-test-suite.md) SEC-* test IDs for machine-verifiable checks.

---

## Development Status

**Phase 5 — Cooperative Inference Protocol (active)** · *last updated 2026-06-29*

The [iicp.network](https://iicp.network) directory is live and continuously verified by conformance and live-baseline probes. The **client SDKs are published at v0.7.75** (PyPI / npm / crates.io) — each includes the full `iicp-node` provider runtime, so anyone can join the mesh today (`iicp-node init` + `iicp-node serve`). Operator onboarding is open: the operator identity system (ed25519, ADR-045 delegations), heartbeat challenge-response liveness, and the founder recognition program are live in production. The first external (non-maintainer) operator joined the mesh on 2026-06-07.

Latest public baseline, 2026-06-29: 5 active nodes, 4/5 reporting the current SDK line, 4/5 discovered nodes advertising CX/public keys, and one relay-capable node passing an HTTP JSON health probe. That means the mesh is usable, but full fail-closed privacy, relay-hardening and Phase 6/federation claims remain gated by adoption and security evidence.

| Feature area | Status | Notes |
|---|---|---|
| Core protocol — register / discover / route | ✅ Live | 48 conformance probes green continuously |
| CIP coordinator (multi-node dispatch) | ✅ Implemented | Credit receipts, response integrity verification |
| Reputation scoring | ✅ Ratified | Tier structure (§5.1.1) + bootstrap floor (§5.1.2) ratified 2026-05-24 — normative |
| Published SDKs (Python / TypeScript / Rust) | ✅ Published v0.7.75 | Full feature parity across all three — see [Client SDKs](#client-sdks) |
| Node runtime (`iicp-node`) | ✅ Published | Ships inside every SDK (`pip install iicp-client` → `iicp-node serve`) |
| Relay transport for unreachable workers | ✅ Shipped (v0.7.56) | HTTP long-poll worker transport — browsers and CGNAT operators bind outbound to a relay-capable node; consumers route through path-scoped relay endpoints with zero client changes |
| **Browser node** (WebGPU, zero install) | ✅ Live | [iicp.network/browser-node](https://iicp.network/browser-node) — runs a real model in the browser via WebLLM, queries the live mesh as an IICP consumer (with a wire-level connection console), and can serve into the mesh via a relay. First **directory-listed browser node** verified end-to-end on 2026-06-12 |
| Browser-consumable nodes (CORS) | ✅ Shipped (v0.7.56) | Every node endpoint answers CORS preflights — any https-exposed node can serve web-page consumers directly |
| Automatic NAT escalation incl. Quick Tunnel | ✅ Shipped (all 3 flavours) | Ladder: direct → UPnP → IPv6 → relay auto-election → zero-account Cloudflare Quick Tunnel fallback. Direct paths stay preferred; Quick Tunnel remains a low-friction bootstrap/fallback rather than a production availability promise |
| Signed event log + compliance attestation | ✅ Live | Every registration/heartbeat/eviction in a cryptographically signed log (federation bootstrap source); signed compliance attestation endpoint |
| Federation (Phase 6 groundwork) | 🟢 FED-READY-1 proven | Rust replica directory bootstraps from the PHP seed via snapshot + signed event tail |
| Operator identity (Ed25519 delegation) | 🟢 Phase A live | ADR-045 — operators sign a delegation binding their Ed25519 key to each node; the directory verifies + resolves a public `operator_display_name` in discovery. `operator_pubkey` is directory-private, never served. |
| Founder recognition | 🟢 Live | Time-gated founder ordinals (iicp-recognition §5.4) — #1 reserved for the maintainer, #2..N earned by genuine served nodes; dedicated non-federated signed chain |

**Estimated progress toward closed beta: ~80%**

The mesh works end-to-end, the SDKs are publicly installable with full three-language parity, and a browser tab can both consume the mesh and (via relay) serve into it. The remaining gaps before closed beta are:
- A standing public relay (the transport is built and verified; one reachable host activates browser/CGNAT serving for everyone)
- A portable operator identity wallet (so node identities survive machine changes)
- Security and authentication hardening to production standard
- Complete live SDK/key adoption and verified privacy receipts before strict fail-closed privacy wording

Follow this repo or [iicp.network](https://iicp.network) for announcements.

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| **v1.9.0** | 2026-05-30 | Security-hardening normative content: per-heartbeat reputation delta cap (§11.2), audit-report griefing cap (§11.5). Directory drift closeout: AUDIT_REPORT endpoint, Public Stats schema, free-credit rules, NODELIST health_label/exposure_mode/public_key + transport fields; credit-endpoint / SCORE_UPDATE-snapshot / tier-enum reconciliations |
| v1.8.0 | 2026-05-25 | S.13 ephemeral-by-design federation (ADR-033): HEARTBEAT/SCORE_UPDATE/REPUTATION_UPDATE removed from federated event log; snapshot+event-tail bootstrap (GET /v1/snapshot); replica registration handshake |
| v1.7.0 | 2026-05-24 | §5.1.1 tier structure + §5.1.2 bootstrap floor ratified; all 13 Phase-5 research tracks closed; mesh-health compound metric live |
| **v1.6.0** | 2026-05-23 | CIP receipt response integrity (TC-9c `response_hash`); framing spec stubs (CBOR/QUIC); 12 additional sub-protocol docs |
| v1.5.0-draft | 2026-05-15 | Spec split (core/semantics/extensions); 7 sub-protocol docs; 40 conformance test IDs; CBOR wire format |
| v1.4.2 | 2024 | Original monolithic Internet-Draft |

v1.5+ is **wire-compatible with v1.4.2** — no message opcodes, field names, or error codes changed.

---

## Reference Implementation

The reference implementation (`RobLe3/iicp.network`) is currently **private** — it will be opened once the system reaches public beta readiness. The architecture is:

| Component | Language | Purpose |
|-----------|----------|---------|
| `directory/` | PHP 8.3 + Laravel | Control plane — registration, discovery, scoring (interim, shared-hosting) |
| `iicp-directory-rs/` | Rust 2021 + axum | Control plane — permanent replacement for the PHP directory (auditable scoring compiled into one binary) |
| `adapter/` | Python 3.11 + FastAPI | Execution plane — task acceptance, backend dispatch |
| `proxy/` | Python 3.11 | Client plane — discovery, routing, retry, fallback |
| `iicp-node/` | Rust 2021 + tokio | High-performance node runtime |

The protocol specification in this repository is the authoritative source for building interoperable implementations. Third-party implementations that conform to the spec (see conformance test suite) are fully compatible with the live network.

---

## Contributing

- **Bug reports / clarifications**: Open an issue
- **New intent URNs**: Open an issue with URN, domain, and example payload
- **Protocol proposals**: Open an issue tagged `protocol-change`
- **Conformance tests**: PRs to `spec/v1.9/conformance-test-suite.md` welcome

All normative language follows RFC 2119 / BCP 14.

---

## Tools

| File | Purpose |
|------|---------|
| [tools/protocol_integrity_analysis.py](tools/protocol_integrity_analysis.py) | Analyses a spec file for internal consistency |
| [tools/quick_validation.py](tools/quick_validation.py) | Quick syntax + field validation against v1.4.2 |
