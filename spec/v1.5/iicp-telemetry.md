# IICP Telemetry Spec

**Version**: 1.0-draft  
**Status**: Draft — under review (see #185)  
**Scope**: `POST /v1/telemetry` endpoint — proxy-observed latency reporting and trust model  
**Linked ADRs**: ADR-012 (reputation weight W_REP), ADR-023 (reputation delta rules)  
**Tracking issues**: #112 (proxy telemetry endpoint), #114 (Sybil resistance)

---

## 1. Purpose

The telemetry endpoint allows proxy nodes to report latency observations for provider nodes
they have routed tasks to. These observations feed the `observed_latency_ms` signal in the
Reputation model (ADR-012 §W_REP), which is an EMA over proxy-reported latency.

Because proxy nodes may be operated by the same party as the provider node, telemetry
reports are not unconditionally trusted. §T4 defines the trust model that prevents
a provider from gaming their own latency signal.

---

## 2. Endpoint — POST /v1/telemetry

```
POST /v1/telemetry
Authorization: Bearer <proxy_token>
Content-Type: application/json
```

### Request body

```json
{
  "node_id":           "string (UUID)",
  "proxy_node_id":     "string (UUID)",
  "latency_ms_observed": "number",
  "tokens_observed":   "integer",
  "status":            "success | failure",
  "qos_met":           "boolean"
}
```

### Response

```json
{ "recorded": true }
```

On auth failure:

```json
{ "error": { "code": "IICP-E032", "message": "Invalid or missing proxy_token" } }
```

---

## 3. Authentication

`POST /v1/telemetry` MUST authenticate via **proxy_token**, NOT node_token.

The proxy_token is a separate 40-byte random token issued at node registration alongside
the node_token. Its hash is stored in the `nodes` table as `proxy_token_hash`. It is
returned once in the registration response and MUST NOT be reused as a node_token.

**Rationale**: If `POST /v1/telemetry` accepted the node_token (the token used for
`POST /v1/heartbeat` and `POST /v1/deregister`), a provider node could report its own
latency observations using its own token — a self-reporting attack that bypasses the
intended "third-party proxy observer" trust model.

---

## §T4 — Telemetry Trust Model

### T4.1 — PROXY_TOKEN_AUTH (MUST)

The `POST /v1/telemetry` endpoint MUST authenticate via `proxy_token`. A directory
implementation that accepts `node_token` Bearer on telemetry submissions is
**non-conformant**.

On auth failure, the directory MUST return HTTP 401 with error code `IICP-E032`
(see `project/ARCHITECTURE.md` Phase 5 proxy telemetry error codes).

The `proxy_node_id` field is REQUIRED in the request body. If absent, the directory
MUST return HTTP 401 with `IICP-E032`.

**Conformance test**: `TEL-AUTH-01` — `POST /v1/telemetry` with node_token → MUST
return 401 IICP-E032. [MUST]

### T4.2 — SYBIL_QUORUM (MUST)

A directory MUST gate EMA updates to `observed_latency_ms` on a **Sybil quorum**:
≥ 3 distinct `proxy_node_id` values must have reported on the same `node_id` within
a rolling 7-day window.

- If `distinct_proxies < 3`: the `observed_latency_ms` field MUST remain unchanged
  (frozen, not zeroed). The report is still recorded for future quorum counting.
- If `distinct_proxies >= 3`: the EMA update MUST be applied:
  `new_observed = α × latency_ms_observed + (1-α) × prev_observed_latency_ms`
  where α = 0.1 (EMA smoothing factor — **PENDING**: this value is a design
  candidate from ADR-012 and has not yet been validated against live production
  data. RESA track RS3 will confirm or revise. Implementations MUST support a
  configurable α in [0.05, 0.3]; the default of 0.1 applies until revised).
- The first report for a node (no prior `observed_latency_ms`) that meets quorum
  MUST set `observed_latency_ms = latency_ms_observed` (no smoothing on first write).

**Rationale**: Without a quorum gate, a provider node and one colluding proxy node can
sustain an artificially low latency signal. Three distinct proxies are required because
the operator of the provider node is assumed to control at most one proxy node.

The rolling window is 7 days to balance freshness (recent reporters matter) with
stability (a node should not lose quorum instantly if one proxy goes offline).

**Conformance test**: `TEL-QUORUM-01` — `POST /v1/telemetry` with 2 distinct
proxy_node_ids does not update `observed_latency_ms`. [MUST]

**Conformance test**: `TEL-QUORUM-02` — `POST /v1/telemetry` with ≥ 3 distinct
proxy_node_ids (cumulative in window) applies EMA update. [MUST]

### T4.3 — OUTLIER_WEIGHT (SHOULD)

A directory SHOULD reduce the weight of telemetry submissions that report latency
exceeding 3× the network median for the reported `node_id`, after at least 10
observations from that `proxy_node_id`.

The weight applied to the EMA update MUST be reduced to 0.1 (10% of the normal
smoothing factor α) when both conditions are met:

1. The reporting proxy has made ≥ 10 prior observations for this `node_id`.
2. The reported `latency_ms_observed` exceeds `3.0 × median(all_recent_reports)`.

The 24-hour rolling window is RECOMMENDED for computing the set of all recent reports.

This guards against a colluding proxy that persistently over-reports latency to damage
a competitor node's reputation. The 10-observation minimum ensures new proxies are not
penalised during their initial calibration period.

**Validation**: RESA track RS3 simulation (8 scenarios × 3 seeds × 200 steps) confirmed:
max false positive rate 0%, 100% detection for minority inflating proxies (≥5× median).
Deflator attacks and majority attacks are separately addressed by the Sybil quorum gate
(§T4.1). Reference: `research/simulation/rep/outlier_weight_validation.py` (#187).

**Conformance test**: TEL-OUTLIER-01 (informative — SHOULD-level).

---

## 4. SCORE_UPDATE event

> **Snapshot-model reconciliation (2026-05-30, db-D4prime / S.13 v0.3.0)**: Under the
> federated **snapshot + event-tail** storage model, high-frequency operational events
> (`SCORE_UPDATE`, `HEARTBEAT`, heartbeat-path `REPUTATION_UPDATE`) are **no longer emitted
> to the federated event log** — replicas derive current reputation from the
> `nodes.reputation_score` snapshot column, not from a per-report event stream. The MUST
> below is therefore **downgraded to "the directory MUST update the node's reputation
> snapshot"**; emitting a discrete `SCORE_UPDATE` event is OPTIONAL and, in the current
> directory, not done. The schema is retained for directories that opt into verbose event
> logging and for the conformance shape. Event types that REMAIN in the federated log:
> `REGISTER`, `DEREGISTER`, `AUDIT_REPORT`, `CREDIT_AWARD`, `REPUTATION_DECAY`. See iicp-dir
> §3.7 for the authoritative live event-type set.

After each accepted telemetry report, the directory MUST update the node's reputation
snapshot (`nodes.reputation_score` / `reputations.score`). A directory MAY additionally emit
a `SCORE_UPDATE` event log entry with the following fields (OPTIONAL under the snapshot model):

```json
{
  "event": "SCORE_UPDATE",
  "node_id": "<node_id>",
  "data": {
    "source":               "proxy_telemetry",
    "proxy_node_id":        "<proxy_node_id>",
    "latency_ms_observed":  "<reported latency>",
    "observed_latency_ms":  "<new value or null if frozen>",
    "status":               "<success|failure>",
    "quorum_met":           "<boolean>",
    "distinct_proxies":     "<count>"
  }
}
```

The `quorum_met` and `distinct_proxies` fields allow conformance probes and auditors to
verify that the Sybil quorum gate is operating correctly without re-querying the database.

---

## 5. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 0.3.0 | 2026-05-30 | §4 SCORE_UPDATE reconciled to snapshot model (R1, #384): MUST downgraded to 'update reputation snapshot'; discrete SCORE_UPDATE event now OPTIONAL/not-emitted under db-D4prime. |
| 1.0-draft | 2026-05-18 | Initial — §T4 Telemetry Trust Model (proxy_token auth + Sybil quorum gate). Derived from #114 implementation. Tracked in #185. |
