# IICP Conformance Test Suite

**Version**: 0.1.0  
**Date**: 2026-05-14  
**Status**: draft  
**Issue**: #22  
**Authority**: Protocol Steward + Integration Validator  
**Relation**: IICP-core-phase1-profile.md, IICP-DIR §3, ADR-008

---

## 1. Purpose

This document defines the conformance test suite for IICP Phase 1 implementations.
A conformant Phase 1 implementation MUST pass all MUST-level tests in §3–§7.

Tests are organized by component role: Directory, Provider Node (Adapter), and Client (Proxy).

---

## 2. Test Environment

### Required stack

```bash
docker compose up -d   # brings up directory + adapter + database
```

### Environment variables

| Variable | Default | Notes |
|----------|---------|-------|
| `DIRECTORY_URL` | `http://localhost:8010` | Directory base URL |
| `ADAPTER_URL` | `http://localhost:8020` | Adapter base URL |
| `NODE_TOKEN` | `test-integration-token` | Pre-shared test token |

### Test marks

| Mark | Meaning |
|------|---------|
| `@conformance` | Required for Phase 1 conformance |
| `@slow` | May take > 10s (heartbeat expiry, rate limit) — skip with `-m 'not slow'` |
| `@phase2` | Not required for Phase 1; skip unless testing Phase 2 |

---

## 3. Directory Conformance Tests

### 3.1 Registration (MUST)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `DIR-REG-01` | `POST /v1/register` with valid payload → 201 | Body contains `node_id`, `node_token` |
| `DIR-REG-02` | `POST /v1/register` missing `endpoint` → 422 | Body contains `error.code = "validation_error"` |
| `DIR-REG-03` | `POST /v1/register` missing `capabilities` → 422 | Body contains `error.code = "validation_error"` |
| `DIR-REG-04` | `POST /v1/register` with unreachable endpoint → 422 | Body contains `error.code = "liveness_failed"` |
| `DIR-REG-05` | `node_token` in response is ≥ 32 bytes (hex-encoded) | Verify length ≥ 64 hex chars |
| `DIR-REG-06` | `node_id` assigned by directory when absent | Response `node_id` is valid UUID-v4 |
| `DIR-REG-07` | `node_token` stored as bcrypt hash, never plaintext | Code review: `NodeRegistry` uses `Hash::make()` before insert |

### 3.2 Heartbeat (MUST)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `DIR-HB-01` | `POST /v1/heartbeat` with valid token → 200 | Body contains `ok: true`, `next_heartbeat_ms` |
| `DIR-HB-02` | `POST /v1/heartbeat` with invalid token → 401 | Body contains `error.code = "unauthorized"` |
| `DIR-HB-03` | `POST /v1/heartbeat` for unknown node_id → 404 | Body contains `error.code = "not_found"` |
| `DIR-HB-04` | Node not seen for > 90s excluded from discover | Poll discover after 90s silence |
| `DIR-HB-05` | `POST /v1/peers` (PEER_EXCHANGE) with invalid token → 401 | `@phase2` — not required for Phase 1 conformance |

### 3.3 Discovery (MUST)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `DIR-DISC-01` | `GET /v1/discover?intent=...` → 200 | Body contains `nodes[]`, `count` |
| `DIR-DISC-02` | Nodes sorted by score descending | `nodes[0].score >= nodes[1].score` |
| `DIR-DISC-03` | All returned nodes have `available: true` | No unavailable node in results |
| `DIR-DISC-04` | Scores are in range [0.1, 1.0] | Per ADR-008 minimum threshold |
| `DIR-DISC-05` | `?limit=N` respected (max 50) | Exactly min(N, available) nodes returned |
| `DIR-DISC-06` | `?region=X` returns region-matched nodes with higher scores | Region-matched node scores ≥ unmatched when equally loaded |
| `DIR-DISC-07` | Nodes with score < 0.1 excluded | No low-score nodes in results |

### 3.4 Rate Limiting (MUST)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `DIR-RL-01` | > 10 `POST /v1/register` requests per minute per IP → 429 | `error.code = "rate_limited"` |

### 3.5 Node Detail (SHOULD)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `DIR-NODE-01` | `GET /v1/node/{id}` for registered node → 200 | Node object with capabilities |
| `DIR-NODE-02` | `GET /v1/node/{unknown}` → 404 | `error.code = "not_found"` |

---

## 4. Provider Node (Adapter) Conformance Tests

### 4.1 Task Submission (MUST)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `NODE-TASK-01` | `POST /v1/task` with valid payload → 200 or 502 | Structured JSON, never raw exception |
| `NODE-TASK-02` | Response contains `task_id` matching request | `response.task_id == request.task_id` |
| `NODE-TASK-03` | Response contains `status` field | One of `success`, `error`, `timeout` |
| `NODE-TASK-04` | Response contains `metrics.latency_ms` | Numeric value ≥ 0 |
| `NODE-TASK-05` | `POST /v1/task` with invalid/missing token → 401 | `error.code = "unauthorized"` |
| `NODE-TASK-06` | `POST /v1/task` with duplicate `task_id` → 409 | `error.code = "conflict"` |
| `NODE-TASK-07` | Backend error returns 502, not raw exception | No `Traceback` in response body |
| `NODE-TASK-08` | Response never exposes internal file paths | No `/Users/`, `/home/`, `/var/` in body |

### 4.2 Health (MUST)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `NODE-HEALTH-01` | `GET /iicp/health` → 200 | `status` in (`ok`, `degraded`) |
| `NODE-HEALTH-02` | Health response contains `load`, `active_jobs` | Numeric values |
| `NODE-HEALTH-03` | `Content-Type: application/json` on all responses | Header present |

### 4.3 Concurrency Gate (MUST)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `NODE-CONC-01` | Tasks beyond `max_concurrent` → 429 | `error.code = "overloaded"` |

### 4.4 Registration on Startup (SHOULD)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `NODE-REG-01` | Adapter registers with directory on startup | Node appears in discover after adapter start |
| `NODE-REG-02` | Heartbeat sent every 30s | Directory `last_seen` updated within 35s |

---

## 5. Client (Proxy) Conformance Tests

### 5.1 Task Routing (MUST)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `PROXY-ROUTE-01` | Proxy discovers nodes via directory before routing | Discover called before task submission |
| `PROXY-ROUTE-02` | Proxy submits to highest-scored node | First node in discover response is used |
| `PROXY-ROUTE-03` | Proxy retries on node failure (≤ 3 attempts) | Task succeeds after first node fails |
| `PROXY-ROUTE-04` | All retries exhausted → structured error | `error.code` not empty; no raw exception |
| `PROXY-ROUTE-05` | TLS certificate validated on all connections | Reject self-signed certs in non-test mode |

### 5.2 Timeout Handling (MUST)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `PROXY-TIMEOUT-01` | Node timeout → retry with next node | Next node attempted within backoff window |
| `PROXY-TIMEOUT-02` | All nodes timeout → error with `code = "timeout"` | Structured error |

### 5.3 OpenAI Compat Interface (SHOULD)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `PROXY-OAI-01` | `POST /v1/chat/completions` translates to IICP CALL | Intent mapped to `urn:iicp:intent:llm:chat:v1` |
| `PROXY-OAI-02` | Response translates to OpenAI format | `choices[0].message.content` present |

---

## 6. Protocol-Level Tests

### 6.1 IICP Message Format (MUST)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `PROTO-MSG-01` | CALL message contains `task_id` (UUID-v4) | Format: `[0-9a-f-]{36}` |
| `PROTO-MSG-02` | CALL message contains `intent` (URN) | Format: `urn:iicp:intent:*:v*` |
| `PROTO-MSG-03` | CALL message contains `constraints.timeout_ms` | Integer > 0 |
| `PROTO-MSG-04` | RESPONSE echoes `task_id` from CALL | Exact match |
| `PROTO-MSG-05` | All messages have `Content-Type: application/json` | Header present |

### 6.2 Intent URN Format (MUST per ADR-007)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `PROTO-URN-01` | Intent begins with `urn:iicp:intent:` | Reject others |
| `PROTO-URN-02` | Intent ends with `:v{N}` version suffix | Reject unversioned |
| `PROTO-URN-03` | Unknown intents return `error.code = "unknown_intent"` | Structured error |

---

## 7. Security Conformance Tests (MUST)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `SEC-AUTH-01` | Task endpoint rejects missing auth → 401 | `error.code = "unauthorized"` |
| `SEC-AUTH-02` | Task endpoint rejects wrong token → 401 | Constant-time comparison (verified by code review) |
| `SEC-TLS-01` | All directory connections over TLS 1.3 | Verified via `openssl s_client` in production |
| `SEC-NONCE-01` | Duplicate HMAC signature on peers endpoint → 429 | Replay detected and rejected (implementation: `StatusCode::TOO_MANY_REQUESTS`) |
| `SEC-LEAK-01` | No stack trace in any error response | Automated scan: `grep -r "Traceback\|at line"` |
| `SEC-LEAK-02` | No internal file paths in any response body | Automated scan: `grep -r "/home/\|/Users/"` |
| `SEC-RN-01` | Rust node rejects empty `auth.node_token` → 401 | Validates `validate_token` never enters open-mode |
| `SEC-RN-02` | Rust node rejects request with no `auth` field → 401 | Missing auth treated same as invalid token |
| `SEC-LOG-01` | Task payload content absent from adapter and proxy logs | Submit task with known content; grep adapter+proxy logs — payload must not appear |

---

## 8. Running the Suite

```bash
# Fast conformance run (skip slow tests)
cd tests/integration
pytest -m "conformance and not slow" -v --asyncio-mode=auto

# Full conformance including slow tests (heartbeat expiry, rate limit)
pytest -m "conformance" -v --asyncio-mode=auto --timeout=120

# Phase 1 milestone gate
pytest -m "conformance and not phase2" -v --asyncio-mode=auto \
  --junit-xml=reports/conformance.xml
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | All tests passed — conformant |
| 1 | Test failures — not conformant |
| 2 | Test collection error |
| 5 | No tests collected — check marks |

---

## 9. Certification

A Phase 1 conformance certificate is issued when:
1. All MUST-level tests pass (exit code 0)
2. `sentrux check .` quality ≥ 7000
3. Security scan (§7) shows no findings
4. Protocol Steward reviews and signs the test report

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.0 | 2026-05-14 | Initial draft — Phase 1 conformance test IDs; DIR-REG, DIR-RL, DIR-HB, DIR-NODE, PROXY-OAI, SEC-* series |
| 0.1.1 | 2026-05-15 | Added Changelog section (A6 spec cleanup) |

---

## Sign-off

**Protocol Steward**: Suite covers IICP-DIR §3, ADR-008, and Phase 1 conformance
profile. All MUST tests are verifiable against the current Docker Compose stack.
Closes GitHub issue #22 (draft). ✓  
**Integration Validator**: Test IDs mapped to integration test files in
`tests/integration/`. All existing tests updated to carry `@conformance` mark. ✓
