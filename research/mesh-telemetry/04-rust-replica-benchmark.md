# Mesh Telemetry — Per-Directory-Implementation Benchmark (Tier 4)

**Issue**: #277
**Date**: 2026-05-24

---

## Purpose

Enable apples-to-apples comparison of the PHP Genesis Seed directory vs future Rust
replica directories (ADR-013 Phase 6) on the same T3 compound mesh-health metric.

---

## Design

### Stratification Key

Each telemetry observation is tagged with the directory implementation that served it:
- `directory_impl: "php-genesis"` — current production directory
- `directory_impl: "rust-replica"` — future ADR-013 federation nodes

The compound metric (T3) is computed per-stratum. The benchmark is the difference in T3
between implementations across comparable time windows and workload conditions.

### Selection Bias Mitigation

**Problem**: Rust replicas will attract early-adopter operators with potentially
different node quality, region distribution, or task type mix. Comparing raw T3
scores would conflate implementation quality with operator selection effects.

**Mitigation**:
1. **Age weighting**: normalize by operator age group (nodes registered ≥30 days vs <30 days).
   New meshes around Rust replicas will skew toward newer operators; correct for this.
2. **Intent-type matching**: compare T3 only for equivalent intent types. A Rust replica
   serving exclusively code generation vs a PHP directory serving chat will differ for
   reasons unrelated to implementation quality.
3. **Region pairing**: if possible, deploy Rust replica alongside PHP directory in the same
   region. Side-by-side comparison eliminates regional latency effects.
4. **Minimum sample floor**: compute benchmark only when each stratum has ≥100 task samples
   in the 24h window. Below this floor, report "insufficient data" rather than a misleading comparison.

### Benchmark Schema Addition to /api/v1/stats

```json
"impl_benchmark": {
  "available": false,
  "reason": "ADR-013 federation not yet deployed",
  "implementations": []
}
```

When federation is active:
```json
"impl_benchmark": {
  "available": true,
  "window": "24h",
  "implementations": [
    {
      "id": "php-genesis",
      "mesh_health": 0.87,
      "sample_count": 842,
      "region": "eu-central"
    },
    {
      "id": "rust-replica-1",
      "mesh_health": 0.91,
      "sample_count": 234,
      "region": "eu-central"
    }
  ]
}
```

---

## Prerequisites (not yet met)

- ADR-013 Phase 6 federation (Rust replica directory)
- Node telemetry tagged with directory implementation they discovered from
- 24h minimum sample accumulation per implementation

**No code work today** — placeholder field added to /api/v1/stats JSON with `available: false`.
