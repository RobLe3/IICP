# Mesh Telemetry — Existing Coverage Audit

**Issue**: #277
**Date**: 2026-05-24

---

## What the Current /api/v1/telemetry Endpoint Collects

The telemetry endpoint (`TelemetryController.php`) accepts proxy-observed metrics for
task-level timing. It records: task_id, proxy_node_id, result_class, latency_ms,
and aggregates them into `iicp_telemetry_aggregates`.

**Currently collected (underutilized)**:
- `discover_p50_ms`, `discover_p95_ms` — directory latency from proxy perspective
- `heartbeat_p50_ms` — heartbeat round-trip
- `reachability_pct` — proportion of probed nodes that responded

**Missing** (for Tier 2 mesh-health):
- Per-node end-to-end task latency (p50, p95) — nodes don't yet self-report per-task granularity
- Intent-type breakdown — telemetry is intent-agnostic
- Task success rate aggregated per node — heartbeat has raw counts but no aggregated rate

**Conclusion**: The telemetry pipeline is in place. The gap is upstream: adapters need
to enrich heartbeat with per-intent-type latency distributions (Tier 2 proposal).

---

## REACH Probe Coverage vs Telemetry Coverage

| Metric | Source | In /api/v1/stats? | Underutilized? |
|--------|--------|-------------------|---------------|
| discover_p50_ms | REACH + proxy telemetry | ✓ | No |
| discover_p95_ms | REACH | ✓ | No |
| heartbeat_p50_ms | REACH | ✓ | No |
| reachability_pct | REACH | ✓ | No |
| task_latency_p50_ms (node-side) | Heartbeat avg_latency_ms | ✗ | Yes — avg not p50 |
| task_success_rate | Heartbeat tasks_total/failed | ✗ not in stats | Yes |
| per-intent latency | Not collected | ✗ | Yes — gap |

**Highest-value gap**: `task_success_rate` is derivable from existing heartbeat data
(`tasks_total - tasks_failed / tasks_total`) but is not surfaced in `/api/v1/stats`.
Adding it to the stats probes block costs zero new collection — just an aggregation query.

---

## Immediate Win: Add task_success_rate to /api/v1/stats

The `probes` block currently shows:
```json
"probes": {
  "aggregate_24h": {
    "discover_p50_ms": 187.7,
    "discover_p95_ms": 253.6,
    "heartbeat_p50_ms": 45.2,
    "reachability_pct": 100.0
  }
}
```

Proposed addition to the same aggregate query (uses existing heartbeat data):
```json
"aggregate_24h": {
  ...existing fields...,
  "task_success_rate_pct": 97.6,
  "active_node_count_24h": 8
}
```

This single addition bridges the "is the mesh healthy for task serving?" gap without
requiring any new data collection.
