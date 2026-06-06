# Mesh Telemetry — Tier Definitions

**Issue**: #277 (ARCS+RESA mesh telemetry)
**Date**: 2026-05-24
**Author**: RESA loop, FORGE iter963
**Status**: Complete

---

## Four-Tier Architecture

| Tier | Subject | Measurement approach | Trust level |
|------|---------|---------------------|-------------|
| 1 | Directory conformance (DIR-*, RECOG-*) | REACH probes, externally measured | HIGH — external measurement |
| 2 | Node/adapter response time (per task served) | Operators self-report via POST /api/v1/telemetry | MED — self-reported but signed |
| 3 | Compound mesh-health metric | Aggregate of T2 latency + T1 conformance + task success rate | HIGH — derived from T1+T2 |
| 4 | Per-directory-implementation benchmark | T3 metric stratified by directory implementation type | HIGH — comparative baseline |

---

## Tier 1: Directory Conformance (Existing)

**Coverage today**: 37 probes across 11 Phase 1 endpoints (DIR-* and RECOG-* test IDs).
**Data flow**: REACH daemon → `/api/v1/telemetry` (proxy_token auth) → `iicp_telemetry_aggregates` table → `/api/v1/stats` probes block.
**Windows**: 24h aggregates for p50/p95 discover latency, reachability_pct, heartbeat p50.
**No change needed** — this tier is fully operational.

---

## Tier 2: Node Response Time (Missing)

**What**: End-to-end task latency from the node's perspective (task received → result returned),
broken down by intent type. Success/failure classification per task.

**Data source**: Adapters (`adapter/src/adapter/handlers/task.py`) already track task
duration in heartbeat metrics. The heartbeat sends `tasks_total`, `tasks_failed`, `avg_latency_ms`.
However, per-task granularity with intent type and latency distribution is not exposed.

**Proposed additions to POST /api/v1/heartbeat**:
```json
"mesh_telemetry": {
  "task_latency_p50_ms": 145,
  "task_latency_p95_ms": 312,
  "intent_breakdown": [
    { "intent": "urn:iicp:intent:llm:chat:v1", "count": 42, "p50_ms": 132, "success_rate": 0.976 }
  ]
}
```

**Trust model**: Self-reported by node. The directory stores these values and uses them
to compute T3. Cross-reference against REACH probes (T1 latency) for anomaly detection.

**Backwards compatibility**: `mesh_telemetry` is optional in heartbeat. Nodes that don't
include it contribute to T3 at reduced weight (missing self-reports counted as "unknown").

---

## Tier 3: Compound Mesh-Health Metric (Missing)

**What**: A single number that answers "is the mesh healthy right now?" across latency,
success rate, and conformance dimensions.

**Formula** (see `02-tier-definitions.md` for derivation):
```
mesh_health = (
    0.35 × normalize(discover_p50_ms, min=50, max=500, invert=True) +
    0.35 × normalize(task_success_rate, min=0.70, max=1.0) +
    0.20 × reachability_pct / 100 +
    0.10 × conformance_pass_rate
)
```
Result in [0.0, 1.0]. Displayed as percentage (multiply by 100).

**Aggregation window**: 24h rolling (same window as T1 aggregates). Updated whenever
`AggregateProbeMetricsJob` runs.

---

## Tier 4: Per-Implementation Benchmark (Future)

**What**: T3 metric stratified by directory implementation: PHP directory (Genesis Seed,
current) vs future Rust replica (ADR-013 Phase 6). Enables apples-to-apples comparison
when the federation lands.

**Prerequisite**: ADR-013 Phase 6 federation. No code work needed today.

**Design note**: The benchmark must account for selection bias — Rust replicas may attract
different operator types. Weight by operator age and task volume to normalize.

---

## Implementation Roadmap

1. **Immediate**: Add `mesh_telemetry` optional block to heartbeat schema (directory validation + storage)
2. **Short-term**: Add T3 compound metric to `/api/v1/stats` response
3. **Website**: Update /stats page to show T3 as "Mesh Health" percentage
4. **Long-term**: T4 per-implementation benchmark (Phase 6 dependency)
