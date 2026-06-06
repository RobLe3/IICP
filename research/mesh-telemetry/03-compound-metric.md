# Mesh Telemetry — Compound Mesh-Health Metric (Tier 3)

**Issue**: #277
**Date**: 2026-05-24

---

## Purpose

A single normalized health score that operators, visitors, and monitors can use to answer
"is the IICP mesh healthy right now?" without needing to understand the individual components.

---

## Formula Design

### Input Components

| Component | Source | Weight | Rationale |
|-----------|--------|--------|-----------|
| discover_latency | REACH 24h p50 | 0.35 | Proxy-visible; direct adoption impact |
| task_success_rate | Heartbeat aggregates | 0.35 | Core quality signal |
| reachability_pct | REACH 24h | 0.20 | Network availability; high weight when degraded |
| conformance_pass_rate | REACH conformance_24h | 0.10 | Protocol correctness |

### Normalization

**discover_latency** (lower = better):
```
lat_score = clamp(1 - (p50_ms - 50) / (500 - 50), 0, 1)
```
- p50 ≤ 50ms → 1.0 (excellent)
- p50 = 275ms → 0.5 (midpoint)
- p50 ≥ 500ms → 0.0 (degraded)

**task_success_rate** (higher = better):
```
sr_score = clamp((rate - 0.70) / (1.0 - 0.70), 0, 1)
```
- rate = 1.00 → 1.0
- rate = 0.85 → 0.50
- rate ≤ 0.70 → 0.0

**reachability_pct** (direct normalization):
```
reach_score = reachability_pct / 100.0
```

**conformance_pass_rate** (derived from conformance_24h):
```
pass_rate = passed / (passed + failed)  if (passed + failed) > 0 else 1.0
conf_score = pass_rate
```

### Composite Formula

```
mesh_health = (
    0.35 × lat_score +
    0.35 × sr_score +
    0.20 × reach_score +
    0.10 × conf_score
)
```

### Interpretation Bands

| mesh_health | Label | Recommended color |
|-------------|-------|-----------------|
| ≥ 0.85 | Healthy | Green |
| 0.65 – 0.84 | Degraded | Yellow |
| 0.40 – 0.64 | Impaired | Orange |
| < 0.40 | Critical | Red |

---

## Implementation Target

**Where to expose**: `/api/v1/stats` response, new `mesh_health` top-level field:
```json
{
  "server": { ... },
  "probes": { ... },
  "credit_schedule": { ... },
  "mesh_health": {
    "score": 0.87,
    "label": "healthy",
    "components": {
      "discover_latency": 0.86,
      "task_success_rate": 1.0,
      "reachability": 1.0,
      "conformance": 0.95
    },
    "window": "24h",
    "computed_at": "2026-05-24T09:40:18Z"
  }
}
```

**Website integration**: The homepage LiveNodeCount component should be extended to show
the mesh_health score as a colored badge. The /stats page should show the full components breakdown.

---

## Sensitivity Analysis

A 10ms increase in discover p50 → lat_score change: -0.10/45 ≈ -0.002 → mesh_health change ≈ -0.0007.
A 5% drop in success rate → sr_score change: -0.05/0.30 ≈ -0.17 → mesh_health change ≈ -0.06.
Going from 100% → 80% reachability → mesh_health change ≈ -0.04.

The formula is most sensitive to task success rate, which is appropriate: a mesh that
serves tasks poorly is fundamentally unhealthy regardless of low discover latency.
