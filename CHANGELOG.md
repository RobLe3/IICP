# IICP Changelog

## Unreleased — lifecycle runtime-control parity 2026-07-16

Recorded three-SDK parity for the pre-normative cancellation and bounded
observation fixture. The TypeScript OpenAI-compatible path demonstrates
task-scoped HTTP abort propagation for Ollama, LM Studio, vLLM and MeshLLM.
This does not change ordinary node routes, the wire protocol, or backend-private
execution and recovery semantics.

## Unreleased — registry profile experimental-candidate decision 2026-07-16

Recorded that the fixture-gated intent/capability/extension registry proposal
has completed its cross-implementation experimental-candidate gate. It remains
pre-normative: stable URNs, the v1.9 suite and runtime defaults are unchanged.
Normative promotion requires a separate reviewed release with independent
implementation or adoption evidence.

## Unreleased — non-normative strategic research 2026-07-11

Added a public research note on layered intent, capability, policy, evidence
and extension profiles. The note records reproducible compatibility,
receipt-boundary and selection-screening results. **It does not change the
v1.9 Protocol Suite, registry, or wire compatibility.** Any future normative
change remains subject to the spec-source release and conformance-fixture gates.

## Unreleased — reference synchronization 2026-07-10

The v1.9 working set has been synchronized from the reference repository without changing the
Protocol Suite version. It includes authenticated dispatch-route contracts, signed node-policy
manifests, operator-wallet credit semantics, relay-bind hardening, updated compliance methodology,
and the completed `cx_public_key` naming cutover. The directory now emits only canonical
`cx_public_key`; maintained clients may retain the retired CX `public_key` read fallback for one
further compatibility release. Node-detail `public_key` remains the distinct Ed25519 gossip key.

Machine-readable intent-risk and MCP-tool-risk taxonomies are now included so independent
implementations can reproduce policy gates rather than relying on website prose.

## v1.9.0 — 2026-05-30

### Summary

Security-hardening normative content from the red-team Block-1 audit, plus a code↔spec
drift closeout that documents endpoints and rules the reference implementation already shipped.

### Updated documents

| File | Change |
|------|--------|
| `iicp-semantics.md` | §11.2 per-heartbeat positive reputation-delta cap (+0.10) MUST (RT-01). §11.5 peer audit-report griefing cap — per-reporter 24h limit + max 2 distinct reporters' deltas per target/day MUST (RT-05). Spec v1.1.0 → 1.3.0. |
| `iicp-dir.md` | §3.9 AUDIT_REPORT endpoint; §3.9b Public Stats (`GET /v1/stats`) schema; §3.10 free-credit allocation rules; §3.4 NODELIST `health_label`/`exposure_mode`/`public_key` + transport fields; §7 credit-endpoint names corrected to shipped routes; §3.7 event-type enum reconciled to snapshot+event-tail model; probation clarified node-detail-only. Spec v0.7.0 → 0.9.0. |
| `iicp-cooperative-inference.md` | §5.1.1 `reputation_tier` enum floor reconciled `none` → `bronze` (matches reference impl). Spec v0.6.8 → 0.6.9. |
| `iicp-telemetry.md` | §4 SCORE_UPDATE reconciled to the snapshot model — directory MUST update the reputation snapshot; discrete event emission OPTIONAL. |

### Wire compatibility

No wire-format changes. New normative caps constrain reputation accounting; new sections
document already-shipped endpoints. Versioning discipline: this is ONE consolidated MINOR
bump for the entire 2026-05-30 spec session (anti-inflation; see VERSIONING.md).

---

## v1.8.0 — 2026-05-25

### Summary

S.13 ephemeral-by-design federation (ADR-033).

### Updated documents

| File | Change |
|------|--------|
| `iicp-federated-directory.md` | v0.3.0: HEARTBEAT/SCORE_UPDATE/REPUTATION_UPDATE removed from the federated event log (snapshot + event-tail model); new `GET /v1/snapshot` bootstrap endpoint. v0.2.0: replica registration handshake (`POST /v1/replicas/register`). |

### Wire compatibility

No wire-format changes. Federated event-log set reduced to durable events only.

---

## v1.7.0 — 2026-05-24

### Summary

v1.7 ratifies the previously PENDING reputation tier structure and bootstrap traffic floor
in S.12 (CIP spec), completing the Phase 5 research validation cycle. All 13 Phase 5
research tracks are closed. The mesh health compound metric (T3) goes live in the
reference implementation.

### Updated documents

| File | Change |
|------|--------|
| `iicp-cooperative-inference.md` | §5.1.1 Tier Structure: PENDING → RATIFIED 2026-05-24. Tier thresholds Silver ≥ 0.40, Gold ≥ 0.65, Platinum ≥ 0.85 + 720h identity-age gate, general reputation update rules (+0.01/−0.05) now normative. §5.1.2 Bootstrap Traffic Floor: PENDING → RATIFIED 2026-05-24. Floor rule normative (1 slot/session, pool ≥ 3 Silver+ guard). Spec version: 0.6.2-draft → 0.6.8. |

### Research tracks closed (Phase 5)

All 13 Phase 5 research tracks confirmed closed:
REP1/REP2 (#168) · REP5 (#171) · REP6 (#172) · MESH1–4 (#180–183) · MESH5 (#184) ·
Transport Phase 3 (#230) · FRAME8 (#242) · Portable identity (#277 #307) · WASM (#292)

### Wire compatibility

No wire format changes. Previously advisory reputation parameters are now normative.

---

## v1.6.0 — 2026-05-23

### Summary

v1.6 adds CIP receipt response integrity verification, expands the sub-protocol suite with 12 additional documents, and introduces the binary framing specification stubs for the Phase 3+ transport roadmap (QUIC + CBOR). The wire format is unchanged.

### Updated documents

| File | Change |
|------|--------|
| `iicp-cooperative-inference.md` | §10.3 canonical message now includes `response_hash` (SHA-256 of canonical result JSON). Coordinator MUST verify hash before returning response and before submitting credit award (TC-9c). |
| `iicp-core.md` | §1 Protocol scope: credit economy clarified as directory-layer optional extension (ADR-031). §6 transport roadmap stub added (QUIC + CBOR Phase 3+). |
| `iicp-dir.md` | Optional extensions section added grouping credit endpoints under `IICP-DIR-EXT-CREDITS`. |
| `conformance-test-suite.md` | DIR-REG-08/09 test IDs annotated; test suite at v4.32.0. |

### New documents (added since v1.5)

| File | Description |
|------|-------------|
| `iicp-framing.md` | Binary framing specification — custom opcode range 0xF0–0xFE, CBOR payload encoding, QUIC stream mapping (Phase 3+ roadmap) |
| `iicp-recognition.md` | Gamification and operator recognition framework — passive scoring, operator leaderboards, badge taxonomy |
| `iicp-federated-directory.md` | Federated directory protocol — Genesis Seed, replica tiers, gossip (Phase 6 roadmap) |
| `iicp-semantics.md` | Routing semantics — intent matching, QoS tiers, ε-greedy node selection, multi-path |
| `iicp-telemetry.md` | Telemetry extension — W3C traceparent, OTel span attributes, proxy reporting |
| `iicp-mcp-binding.md` | MCP ↔ IICP translation rules |
| `iicp-billing-extension.md` | Credit economy extension — earn/spend/quote, HMAC receipts |

### Wire compatibility

v1.6 is **fully wire-compatible with v1.4.x and v1.5**. The `response_hash` field in `CIPWorkerReceipt` is a CIP-specific addition and does not affect non-CIP task routing.

---

## v1.5.0-draft — 2026-05-15

### Summary

v1.5 reorganises the v1.4.2 monolithic Internet-Draft into a structured set of focused documents. **The wire format is unchanged.** Any v1.4.x implementation is automatically v1.5 Core conformant.

### New documents

| File | Description |
|------|-------------|
| `spec/v1.5/iicp-core.md` | MUST-only requirements extracted from v1.4.2 — the minimal conformance baseline |
| `spec/v1.5/iicp-semantics.md` | SHOULD/MAY routing, QoS, node selection, retry, circuit breaker |
| `spec/v1.5/iicp-extensions.md` | MAY/future: billing, reputation, CIP, post-quantum, MCP binding |
| `spec/v1.5/iicp-dir.md` | IICP-DIR sub-protocol: registration, heartbeat, discovery, peer exchange |
| `spec/v1.5/iicp-mcp-binding.md` | Formal MCP ↔ IICP translation specification |
| `spec/v1.5/node-capability-format.md` | Capability object JSON schema and semantics |
| `spec/v1.5/iicp-billing-extension.md` | Credits, billing fields, receipt protocol |
| `spec/v1.5/IICP-core-phase1-profile.md` | Phase 1 field subset (minimum viable implementation) |
| `spec/v1.5/conformance-test-suite.md` | 40 machine-verifiable test IDs across 8 categories |
| `spec/v1.5/validation-methodology.md` | Implementation validation approach; performance claim disclosure |
| `spec/v1.5/iicp-cbor-wire.md` | Optional CBOR wire encoding (Phase 3) |
| `spec/v1.5/iicp-v1.5-overview.md` | Change summary and migration guide |
| `schemas/task.json` | JSON Schema 2020-12 for `IicpTask` |
| `schemas/nodelist.json` | JSON Schema 2020-12 for `NodeListResponse` |
| `registry/intents.json` | Official intent URN registry |

### What did NOT change (wire-compatible)

- Message opcodes: INIT, ACK, CALL, RESPONSE, PING, PONG, CLOSE
- Intent URN format: `urn:iicp:intent:<domain>:<action>:v<N>`
- Required field names: `task_id`, `intent`, `payload`, `constraints`, `auth`
- Error code semantics
- Phase 1 conformance requirements

### Repository restructuring

```
Before (v1.4.2):           After (v1.5):
─────────────────          ────────────────────────────
IICP_draft_1.4.2.txt       spec/v1.4/IICP_draft_1.4.2.txt  (archived)
README.md                  spec/v1.5/iicp-core.md
                           spec/v1.5/iicp-semantics.md
                           spec/v1.5/iicp-extensions.md
                           spec/v1.5/iicp-dir.md
                           spec/v1.5/... (11 total)
                           schemas/task.json
                           schemas/nodelist.json
                           registry/intents.json
                           tools/  (moved from root)
```

---

## v1.4.2 — 2024

Original Internet-Draft. Single monolithic document. Archived at `spec/v1.4/IICP_draft_1.4.2.txt`.

## Unreleased

- Added fixture-gated, pre-normative profile proposals and their digest-pinned
  compatibility fixture. These documents are explicitly outside the ratified
  suite and introduce no wire-contract change.
- Clarified the v1.9 routing-authority boundary: directories own canonical
  scores and hard eligibility, while a declared client selection profile may
  choose only within the eligible set and must preserve directory evidence.
  Legacy clients continue to use directory recommendation order.
