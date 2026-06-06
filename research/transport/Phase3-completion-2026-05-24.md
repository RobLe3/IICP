# Transport Roadmap — Phase 3 Completion Assessment

**Issue**: #230 (Transport: IICP network-layer standard)
**Date**: 2026-05-24
**Author**: RESA loop, FORGE iter963

---

## Phase 3 Status: Mostly Complete

Per the issue's self-tracking checklist:

| Item | Status |
|------|--------|
| spec/iicp-core.md §6 transport table Phase 3 column | ✓ Done (2026-05-20) |
| ADR-002-phase1-transport.md Phase 3 resolution | ✓ Done (2026-05-20) |
| ARCHITECTURE.md §Node-to-Node: port 9484 canonical | ✓ Done (2026-05-20) |
| Adapter port migration (8080 → 9484) | ✗ Tracked as W-011 — NOT YET |
| CBOR encoding path | ✗ Not implemented |

**Phase 3 is 60% complete**. The documentation and spec work is done. Two implementation
items remain: W-011 (adapter port) and CBOR middleware.

---

## W-011: Adapter Port 8080 → 9484

**Blocker**: W-011 is the primary infrastructure blocker in warden_backlog.md. The
adapter default port is 8080; the canonical IICP port is 9484.

**Risk**: Changing the default port is a breaking change for any operator who has
deployed the adapter at port 8080 without explicit port configuration. The adapter
already accepts `IICP_PORT` environment variable override, so the migration path is:
1. Operators set `IICP_PORT=9484` explicitly in their deployment config
2. The default changes from 8080 → 9484 in a version-bumped release
3. CHANGELOG documents the breaking change

**Recommendation**: Include port migration in the Phase 5 release version bump.
Do not ship CBOR without also migrating the port — they should ship together as
"transport hardening release."

---

## CBOR Encoding Path

**What CBOR buys**: ~30–45% payload size reduction for structured task payloads
(task_id, intent, payload fields compress well with CBOR). Negligible latency impact
at current mesh scale (8 nodes, low throughput).

**Implementation scope**:

### Adapter (Python, FastAPI):

```python
# requirements.txt: cbor2 (already in adapter .venv per test coverage)
from cbor2 import dumps as cbor_dumps, loads as cbor_loads

# Middleware: if Accept: application/cbor → respond in CBOR
# Middleware: if Content-Type: application/cbor → decode CBOR body
```

FastAPI middleware (~30 lines) that detects `Content-Type: application/cbor` and
`Accept: application/cbor` headers, decoding/encoding with cbor2.

### Directory (PHP):

```bash
composer require 2tvenom/cborencode
```

Laravel middleware (~40 lines) that intercepts CBOR requests and responses.
Add `Content-Type: application/cbor` handling to HeartbeatController,
RegisterController, and DiscoverController.

### Spec requirement (existing):

From spec/iicp-core.md §6 (Phase 3 column): CBOR is OPTIONAL for Phase 3.
Nodes that don't advertise CBOR support fall back to JSON. CBOR is SHOULD
(not MUST) in Phase 3; it becomes MUST in Phase 4 for node-to-node traffic.

---

## Phase 4 Roadmap Items (Post-Phase-5)

| Item | Effort | Dependency |
|------|--------|-----------|
| QUIC transport (port 9484 UDP) | HIGH — quinn crate + aioquic | Stable Phase 5 deployment |
| CBOR as default encoding | LOW — already defined | CBOR optional (Phase 3) already done |
| IICP binary framing | HIGH — new spec section needed | #231 framing spec |
| Post-quantum crypto | VERY HIGH | Phase 4 stretch goal |

---

## Conclusion

**Phase 3 transport is documentation-complete**. The two remaining implementation items
(W-011 port, CBOR middleware) should be bundled with the Phase 5 CIP release as a
"transport hardening" component. They do not need to block CIP implementation.

**Code impact assessment**:
- CBOR middleware: implement in Phase 5 release (OPTIONAL, ~70 lines total)
- W-011 port: implement in Phase 5 release (breaking change, requires version bump + CHANGELOG)
- No changes to existing API contracts — CBOR is additive; JSON remains supported
