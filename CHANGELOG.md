# IICP Changelog

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
