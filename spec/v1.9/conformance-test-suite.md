# IICP Conformance Test Suite

**Version**: 4.45.0
**Date**: 2026-06-28
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
| `@sdk` | SDK conformance tests (ADR-016); requires SDK under test, not Docker stack |
| `@federated` | Federated directory tests (S.13); requires a running replica + Genesis Seed |

---

## 3. Directory Conformance Tests

### 3.1 Registration (MUST)

| Test ID | Requirement | Expected | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-REG-01` | `POST /v1/register` with valid payload → 201 | Body contains `node_id`, `node_token` | — (requires registered node) |
| `DIR-REG-02` | `POST /v1/register` missing `endpoint` → 422 | Body contains `error.code = "validation_error"` | `probe_dir_reg_02` |
| `DIR-REG-03` | `POST /v1/register` missing `capabilities` → 422 | Body contains `error.code = "validation_error"` | `probe_dir_reg_03` |
| `DIR-REG-04` | `POST /v1/register` with unreachable endpoint → 422 | Body contains `error.code = "liveness_failed"` | — (requires unreachable endpoint) |
| `DIR-REG-05` | `node_token` in response is ≥ 32 bytes (hex-encoded) | Verify length ≥ 64 hex chars | — (requires node_token from registration) |
| `DIR-REG-06` | `node_id` assigned by directory when absent | Response `node_id` is valid UUID-v4 | — (requires node_token from registration) |
| `DIR-REG-07` | `node_token` stored as bcrypt hash, never plaintext | Code review: `NodeRegistry` uses `Hash::make()` before insert | code review only |
| `DIR-REG-08` | `POST /v1/register` with unrecognised `capabilities[].quantization` value (e.g. `"fp64"`) → 201 | Directory MUST NOT reject unrecognised advisory field values; per iicp-core.md §2.1 v1.2.4 | — (directory unit test: `RegisterTest::test_accepts_unrecognised_quantization_value`) |
| `DIR-REG-09` | `POST /v1/register` with unrecognised `capabilities[].inference_engine` value (e.g. `"tensorrt"`) → 201 | Directory MUST NOT reject unrecognised advisory field values; per iicp-core.md §2.1 v1.2.4 | — (directory unit test: `RegisterTest::test_accepts_unrecognised_inference_engine_value`) |

### 3.2 Heartbeat (MUST)

| Test ID | Requirement | Expected | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-HB-01` | `POST /v1/heartbeat` with valid token → 200 | Body contains `ok: true`, `next_heartbeat_ms` | `probe_dir_hb_01` (provisioned token) |
| `DIR-HB-02` | `POST /v1/heartbeat` with invalid token → 401 | Body contains `error.code = "unauthorized"` | `probe_dir_hb_02` |
| `DIR-HB-03` | `POST /v1/heartbeat` for unknown node_id → 404 | Body contains `error.code = "not_found"` | — (requires unknown node) |
| `DIR-HB-04` | Node not seen for > 90s excluded from discover | Poll discover after 90s silence | — (90s timing test) |
| `DIR-HB-05` | `POST /v1/peers` (PEER_EXCHANGE) without a valid Ed25519 gossip signature → 401/403 | `@phase2` — not required for Phase 1 conformance | → DIR-PEER-01 |

### 3.3 Discovery (MUST)

| Test ID | Requirement | Expected | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-DISC-01` | `GET /v1/discover?intent=...` → 200 | Body contains `nodes[]`, `count` | `probe_dir_disc_01` |
| `DIR-DISC-02` | Nodes sorted by score descending | `nodes[0].score >= nodes[1].score` | `probe_dir_disc_02` |
| `DIR-DISC-03` | All returned nodes have `available: true` | No unavailable node in results | `probe_dir_disc_03` |
| `DIR-DISC-04` | Scores are in range [0.1, 1.0] | Per ADR-008 minimum threshold | `probe_dir_disc_04` |
| `DIR-DISC-05` | `?limit=N` respected (max 50) | Exactly min(N, available) nodes returned | `probe_dir_disc_05` |
| `DIR-DISC-06` | `?region=X` returns region-matched nodes with higher scores | Region-matched node scores ≥ unmatched when equally loaded | — (conditional, region-load dependent) |
| `DIR-DISC-07` | Nodes with score < 0.1 excluded | No low-score nodes in results | — (covered by DIR-DISC-04 score range check) |
| `DIR-DISC-09` | `?min_reputation=2.0` (out-of-range, max=1.0) MUST return 422 | Input validation for min_reputation query parameter | `probe_dir_disc_09` |
| `DIR-DISC-10` | `GET /v1/discover` without `intent` parameter MUST return 422 | intent is a required query parameter | `probe_dir_disc_10` |
| `DIR-DISC-08` | `GET /v1/discover` response includes `Cache-Control: public, max-age=5, s-maxage=10, stale-while-revalidate=5` | Live tunnel and relay routes remain fresh across endpoint rotation; longer caching is non-conformant | `probe_dir_disc_08` |
| `DIR-DISC-11` | `GET /v1/discover?intent=urn:iicp:intent:x.<vendor>:*:v*` MUST return 200, not 422 | Directory MUST accept custom intent URNs (x.<vendor>); per iicp-core.md §4.1 | `probe_dir_disc_11` — live 2026-05-22 |

### 3.3b Mesh Bootstrap (MUST, Phase 2)

| Test ID | Requirement | Expected | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-BS-01` | `GET /v1/bootstrap` → 200 with `peers[]` array | Body contains `peers` key (may be empty if no known peers) | `probe_dir_bs_01` |
| `DIR-BS-02` | All bootstrap peers have `last_seen` within the 90s staleness window | Stale peers must not appear in bootstrap response | `probe_dir_bs_02` |
| `DIR-PEER-01` | `POST /v1/peers` with no `X-IICP-Signature` / sender identity → 401 | Peer exchange uses Ed25519 gossip signatures; node_token MUST NOT be sent to peers | `probe_dir_peer_01` |

### 3.3c Credit Endpoints Auth Boundary (Phase 3 — MUST)

Credit endpoints MUST enforce auth on all methods. Test IDs back-filled from REACH probes live as of 2026-05-20.

| Test ID | Requirement | Expected | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-CRED-01` | `GET /v1/credits/balance` with no auth → 401 | Credit balance is node-private; unauthenticated access MUST be denied | `probe_dir_cred_01` |
| `DIR-CRED-02` | `GET /v1/credits/transactions` with no auth → 401 | Transaction history is node-private; unauthenticated access MUST be denied | `probe_dir_cred_02` |
| `DIR-CRED-03` | `POST /v1/credits/award` with no auth → 401 | Credit award requires HMAC-authenticated node token; no auth MUST return 401 | `probe_dir_cred_03` |

### 3.3d CIP Conformance Level in Discovery (Phase 5 — MUST)

Every node in the discover response MUST declare its CIP conformance level (S.12 §5.2 REP1).
The `?cip_capable=1` filter MUST exclude non-Provider nodes. REACH probes live as of 2026-05-20.

| Test ID | Requirement | Expected | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-CIP-01` | `GET /v1/discover` — every returned node has `cip_conformance_level` in `['CIP-Provider', 'CIP-None']` | Field present and valid for all nodes (S.12 §5.2 REP1) | `probe_dir_cip_01` |
| `DIR-CIP-02` | `GET /v1/discover?cip_capable=1` — all returned nodes have `cip_conformance_level = 'CIP-Provider'` | Filter must exclude CIP-None nodes; result may be empty if no CIP nodes registered | `probe_dir_cip_02` |
| `DIR-CIP-03` | `GET /v1/discover` — every returned node has `reputation_tier` in `['bronze', 'none', 'silver', 'gold', 'platinum']` | Field present and valid for all nodes (S.12 §5.1.1 REP2); `bronze` is the floor tier (CIP v0.6.9, 2026-05-30); `none` accepted transitionally | `probe_dir_cip_03` |

### 3.3e External Reachability Probe — SSRF Guard (MUST)

The probe endpoint (`GET /v1/probe`) MUST refuse requests targeting private or loopback addresses
to prevent SSRF exploitation. REACH probes live as of 2026-05-20.

| Test ID | Requirement | Expected | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-PROBE-01` | `GET /v1/probe?host=127.0.0.1&port=9484` — loopback MUST be rejected | 422, `error = "private_address"` | `probe_dir_probe_01` |
| `DIR-PROBE-02` | `GET /v1/probe?host=10.0.0.1&port=9484` — RFC-1918 MUST be rejected | 422, `error = "private_address"` | `probe_dir_probe_02` |

### 3.3f Trust Audit — Declaration Consistency (Phase 5 — SHOULD)

Registered nodes MUST declare all models they actively serve. A trust auditor (adapter-side
background loop) discovers registered nodes, probes each node's `/iicp/health` endpoint, and
verifies that `registered_models ⊆ health_models`. Divergent reachable nodes receive a −0.05
reputation penalty via `POST /api/v1/audit-report`. REACH probe live as of 2026-05-21.

| Test ID | Requirement | Expected | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-TRUST-01` | First node from `/v1/discover` — `registered_models` ⊆ `health_models` | PASS: superset match; INFO: NATted/unreachable (not a violation); FAIL: reachable but divergent | `probe_dir_trust_01` |

### 3.3g Telemetry Auth Boundary (Phase 3 — MUST)

`POST /v1/telemetry` (proxy-observed latency) MUST authenticate via `proxy_token`. Unauthenticated
requests MUST return 401. REACH probe live as of 2026-05-21 (spec §T4.1 TEL-AUTH-01).

| Test ID | Requirement | Expected | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-TEL-01` | `POST /v1/telemetry` with no auth → 401 | Telemetry ingestion requires proxy_token Bearer; no auth MUST return 401 | `probe_dir_tel_01` |

### 3.3h Public Stats Endpoint Contract (Phase 5 — MUST)

`GET /api/v1/stats` MUST return the T3 compound `mesh_health` metric as an object
with at least `{score: float in [0,1], label: string, window: string}` (REP1
ratification, directory v1.9.19+). Consumer dashboards and the website MeshStatusWidget
depend on this shape. A regression that returns `mesh_health` as a scalar (or
removes required fields) silently breaks client rendering — caught iter-1337
when website v1.9.25 shipped `NaN%` to live visitors.

| Test ID | Requirement | Expected | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-STATS-01` | `GET /api/v1/stats` — `mesh_health` is object with `{score, label, window}`, `score ∈ [0,1]` | 200, response includes all three keys, score validates as float in range | `probe_dir_stats_01` |

### 3.3i Active Per-Node Reachability Probing (Phase 5 — SHOULD)

Directory MUST probe registered nodes' endpoints autonomously (not relying solely on
self-attested `public_reachable`). Probes fire every 5 minutes, are SSRF-guarded (RFC1918/
loopback rejected), use a 5-second TCP timeout, and record results in `iicp_telemetry_probes`
with `test_id = "DIR-PROBE-NODE-01"`. Once a directory probe is recorded, `GET /v1/node/{id}`
health response SHOULD reflect the independently observed `reachability` with `observed: true`.

Note: This conformance test activates only when the directory origin or a signed external
probe worker has IPv6 egress available to probe DS-Lite/IPv6 nodes. On the current df.eu
shared production server, IPv6 egress is unavailable and a VPS is not an active/funded
deployment path; probe rows may therefore exist but remain `passed=false` for IPv6-only
routes without implying a node fault. Once an IPv6-capable probe lane exists, at least
one `passed=true` row is expected within 10 minutes for a known reachable IPv6 node.

| Test ID | Requirement | Expected | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-PROBE-NODE-01` | Directory records probed nodes in `iicp_telemetry_probes` with `test_id='DIR-PROBE-NODE-01'` | Probe row exists for at least one registered node within 10 min of registration | Unit tests: `ProbeNodesCommandTest` (PHP), `run_probe_nodes_loop` (Rust). IPv6 REACH probe requires IPv6-capable origin egress or a signed external probe worker (not live on current df.eu shared hosting; requires `IICP_REACH_NODE_PROBE=true` env flag). |

### 3.3j WebRTC Signaling Mailbox (draft, SHOULD, #523)

These tests apply only to directories that implement the optional WebRTC signaling mailbox
from `iicp-dir.md §3.13`. The mailbox carries SDP/ICE control-plane metadata only; task
payloads MUST remain off-directory.

| Test ID | Requirement | Expected | Implementation |
|---------|-------------|---------|----------------|
| `DIR-SIGNAL-01` | Provider mailbox create requires node-token auth | Missing/invalid auth returns 401; valid owner token returns `mailbox_id` + `expires_at` | Future PHP/Rust directory tests |
| `DIR-SIGNAL-02` | Message size and type are bounded | Oversize message returns `413 IICP-E053`; unknown `type` returns 422 | Future PHP/Rust directory tests |
| `DIR-SIGNAL-03` | Expired mailboxes/messages are not returned | Poll after TTL returns empty/404; cleanup removes expired records | Future PHP/Rust directory tests |
| `DIR-SIGNAL-04` | Mailbox never accepts task payload message types | `CALL`, `RESPONSE`, prompt/file/tool payload fields are rejected with 422 | Future PHP/Rust directory tests |
| `DIR-SIGNAL-05` | Discover metadata for `webrtc_datachannel` includes live `mailbox_id`, `expires_at`, and `datachannel_protocol` | Consumers can decide whether to attempt WebRTC without a second metadata fetch | Future discover contract tests |

### 3.4 Rate Limiting (MUST)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `DIR-RL-01` | > 10 `POST /v1/register` requests per minute per IP → 429 | `error.code = "rate_limited"` |

### 3.5 Node Detail (SHOULD)

| Test ID | Requirement | Expected | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-NODE-01` | `GET /v1/node/{id}` for registered node → 200 | Node object with capabilities | `probe_dir_node_01` |
| `DIR-NODE-02` | `GET /v1/node/{unknown}` → 404 | `error.code = "not_found"` | `probe_dir_node_02` |

### 3.5b Per-Node Health Vector (ADR-044 / #492 — SHOULD)

`GET /api/v1/node/{id}` MUST include a `health` block reflecting endpoint liveness. Per ADR-044 amendment (#492) the formula is liveness-only: W_REACHABILITY=0.70, W_LATENCY=0.30. Reputation and task-success are intentionally absent — health is not earned, it is observed. Additive v2 evidence fields (`confidence`, `evidence_level`, `latency_ms_basis`) clarify whether a healthy-looking score is independently measured or merely reachable but not yet performance-measured.

| Test ID | Requirement | Expected | Implementation |
|---------|-------------|---------|----------------|
| `DIR-NODE-HEALTH-01` | Node-detail `health` block present with `score`, `label`, `observed`, `confidence`, `evidence_level`, `latency_ms_basis`, `components`, `evaluated_at` | Required legacy keys plus additive evidence keys present; `score ∈ [0,100]` int; `label ∈ {healthy,degraded,impaired,critical,offline}` | PHP: `NodeDetailHealthTest::test_node_detail_includes_health_block`; Rust: `health.rs::score_node_all_perfect` |
| `DIR-NODE-HEALTH-02` | Health components MUST include `{liveness, reachability, latency}` and MUST NOT include old `success_rate` or `reputation` (#492) | Additive components such as `uptime`, `stability`, `freshness` are allowed; no reputation/task-success health inputs | PHP: `NodeDetailHealthTest::test_node_detail_includes_health_block` assertJsonStructure; Rust: `health.rs::components_match_score` |
| `DIR-NODE-HEALTH-03` | New reachable node with no task history MUST show `label = "healthy"` (score ≥85) | `health.label = "healthy"` — old formula would yield 65 ("degraded") | PHP: `NodeDetailHealthTest::test_new_reachable_node_with_no_task_history_shows_healthy`; Rust: `health.rs::new_reachable_node_with_no_task_history_is_healthy` |
| `DIR-NODE-HEALTH-04` | Offline node (heartbeat > 90s) MUST return `label = "offline"`, `score = 0` | `health.score = 0`, `health.label = "offline"` | PHP: `NodeDetailHealthTest::test_offline_node_detail_reports_offline_health` |

### 3.6 Proxy Telemetry — OUTLIER_WEIGHT (SHOULD)

Informative tests — SHOULD-level. Implementations SHOULD pass; non-compliance does not
invalidate overall conformance but reduces ARCS telemetry dimension credit.

| Test ID | Requirement | Expected | Implementation |
|---------|-------------|----------|----------------|
| `TEL-OUTLIER-01` | Proxy with ≥10 obs reporting >3× median is down-weighted to α×0.1 | SCORE_UPDATE event `outlier_weight = 0.1` | `directory/tests/Feature/ProxyTelemetryTest.php::test_outlier_proxy_with_sufficient_observations_is_down_weighted` |
| `TEL-OUTLIER-02` | New proxy (<10 obs) is never flagged — min-obs gate holds | SCORE_UPDATE event `outlier_weight = 1.0` | `directory/tests/Feature/ProxyTelemetryTest.php::test_new_proxy_below_min_observations_not_flagged_as_outlier` |
| `TEL-OUTLIER-03` | Honest noisy proxy (within 3× median) receives full weight | SCORE_UPDATE event `outlier_weight = 1.0` | `directory/tests/Feature/ProxyTelemetryTest.php::test_honest_high_noise_proxy_not_flagged_as_outlier` |

Spec reference: `spec/iicp-telemetry.md §T4.3`. Issue: #187. Validated by RESA RS3 simulation.

---

## 4. Provider Node (Adapter) Conformance Tests

### 4.1 Task Submission (MUST)

| Test ID | Requirement | Expected | Test file |
|---------|-------------|---------|-----------|
| `NODE-TASK-01` | `POST /v1/task` with valid payload → 200 or 502 | Structured JSON, never raw exception | `adapter/tests/test_task.py::test_task_success` |
| `NODE-TASK-02` | Response contains `task_id` matching request | `response.task_id == request.task_id` | `adapter/tests/test_task.py::test_task_success` |
| `NODE-TASK-03` | Response contains `status` field | One of `success`, `error`, `timeout` | `adapter/tests/test_task.py::test_task_success` |
| `NODE-TASK-04` | Response contains `metrics.latency_ms` | Numeric value ≥ 0 | `adapter/tests/test_task.py::test_task_success` |
| `NODE-TASK-05` | `POST /v1/task` with invalid/missing token → 401 | `error.code = "unauthorized"` | `adapter/tests/test_task.py::test_task_rejects_invalid_token` |
| `NODE-TASK-06` | `POST /v1/task` with duplicate `task_id` → 409 | `error.code = "conflict"` | `adapter/tests/test_idempotency.py::test_duplicate_task_id_returns_409` |
| `NODE-TASK-07` | Backend error returns 502, not raw exception | No `Traceback` in response body | `adapter/tests/test_task.py::test_task_returns_502_on_backend_error` |
| `NODE-TASK-08` | Response never exposes internal file paths | No `/Users/`, `/home/`, `/var/` in body | `adapter/tests/test_task.py::test_task_structured_error_never_exposes_internals` |

### 4.2 Health (MUST)

| Test ID | Requirement | Expected | Test file |
|---------|-------------|---------|-----------|
| `NODE-HEALTH-01` | `GET /iicp/health` → 200 | `status` in (`ok`, `degraded`) | `adapter/tests/test_health.py::test_health_returns_ok` |
| `NODE-HEALTH-02` | Health response contains `load`, `active_jobs` | Numeric values | `adapter/tests/test_health.py::test_health_returns_ok` |
| `NODE-HEALTH-03` | `Content-Type: application/json` on all responses | Header present | `adapter/tests/test_coverage_gates.py::test_health_response_includes_node_id` |

### 4.3 Concurrency Gate (MUST)

| Test ID | Requirement | Expected | Test file |
|---------|-------------|---------|-----------|
| `NODE-CONC-01` | Tasks beyond `max_concurrent` → 429 | `error.code = "overloaded"` | `adapter/tests/test_concurrency.py::test_qos_admit_01_second_realtime_gets_429_capacity_exceeded` |

### 4.4 Registration on Startup (SHOULD)

| Test ID | Requirement | Expected |
|---------|-------------|---------|
| `NODE-REG-01` | Adapter registers with directory on startup | Node appears in discover after adapter start |
| `NODE-REG-02` | Heartbeat sent every 30s | Directory `last_seen` updated within 35s |

---

## 5. Client (Proxy) Conformance Tests

### 5.1 Task Routing (MUST)

| Test ID | Requirement | Expected | Test file |
|---------|-------------|---------|-----------|
| `PROXY-ROUTE-01` | Proxy discovers nodes via directory before routing | Discover called before task submission | `proxy/tests/test_router.py::test_route_returns_result_on_success` |
| `PROXY-ROUTE-02` | Proxy submits to highest-scored node | First node in discover response is used | `proxy/tests/test_selector.py::test_selector_preserves_directory_order` |
| `PROXY-ROUTE-03` | Proxy retries on node failure (≤ 3 attempts) | Task succeeds after first node fails | `proxy/tests/test_retry.py::test_retry_retries_on_timeout`, `proxy/tests/test_coverage_gates.py::test_retry_retries_on_503` |
| `PROXY-ROUTE-04` | All retries exhausted → structured error | `error.code` not empty; no raw exception | `proxy/tests/test_coverage_gates.py::test_fallback_chain_all_nodes_fail_returns_structured_error` |
| `PROXY-ROUTE-05` | TLS certificate validated on all connections | Reject self-signed certs in non-test mode | Code review: `httpx.AsyncClient(verify=ssl.create_default_context())` in `proxy/src/proxy/routing/router.py` |

### 5.2 Timeout Handling (MUST)

| Test ID | Requirement | Expected | Test file |
|---------|-------------|---------|-----------|
| `PROXY-TIMEOUT-01` | Node timeout → retry with next node | Next node attempted within backoff window | `proxy/tests/test_retry.py::test_retry_retries_on_timeout` |
| `PROXY-TIMEOUT-02` | All nodes timeout → error with `code = "timeout"` | Structured error | `proxy/tests/test_retry.py::test_retry_exhausts_and_raises` |

### 5.3 OpenAI Compat Interface (SHOULD)

| Test ID | Requirement | Expected | Test file |
|---------|-------------|---------|-----------|
| `PROXY-OAI-01` | `POST /v1/chat/completions` translates to IICP CALL | Intent mapped to `urn:iicp:intent:llm:chat:v1` | `proxy/tests/test_translator.py::test_to_iicp_task_generates_uuid_and_intent` |
| `PROXY-OAI-02` | Response translates to OpenAI format | `choices[0].message.content` present | `proxy/tests/test_translator.py::test_to_openai_response_maps_fields` |

### 5.4 Proxy Error Code Semantics (MUST) — WQ-030 / iicp-core.md §7

Proxy MUST distinguish two failure modes that were previously conflated by a generic
`no_available_node` code. The distinction is actionable for operators: IICP-E033 means the
directory was reachable and returned zero candidates (check intent URN / wait for providers);
`no_available_node` means the directory returned candidates but all routing attempts failed at
runtime (transient network or node issue).

| Test ID | Requirement | Spec ref | Test file |
|---------|-------------|----------|-----------|
| `PROXY-ERR-01` | When discover returns 0 candidates → proxy returns `error.code = "IICP-E033"`, HTTP 503 | iicp-core.md §7, WQ-030 | `proxy/tests/test_aggregator.py::test_aggregator_empty_nodes_returns_error`, `proxy/tests/test_fallback.py::test_fallback_returns_error_on_empty_node_list` |
| `PROXY-ERR-02` | When discover returns candidates but all fail during routing → proxy returns `error.code = "no_available_node"` (NOT IICP-E033) | iicp-core.md §7 | `proxy/tests/test_coverage_gates.py::test_circuit_breaker_blocks_after_threshold` |

---

## 6. Protocol-Level Tests

### 6.1 IICP Message Format (MUST)

| Test ID | Requirement | Expected | Test file |
|---------|-------------|---------|-----------|
| `PROTO-MSG-01` | CALL message contains `task_id` (UUID-v4) | Format: `[0-9a-f-]{36}` | `adapter/tests/test_models_validators.py::test_task_id_accepts_valid_v4_uuid` |
| `PROTO-MSG-02` | CALL message contains `intent` (URN) | Format: `urn:iicp:intent:*:v*` | `adapter/tests/test_models_validators.py::test_task_request_valid` |
| `PROTO-MSG-03` | CALL message contains `constraints.timeout_ms` | Integer > 0 | `adapter/tests/test_models_validators.py::test_task_request_valid` |
| `PROTO-MSG-04` | RESPONSE echoes `task_id` from CALL | Exact match | `adapter/tests/test_task.py::test_task_success` |
| `PROTO-MSG-05` | All messages have `Content-Type: application/json` | Header present | `adapter/tests/test_coverage_gates.py` |

### 6.2 Intent URN Format (MUST per ADR-007)

| Test ID | Requirement | Expected | Test file |
|---------|-------------|---------|-----------|
| `PROTO-URN-01` | Intent begins with `urn:iicp:intent:` | Reject others | `adapter/tests/test_models_validators.py::test_intent_rejects_missing_urn_prefix` |
| `PROTO-URN-02` | Intent ends with `:v{N}` version suffix | Reject unversioned | `adapter/tests/test_models_validators.py::test_intent_rejects_missing_version` |
| `PROTO-URN-03` | Unknown intents return `error.code = "unknown_intent"` | Structured error | `adapter/tests/test_task.py::test_task_rejects_invalid_intent` |

---

## 7. Security Conformance Tests (MUST)

| Test ID | Requirement | Expected | Test file |
|---------|-------------|---------|-----------|
| `SEC-AUTH-01` | Task endpoint rejects missing auth → 401 | `error.code = "unauthorized"` | `adapter/tests/test_task.py::test_task_rejects_missing_token` |
| `SEC-AUTH-02` | Task endpoint rejects wrong token → 401 | Constant-time comparison (verified by code review) | `adapter/tests/test_task.py::test_task_rejects_invalid_token` |
| `SEC-TLS-01` | All directory connections over TLS 1.3 | Verified via `openssl s_client` in production | `reach/src/reach/probes/directory_conformance.py::probe_tls_version` |
| `SEC-NONCE-01` | Duplicate Ed25519 gossip signature on peers endpoint → 409 | Replay detected and rejected within the peer replay window | `adapter/tests/test_nonce_replay.py::test_duplicate_nonce_rejected` |
| `SEC-LEAK-01` | No stack trace in any error response | Automated scan: `grep -r "Traceback\|at line"` | `reach/src/reach/probes/directory_conformance.py::probe_no_stack_trace` |
| `SEC-LEAK-02` | No internal file paths in any response body | Automated scan: `grep -r "/home/\|/Users/"` | `reach/src/reach/probes/directory_conformance.py::probe_no_path_leak` |
| `SEC-RN-01` | Rust node rejects empty `auth.node_token` → 401 | Validates `validate_token` never enters open-mode | `iicp-node/tests/` (Rust integration tests) |
| `SEC-RN-02` | Rust node rejects request with no `auth` field → 401 | Missing auth treated same as invalid token | `iicp-node/tests/` (Rust integration tests) |
| `SEC-LOG-01` | Task payload content absent from adapter and proxy logs | Submit task with known content; grep adapter+proxy logs — payload must not appear | `adapter/tests/test_coverage_gates.py` |

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

## 10. SDK Conformance Tests (ADR-016)

Applies to all official IICP SDKs: Python `iicp-client`, TypeScript `@iicp/client`, Rust `iicp-client`.

Run with the SDK test harness: `iicp-conformance-sdk --sdk python --directory http://localhost:8010`

---

## 11. Changelog

| Version | Date | Change |
|---------|------|--------|
| 4.46.0 | 2026-07-13 | `DIR-DISC-08` now verifies the short live-route discovery cache contract: `public, max-age=5, s-maxage=10, stale-while-revalidate=5`. This preserves prompt-free discovery freshness across relay and tunnel endpoint rotation; historical 30/60-second expectations are retired. |
| 4.45.0 | 2026-06-28 | §10.4 adds SDK-NODE-03..05 for SDK 0.7.75 external-tunnel guardrails: persistent provider-rate-limit cooldown, host-wide creation pacing/lease, and fallback to safe reachability methods rather than tunnel-create loops or unverified endpoint advertisement. §3.2/§3.3b/§7 reconcile peer-exchange conformance rows with Ed25519 gossip signatures instead of node-token/HMAC auth. |
| 4.44.0 | 2026-06-21 | §3.3j DIR-SIGNAL-01..05 draft SHOULD tests added for optional WebRTC signaling mailbox (#523): auth, TTL/cleanup, size/type caps, no task payloads, and discover metadata shape. |
| 4.42.0 | 2026-06-01 | §3.3i DIR-PROBE-NODE-01 added: active per-node reachability probing (#373 Phase B). Directory autonomously probes registered node endpoints (TCP/HTTP, SSRF-guarded, 5s timeout, 5-min interval). Records `test_id='DIR-PROBE-NODE-01'` in iicp_telemetry_probes. NodeHealthService uses independently observed signal when recent probe exists. PHP: `ProbeNodesCommandTest` 7 tests; Rust: `run_probe_nodes_loop`. IPv6 REACH probing requires IPv6-capable origin egress or a signed external probe worker; the current df.eu shared production server does not provide this. |
| 4.41.0 | 2026-06-01 | §13.6 REP-04..07 added: security hardening bypass mitigations (#380-383, 2026-06-01). REP-04: per-node hourly velocity ceiling (RT-01b, MAX_HOURLY_GAIN=0.20). REP-05: IP-level free credit gate (RT-02b). REP-06: Sybil quorum reporter independence — min age 3d + rep ≥0.55 (RT-03b). REP-07: audit-report reporter eligibility — same age+reputation gate (RT-05b). Tests added to CreditHarvestRegressionTest, ReputationServiceTest, ProxyTelemetryTest, AuditReportTest. |
| 4.40.0 | 2026-05-31 | §3.3d DIR-CIP-03: valid `reputation_tier` set updated to include `"bronze"` (CIP spec v0.6.9, 2026-05-30 reconciliation). `bronze` is the floor tier for all sub-Silver nodes; `none` retained transitionally. Probe `valid_tiers` updated; PHP NodeScorer `none`→`bronze` for `score < 0.40`; Rust `tier_from_score` floor updated. REACH unit test updated (bronze PASS, `"probation"` used as the invalid-tier test case). |
| 4.39.0 | 2026-05-26 | §11.9 Trust Precedence added per Phase 6 charter P6-4.3: DIR-FED-TRUST-01 (S.13 §3.2) — proxy resolves conflicting node-state per strict precedence Seed > Replica-by-seq > Tier-tiebreaker > Gossip; field-level (not row-level). 14 unit tests in proxy/tests/test_trust_resolver.py + INFO-skip REACH probe (activates when replica deployed); reach run_all 39→40. |
| 4.38.0 | 2026-05-26 | §11.8 Replica Response Signing added per Phase 6 charter P6-4.2b: DIR-FED-20 (S.13 v0.3.6 §6.5) requires replicas to sign discovery responses with Ed25519 + X-IICP-Replica-Sig header. Proxy verifier helper `proxy/src/proxy/clients/replica_sig_verifier.py` ships with 16 unit tests. New `cryptography>=42` dep added to proxy. |
| 4.37.0 | 2026-05-26 | §11.7 Trusted-Replicas Registry added per Phase 6 charter P6-3.2: DIR-FED-19 probe (S.13 v0.3.4 §6.4) validates v2-schema `/.well-known/iicp-replicas.json` with required entry fields (replica_id, did, endpoint, trust_tier, registered_at). 5 unit tests added; run_all count 38→39. |
| 4.36.0 | 2026-05-25 | §11.6 Chain-of-Custody added per Phase 6 charter P6-2.1: DIR-FED-EVENTCHAIN-01 probe (S.13 v0.3.2) verifies the federated event log is append-only — past events MUST NOT mutate across successive `GET /v1/events` calls; mismatched (seq, event_id) tuples or `genesis_hash` drift fail the probe. 4 unit tests added. |
| 1.7.0 | 2026-05-21 | §3.1–3.3g: Added REACH probe column to all directory conformance sections (traceability parity with §4–7); REACH test mock fix (coroutine warning eliminated) |
| 0.2.1 | 2026-05-20 | §3.1: Added DIR-REG-08/DIR-REG-09 for advisory capability field MUST NOT constraints (iicp-core.md §2.1 v1.2.4, #118) |
| 0.2.0 | 2026-05-14 | §3.3b–3.3e: Added Phase 2 mesh bootstrap, credit endpoints auth, CIP conformance, SSRF guard probes; §7: SEC-RN-01/02, SEC-LOG-01 |

### 10.1 Submit Behavior (MUST)

| Test ID | Requirement | Spec ref |
|---------|-------------|---------|
| `SDK-01` | `submit()` retries exactly 3 times on transient errors before returning `IicpError` | ADR-016 §5 SDK-01 |
| `SDK-02` | `chat()` output format is identical to OpenAI Chat Completions API (`choices[0].message.content` present) | ADR-016 §5 SDK-02 |
| `SDK-03` | `IicpClient` validates intent URN format (`urn:iicp:intent:*:v*`) before sending; rejects invalid intent | ADR-016 §5 SDK-03 |
| `SDK-04` | `timeout_ms > 120000` is rejected at `IicpClient` construction time with `IicpError(code="invalid_config")` | ADR-016 §5 SDK-04 |
| `SDK-05` | `tls_verify: false` is not available in non-debug builds; attempting to pass it raises `IicpError` | ADR-016 §5 SDK-05 |
| `SDK-06` | `node_token` does not appear in log output or error messages when a task fails | ADR-016 §5 SDK-06 |

### 10.2 Discovery (MUST)

| Test ID | Requirement | Spec ref |
|---------|-------------|---------|
| `SDK-DISC-01` | `discover()` returns `NodeList` with `nodes[].score` in [0.0, 1.0] | ADR-016 §1 NodeList |
| `SDK-DISC-02` | `discover()` with `limit=N` returns at most N nodes | ADR-016 §1 DiscoverOptions |

### 10.3 Error Model (MUST)

| Test ID | Requirement | Spec ref |
|---------|-------------|---------|
| `SDK-ERR-01` | All errors surface as `IicpError` — never as raw HTTP exceptions | ADR-016 §3 |
| `SDK-ERR-02` | `IicpError.retryable` is `true` for IICP-E004, IICP-E005, IICP-E008 | ADR-016 §3; ARCHITECTURE.md error codes |

### 10.4 Node SDK (MUST — provider-side SDKs only)

| Test ID | Requirement | Spec ref |
|---------|-------------|---------|
| `SDK-NODE-01` | `node.start()` auto-registers with directory and sends first heartbeat within 35s | ADR-016 §2 |
| `SDK-NODE-02` | `node.on_task(handler)` receives `TaskRequest` + `TaskContext`; result returned to directory | ADR-016 §2 |
| `SDK-NODE-03` | Provider SDK persists accountless external-tunnel rate-limit cooldown across process restarts and refuses immediate tunnel recreation while cooldown is active | iicp-dir §3.1; iicp-semantics §6.4 |
| `SDK-NODE-04` | Provider SDK paces and serializes accountless external-tunnel creation across local services on the same host | iicp-dir §3.1 |
| `SDK-NODE-05` | Provider SDK falls back to the next safe reachability method instead of spinning on tunnel creation or advertising an unverified public route | iicp-semantics §6.4 |

---

## 11. Federated Directory Conformance Tests (S.13)

Applies to replica directories. Run with `iicp-conformance-federated --genesis https://iicp.network --replica http://replica.example.com`.

Test mark: `@federated` — not required for Phase 1–5 conformance.

### 11.1 Event Log Verification (MUST)

| Test ID | Requirement | Spec ref | Unit test |
|---------|-------------|---------|-----------|
| `DIR-FED-01` | Replica verifies Ed25519 signature for every event before applying state | S.13 §8 DIR-FED-01 | `directory/tests/Feature/ReplicaEventApplierSigVerifyTest::test_invalid_signature_rejects_event` + 6 more (P6-1.3b-iv) |
| `DIR-FED-02` | Replica rejects events with non-monotonic `seq` (emits IICP-E014) | S.13 §8 DIR-FED-02 | (replica state-mirror tests — P6-1.4) |
| `DIR-FED-03` | Replica verifies `signer_did` resolves to Genesis Seed DID document | S.13 §8 DIR-FED-03 | `directory/tests/Feature/SeedDidResolverTest::test_extracts_valid_ed25519_public_key` (DID fetch + Ed25519-only key extraction) |
| `DIR-FED-04` | Replica rejects events without valid Genesis Seed signature | S.13 §8 DIR-FED-04 | `directory/tests/Feature/ReplicaEventApplierSigVerifyTest::test_wrong_pubkey_rejects_event` |

### 11.2 Client Redirect Handling (MUST)

| Test ID | Requirement | Spec ref |
|---------|-------------|---------|
| `DIR-FED-05` | Client follows `307` transparently and repeats original request at `Location` | S.13 §8 DIR-FED-05 |
| `DIR-FED-06` | Client stops following redirects after 3 consecutive `307` responses | S.13 §8 DIR-FED-06 |

### 11.3 Genesis Seed Requirements (MUST)

| Test ID | Requirement | Spec ref | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-FED-07` | Every `GET /v1/events` response includes `genesis_hash` field | S.13 §8 DIR-FED-07 | `probe_dir_fed_07` — live 2026-05-21 |
| `DIR-FED-08` | Replica with `replica_lag_ms` > 300000 (5 min) returns `503` with `Retry-After` on discover | S.13 §8 DIR-FED-08 | None (requires replica) |
| `DIR-FED-09` | `GET /v1/events` returns events with monotonically increasing `seq` values | S.13 §8 DIR-FED-02 (producer side) | `probe_dir_fed_09` — live 2026-05-22 |
| `DIR-FED-10` | Each event in `GET /v1/events` MUST include `event_id` (UUID-v4), `event_type` (valid enum), `ts_ms` (integer), `signer_did` (string), `payload` (object) | S.13 §3.7 event schema table (6 MUST fields) | `probe_dir_fed_10` — live 2026-05-22 |

### 11.4 Replica Registration Handshake (MUST, Phase 6 — added 2026-05-25, S.13 v0.2.0)

| Test ID | Requirement | Spec ref | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-FED-11` | Genesis Seed MUST validate `did` resolves to a DID document with an Ed25519 verification method (IICP-E040/E041 on failure) | S.13 §7.1 + §8 DIR-FED-11 | None yet (endpoint to be built P6-1.2; probe in P6-X) |
| `DIR-FED-12` | Genesis Seed MUST reject `endpoint` that is non-https or resolves to a private/loopback address (IICP-E043; SSRF parity with /v1/probe) | S.13 §7.1 + §8 DIR-FED-12 | None yet (P6-1.2 endpoint) |
| `DIR-FED-13` | `POST /v1/replicas/register` MUST be idempotent on `did`: re-registration returns the same `replica_id` with a freshly rotated `replica_token` | S.13 §7.1 + §8 DIR-FED-13 | None yet (P6-1.2 endpoint) |
| `DIR-FED-14` | Response MUST include `genesis_hash` matching `GET /v1/events` (DIR-FED-07 parity) so replicas can pin-on-first-use | S.13 §7.1 + §8 DIR-FED-14 | None yet (P6-1.2 endpoint) |

### 11.5 Snapshot+Event-Tail Federation (MUST, Phase 6 — added 2026-05-25, S.13 v0.3.0)

Replicas bootstrap via `GET /v1/snapshot` then catch up via `GET /v1/events?since_seq=<snapshot_seq>`. Per ADR-033: ephemeral-by-design directory; HEARTBEAT/SCORE_UPDATE/REPUTATION_UPDATE no longer in federated event log (derivable from canonical row).

| Test ID | Requirement | Spec ref | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-FED-15` | `GET /v1/snapshot` MUST return current state with `snapshot_seq` = highest emitted event seq at generation time | S.13 §5.5 + §8 DIR-FED-15 | `SnapshotEndpointTest::test_returns_snapshot_for_authenticated_replica` (verifies snapshot_seq = max event.seq) |
| `DIR-FED-16` | Federated event log MUST emit ONLY {REGISTER, DEREGISTER, CREDIT_AWARD, REPLICA_REGISTERED, REPUTATION_DECAY} — closed type list | S.13 §5.1 + §8 DIR-FED-16 | Probe extending `probe_dir_fed_10` to assert no HEARTBEAT/SCORE_UPDATE/REPUTATION_UPDATE rows appear within a 5-min sample window |
| `DIR-FED-17` | Snapshot response `genesis_hash` MUST match `GET /v1/events` (parity with DIR-FED-07) | S.13 §5.5 + §8 DIR-FED-17 | `SnapshotEndpointTest::test_genesis_hash_matches_events_endpoint` |

### 11.6 Chain-of-Custody (MUST, Phase 6 — added 2026-05-25, S.13 v0.3.2)

The federated event log is the trust root replicas pin against. If the seed silently mutates a past event, replicas diverge undetectably until the next genesis_hash check trips — and may never re-pin if the chain is mutated atomically.

| Test ID | Requirement | Spec ref | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-FED-EVENTCHAIN-01` | Federated event log MUST be append-only — past events MUST NOT mutate: for any `(seq, event_id)` pair observed in two successive `GET /v1/events` responses, every field (`event_type`, `ts_ms`, `signer_did`, `payload`, `sig`) MUST be byte-identical, and `genesis_hash` MUST match across calls | S.13 §3 + §8 DIR-FED-EVENTCHAIN-01 | `probe_dir_fed_eventchain_01` (`reach/src/reach/probes/directory_conformance.py`) — 4 unit tests cover overlap-identical, mutation-detected, genesis-hash-drift, no-overlap-trivially-pass |

### 11.7 Trusted-Replicas Registry (MUST, Phase 6 — added 2026-05-26, S.13 v0.3.4)

The genesis seed publishes the canonical replica registry at `/.well-known/iicp-replicas.json`. Discovery clients use this to bootstrap-without-seed during outages, ranking replicas by `trust_tier` and region. The registry carries static metadata only — dynamic freshness comes from each replica's `/api/v1/stats`.

| Test ID | Requirement | Spec ref | REACH probe |
|---------|-------------|---------|-------------|
| `DIR-FED-19` | Genesis Seed MUST serve a valid v2-schema `/.well-known/iicp-replicas.json` with required entry fields `{replica_id, did, endpoint, trust_tier, registered_at}` | S.13 §6.4 + §8 DIR-FED-19 | `probe_dir_fed_19` (`reach/src/reach/probes/directory_conformance.py`) — 5 unit tests cover empty-registry, valid-entries, wrong-schema-version, missing-required-field, 404 |

### 11.8 Replica Response Signing (MUST, Phase 6 — added 2026-05-26, S.13 v0.3.6)

Replicas sign their discovery responses with Ed25519; proxies verify against the replica's published DID key. Without this, a misconfigured TLS terminator or compromised intermediary could substitute response bytes; verification is end-to-end (signed at replica, verified at proxy) and bypasses all intermediaries.

| Test ID | Requirement | Spec ref | Unit test |
|---------|-------------|---------|-----------|
| `DIR-FED-20` | Replicas MUST sign discovery responses with Ed25519 + emit `X-IICP-Replica-Sig`/`-DID`/`-Snapshot-Seq` headers; clients MUST verify against the replica's DID key and reject on failure | S.13 §6.5 + §8 DIR-FED-20 | `proxy/tests/test_replica_sig_verifier.py` — 16 tests cover canonicalize-query (empty/single/sorted/repeated-keys), signing-input (deterministic, method-case-insensitive, query-order-invariant, tamper-changes-hash), verify (valid, tampered-body, wrong-pubkey, wrong-path, wrong-snapshot-seq replay, malformed-sig-hex, malformed-pubkey, server-client-query-order-round-trip). Integration: `proxy/tests/test_directory_sig_verify.py` 6 tests (valid-sig-accepted, missing-sig-rejected, tampered-body-rejected, did-unresolvable-rejected, no-verifier-back-compat, seed-response-skips-verify). Seed-side: `directory/tests/Feature/SignReplicaResponseTest.php` 7 tests (round-trip canonical input verification). |

### 11.9 Trust Precedence (MUST, Phase 6 — added 2026-05-26, S.13 v0.3.1 §3.2)

When proxies/SDKs receive node state from multiple sources within the same query window, they MUST resolve conflicts per the strict precedence Seed > Replica-by-newer-seq > Trust-tier-tiebreaker > Gossip-suggestion-only. Field-level resolution (not row-level).

| Test ID | Requirement | Spec ref | Unit + REACH |
|---------|-------------|---------|--------------|
| `DIR-FED-TRUST-01` | Proxy MUST resolve conflicting node-state across seed/replica/gossip per §3.2 strict precedence; field-level (not row-level) | S.13 §3.2 + §8 DIR-FED-TRUST-01 | `proxy/tests/test_trust_resolver.py` — 14 unit tests cover rule 1 (seed beats replica per-field), rule 2 (newer seq + tier tiebreaker), rule 3 (gossip suggestion-only, gossip-only node included), rule 4 (field-level mix, multiple replicas pick winner only). Live: `probe_dir_fed_trust_01` (`reach/src/reach/probes/directory_conformance.py`) — INFO-skip until IICP_REACH_REPLICA_URL set; activates once P6-X.1 deploys a replica. |

**Phase**: 5 (pending ADR-012 Accepted status)
**Status**: IDs reserved; implementation deferred until Phase 4 Milestone 1 gate is closed.
**Test mark**: `@pytest.mark.phase5` — skipped in Phase 1–4 conformance runs.

### 12.1 Coordinator Behavior (MUST)

| Test ID | Requirement | Spec ref | Unit test |
|---------|-------------|---------|-----------|
| `CIP-01` | Coordinator fans out to exactly `cip.replicas` worker nodes per task; MUST return IICP-E022 if fewer workers available than `cip.replicas` | S.12 §3 CIP-01 | `proxy/tests/test_cip_coordinator.py::test_no_workers_remote_first_returns_iicp_e022` (covers insufficient-workers → IICP-E022 fallback; full multi-replica dispatch is Phase 5+) |
| `CIP-02` | Worker receiving `cip_role = worker` MUST NOT further fan out | S.12 §8 CIP-02 | `adapter/tests/test_cip_task_worker.py::test_cip_worker_does_not_fan_out` |
| `CIP-03` | Coordinator falls back to local result if worker quorum not met within `worker_timeout` | S.12 §6 CIP-03 | `proxy/tests/test_cip_coordinator.py::test_no_workers_local_first_returns_local` (covers local fallback when no eligible workers; timeout-triggered fallback is Phase 5+) |

### 12.2 Credit Accounting (MUST)

| Test ID | Requirement | Spec ref | Unit test |
|---------|-------------|---------|-----------|
| `CIP-04` | All credit reports in CIP mode include `cip_parent_task_id` for auditability | S.12 §7 CIP-04 | `adapter/tests/test_cip_task_worker.py::test_cip_worker_receipt_includes_parent_task_id` |

### 12.3 Map-Reduce Mode (SHOULD — Phase 5+)

| Test ID | Requirement | Spec ref | Unit test |
|---------|-------------|---------|-----------|
| `CIP-05` | Map-reduce subtask split produces independently-executable tasks (no cross-subtask deps) | S.12 §3.3 CIP-05 | Phase 5+ deferred |

### 12.4 Worker Behavior (MUST)

| Test ID | Requirement | Spec ref | Unit test |
|---------|-------------|---------|-----------|
| `CIP-W01` | Worker MUST include `trace.cip_role = "worker"` in RESPONSE trace when executing CIP sub-task | S.12 §4.2 CIP-W01 | `adapter/tests/test_cip_task_worker.py::test_cip_worker_response_trace_has_cip_role_worker` |
| `CIP-SESSION` | Worker MUST echo `cip_session_key` unchanged in RESPONSE trace (§10.4 session binding — prevents cross-session injection) | S.12 §10.4 | `adapter/tests/test_cip_task_worker.py::test_cip_worker_receipt_includes_session_key` + `test_cip_worker_response_trace_has_cip_role_worker` |
| `CIP-W01-RUST` | Rust node worker MUST emit `trace.cip_role = "worker"` and `trace.cip_session_key` (echoed verbatim from request `cip.cip_session_key`) in the RESPONSE JSON when `cip.cip_role == "worker"`. A missing `cip_session_key` in the request MUST result in `null` in the trace (not omitted). Non-CIP requests (no `cip` envelope) MUST NOT emit a trace block. `cip_worker_trace()` in `iicp-node/src/main.rs` implements this; without it the coordinator's CIP-BIND-01 check would discard all Rust node CIP responses. | S.12 §4.2 + §10.4 | `iicp-node/src/main.rs::tests::cip_w01_worker_role_emits_trace_with_session_key` + `cip_w01_worker_role_null_session_key_still_emits_trace` + `cip_w01_coordinator_role_does_not_emit_worker_trace` + `cip_w01_no_cip_envelope_does_not_emit_trace` |
| `CIP-V03-RUST` | Rust node MUST reject any CALL whose `trace.cip_role` is neither `"coordinator"` nor `"worker"` with 422 IICP-E028 (invalid CIP role). Absent `trace.cip_role` is allowed. `task_handler` validates after PH4-T3 before any CIP dispatch. `TaskRequestTrace.cip_role` field added. | S.12 §4.2 | `iicp-node/src/main.rs::tests::cip_v03_trace_cip_role_accepts_coordinator` + `cip_v03_trace_cip_role_accepts_worker` |
| `CIP-V04-RUST` | Rust node MUST reject any CALL whose `cip.cip_parent_task_id` is present but not a valid UUID v4 with 422 IICP-E028. `TaskRequestCip.cip_parent_task_id` field added; handler validates via `Uuid::parse_str` + version check. | S.12 §4.2 | `iicp-node/src/main.rs::tests::cip_v04_cip_parent_task_id_valid_uuid4_passes` + `cip_v04_cip_parent_task_id_non_v4_fails_check` + `cip_v04_cip_parent_task_id_malformed_fails_check` |
| `CIP-04-RUST` | Rust node credit award request MUST include `cip_parent_task_id` (the coordinator's `task_id`) when acting as a CIP worker. `report_credits()` extended with `cip_parent_task_id: Option<String>` parameter; always serialized in the award JSON body (null for non-CIP tasks, non-null for CIP tasks). Without this, the directory MUST reject the credit award. | S.12 §9 CIP-04 | `iicp-node/src/main.rs::tests::cip_04_credit_body_includes_cip_parent_when_present` + `cip_04_credit_body_null_when_no_cip_parent` |
| `CIP-V05-RUST` | Rust node MUST reject any CALL whose `cip.cip_role` is present but not `"worker"` with 422 IICP-E028. The `cip` envelope is sent by a coordinator instructing the recipient to act as the worker; any value other than `"worker"` is malformed. Python adapter enforces this via `Literal["worker"]` in `CipBlock`; Rust node now has parity via explicit validation in `task_handler`. `TaskRequestCip.cip_role` field already existed; handler now validates it post-CIP-V04 block. | S.12 §4.2 | `iicp-node/src/main.rs::tests::cip_v05_cip_role_worker_is_valid` + `cip_v05_cip_role_coordinator_in_envelope_is_invalid` |
| `CIP-TC9C-RUST` | Rust node MUST include a signed `cip_receipt` in its RESPONSE when acting as a CIP worker (S.12 §7 + §10.3 TC-9c). The receipt contains `task_id`, `worker_node_id`, `tokens_used`, `cip_parent_task_id`, `cip_session_key`, `nonce` (UUID v4), `issued_at` (ISO-8601 UTC), and `signature` (HMAC-SHA256, 64-char hex). Canonical message: `task_id:tokens_used:parent_or_empty:session_or_empty:nonce`. Key: `node_hmac_key` provisioned by the directory at registration (returned in the 201 response body and stored in `AppState.node_hmac_key`). When `node_hmac_key` is empty (node registered without HMAC support), `cip_receipt` is null. Non-CIP responses MUST NOT include a `cip_receipt`. The coordinator verifies the signature (TC-9a) before submitting to the directory ledger. Python adapter parity: `adapter/src/adapter/services/cip_receipt.py::build_worker_receipt()`. | S.12 §7 + §10.3, TC-9c | `iicp-node/src/main.rs::tests::cip_tc9c_receipt_built_when_hmac_key_provided` + `cip_tc9c_receipt_not_built_without_hmac_key` + `cip_tc9c_receipt_signature_verifiable` + `cip_tc9c_receipt_canonical_message_matches_python_format` |
| `CIP-CR1-RUST` | Rust node MUST send an HMAC-SHA256-signed credit award body to `POST /api/v1/credits/award` for non-CIP tasks (direct credit reporting). Required fields: `node_id`, `task_id`, `tokens_used`, `nonce`, `expires_at`, `signature`, `amount`. Canonical message matches `CreditsController.php` format: `task_id:tokens_used:cip_parent_or_empty:cip_session_or_empty:nonce`. **CIP worker tasks MUST NOT call `report_credits()` directly** — settlement is handled by the coordinator via `cip_receipt` verification to avoid double-crediting. `build_worker_receipt()` reused for signing; body assembled with all required fields. Bug fix: the previous `report_credits()` sent only `node_id + amount + reason` which was unconditionally rejected by `CreditsController` with IICP-E027. | S.12 §9, ADR-008 | `iicp-node/src/main.rs::tests::cip_cr1_credit_body_has_all_required_fields` + `cip_cr1_credit_award_canonical_matches_directory_controller` + `cip_cr1_cip_worker_role_gates_direct_credit_report` |
| `CIP-CR1-ADAPTER` | Python adapter `CIPWorkerReceipt` MUST include `expires_at` (ISO-8601 UTC, `issued_at + 300s`) in the signed receipt. `CreditsController.php` requires `expires_at` as a mandatory field (`required`, `date` validation). `build_worker_receipt()` in `cip_receipt.py` extended with `timedelta(seconds=300)` to compute and set `expires_at`. Without this field the coordinator's `submit_award()` call to the directory will always receive a 422 validation error. | S.12 §7, ADR-008 | `adapter/tests/test_cip_receipt.py::test_receipt_expires_at_present` + `test_receipt_expires_at_is_valid_iso8601` + `test_receipt_expires_at_is_300s_after_issued_at` |
| `CIP-CR1-PROXY` | Coordinator MUST include `expires_at` in the credit award POST body forwarded to the directory (`POST /api/v1/credits/award`). `CIPWorkerReceipt` model in `coordinator.py` extended with `expires_at: str \| None = None` field; `from_dict()` parses it; `submit_award()` payload includes it. Without `expires_at` the directory returns 422 and the worker never receives credit. | S.12 §7, ADR-008, ADR-012 | `proxy/tests/test_cip_coordinator.py::test_submit_award_payload_includes_expires_at` + `test_cip_worker_receipt_from_dict_parses_expires_at` + `test_cip_worker_receipt_from_dict_expires_at_defaults_none` |
| `CIP-CR1-WIRE` | `FallbackChain.execute()` MUST call `submit_award()` as a background task when a successful CIP response contains a `cip_receipt` field (TC-9d coordinator wiring). Before this fix `submit_award()` was defined in `coordinator.py` but never called from production code — credits were computed locally but never submitted to the directory ledger. `FallbackChain` now accepts `replay_cache`, `directory_url`, and `node_token`; on CIP success it schedules `_fire_award()` via `asyncio.create_task()`. Award is best-effort (non-blocking). Skipped gracefully when `replay_cache` is None (dev mode) or `cip_receipt` is absent (non-CIP task). | S.12 §7, ADR-012 TC-9d | `proxy/tests/test_fallback.py::test_cip_cr1_wire_submit_award_called_on_cip_receipt` + `test_cip_cr1_wire_no_award_without_cip_receipt` + `test_cip_cr1_wire_no_award_when_no_replay_cache` |

### 12.5 Coordinator Security (MUST — ADR-012 TC-9)

Trust model: the coordinator validates workers via `cip_receipt` HMAC-SHA256 (TC-9a/c), not via `trace.cip_role`. These three checks MUST all pass before the coordinator forwards a credit award to the directory ledger.

| Test ID | Requirement | Spec ref | Unit test |
|---------|-------------|---------|-----------|
| `CIP-TC9A` | Coordinator MUST verify `cip_receipt.signature` with HMAC-SHA256 keyed by `cip_session_key`; unsigned or tampered receipts MUST be rejected without a directory call | ADR-012 TC-9a, S.12 §10.3 | `proxy/tests/test_cip_coordinator.py::test_verify_receipt_valid_signature_passes` + `test_verify_receipt_wrong_secret_rejected` + `test_verify_receipt_tampered_field_rejected` + `test_verify_receipt_no_signature_rejected` |
| `CIP-TC9B` | Coordinator MUST reject receipts whose nonce appears in the replay cache (5-minute window); prevents credit double-spend | ADR-012 TC-9b, S.12 §10 | `proxy/tests/test_cip_coordinator.py::test_replay_cache_second_use_is_replay` + `test_submit_award_replay_nonce_rejected` |
| `CIP-TC9D` | Coordinator MUST verify `cip_receipt.cip_session_key` matches the key issued at dispatch; mismatch MUST abort before any directory network call | ADR-012 TC-9d, S.12 §7 | `proxy/tests/test_cip_coordinator.py::test_submit_award_session_key_mismatch_rejected` + `test_cip_flow_session_key_binds_receipt_to_dispatch` |

### 12.6 Coordinator CALL Format (MUST — S.12 §4.1)

Requirements on the outbound CALL body the coordinator sends to worker nodes. The `cip`
envelope is what signals to the worker adapter that it should execute as a CIP sub-task
and produce a `cip_receipt` in its RESPONSE.

| Test ID | Requirement | Spec ref | Unit test |
|---------|-------------|---------|-----------|
| `CIP-CALL-01` | Consumer MUST include `cip.cip_role = "worker"` and `cip.cip_session_key` in the outbound CALL body when dispatching a CIP sub-task; `build_cip_envelope()` constructs the envelope from a REMOTE DispatchDecision; `NodeClient.submit_task()` propagates it via `cip_envelope` parameter; `compute_cip_envelope()` in `proxy/cip/dispatch.py` evaluates §2.2 consumer gates and is invoked from all three proxy protocol surfaces (OpenAI-compat `/v1/chat/completions`, Ollama-compat `/api/chat` + `/api/generate`, Anthropic-compat `/v1/messages`); eligible worker filter applies `min_reputation` threshold (CIP-CALL-02) and session budget ceiling (CIP-CALL-03) | S.12 §4.1, §10.4, §2.2, CIP-04 | `proxy/tests/test_cip_coordinator.py::test_build_cip_envelope_remote_decision_produces_correct_fields` + `test_build_cip_envelope_local_decision_returns_none` + `test_build_cip_envelope_error_decision_returns_none` + `test_build_cip_envelope_integrates_with_decide_dispatch` + `proxy/tests/test_node_client.py::test_submit_task_includes_cip_envelope_in_body` + `test_submit_task_omits_cip_key_when_envelope_is_none` + `proxy/tests/test_openai_cip_dispatch.py` (22 tests: `test_returns_none_when_cip_config_is_none`, `test_returns_none_when_cip_disabled`, `test_returns_none_for_realtime_qos`, `test_returns_none_when_no_eligible_workers_local_first`, `test_returns_envelope_remote_first_with_eligible_worker`, `test_envelope_filters_incapable_nodes`, `test_returns_none_error_when_remote_first_no_capable_nodes`, `test_sensitive_body_blocked_without_opt_in`, `test_trusted_peers_allows_matching_node`, `test_trusted_peers_blocks_unlisted_node`, `test_trusted_peers_empty_allows_any`, `test_node_without_node_id_is_excluded`, `test_node_with_empty_node_id_is_excluded`, `test_min_reputation_zero_allows_node_without_score`, `test_min_reputation_blocks_low_score_node`, `test_min_reputation_allows_node_at_threshold`, `test_min_reputation_filters_mixed_pool`, `test_session_tracker_none_allows_dispatch`, `test_session_tracker_with_budget_allows_first_dispatch`, `test_session_tracker_exhausted_budget_blocks_dispatch`, `test_session_tracker_unlimited_budget_always_allows`, `test_session_tracker_auto_records_spend_on_remote_dispatch`) |
| `CIP-CALL-02` | `compute_cip_envelope()` MUST exclude eligible workers whose `reputation_score` is below `min_reputation` from `CIPDispatchConfig`; `min_reputation` flows from `proxy.toml` `[cooperative_inference]` through `ProxyConfig.cip_min_reputation` → `to_cip_dispatch_config()` → `CIPDispatchConfig.min_reputation`; default 0.0 allows all nodes | S.12 §2.2 | `proxy/tests/test_openai_cip_dispatch.py::test_min_reputation_zero_allows_node_without_score` + `test_min_reputation_blocks_low_score_node` + `test_min_reputation_allows_node_at_threshold` + `test_min_reputation_filters_mixed_pool` |
| `CIP-CALL-03` | `compute_cip_envelope()` MUST pass `session_tracker` to `decide_dispatch()`; when `session_credit_budget` is configured, the `SessionBudgetTracker` (stored in `app.state.cip_budget_tracker`) gates dispatch via Gate 2b — tasks are routed locally when accumulated spend would exceed the session ceiling (§2.2); `decide_dispatch()` MUST call `record_spend()` on REMOTE decisions to decrement the running total; tracker is app-lifetime, shared across all three compat surfaces; `None` tracker means unlimited (no budget configured) | S.12 §2.2 | `proxy/tests/test_openai_cip_dispatch.py::test_session_tracker_none_allows_dispatch` + `test_session_tracker_with_budget_allows_first_dispatch` + `test_session_tracker_exhausted_budget_blocks_dispatch` + `test_session_tracker_unlimited_budget_always_allows` + `test_session_tracker_auto_records_spend_on_remote_dispatch` |
| `CIP-CALL-04` | Coordinator MUST fan out to exactly `cip.replicas` Worker nodes; MUST NOT dispatch to a reduced replica count when fewer eligible workers exist — return IICP-E022 instead (or LOCAL for local-first strategy). `decide_dispatch()` Gate 6 enforces: when `replicas > 1` and `len(eligible_workers) < replicas`, return ERROR/LOCAL. `compute_cip_envelope()` extracts `replicas` from `body.cip.replicas` and passes to `decide_dispatch()` | S.12 §2.2 | `proxy/tests/test_cip_coordinator.py::test_insufficient_workers_for_replicas_returns_e022` + `test_insufficient_workers_local_first_falls_back_to_local` + `test_exact_worker_count_meets_replica_requirement` + `test_replicas_equals_one_never_triggers_gate` |
| `CIP-TIMEOUT-01` | When zero workers respond within `worker_timeout`, Coordinator MUST fall back to local execution if a local model is available; otherwise MUST return IICP-E024 (all workers timed out). §6 formula: `worker_timeout = coordinator_timeout × 0.6`. `compute_worker_timeout_s(coordinator_timeout_ms)` returns seconds; `cip_exhaustion_result(fallback_to_local=True)` → LOCAL, `cip_exhaustion_result(fallback_to_local=False)` → IICP-E024. `CIPDispatchConfig.coordinator_timeout_ms` defaults to 30 000 ms. | S.12 §3.1, §6 | `proxy/tests/test_cip_coordinator.py::test_compute_worker_timeout_is_60pct_of_coordinator` + `test_cip_exhaustion_fallback_to_local_returns_local` + `test_cip_exhaustion_no_local_returns_iicp_e024` + `test_cip_dispatch_config_default_coordinator_timeout` |
| `CIP-CALL-05` | Workers MUST have `load < 0.8` at selection time; `NodeSelector.rank()` drops nodes whose `load` field is ≥ 0.8 before returning the candidate list. Nodes with no `load` field default to 0.0 (admitted). The directory ADR-008 scoring formula penalises high-load nodes but does not hard-drop them — this client-side gate enforces the spec MUST. | S.12 §5.1 | `proxy/tests/test_selector.py::test_load_ceiling_drops_overloaded_node` + `test_load_ceiling_admits_node_just_below_threshold` + `test_load_ceiling_node_without_load_field_admitted` + `test_load_ceiling_preserves_directory_order_among_admitted` + `test_load_ceiling_all_overloaded_returns_empty` |
| `CIP-CALL-06` | Coordinator MUST set `trace.cip_role = "coordinator"` in its own CALL `trace` when initiating CIP dispatch (S.12 §4.2). `NodeClient.submit_task()` assembles a unified `trace_block` dict: `trace_id` (when provided) + `cip_role = "coordinator"` (when `cip_envelope` is not None). Non-CIP dispatches (`cip_envelope=None`) MUST NOT include `cip_role` in `trace`. | S.12 §4.2 | `proxy/tests/test_node_client.py::test_submit_task_sets_cip_role_coordinator_when_cip_envelope_provided` + `test_submit_task_omits_cip_role_from_trace_for_non_cip_dispatch` + `test_submit_task_cip_role_coordinator_without_trace_id` |
| `CIP-VAL-01` | Coordinator MUST validate `cip.policy`, `cip.replicas`, and `cip.quorum` at parse time before any worker selection or dispatch (S.12 §5.2). Rules: (1) `cip.policy` if present MUST be one of `"best_of_n"`, `"majority_vote"`, `"map_reduce"` → else IICP-E028; (2) `cip.replicas` if present MUST be int [1, 10] → else IICP-E028; for `majority_vote`, replicas MUST be odd → else IICP-E025; (3) `cip.quorum` if non-null MUST be int ≤ `cip.replicas` → else IICP-E028. `validate_cip_request_fields(body)` in `coordinator.py` encodes all three rules; called from `compute_cip_envelope()` before dispatch begins. | S.12 §5.2 | `proxy/tests/test_cip_coordinator.py::test_validate_no_cip_block_returns_none` + `test_validate_cip_block_not_dict_returns_none` + `test_validate_valid_policy_best_of_n_passes` + `test_validate_valid_policy_majority_vote_passes` + `test_validate_valid_policy_map_reduce_passes` + `test_validate_invalid_policy_returns_e028` + `test_validate_replicas_bounds_pass` + `test_validate_replicas_zero_returns_e028` + `test_validate_replicas_eleven_returns_e028` + `test_validate_majority_vote_odd_replicas_passes` + `test_validate_majority_vote_even_replicas_returns_e025` + `test_validate_quorum_at_replicas_passes` + `test_validate_quorum_exceeds_replicas_returns_e028` + `test_validate_quorum_without_explicit_replicas_uses_default_one` + `test_validate_null_quorum_always_passes` |
| `CIP-AGG-01` | Coordinator MUST include `trace.cip_aggregation` in its RESPONSE when CIP dispatch was activated (S.12 §4.3). Fields: `policy`, `replicas_dispatched`, `replicas_responded`, `selected_worker_id` are MUST. `selected_worker_id` MUST be null when `replicas_responded == 0`. For `majority_vote` policy, `cip_vote_count` and `cip_quorum_threshold` are also MUST. `FallbackChain.execute()` builds and injects the aggregation dict on every CIP-enabled path (success, exhaustion, and empty-node-list). Non-CIP dispatches (`cip_envelope=None`) MUST NOT include `cip_aggregation`. | S.12 §4.3 | `proxy/tests/test_fallback.py::test_cip_agg_present_on_success` + `test_cip_agg_zero_responded_when_all_fail` + `test_cip_agg_present_on_empty_node_list` + `test_cip_agg_not_present_without_cip_envelope` + `test_cip_agg_majority_vote_includes_vote_fields` |
| `CIP-BIND-01` | Coordinator MUST discard worker RESPONSE whose `trace.cip_session_key` does not match the dispatched session key (S.12 §10.4). A missing `trace.cip_session_key` is treated as mismatch and the response is discarded. Discarded responses are logged at WARNING and the chain continues to the next candidate node (same semantics as a transport error). Non-CIP dispatches (`cip_envelope=None`) MUST NOT apply this check. `FallbackChain.execute()` enforces via `continue` in the candidate loop. | S.12 §10.4 | `proxy/tests/test_fallback.py::test_cip_bind_matching_key_accepted` + `test_cip_bind_wrong_key_discarded_tries_next` + `test_cip_bind_missing_key_discarded` + `test_cip_bind_no_check_without_cip_envelope` |

---

### §12.7 Consumer Config Loading (MUST — S.12 §2.2)

`ProxyConfig.from_toml()` MUST load all `[cooperative_inference]` keys into the config
object, and `to_cip_dispatch_config()` MUST map them faithfully to a `CIPDispatchConfig`.
Without this, an operator setting `enabled = true` in `proxy.toml` would have no effect —
the coordinator would always return `LOCAL` (the safe default), silently ignoring the
operator's explicit opt-in.

| Test ID | Requirement | Spec ref | Unit test |
|---------|-------------|---------|-----------|
| `CIP-CFG-01` | `ProxyConfig.from_toml()` loads all `[cooperative_inference]` §2.2 keys (`enabled`, `strategy`, `max_credits_per_task`, `session_credit_budget`, `send_sensitive_prompts`, `trusted_peers`, `min_reputation`) and `to_cip_dispatch_config()` maps them to a correctly-typed `CIPDispatchConfig` including `min_reputation`; `enabled` MUST default `false`; `min_reputation` MUST default `0.0` | S.12 §2.2 | `proxy/tests/test_proxy_config.py` (12 tests: `test_cip_defaults_off_without_toml`, `test_to_cip_dispatch_config_defaults_disabled`, per-field loading tests ×6, `test_to_cip_dispatch_config_full_round_trip`, strategy round-trips ×2, regression `test_min_reputation_still_loaded`) |

---

## §13 Observability Conformance Tests (ADR-014 — RALPH-2 C2)

Covers Prometheus metrics exposition and OTel trace propagation. All MUST items are verified
in `adapter/tests/test_prometheus_metrics.py`, `proxy/tests/test_prometheus_metrics.py`,
and `tests/integration/test_prometheus_integration.py`.

### 13.1 Prometheus /metrics Endpoint (MUST)

| Test ID | Requirement | Spec ref |
|---------|-------------|---------|
| `METRICS-01` | `GET /metrics` on adapter returns HTTP 200 | ADR-014 §3.1 |
| `METRICS-02` | `GET /metrics` on proxy returns HTTP 200 | ADR-014 §3.1 |
| `METRICS-03` | `/metrics` response Content-Type contains `text/plain` | Prometheus exposition format |
| `METRICS-04` | Adapter `/metrics` includes `iicp_tasks_total`, `iicp_task_latency_ms`, `iicp_tokens_used_total` | ADR-014 §4 mandatory metrics |
| `METRICS-05` | Proxy `/metrics` includes `iicp_proxy_routing_ms`, `iicp_proxy_retries_total` | ADR-014 §4 mandatory metrics |

### 13.2 OTel Trace Context Propagation (MUST)

| Test ID | Requirement | Spec ref | Test file |
|---------|-------------|---------|-----------|
| `TRACE-01` | W3C `traceparent` header propagated from proxy request to adapter; `iicp.task.validate` span created | ADR-014 §5, W3C Trace Context | `adapter/tests/test_coverage_gates.py::test_otel_tracer_task_validate_span_noop_when_no_sdk` |
| `TRACE-02` | `X-IICP-Trace-Id` header echoed in adapter task response; `iicp.task.execute` span created | ADR-014 §5.2 | `adapter/tests/test_coverage_gates.py::test_otel_tracer_task_execute_span_noop_when_no_sdk` |
| `TRACE-03` | `tracestate` header preserved; `iicp.backend.call` span wraps outbound inference request | W3C Trace Context §3.3 | `adapter/tests/test_coverage_gates.py::test_otel_tracer_backend_call_span_noop_when_no_sdk` |
| `TRACE-04` | `traceparent` format MUST be 4-part dash-separated hex (`version-traceid-parentid-flags`) | W3C Trace Context §2.2 | `adapter/tests/test_coverage_gates.py::test_traceparent_w3c_format_is_validated` |

**Span lifecycle invariants**:
- Spans MUST be no-op (zero overhead) when `OTEL_EXPORTER_OTLP_ENDPOINT` is not set
- Spans MUST export to OTLP/HTTP when the env var is configured
- `iicp.task_id` attribute MUST be set on `iicp.task.validate` and `iicp.task.execute` spans
- `iicp.intent` attribute MUST be set on `iicp.task.execute` span

**Implementation**: `adapter/src/adapter/services/otel_tracer.py` (RALPH-2 C3, commit 07617cd)

### 13.3 CIP Policy Gate (Phase 5 prerequisite — MUST when CIP enabled)

These tests verify the provider-side policy gate before CIP goes live. The gate MUST deny by default (safe default — CIP off until operator configures `[cooperative_inference]`).

| Test ID | Requirement | Phase | Test file |
|---------|-------------|-------|-----------|
| `CIP-W01-GATE` | `check_coordinator()` returns `False` when `enabled=False` (safe default) | Phase 5 pre-req | `adapter/tests/test_coverage_gates.py::test_cip_policy_defaults_deny_all` |
| `CIP-W02-GATE` | `check_worker()` returns `False` when `enabled=False` (safe default) | Phase 5 pre-req | `adapter/tests/test_coverage_gates.py::test_cip_policy_defaults_deny_all` |
| `CIP-W01-ALLOW` | `check_coordinator()` returns `True` only when both `enabled=True` AND `allow_coordinator=True` | Phase 5 | `adapter/tests/test_coverage_gates.py::test_cip_policy_coordinator_requires_enabled_and_flag` |
| `CIP-W02-ALLOW` | `check_worker()` returns `True` only when both `enabled=True` AND `allow_worker=True` | Phase 5 | `adapter/tests/test_coverage_gates.py::test_cip_policy_worker_requires_enabled_and_flag` |
| `CIP-W03-CLAMP` | `max_replicas` is always ≥ 1 regardless of config input | Phase 5 | `adapter/tests/test_coverage_gates.py::test_cip_policy_max_replicas_clamped_to_one` |

**Implementation**: `adapter/src/adapter/services/cip_policy.py` (RALPH-2 C3, commit 07617cd)

### 13.3a CIP Task-Level Admission Gate (Phase 5 — MUST when CIP enabled)

These tests verify the `CooperativeInferenceGate` — the per-task admission gate (`cip_gate.py`) that enforces intent-domain restrictions, reputation thresholds, and credit floor checks before any CIP sub-task is accepted. Separate from the node-level policy gate in §13.3.

| Test ID | Requirement | Spec ref | Test file |
|---------|-------------|----------|-----------|
| `CIP-A1-GATE-01` | Tool-domain intents rejected when `allow_tool_execution=False` → 403 `tool_execution_denied` | S.12 §3.2 | `adapter/tests/test_cip_gate.py::test_gate_rejects_tool_execution_intent` |
| `CIP-A1-GATE-02` | Tool-domain intents allowed when `allow_tool_execution=True` | S.12 §3.2 | `adapter/tests/test_cip_gate.py::test_gate_allows_tool_when_explicitly_permitted` |
| `CIP-A1-GATE-03` | Caller reputation below `minimum_reputation` → 403 `reputation_too_low` | S.12 §3.3 | `adapter/tests/test_cip_gate.py::test_gate_rejects_low_reputation` |
| `CIP-A1-GATE-04` | Caller credits below `minimum_credits` → 402 `insufficient_credits` | S.12 §3.3 | `adapter/tests/test_cip_gate.py::test_gate_rejects_insufficient_credits` |
| `CIP-A1-GATE-05` | All conditions met → gate passes (no exception) | S.12 §3.3 | `adapter/tests/test_cip_gate.py::test_gate_passes_all_checks` |
| `CIP-A1-GATE-06` | CIP worker at `max_concurrent_remote` capacity → 503 IICP-E021 `capacity_exhausted`; MUST NOT silently queue or delay; slot released after task completes | S.12 §2.2 | Python: `adapter/tests/test_coverage_gates.py::test_cip_policy_acquire_slot_blocked_at_capacity` + 4 more; Rust: `iicp-node/src/main.rs::tests::cip_r3_semaphore_acquire_fails_at_capacity` + 4 more |

**Implementation**: Python adapter — `adapter/src/adapter/services/cip_policy.py` (`CooperativeInferencePolicy.try_acquire_cip_slot()` / `release_cip_slot()` — BoundedSemaphore non-blocking acquire), `adapter/src/adapter/handlers/task.py` (submit_task: CIP slot acquired before dispatch, released in finally). Rust node — `iicp-node/src/main.rs` (`AppState.cip_sem: Arc<Semaphore>`, initialized from `config.cooperative_inference.max_concurrent_remote`; task_handler CIP-R3 step uses `try_acquire()` non-blocking, `SemaphorePermit` auto-releases on drop). Config: `cip_max_concurrent_remote` (adapter.toml) / `max_concurrent_remote` (iicp-node TOML), default 2 in both.

### 13.4 CIP Wire Format Validation (Phase 5 — MUST, IICP-E028)

These tests verify §4.1/§4.2 normative field validation. All MUST trigger `IICP-E028` (422) on invalid input.

| Test ID | Requirement | Spec ref | Test file |
|---------|-------------|----------|-----------|
| `CIP-V01` | Invalid `cip.policy` value (not best_of_n/majority_vote/map_reduce) → 422 IICP-E028 | S.12 §4.1 | `proxy/tests/test_cip_call_validators.py::test_policy_rejects_unknown_value` |
| `CIP-V02` | `cip.replicas` outside [1, 10] → 422 IICP-E028 | S.12 §4.1 | `proxy/tests/test_cip_call_validators.py::test_replicas_rejects_zero` |
| `CIP-V02a` | `majority_vote` with even or < 3 `cip.replicas` → IICP-E025 (S.12 §3.2) | S.12 §3.2 | `proxy/tests/test_cip_call_validators.py::test_majority_vote_even_replicas_rejected` |
| `CIP-V03` | `cip_role` not "coordinator" or "worker" in trace → 422 IICP-E028 | S.12 §4.2 | `adapter/tests/test_models_validators.py::test_cip_role_rejects_invalid_value` |
| `CIP-V04` | `cip_parent_task_id` not valid UUID v4 → 422 IICP-E028 | S.12 §4.2 | `adapter/tests/test_models_validators.py::test_cip_parent_task_id_rejects_non_uuid` |
| `CIP-V05` | Worker echoes `cip_session_key` unchanged in RESPONSE trace | S.12 §4.2, §10.4 | `adapter/tests/test_cip_task_worker.py` |
| `CIP-V06` | Coordinator RESPONSE includes `cip_aggregation` object with required fields | S.12 §4.3 | `proxy/tests/test_cip_aggregation.py` |
| `CIP-V07` | `cip.quorum` MUST be null OR a positive integer ≤ `cip.replicas` → IICP-E028 | S.12 §4.1 | `proxy/tests/test_cip_call_validators.py::test_quorum_exceeds_replicas_rejected` |
| `CIP-V08` | `cip` object present but `cip.policy` key absent → 422 IICP-E028; distinct from `policy=null` (CIP-V01) | S.12 §4.1 | `proxy/tests/test_cip_call_validators.py::test_policy_key_absent_in_cip_object_rejected` |

**CIP-V01/V02/V02a status**: Implemented — `CIPCallFields` in `proxy/src/proxy/cip/consumer.py`. V01: `policy` enum validator (IICP-E028). V02: `replicas` Field(ge=1, le=10) (IICP-E028). V02a (iter-436): `validate_majority_vote_replicas()` model_validator enforces odd ≥ 3 for majority_vote (IICP-E025, S.12 §3.2). V08 (iter-504): absent-key case (distinct from null value). 33 unit tests in `proxy/tests/test_cip_call_validators.py`.
**CIP-V07 status**: Implemented iter-440 — `validate_majority_vote_replicas()` model_validator (mode="after") also enforces quorum cross-field constraint: null OR positive integer ≤ replicas (IICP-E028, S.12 §4.1). 9 new tests in `proxy/tests/test_cip_call_validators.py`.
**CIP-V03/V04 status**: Implemented iter-428 — `TaskCip.cip_role` uses `Literal["coordinator","worker"]` (Pydantic v2 rejects unknown values at model parse → 422); `cip_parent_task_id` has `field_validator` for UUID v4. 10 unit tests in `test_models_validators.py`.
**CIP-V05 status**: Implemented iter-472 — `test_cip_task_worker.py::test_cip_worker_receipt_includes_session_key` (verifies `cip_receipt.cip_session_key == original`) + `test_cip_worker_response_trace_has_cip_role_worker` (verifies `trace.cip_session_key == session_key` in RESPONSE). `ResponseTrace` model added to `adapter/src/adapter/models.py`; handler populates `trace.cip_session_key` when CIP worker gate passes. See also §12.4 CIP-SESSION.
**CIP-V06 status**: Implemented — `CIPAggregationResult` in `proxy/src/proxy/cip/aggregation.py`. Enforces: `replicas_responded ≤ replicas_dispatched`; `selected_worker_id` null when `replicas_responded == 0`; all MUST fields present; iter-436 added: `majority_vote` requires non-null `cip_vote_count` + `cip_quorum_threshold` (S.12 §4.3 line 284). 25 unit tests in `proxy/tests/test_cip_aggregation.py`.

### 13.6 Reputation Update Rules (Phase 5 — MUST)

These tests verify §11 normative delta rules. Implementations MUST pass REP-01..07.

| Test ID | Requirement | Spec ref | Test file |
|---------|-------------|----------|-----------|
| `REP-01` | Successful task within latency budget increases `reputation_score` | §11.2, §11.4 | `directory/tests/Feature/ReputationServiceTest.php` |
| `REP-02` | Failed task decreases `reputation_score` | §11.2, §11.4 | `directory/tests/Feature/ReputationServiceTest.php` |
| `REP-03` | `reputation_score` never falls below 0.0 or exceeds 1.0 | §11.4 | `directory/tests/Feature/ReputationServiceTest.php` |
| `REP-04` | Per-node hourly reputation gain MUST NOT exceed MAX_HOURLY_GAIN (0.20) regardless of heartbeat frequency (RT-01b, #381) | §11.2 | `directory/tests/Feature/ReputationServiceTest.php::test_rt01b_hourly_velocity_ceiling_caps_gain` |
| `REP-05` | Free credit allocation MUST be gated per source IP — per-node_id gate alone is insufficient (RT-02b, #380) | §6.5 | `directory/tests/Feature/CreditHarvestRegressionTest.php::test_new_node_id_from_same_ip_is_blocked_by_ip_gate` |
| `REP-06` | Proxy reporters for Sybil latency-EMA quorum MUST be ≥3 days old with reputation ≥0.55 — fresh nodes do not satisfy the quorum gate (RT-03b, #382) | §T4.3 | `directory/tests/Feature/ProxyTelemetryTest.php::test_rt03b_fresh_proxy_nodes_do_not_count_toward_quorum` |
| `REP-07` | Audit-report reporters MUST be ≥3 days old with reputation ≥0.55 for their report to carry a reputation delta — fresh reporter rotation is blocked (RT-05b, #383) | §7 | `directory/tests/Feature/AuditReportTest.php::test_rt05b_fresh_reporter_delta_suppressed` |

**Implementation**: `directory/app/Services/ReputationService.php` (iter 30, closes #113). Security hardening REP-04..07 added 2026-06-01 (iter-1736, #380-383).

### 13.5 Metrics Semantic Correctness (SHOULD)

| Test ID | Requirement | Spec ref |
|---------|-------------|---------|
| `METRICS-06` | `iicp_tasks_total` counter increments on each task completion | ADR-014 §4.1 |
| `METRICS-07` | `iicp_proxy_retries_total` increments on each retry attempt | ADR-014 §4.3 |
| `METRICS-08` | `iicp_task_latency_ms` histogram includes 5000ms bucket | ADR-014 §4.2 SLA bucket |

### 13.7 QoS Admission Control (Phase 5 — MUST)

These tests verify §2.2 normative admission control rules. Implementations MUST pass QOS-ADMIT-01.

| Test ID | Requirement | Spec ref | Test file |
|---------|-------------|----------|-----------|
| `QOS-ADMIT-01` | Node with `max_concurrent=1` returns HTTP 429 `capacity_exceeded` with `qos_class` and `retry_after_ms` on second concurrent realtime request | §2.2 | `adapter/tests/test_concurrency.py` |
| `QOS-ADMIT-02` | Proxy treats `capacity_exceeded` 429 as node-switch signal (next node, no backoff) | §2.2 | `proxy/tests/test_retry.py` |

**Test procedure for QOS-ADMIT-01**:
1. Start adapter with `max_concurrent=1`
2. Submit a `realtime` task that runs ≥ 500ms
3. While first task is in-flight, submit a second `realtime` task
4. Assert second response is HTTP 429 with `error.code == "capacity_exceeded"`
5. Assert response body includes `error.qos_class` and `error.retry_after_ms`

### 13.8 CIP Conformance Level Declarations (Phase 5 — MUST)

These tests verify that `cip_conformance_level` is correctly declared in REGISTER payloads and enforced during routing and execution. Required for any node claiming `CIP-Consumer`, `CIP-Provider`, or `CIP-Full` conformance (§5.2).

| Test ID | Requirement | Spec ref | Test file |
|---------|-------------|----------|-----------|
| `CIP-CONF-01` | Node registering with `cip_conformance_level: "CIP-Consumer"` has field preserved and surfaced in NODELIST | S.12 §5.2 | `directory/tests/Feature/NodeRegistrationTest.php` |
| `CIP-CONF-02` | Adapter with `cip_conformance_level: "CIP-Provider"` enforces `check_worker()` gate — rejects sub-tasks when `enabled=False` | S.12 §5.2 | `adapter/tests/test_coverage_gates.py` |
| `CIP-CONF-03` | Proxy claiming `CIP-Full` passes both `check_coordinator()` and `check_worker()` gates simultaneously | S.12 §5.2 | `adapter/tests/test_coverage_gates.py` |

**Status**: Defined in v1.0.0 (2026-05-17). Implementation tracks issue #67 (CIP spec v0.6.0 CLOSED). Test IDs added to Phase 5 gate requirements in GOVERNANCE.md.

---

### 13.9 Conformance Badge System (S.14 — MUST)

These tests verify the badge submission, verification, and lifecycle requirements from `spec/conformance-badges.md`. The directory is the Genesis Seed issuer for `genesis-verified` badges.

| Test ID | Requirement | Spec ref | Test file |
|---------|-------------|----------|-----------|
| `BADGE-SUBMIT-01` | `POST /v1/conformance/submit` accepts a well-formed self-attested badge record and returns 201 with `badge_id` and `expires_at` | S.14 §7, BADGE-02 | `directory/tests/Feature/ConformanceBadgeTest.php` |
| `BADGE-SUBMIT-02` | `POST /v1/conformance/submit` rejects records with `expires_at` > 91 days after `passed_at` with 422 | S.14 §4, BADGE-03 | `directory/tests/Feature/ConformanceBadgeTest.php` |
| `BADGE-SUBMIT-03` | `POST /v1/conformance/submit` rejects duplicate `badge_id` with 409 | S.14 §4 | `directory/tests/Feature/ConformanceBadgeTest.php` |
| `BADGE-VERIFY-01` | `GET /v1/conformance/verify?did=&tier=` returns `is_valid: true` for an active, non-expired badge | S.14 §7 | `directory/tests/Feature/ConformanceBadgeTest.php` |
| `BADGE-VERIFY-02` | `GET /v1/conformance/verify?did=&tier=` returns `is_valid: false` for an expired badge | S.14 §4, BADGE-03 | `directory/tests/Feature/ConformanceBadgeTest.php` |
| `BADGE-LIST-01` | `GET /v1/conformance/badges?did=` lists all active badges for a DID, excluding expired | S.14 §7 | `directory/tests/Feature/ConformanceBadgeTest.php` |

**Status**: Defined in v1.1.0 (2026-05-18). Implementation: `directory/app/Http/Controllers/ConformanceController.php` + `directory/tests/Feature/ConformanceBadgeTest.php` (200 lines, 13 tests). Tracks issue #94 (CLOSED) and #96. Ed25519 genesis-verified signing (BADGE-01) deferred to `#96` Phase 5B.

---

## 14. End-to-End Mesh Invariant Tests (Phase 5 — research/gamification-track/03-anti-gaming.md)

These test IDs capture emergent mesh properties that can only be verified at the multi-node
level. They are not MUST assertions about a single implementation component; instead they
encode invariants that MUST hold across the live system once the mesh is operating correctly.

**Phase**: 5 (operator-diversity features) — IICP-E2E-01 and IICP-E2E-03 require the
multi-node integration harness (#299). IICP-E2E-04 is covered by proxy unit tests (iter-969).

**Status**: IDs reserved (iter-965, ADR-030 Proposed unblocks scope). IICP-E2E-04 closed
(iter-969 — proxy unit tests `test_cip_response_hash_mismatch_discards_retries_next` +
`test_cip_response_hash_missing_discards_node` in `proxy/tests/test_fallback.py`). IICP-E2E-01/03
deferred until #299 multi-node harness.

**Test mark**: `@pytest.mark.e2e_mesh` — separate from `@pytest.mark.phase5`; requires
multi-node Docker Compose stack or live production.

### 14.1 Discovery Liveness (MUST — iicp-core.md §3 + ADR-008)

| Test ID | Requirement | Spec ref | Test method |
|---------|-------------|---------|-------------|
| `IICP-E2E-01` | Any node that is `active` in the directory MUST appear in `GET /v1/discover` results for a matching intent within 2× the heartbeat interval (120 s) of its last heartbeat. The discover response MUST NOT exclude active nodes whose `score` > 0.0. | iicp-core.md §3, ADR-008 §3 | Multi-node harness (#299): register N nodes, heartbeat all, discover, assert N nodes in response. Currently unimplemented — blocked on #299. |

### 14.2 Credit Integrity (MUST — ADR-012 TC-9, iicp-core.md §9)

| Test ID | Requirement | Spec ref | Test method |
|---------|-------------|---------|-------------|
| `IICP-E2E-03` | Within a 24-hour reconciliation window, total credits awarded to all nodes (via `POST /v1/credits/award`) MUST be ≥ total credits debited (via CIP sub-task settlement). The ledger MUST be monotonically non-decreasing — no net credit disappears without a corresponding debit event in the directory event log. | ADR-012 TC-9, iicp-core.md §9.4 | Multi-node CIP harness (#299): run N CIP tasks, audit ledger via `GET /v1/credits/balance` + event log. Currently unimplemented — blocked on #299. |

### 14.3 CIP Receipt Integrity (MUST — TC-9c §10.3, iicp-cooperative-inference.md §10.3)

| Test ID | Requirement | Spec ref | Test method |
|---------|-------------|---------|-------------|
| `IICP-E2E-04` | When a CIP worker response includes a `cip_receipt`, the coordinator MUST independently compute the SHA-256 of the canonical result JSON and compare it against `cip_receipt.response_hash`. A mismatch or absent `response_hash` MUST cause the coordinator to discard the response and continue to the next available node (fallback chain proceeds). | iicp-cooperative-inference.md §10.3, TC-9c Phase 5, ADR-012 TC-9 | Unit tests in `proxy/tests/test_fallback.py`: `test_cip_response_hash_mismatch_discards_retries_next` (tampered hash → next node), `test_cip_response_hash_missing_discards_node` (missing field → no_available_node). Adapter coverage: `adapter/tests/test_cip_receipt.py::test_verify_rejects_tampered_response_hash`. |

**Implementation notes**:
- `_verify_receipt_hash()` in `proxy/src/proxy/routing/fallback.py` implements the coordinator
  verification: independently computes SHA-256 of canonical result JSON (sorted keys, no whitespace)
  and compares against `cip_receipt.response_hash`. Discard on mismatch or absent field.
- Adapter implementation: `compute_response_hash()` in `adapter/src/adapter/services/cip_receipt.py`
  produces the hash; `verify_worker_receipt()` verifies HMAC binding that includes `response_hash`.
- IICP-E2E-01 and IICP-E2E-03 require the multi-node harness from #299 (full-stack Docker
  Compose with ≥2 provider nodes, a proxy, and the live directory).
- ADR-030 operator identity layer is a prerequisite for testing operator-diversity invariants
  (W-034 scope); once ADR-030 is Accepted and Tier-2 attestation ships, IICP-E2E-02 (reputation
  convergence across operators) can be defined and added here.

---

## 15. Operator Recognition Conformance Tests (Phase 5D — spec/iicp-recognition.md)

**Status**: Phase 5D — deferred until G1 (ADR-030 Accepted) + G6 (spec v1.0 + PS ratification).
**Spec**: `spec/iicp-recognition.md` v0.1.0-draft.
**Tracking**: #309 (spec), #310 (implementation tracker).
**REACH probes**: `reach/src/reach/probes/recognition_conformance.py` (not yet created — pending G1+G6).

These test IDs are registered from `spec/iicp-recognition.md §10` for traceability. Implementation and REACH probes activate after ADR-030 Accepted + spec at v1.0.

### 15.1 Profile API

| Test ID | Method | Endpoint | Level | Assertion |
|---------|--------|----------|-------|-----------|
| RECOG-PROF-01 | GET | `/v1/operator/{handle}/profile` | MUST | Returns valid profile schema with `rank`, `badges`, `leaderboard_positions` |
| RECOG-PROF-02 | GET | `/v1/operator/{handle}/profile` (unknown) | MUST | 404 for unknown handle; 410 for opted-out operator |

### 15.2 Leaderboards

| Test ID | Method | Endpoint | Level | Assertion |
|---------|--------|----------|-------|-----------|
| RECOG-LEAD-01 | GET | `/v1/leaderboards/{board_id}` | MUST | Returns entries sorted by declared criteria; excludes opted-out operators |

### 15.3 Catalog endpoints

| Test ID | Method | Endpoint | Level | Assertion |
|---------|--------|----------|-------|-----------|
| RECOG-BADG-01 | GET | `/v1/badges` | MUST | Returns complete badge catalog with stable IDs and `trigger` fields |
| RECOG-SEAS-01 | GET | `/v1/seasons/current` | MUST | Returns valid season window with `start`, `end`, `id` |

### 15.4 Operator-authenticated endpoints

| Test ID | Method | Endpoint | Level | Assertion |
|---------|--------|----------|-------|-----------|
| RECOG-VIS-01 | POST | `/v1/operator/{handle}/visibility` | MUST | 401 without operator auth; accepts valid operator-signed request |
| RECOG-HAN-01 | POST | `/v1/operator/{handle}/handle` | MUST | Rejects reserved words and squatting patterns (≥ 3 chars, ASCII-only) |
| RECOG-PRIV-01 | GET | `/v1/operator/{handle}/private_summary` | MUST | 401 without operator auth; returns full private profile for auth'd operator |

### 15.5 Rank semantics

| Test ID | Level | Assertion |
|---------|-------|-----------|
| RECOG-RANK-01 | MUST | Rank earned persists even if trigger condition later fails (ratchet property); Mesh Legend (top-10) recomputed dynamically |
| RECOG-RANK-02 | MUST | Rank ≥ 4 (CIP Provider) requires Tier 2 attestation per ADR-030 |

### 15.6 Anti-gaming invariants

| Test ID | Level | Assertion |
|---------|-------|-----------|
| RECOG-ANTI-01 | MUST | Same operator's nodes do not multiply operator-diversity scores |
| RECOG-ANTI-02 | MUST | Task badges with threshold ≥ 1000 require ≥ 3 distinct proxy contributors |
| RECOG-SEAS-02 | MUST | Season-exclusive badges cannot be earned after season window closes |

### 15.7 Privacy

| Test ID | Level | Assertion |
|---------|-------|-----------|
| RECOG-OPT-01 | MUST | Opt-out applied within 5 minutes (leaderboard + profile removed); private profile still accessible to operator |

### 15.8 Founder ordinals (spec/iicp-recognition.md §5.4)

| Test ID | Level | Assertion |
|---------|-------|-----------|
| RECOG-FND-01 | MUST | Founder ordinal #2+ assigned only after ≥30d healthy + a genuine served node (operator_verified + public_reachable + active + available); #1 reserved + gate-exempt; provisional slots hold no number |
| RECOG-FND-02 | MUST | Tier (Genesis-50/3mo, Founders-500/6mo, Founders-1000/12mo, from GENESIS_MS) computed on lock-in timestamp; single-best bracket returned |
| RECOG-FND-03 | MUST | Ordinals are immutable once locked; reclaiming a provisional slot renumbers no locked founder |
| RECOG-FND-04 | MUST | `FOUNDER_SUCCESSION` preserves provenance lineage, does not reset lock-in, cannot re-open a closed tier |
| RECOG-FND-05 | MUST | Founder ordinal keyed to `operator_pubkey` (ed25519 operator_id), never node_id; dev/test identities purged |
| RECOG-FND-06 | MUST | `FOUNDER_LOCKIN` / `FOUNDER_SUCCESSION` events carry valid Ed25519 sig + `prev_hash` on a dedicated non-federated chain (NOT `node_events`, per DIR-FED-16); emission is a tracked follow-up |

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 4.45.0 | 2026-06-28 | §10.4 adds SDK-NODE-03..05 for SDK 0.7.75 external-tunnel guardrails: persistent provider-rate-limit cooldown, host-wide creation pacing/lease, and fallback to safe reachability methods rather than tunnel-create loops or unverified endpoint advertisement. §3.2/§3.3b/§7 reconcile peer-exchange conformance rows with Ed25519 gossip signatures instead of node-token/HMAC auth. |
| 4.44.0 | 2026-06-09 | §3.5b Per-Node Health Vector (ADR-044 / #492): DIR-NODE-HEALTH-01..04 registered. Formula W_REACHABILITY=0.70 + W_LATENCY=0.30; success_rate + reputation absent. Key test: DIR-NODE-HEALTH-03 — new reachable node with no task history MUST score ≥85 ("healthy"). PHP: `NodeDetailHealthTest` (3 tests); Rust: `health.rs` (27 tests including `new_reachable_node_with_no_task_history_is_healthy`). |
| 4.43.0 | 2026-06-06 | §15.8 Founder ordinals — register RECOG-FND-01..06 (claimed registered in iicp-recognition §10 but absent here). Reconciled to the shipped #310 detector + iicp-recognition v0.6.0 (operator_pubkey keying, genuine-served-node gate, #1 reserved/gate-exempt, GENESIS_MS, founder events on a dedicated non-federated chain). SPEC_UPDATE_PLAN Unit A tail. |
| 4.35.0 | 2026-05-24 | §15 Operator Recognition Conformance Tests added: 14 RECOG-* test IDs (RECOG-PROF-01/02, RECOG-LEAD-01, RECOG-BADG-01, RECOG-SEAS-01/02, RECOG-VIS-01, RECOG-HAN-01, RECOG-PRIV-01, RECOG-RANK-01/02, RECOG-ANTI-01/02, RECOG-OPT-01). Phase 5D deferred — pending G1 (ADR-030 Accepted) + G6 (spec v1.0 PS ratification). Sourced from `spec/iicp-recognition.md §10`. Closes spec traceability gap in #309. |
| 4.34.0 | 2026-05-24 | §14.3 corrected: IICP-E2E-04 re-defined from incorrect "discover response_hash" to correct "CIP receipt hash integrity" (TC-9c §10.3). Section renamed from "Routing Diversity" to "CIP Receipt Integrity". Two proxy unit tests added: `test_cip_response_hash_mismatch_discards_retries_next` + `test_cip_response_hash_missing_discards_node`. IICP-E2E-04 **CLOSED** (iter-969). Closes #312. |
| 4.33.0 | 2026-05-24 | §14 End-to-End Mesh Invariants added: IICP-E2E-01 (discovery liveness), IICP-E2E-03 (credit integrity), IICP-E2E-04 (routing diversity / response_hash). IDs reserved per W-034 scope-expansion (WARDEN-067, iter-965). IICP-E2E-01/03 blocked on #299 multi-node harness. IICP-E2E-04 REACH probe deferred to #312. ADR-030 Proposed unblocked this scope. IICP-E2E-02 (reputation convergence) deferred until ADR-030 Tier-2 attestation ships. |
| 4.32.0 | 2026-05-22 | §3.1: DIR-REG-08/DIR-REG-09 — annotated directory unit test coverage (`RegisterTest::test_accepts_unrecognised_quantization_value` + `test_accepts_unrecognised_inference_engine_value`). REACH live probe not feasible (would create live nodes); PHP feature tests cover the MUST constraint. |
| 4.31.0 | 2026-05-22 | §13.5 CIP-BUG-01 fix: `DirectoryClient.discover(cip_capable=True)` MUST send `cip_capable=1` (integer), not `"true"` (string) — Laravel boolean validation rejects string form. CIP-capable filter silently broken since iter-486 (coordinators received all nodes); fixed to `1`/`0` integers. 2 proxy tests updated; proxy test count unchanged at 391. |
| 4.30.0 | 2026-05-22 | §12.4 task_handler CC refactor: `validate_task_fields()` + `validate_cip_wire_fields()` extracted from `task_handler()` to reduce cyclomatic complexity (Sentrux cc 36→≤30). Existing CIP-V03-RUST/CIP-V04-RUST/CIP-V05-RUST requirements unchanged — moved to helper functions with 15 additional direct unit tests (`validate_task_fields_*` ×8, `validate_cip_wire_fields_*` ×7). `cargo test` 131→146. Quality 7089→7092. |
| 4.29.0 | 2026-05-22 | §12.4 CIP-CR1-WIRE added: `FallbackChain.execute()` now wired to call `submit_award()` as background task when CIP response contains `cip_receipt` (TC-9d). `FallbackChain` accepts `replay_cache`, `directory_url`, `node_token`; `_schedule_award()` helper + `_fire_award()` module-level coroutine added. `proxy.main` passes `ReplayCache()` at startup. 3 new proxy tests; proxy 388→391 tests. |
| 4.28.0 | 2026-05-22 | §12.4 CIP-CR1-ADAPTER + CIP-CR1-PROXY added: Python adapter `build_worker_receipt()` + `CIPWorkerReceipt` model now include `expires_at` (issued_at + 300s). Coordinator `submit_award()` payload includes `expires_at`. `CreditsController.php` requires it — all credit award calls were rejected with 422 without this field. Adapter 209→212, proxy 385→388 tests. |
| 4.27.0 | 2026-05-22 | §12.4 CIP-CR1-RUST added: Rust node `report_credits()` now sends HMAC-SHA256-signed body with all required fields (`task_id`, `tokens_used`, `nonce`, `expires_at`, `signature`). CIP worker tasks gated from direct credit report — coordinator handles settlement via `cip_receipt`. Bug fix: previous body missing required fields was rejected by `CreditsController` with IICP-E027. 3 new tests; `cargo test` 128→131. |
| 4.26.0 | 2026-05-22 | §12.4 CIP-TC9C-RUST added: Rust node MUST include HMAC-SHA256 signed `cip_receipt` in CIP worker RESPONSE (S.12 §7 + §10.3, TC-9c). `build_worker_receipt()` helper added to `iicp-node/src/main.rs`; `AppState.node_hmac_key` field added (read from directory registration 201 response). Canonical message matches Python adapter format. 4 new tests; `cargo test` 124→128. |
| 4.25.0 | 2026-05-22 | §12.4 CIP-V05-RUST added: Rust node MUST reject `cip.cip_role` ≠ `"worker"` with 422 IICP-E028 (S.12 §4.2). Closes adapter/Rust parity gap (#284). 2 new tests; `cargo test` 122→124. |
| 4.24.0 | 2026-05-22 | §12.4 CIP-04-RUST added: Rust node credit award MUST include `cip_parent_task_id` for CIP worker tasks (S.12 §9). `report_credits()` extended with optional param; always serialized (null for non-CIP). 2 new tests; `cargo test` 120→122. #283 CLOSED. |
| 4.23.0 | 2026-05-22 | §12.4 CIP-V03-RUST + CIP-V04-RUST added: Rust node MUST reject invalid `trace.cip_role` values with 422 IICP-E028 (S.12 §4.2); MUST reject malformed `cip.cip_parent_task_id` (non-UUID-v4) with 422 IICP-E028. `TaskRequestTrace.cip_role` and `TaskRequestCip.cip_parent_task_id` fields added. 5 new unit tests; `cargo test` 115→120 passed. |
| 4.22.0 | 2026-05-22 | §12.4 CIP-W01-RUST added: Rust node MUST emit `trace.cip_role="worker"` + `trace.cip_session_key` echo in CIP worker RESPONSE (S.12 §4.2 + §10.4). `cip_worker_trace()` helper added to `iicp-node/src/main.rs`; `TaskRequestCip.cip_session_key` field added. Without this, the coordinator's CIP-BIND-01 check discards all Rust node CIP responses. 4 new Rust unit tests; `cargo test` 111→115 passed. |
| 4.21.0 | 2026-05-22 | §12.6 CIP-BIND-01 added: Coordinator MUST discard worker RESPONSE whose `trace.cip_session_key` does not match dispatched session key (S.12 §10.4). Missing key treated as mismatch. `FallbackChain.execute()` enforces via `continue` in candidate loop. 4 new tests in `proxy/tests/test_fallback.py`. Proxy test count: 381→385. |
| 4.20.0 | 2026-05-22 | §12.6 CIP-AGG-01 added: Coordinator MUST include `trace.cip_aggregation` in RESPONSE when CIP dispatch was activated (S.12 §4.3). `FallbackChain.execute()` now accepts `cip_policy/cip_replicas/cip_quorum` params and injects the aggregation object on all CIP paths (success, exhaustion, empty-node-list). 5 new tests in `proxy/tests/test_fallback.py`. Proxy test count: 376→381. |
| 4.19.0 | 2026-05-22 | §12.6 CIP-VAL-01 added: parse-time validation of `cip.policy`, `cip.replicas`, `cip.quorum` (S.12 §5.2). `validate_cip_request_fields()` in `coordinator.py` encodes all three rules; called from `compute_cip_envelope()` before dispatch. 15 new tests in `proxy/tests/test_cip_coordinator.py`. Proxy test count: 361→376. |
| 4.18.0 | 2026-05-22 | §12.6 CIP-CALL-06 added: Coordinator MUST set `trace.cip_role = "coordinator"` when initiating CIP dispatch (S.12 §4.2). `NodeClient.submit_task()` now assembles a unified `trace_block` that merges `trace_id` and `cip_role`; non-CIP dispatches leave `cip_role` absent. 3 new tests in `proxy/tests/test_node_client.py`. Proxy test count: 358→361. |
| 4.17.0 | 2026-05-22 | §12.6 CIP-CALL-05 added: Workers MUST have `load < 0.8` at selection time (S.12 §5.1). `NodeSelector.rank()` now drops nodes with `load >= 0.8`; nodes without a `load` field default to 0.0. Module docstring updated to reflect three filter axes. 5 new tests in `proxy/tests/test_selector.py`. Proxy test count: 353→358. |
| 4.16.0 | 2026-05-22 | §12.6 CIP-TIMEOUT-01 added: §3.1 + §6 worker_timeout / IICP-E024. `compute_worker_timeout_s()` applies §6 formula (coordinator_timeout × 0.6); `cip_exhaustion_result(fallback_to_local)` encodes §3.1 rule — LOCAL when local model available, IICP-E024 otherwise. `CIPDispatchConfig.coordinator_timeout_ms` field added (default 30 000 ms). 4 new tests in `test_cip_coordinator.py`. Proxy test count: 349→353. Quality: 7088→7089. |
| 4.15.0 | 2026-05-22 | §12.6 CIP-CALL-04 added: Coordinator MUST fan out to exactly cip.replicas workers; MUST NOT dispatch to reduced replica count (S.12 §2.2). Gate 6 in `decide_dispatch()`: when `replicas > 1` and `len(eligible_workers) < replicas` → IICP-E022 (or LOCAL for local-first). `compute_cip_envelope()` extracts replicas from `body.cip.replicas`. 4 new tests in `test_cip_coordinator.py`. Proxy test count: 345→349. |
| 4.14.0 | 2026-05-22 | §13.3 CIP-A1-GATE-06 updated: Rust node parity — IICP-E021 capacity gate now enforced in `iicp-node` task_handler (CIP-R3 step). `AppState.cip_sem: Arc<Semaphore>` initialized from `config.cooperative_inference.max_concurrent_remote` (default 2). `try_acquire()` non-blocking; `SemaphorePermit` auto-releases on drop (no finally needed). 5 new cargo tests. Rust test count: 105→110. Closes #281. |
| 4.13.0 | 2026-05-22 | §13.3 CIP-A1-GATE-06 added: IICP-E021 capacity_exhausted gate — CIP worker at max_concurrent_remote capacity MUST return 503 immediately without queuing (S.12 §2.2). Implementation: `CooperativeInferencePolicy.try_acquire_cip_slot()` / `release_cip_slot()` (threading.BoundedSemaphore non-blocking); `config.cip_max_concurrent_remote` (default 2, ge=1, le=100); `submit_task()` acquires slot before dispatch, releases in finally. 5 new tests in `adapter/tests/test_coverage_gates.py`. Adapter test count: 204→209. |
| 4.12.0 | 2026-05-22 | §13.5 CIP-V08 added: `cip` object present but `cip.policy` key entirely absent → 422 IICP-E028 (S.12 §4.1 MUST). Distinct from `policy=null` (CIP-V01): absent key is a required-field validation error, null value is a type error. 1 new test `test_policy_key_absent_in_cip_object_rejected` in `proxy/tests/test_cip_call_validators.py`. Proxy test count: 344→345. |
| 4.11.0 | 2026-05-22 | §12.6 CIP-CALL-03 updated: MEDIUM BUG fixed — `decide_dispatch()` checked `can_spend()` but never called `record_spend()` on REMOTE decisions, making the session budget ceiling non-functional in production. Fixed: `record_spend(estimated_credits)` called in `coordinator.py` on all REMOTE decisions. New test `test_session_tracker_auto_records_spend_on_remote_dispatch` verifies sequential dispatch auto-decrements budget and blocks on exhaustion. Proxy test count: 343→344. |
| 4.10.0 | 2026-05-22 | §12.6 CIP-CALL-03 added + CIP-CALL-01 updated: `session_credit_budget` enforcement wired end-to-end — `SessionBudgetTracker` instantiated in `proxy/main.py` lifespan when `cip_session_credit_budget` is set; stored in `app.state.cip_budget_tracker` and propagated to `compat.state`; `compute_cip_envelope()` signature extended with `session_tracker` parameter, passed to `decide_dispatch()` Gate 2b; all three compat surfaces (OpenAI/Ollama/Anthropic) read and pass tracker. 4 new tests in `test_openai_cip_dispatch.py` (unlimited=None allows, fresh budget allows, exhausted budget blocks, unlimited tracker always allows). Proxy test count: 339→343. |
| 4.9.0 | 2026-05-22 | §12.6 CIP-CALL-02 added + CIP-CALL-01 + CIP-CFG-01 updated: `min_reputation` enforcement wired end-to-end — `CIPDispatchConfig.min_reputation` field added; `ProxyConfig.to_cip_dispatch_config()` now passes `cip_min_reputation`; `compute_cip_envelope()` filters eligible workers by `reputation_score >= min_reputation`. 4 new tests in `test_openai_cip_dispatch.py` (zero-default allows missing score, below-threshold blocked, exact-threshold allowed, mixed-pool filtered). Proxy test count: 335→339. |
| 4.8.0 | 2026-05-22 | §12.6 CIP-CALL-01 extended: `compute_cip_envelope()` in `proxy/cip/dispatch.py` (shared helper) now evaluates §2.2 consumer gates from all three proxy protocol surfaces — OpenAI-compat (`/v1/chat/completions`), Ollama-compat (`/api/chat` + `/api/generate`), Anthropic-compat (`/v1/messages`). 13 new unit tests in `proxy/tests/test_openai_cip_dispatch.py` (config-disabled, realtime-QoS bypass, no-eligible-workers, REMOTE envelope fields, trusted_peers enforcement ×3, node_id guard ×2, sensitivity block). Proxy test count: 322→335. |
| 4.7.0 | 2026-05-22 | §12.7 CIP-CFG-01: `ProxyConfig` extended with all `[cooperative_inference]` §2.2 keys (`cip_enabled`, `cip_strategy`, `cip_max_credits_per_task`, `cip_session_credit_budget`, `cip_send_sensitive_prompts`, `cip_trusted_peers`). `from_toml()` iterates a key→dest mapping; `to_cip_dispatch_config()` constructs a `CIPDispatchConfig` (function-local import, no circular-import risk). 12 new tests in `proxy/tests/test_proxy_config.py`. Proxy test count: 310→322. |
| 4.6.0 | 2026-05-22 | §12.6 CIP-CALL-01: `build_cip_envelope()` helper added to `coordinator.py` — constructs `{cip_role, cip_session_key, cip_parent_task_id}` from a REMOTE DispatchDecision, returns None for LOCAL/ERROR. 4 new tests in `test_cip_coordinator.py`: `test_build_cip_envelope_remote_decision_produces_correct_fields` + local + error + round-trip. Proxy test count: 302→306. |
| 4.5.0 | 2026-05-22 | §12.6 CIP-CALL-01 wire-body test references added: `test_node_client.py::test_submit_task_includes_cip_envelope_in_body` + `test_submit_task_omits_cip_key_when_envelope_is_none` — directly verify the outbound HTTP body contains (or omits) the `cip` key. Proxy test count: 300→302. |
| 4.4.0 | 2026-05-22 | §12.6 Coordinator CALL Format: `CIP-CALL-01` added — Coordinator MUST include `cip.cip_role="worker"` and `cip.cip_session_key` in outbound CALL body (S.12 §4.1, §10.4). Implementation: `NodeClient.submit_task()` extended with `cip_envelope` parameter; `TaskRouter.route()` propagates it. Tests: `test_route_passes_cip_envelope_to_submit_task` + `test_route_omits_cip_envelope_when_not_provided` (proxy test count: 298→300). |
| 4.3.0 | 2026-05-22 | §12.5 Coordinator Security (TC-9): 3 new conformance test IDs registered — CIP-TC9A (HMAC signature verification, 4 unit tests), CIP-TC9B (nonce replay protection, 2 unit tests), CIP-TC9D (session binding pre-directory-call check, 2 unit tests). All map to ADR-012 TC-9 coordinator MUST requirements; implemented in `proxy/tests/test_cip_coordinator.py` but previously unregistered in the conformance suite. Trust model documented: coordinator uses cip_receipt HMAC (not trace.cip_role) as authoritative trust mechanism. |
| 4.2.0 | 2026-05-22 | §13.4 ResponseTrace validators: `test_models_validators.py` extended with 3 `ResponseTrace` tests (worker role accepted, coordinator rejected, all-None accepted). Adapter test count: 201→204. CIP-V05 status note corrected: was pointing to wrong test; now references `test_cip_worker_receipt_includes_session_key` + `test_cip_worker_response_trace_has_cip_role_worker`. |
| 4.1.0 | 2026-05-22 | CIP-V05 status note corrected: was pointing to `test_cip_worker_receipt_includes_parent_task_id` (wrong test — that's CIP-V04's parent_task_id, not session_key echo). Correct tests: `test_cip_worker_receipt_includes_session_key` + `test_cip_worker_response_trace_has_cip_role_worker` (iter-472 adds RESPONSE trace session_key assertion). |
| 4.0.0 | 2026-05-22 | §12.4 Worker Behavior added: CIP-W01 (`trace.cip_role="worker"` in RESPONSE — S.12 §4.2 MUST) and CIP-SESSION (§10.4 `cip_session_key` echo). Implementation: `ResponseTrace` model added to adapter, `TaskResponse.trace` populated when gate_pass. Tests: `test_cip_worker_response_trace_has_cip_role_worker` + `test_cip_worker_response_trace_absent_when_gate_disabled`. Adapter test count: 199→201. |
| 3.9.0 | 2026-05-22 | CIP BALANCED strategy gap: `test_balanced_strategy_with_workers_returns_remote` and `test_balanced_strategy_no_workers_returns_iicp_e022` added to `proxy/tests/test_cip_coordinator.py`. BALANCED is a supported CIPStrategy enum value (local-first / remote-first / balanced); both tests verify BALANCED routes correctly (workers → REMOTE; no workers → IICP-E022). Proxy test count: 296→298. |
| 3.8.0 | 2026-05-22 | §12 table headers fixed to 4-column format (Test ID / Requirement / Spec ref / Unit test). CIP-01 partial reference: `proxy/tests/test_cip_coordinator.py::test_no_workers_remote_first_returns_iicp_e022` (IICP-E022 fallback when fewer workers than replicas). CIP-03 partial reference: `test_no_workers_local_first_returns_local` (structural local fallback). CIP-05 marked Phase 5+ deferred. |
| 3.7.0 | 2026-05-22 | §12.2 CIP-04: concrete unit test reference added — `adapter/tests/test_cip_task_worker.py::test_cip_worker_receipt_includes_parent_task_id`. SYNC: iicp-telemetry.md T4.3 OUTLIER_WEIGHT "PENDING" removed (RESA RS3 validated); TEL-OUTLIER-01..03 already live. |
| 3.6.0 | 2026-05-22 | §12.1 CIP-02: concrete unit test reference added — `adapter/tests/test_cip_task_worker.py::test_cip_worker_does_not_fan_out`. Test verifies worker MUST NOT fan out (S.12 §8) by asserting exactly 1 outbound HTTP call (local backend only) when cip_role=worker. Adapter test count: 198→199. |
| 3.5.0 | 2026-05-22 | §3.3 DIR-DISC-11: GET /v1/discover with custom intent URN (x.<vendor>) MUST return 200 — directory MUST NOT reject custom intent URNs per iicp-core.md §4.1. REACH probe `probe_dir_disc_11` added; 2 new unit tests (96 tests, 35 probes). Verified live (count=0, as expected for unknown intent). |
| 3.4.0 | 2026-05-22 | §11.3 DIR-FED-10: each event in GET /v1/events MUST include 6 required fields (event_id UUID-v4, event_type valid enum, ts_ms int, signer_did str, payload obj). REACH probe `probe_dir_fed_10` added; 3 new unit tests (94 tests, 34 probes). Closes spec↔probe gap for iicp-dir.md §3.7 event schema MUST fields. |
| 3.3.0 | 2026-05-22 | §11.3 DIR-FED-09: GET /v1/events MUST return events with monotonically increasing seq values (S.13 §8 producer side). REACH probe `probe_dir_fed_09` added; 2 new unit tests (reach 80→82 tests, 33 probes in run_all). Fixes `probe_dir_fed_07` TLS regression (`verify=False` → `_tls_ctx()`). |
| 3.2.0 | 2026-05-22 | §3.5 DIR-NODE-01: GET /v1/node/{id} → 200 with capabilities (2-step probe: discover → node detail). REACH probe `probe_dir_node_01` added; 2 new unit tests (reach 78→80 tests, 32 probes in run_all). Both DIR-NODE probes now live. |
| 3.1.0 | 2026-05-22 | §3.5 DIR-NODE-02: GET /v1/node/{unknown} → 404 + not_found. REACH probe `probe_dir_node_02` added; 2 new unit tests (reach 76→78 tests, 31 probes in run_all). §3.5 table expanded to 4 columns with REACH probe column. Closes spec↔probe gap for node-detail 404 path. |
| 3.0.0 | 2026-05-22 | §3.3 DIR-DISC-10: GET /v1/discover without `intent` parameter MUST return 422 (intent is required). REACH probe `probe_dir_disc_10` added; 2 new unit tests (reach 74→76 tests, 30 probes in run_all). Closes spec↔probe traceability gap for intent-required validation. |
| 2.9.0 | 2026-05-22 | §3.3 DIR-DISC-09: min_reputation > 1.0 MUST return 422 (input validation). REACH probe `probe_dir_disc_09` added; 2 new unit tests (reach 72→74 tests). Closes spec↔probe gap for min_reputation query param range guard. |
| 2.8.0 | 2026-05-22 | §3.3d DIR-CIP-03: every node in discover MUST have reputation_tier in {none,silver,gold,platinum} (S.12 §5.1.1 REP2). REACH probe `probe_dir_cip_03` added; 5 new unit tests (reach 67→72 tests). Closes spec↔probe traceability gap for REP2 discover field. |
| 2.7.0 | 2026-05-22 | §13.4 CIP-V07: cip.quorum cross-field constraint (S.12 §4.1 IICP-E028). quorum MUST be null OR positive integer ≤ replicas. Implemented in CIPCallFields.validate_majority_vote_replicas() model_validator(mode="after"). 9 new tests (proxy 287→296). CIP-V07 row added. |
| 2.6.0 | 2026-05-22 | §13.4 CIP-V02a + CIP-V06 extended: (1) CIPCallFields.validate_majority_vote_replicas() enforces odd ≥ 3 replicas for majority_vote → IICP-E025 (S.12 §3.2). (2) CIPAggregationResult model_validator: majority_vote requires non-null cip_vote_count + cip_quorum_threshold (S.12 §4.3). 10 new tests (proxy 277→287). Conformance suite CIP-V02a test ID added. |
| 2.5.0 | 2026-05-22 | §13.4 CIP-V06: CIPAggregationResult Pydantic model in proxy/src/proxy/cip/aggregation.py enforces coordinator RESPONSE cip_aggregation object (S.12 §4.3 MUST). Cross-field invariants: replicas_responded ≤ replicas_dispatched; selected_worker_id null when replicas_responded == 0. 22 unit tests in proxy/tests/test_cip_aggregation.py. Proxy test count: 277 (was 255). |
| 2.4.0 | 2026-05-22 | §13.4 CIP-V01/V02: CIPCallFields Pydantic model in proxy/src/proxy/cip/consumer.py validates cip.policy enum (CIP-V01) and cip.replicas [1,10] (CIP-V02). 16 unit tests in proxy/tests/test_cip_call_validators.py. Test references updated from integration placeholder to concrete unit test paths. |
| 2.3.0 | 2026-05-22 | §13.4 CIP-V03/V04: TaskCip.cip_role (Literal["coordinator","worker"]) and cip_parent_task_id (UUID v4 validator) implemented. 10 new unit tests in adapter/tests/test_models_validators.py. Adapter test count: 198 (was 189). Bug fix: test_cip_task_worker used non-v4 UUID — corrected to 550e8400. CIP-V05 reference updated to correct test file. |
| 2.2.0 | 2026-05-22 | §13.3a CIP Task-Level Admission Gate: CIP-A1-GATE-01..05 test IDs for CooperativeInferenceGate (tool-domain control, reputation floor, credit floor). Tests already live in adapter/tests/test_cip_gate.py. Closes spec↔test traceability gap for S.12 §3.2/3.3 MUST constraints. |
| 2.1.0 | 2026-05-21 | §6.1/6.2/7 Protocol + Security: back-fill test file references for PROTO-MSG-01..05, PROTO-URN-01..03, SEC-AUTH-01/02, SEC-TLS-01, SEC-NONCE-01, SEC-LEAK-01/02, SEC-LOG-01. Conformance ID docstring markers added to test_models_validators.py. Full spec↔test traceability across §4/5/6/7. |
| 2.0.0 | 2026-05-21 | §4.1/4.2/4.3 Adapter conformance: back-fill test file references for NODE-TASK-01..08, NODE-HEALTH-01..03, NODE-CONC-01. Conformance ID docstring markers added to adapter/tests/test_task.py. Full spec↔test traceability across §4/5 adapter+proxy. |
| 1.9.0 | 2026-05-21 | §5.1/5.2/5.3 Proxy conformance: back-fill test file references for PROXY-ROUTE-01..05, PROXY-TIMEOUT-01..02, PROXY-OAI-01..02. Test traceability now matches §5.4 PROXY-ERR format. |
| 1.8.0 | 2026-05-21 | §3.3 Discovery: DIR-DISC-02 (nodes sorted score-desc) REACH probe live (`probe_dir_disc_02`); 27 probes total, 71 tests. Back-fills spec↔probe gap for §4.2 sort MUST constraint active since v1.0. |
| 1.7.0 | 2026-05-21 | §3.3g Telemetry Auth Boundary (Phase 3 — MUST): DIR-TEL-01 (POST /v1/telemetry no auth → 401). REACH probe live (`probe_dir_tel_01`); 26 probes total, 69 tests. Back-fills spec↔probe loop for iicp-telemetry.md §T4.1 TEL-AUTH-01 MUST constraint. |
| 1.6.0 | 2026-05-21 | §5.4 Proxy Error Code Semantics (MUST): PROXY-ERR-01 (empty discover → IICP-E033 503) + PROXY-ERR-02 (all routing failed → no_available_node, not IICP-E033). Back-fills conformance IDs for iicp-core.md §7 IICP-E033 (added v1.2.5, WQ-030). Tests already live in proxy/tests/. |
| 1.5.0 | 2026-05-21 | §3.3f Trust Audit — Declaration Consistency (Phase 5): DIR-TRUST-01 (registered_models ⊆ health_models for discovered nodes). REACH probe live (`probe_dir_trust_01`); 25 probes total. §11.3 DIR-FED-07 REACH probe status added (live 2026-05-21). Closes spec↔probe loop for #118 Part D trust audit. |
| 1.4.0 | 2026-05-20 | §3.3e External Reachability Probe SSRF Guard (Phase 5): DIR-PROBE-01 (loopback 127.0.0.1 → 422 private_address), DIR-PROBE-02 (RFC-1918 10.0.0.1 → 422 private_address). REACH probes live; 58 unit tests pass. Closes spec↔probe↔production loop for GET /v1/probe SSRF guards (#122). |
| 1.3.0 | 2026-05-20 | §3.3d CIP Conformance Level in Discovery (Phase 5): DIR-CIP-01 (discover nodes include cip_conformance_level in CIP-Provider/CIP-None), DIR-CIP-02 (discover?cip_capable=1 returns only CIP-Provider nodes). REACH probes live and passing. Closes spec↔probe↔production loop for S.12 §5.2 REP1 in discovery path. |
| 1.2.0 | 2026-05-20 | §3.3c Credit Endpoints Auth Boundary (Phase 3): DIR-CRED-01 (GET /v1/credits/balance no-auth → 401), DIR-CRED-02 (GET /v1/credits/transactions no-auth → 401), DIR-CRED-03 (POST /v1/credits/award no-auth → 401). REACH probes for all three already live and passing; this back-fills the spec-side registration. |
| 1.1.0 | 2026-05-18 | §13.9 Conformance Badge System: BADGE-SUBMIT-01..03, BADGE-VERIFY-01..02, BADGE-LIST-01 (6 test IDs for S.14 requirements). Tracks #94 (CLOSED). |
| 1.0.0 | 2026-05-17 | §13.8 CIP Conformance Level Declarations: CIP-CONF-01/02/03 test IDs for §5.2 conformance level requirements. Closes alignment gap with iicp-cooperative-inference.md v0.6.0. |
| 0.1.0 | 2026-05-14 | Initial draft — Phase 1 conformance test IDs; DIR-REG, DIR-RL, DIR-HB, DIR-NODE, PROXY-OAI, SEC-* series |
| 0.1.1 | 2026-05-15 | Added Changelog section (A6 spec cleanup) |
| 0.2.0 | 2026-05-15 | Extended with §10 SDK conformance (SDK-01–SDK-06, SDK-DISC-*, SDK-ERR-*, SDK-NODE-*) and §11 Federated Directory conformance (DIR-FED-01–08). Covers ADR-016 and S.13. |
| 0.3.0 | 2026-05-15 | Added §12 Cooperative Inference Protocol (S.12) test IDs CIP-01–CIP-05. Phase 5 deferred, test mark @phase5. |
| 0.4.0 | 2026-05-15 | All 40 Phase 1 spec IDs mapped to integration tests (RALPH-2 C1-iter-3). PROTO-MSG-01..04, PROTO-URN-01..03, DIR-DISC-06, DIR-HB-03, PROXY-ROUTE-02..03 now explicitly labeled. 3 new tests added. |
| 0.5.0 | 2026-05-20 | Added DIR-DISC-08 (Cache-Control: public, max-age=30 on discover — CDN edge caching requirement). Registered Phase 2 mesh probe IDs: DIR-BS-01 (bootstrap returns peers[]), DIR-BS-02 (stale peers excluded), DIR-PEER-01 (peers auth MUST) in new §3.3b. REACH probes for all three IDs already live; this entry back-fills the spec-side registration. |
| 0.5.0 | 2026-05-15 | Added §13 Observability conformance (METRICS-01..08, TRACE-01..03). Covers ADR-014 Prometheus + OTel trace propagation. 8 MUST test IDs. All implemented in RALPH-2 C2 iter-1..3. |
| 0.7.0 | 2026-05-17 | §13.4 CIP Wire Format Validation: CIP-V01..V06 test IDs for §4.1/§4.2/§4.3 normative requirements (IICP-E028 validation gate). |
| 0.8.0 | 2026-05-17 | §13.6 Reputation Update Rules: REP-01..REP-03 test IDs for §11 normative delta rules. Closes #113. |
| 0.9.0 | 2026-05-17 | §13.7 QoS Admission Control: QOS-ADMIT-01..02 test IDs for §2.2 normative admission rules (capacity_exceeded 429 + proxy node-switch). Closes #119. |
| 0.6.0 | 2026-05-15 | §13 expanded: TRACE-01..03 test file references + TRACE-04 W3C format validation. §13.3 CIP policy gate test IDs (CIP-W01-GATE, CIP-W02-GATE, CIP-W01-ALLOW, CIP-W02-ALLOW, CIP-W03-CLAMP — Phase 5 pre-req). §13.4 renumbered to §13.5. All TRACE-* tests implemented (RALPH-2 C3, commit 07617cd). |

---

## Sign-off

**Protocol Steward**: Suite covers IICP-DIR §3, ADR-008, and Phase 1 conformance
profile. All MUST tests are verifiable against the current Docker Compose stack.
40/40 Phase 1 spec IDs + 8 observability MUST IDs labeled (v0.5.0).
Closes GitHub issue #22 (draft). ✓
**Integration Validator**: Test IDs mapped to integration test files in
`tests/integration/`. All existing tests updated to carry `@conformance` mark.
v0.4.0: 40/40 spec IDs verified. v0.5.0: METRICS-01..05 verified in unit tests
(adapter/tests/test_prometheus_metrics.py, proxy/tests/test_prometheus_metrics.py)
and integration tests (tests/integration/test_prometheus_integration.py). ✓
