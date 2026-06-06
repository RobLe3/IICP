# Field Injection Resistance Audit
**Issue**: #303 | **Date**: 2026-05-24 | **Author**: CORC iter-879

---

## Verified Field Classification

Fields in the `/v1/discover` response, classified by source and manipulation risk.
Verified against codebase: `NodeScorer.php`, `HeartbeatController.php`, migrations.

| Field | Source | Risk | Mitigation | Verified |
|-------|--------|------|-----------|---------|
| `score` | Directory-computed (NodeScorer) | None | Fully server-side | ✓ NodeScorer.php:130 |
| `reputation_score` | Directory-computed (ReputationService) | None | Quorum + outlier weighting | ✓ NodeScorer.php:110–113 |
| `region` | Node-submitted (registration) | **HIGH** | None — no IP geolocation | ✓ migrations/create_nodes_table.php:14 |
| `models[]` | Node-submitted (registration) | MEDIUM | Trust auditor: −0.05 rep on divergence | ✓ trust_auditor.py iter-268 |
| `max_concurrent` | Node-submitted | LOW | Reputation penalty via telemetry | ✓ HeartbeatController |
| `latency_estimate_ms` | Always null (hardcoded) | N/A — server must measure | Must stay directory-measured | ✓ NodeScorer.php, see #300 |
| `pricing.credit_cost_multiplier` | Node-submitted | LOW | Affects cost only, not routing priority | ✓ CIP spec §5.2 |
| `available` | Node-submitted (heartbeat) | MEDIUM | 90s stale prune | ✓ HeartbeatController.php:87 |

---

## Risk Ranking

### HIGH — `region` field

A node can register with any region string (no validation beyond `string, max:64`). Concrete exploits:
1. **Latency arbitrage**: EU node claims `us-west` to appear closer to US consumers → wins routing over legitimate US nodes
2. **Data residency fraud**: A node in a jurisdiction with weak privacy laws claims a GDPR-compliant region → consumers violate their own compliance requirements unknowingly

**Recommended mitigation** (phased):
- **Phase 5A** (low cost): Add soft warning — if node IP geolocates to a different continent than declared region, log a trust_auditor flag. Use MaxMind GeoLite2 (free, Apache-licensed). No hard rejection (VPNs exist legitimately).
- **Phase 6** (ADR-030): Region attestation as part of Tier 2 operator identity — verifiable jurisdiction declaration.

### MEDIUM — `available` flag (heartbeat)

A node can claim `available: true` indefinitely even when overloaded, crashing, or deliberately cherry-picking requests. Current protection (90s stale prune) only catches dead nodes, not misbehaving ones.

**Recommended mitigation**: Cross-reference `available: true` against recent telemetry — if `error_rate > 0.5` in last 10 heartbeats AND `available: true`, set `available: false` at directory level (override). Already partially implemented (IICP-E033 over-claim path). Can be tightened without spec change.

### MEDIUM — `models[]` (registration)

Trust auditor (iter-268) fires after a task routes to a node whose model turns out to be absent. The −0.05 reputation penalty is a deterrent but not a blocker — a sophisticated node can claim models it occasionally serves to maintain high enough reputation.

**Recommended mitigation**: Cache last-verified model list per node; reject registration updates that add new models mid-session without a fresh audit probe. Strengthen audit frequency from 1h → 30min for nodes with recent model-claim mismatches.

---

## Conclusion

The most impactful security improvement is **region IP cross-check** (Phase 5A). It requires:
- One new directory service method in `GeoService` (MaxMind GeoLite2 lookup on registration IP)
- One new `trust_auditor` check at registration time (soft flag, not hard reject)
- ~40 lines of PHP + ~20 lines of test coverage
- No spec change required

The `available` flag tightening is the second-highest-value item and requires no external dependency.

Both can be implemented before Phase 6 identity work (ADR-030) is finalized.

---

## Related

- Issue: [#303](https://github.com/RobLe3/iicp.network/issues/303)
- Issue: [#300](https://github.com/RobLe3/iicp.network/issues/300) — latency_estimate_ms
- ADR-013 — Ed25519 operator identity
- ADR-030 — Operator identity & anti-sybil (ADR draft)
- `directory/app/Services/TrustAuditorService.php` — existing auditor
