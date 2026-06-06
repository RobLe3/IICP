# Research: Null Field Injection Resistance
## /v1/discover Field-by-Field Manipulation Audit

**Date**: 2026-05-24
**Status**: Research / Pre-spec
**Issue**: #303
**Author**: CORC sub-loop, FORGE iter-957
**Feeds**: spec/iicp-dir.md §field-integrity, ADR-030 §Tier-2 attestation, NodeScorer.php, RegisterController.php

---

## 1. Scope

The `/v1/discover` response combines directory-computed signals (safe) with
node-submitted fields (potentially manipulable). This document audits every
field in the current discover response, classifies its manipulation risk, evaluates
existing mitigations, and proposes mitigations for gaps.

Terminology:
- **directory-computed**: derived entirely from directory's own telemetry/logic — no node can inject false values
- **node-submitted at registration**: accepted from the node at `POST /v1/register`
- **node-submitted at heartbeat**: accepted from the node at `POST /v1/heartbeat`
- **hybrid**: base is node-submitted, but directory applies bounds or transformation

---

## 2. Complete Field Risk Matrix

| Field | Source | Manipulation goal | Risk | Existing mitigation | Residual gap |
|-------|--------|-------------------|------|---------------------|-------------|
| `score` | Directory-computed (NodeScorer) | Inflate routing priority | **None** | 100% server-side | None |
| `reputation_score` | Directory-computed (ReputationService) | Inflate trust signal | **None** | Quorum weighting + DELTA_LATENCY_BREACH (-0.05) | None |
| `node_id` | Directory-assigned (UUID) | Impersonation | **None** | UUID assigned at registration, not self-chosen | None |
| `endpoint` | Node-submitted (registration) | Redirect traffic to third-party | **LOW** | JWT-verified heartbeat proves liveness at endpoint | Man-in-middle at registration (pre-JWT) |
| `region` | Node-submitted (registration) | Attract regional consumers; evade data residency | **HIGH** | Character-safety check only (REGION_PATTERN, max 64 chars) | **No IP geolocation verification** |
| `models[]` | Node-submitted (registration) | Claim unowned models → attract high-value tasks | **MEDIUM** | Reputation penalty via latency breach if model mismatch causes slow/failed tasks (-0.05/task) | Penalty is reactive, not proactive; slow accumulation |
| `max_concurrent` | Node-submitted (registration) | Over-claim → receive excess tasks; deny to legitimate nodes | **LOW** | IICP-E033 probe detects queue overflow → reputation penalty | Penalty is reactive |
| `latency_estimate_ms` | Hardcoded null (NodeScorer:146) | N/A — field always null | **None** | Must remain directory-measured (see #300) | Field is misleadingly present as null |
| `available` | Node-submitted (heartbeat) | Claim available while processing-at-capacity | **MEDIUM** | 90s stale prune; active probe via REACH | REACH probes liveness, not capacity truthfulness |
| `pricing.credit_cost_multiplier` | Node-submitted (registration, min:0 max:1000) | Over-charge or under-charge strategically | **LOW** | Consumer-visible; consumer selects lowest cost; max:1000 cap | Market self-corrects; no protocol harm |
| `cip_policy.*` | Node-submitted (registration) | Lie about CIP capabilities | **MEDIUM** | IICP-CIP probes validate CIP behavior in conformance suite | Not continuously verified by REACH |
| `capabilities.intent_urns[]` | Node-submitted (registration) | Claim unsupported intent URNs → receive wrong-type tasks | **MEDIUM** | Failed tasks → DELTA_FAILURE (-0.05/task) reputation penalty | Reactive only; attacker absorbs losses to flood |

---

## 3. Finding F1: Region Injection is the Highest-Risk Gap

**Attack**: Node registers with `region: "eu-central"` from an IP in a jurisdiction
without GDPR compliance. North American or European consumers routing privacy-sensitive
tasks get no indication the compute is outside their expected region.

**Impact**:
1. Consumer data residency guarantees violated silently
2. "Country Pioneer" badge (gamification #267) can be won with false region claim
3. Regional reputation tiers (ADR-030 Diversity Champion) manipulable

**Proposed mitigation — IP geolocation cross-check (F1-M1)**:

At `POST /v1/register`, resolve the registering IP via MaxMind GeoLite2 (free, local DB):
```
observed_country = geoip_lookup(request->ip())
declared_region  = validated['region']
```

If `observed_country` falls outside `declared_region`'s continent prefix (us-* → NA,
eu-* → EU, ap-* → APAC), the directory:
1. Stores `geo_mismatch: true` on the `nodes` row
2. Emits a `geo_mismatch` event to the event log
3. **Does not block registration** (geo data is imperfect; VPN users are legitimate)
4. Reduces `NodeScorer` region-diversity bonus by 50% for `geo_mismatch=true` nodes

This is a soft penalty, not a hard block. A node behind Cloudflare may trigger it
legitimately — hence no registration block.

**Proposed mitigation — ADR-030 Tier 2 region attestation (F1-M2)**:

ADR-030 §Tier 2 — DID:web attestation naturally provides jurisdiction verification:
if the node operator publishes `https://operator-domain/.well-known/iicp-operator.json`,
the domain's TLD and WHOIS country provides an independent jurisdiction signal.
Recommend adding `jurisdiction_cc` (ISO 3166-1 alpha-2) as an optional field in the
DID:web operator document, verified at attestation time.

This is non-blocking for Phase 5 — ADR-030 implementation checklist item; not a
registration hard gate.

---

## 4. Finding F2: Model Injection Penalty is Reactive and Slow

**Attack**: A node claims `models: ["gpt-4o", "claude-opus-4"]` but only serves
responses from a local 3B parameter model. Reputation penalty (-0.05 per latency
breach) requires consumer tasks to fail or underperform before the signal accumulates.

**Slow accumulation math**: At starting reputation 0.5, and penalty 0.05 per task:
- 5 bad tasks → reputation 0.25 (below Tier 1 threshold in ADR-026)
- At 10 tasks/hour, a node can do ~30 minutes of fraudulent serving before dropping
- In 30 minutes the node could absorb O(100) high-value tasks

**Proposed mitigation — Proactive model audit trigger (F2-M1)**:

After registration, schedule a background probe (within 60 minutes, not immediately):
1. Fire one inference task at the node using each declared model family
2. Measure token throughput; compare against registered model tier's expected throughput
   (baseline from REACH latency data: 70B → ~500ms/token, 3B → ~50ms/token at consumer GPU)
3. If throughput is inconsistent with declared model tier, flag `model_audit_fail: true`,
   emit event log entry, apply a one-time -0.2 reputation penalty (4× the per-task penalty)

This is an extension of the existing AuditReportController pattern. The penalty is steep
enough that the attack window collapses from 30 minutes to ~15 minutes even if the
fraudulent node re-registers.

**Cost**: One inference request per model family per registration. With 8 current nodes,
negligible. At 100 nodes this costs 100 probes on registration day — acceptable.

---

## 5. Finding F3: `latency_estimate_ms` Null Field Creates Client Confusion

**Current state**: `NodeScorer.php:146` hardcodes `latency_estimate_ms = null`. The
field is present in every discover response but always null — making it a deceptive
no-op.

**Risk**: A malicious node that discovers the field is null could submit a heartbeat
attempting to inject a value (if the heartbeat schema is looser than the score schema).
More practically: any client that sorts by `latency_estimate_ms ASC` will see
non-deterministic sort order for all null values, which could be exploited to cause
all traffic to route to a single node (if that node somehow has a non-null value).

**Resolution (F3-R1)**:
1. Remove `latency_estimate_ms` from the discover response until it is directory-measured
   per #300 (directory-measured latency backlog). Do not expose fields that are always null —
   they invite misuse.
2. If backward compatibility requires keeping the field, hardcode it to -1 (sentinel
   "not measured") rather than null, and document this in the OpenAPI spec so clients
   know to ignore -1 values.

This is a minor spec change, not a security gap — low urgency.

---

## 6. Finding F4: Available + Stale Data Window Allows Gaming

**Attack**: A node holds its heartbeat to the directory for 85 seconds while processing
a batch of tasks, then sends a heartbeat claiming `available: true`. Consumers see
`available: true` in discover responses during the 90-second stale window even if the
node is actually busy.

**Impact**: Over-subscription to one node degrades latency for all consumers routed
there. Not a safety issue — reputation penalizes latency breaches.

**Proposed mitigation (F4-M1)**: REACH active probes (already every 30s in the liveness
probe set) should include a "task acceptance test" — submit a minimal valid task and
measure response time. If response time > tier's p95 threshold (from doc 02 tier_weight
table), mark the node's `busy_detected: true` and the discover response excludes the
node from `available: true` results for the next 60 seconds.

This upgrades REACH from liveness-only to capacity-awareness. Implementation:
`reach/src/reach/probes/capacity_probe.py` (new probe, ~60 lines).

---

## 7. Finding F5: Signed Registration Payload (Low Priority)

**Research question from #303**: Should nodes sign their registration payload with their
Ed25519 key (ADR-030) to detect MITM modification of declared fields in transit?

**Assessment**: HTTPS (Cloudflare TLS) already protects against MITM for the transport
layer. The attack this would defend against is: a compromised Cloudflare edge that rewrites
registration payloads. This is a nation-state-level threat, outside the IICP threat model
(TC-1 through TC-8 in THREAT_MODEL.md).

**Recommendation**: Do NOT add signed payload requirement in Phase 5. When ADR-030
operator identity ships, the `operator_signature: Ed25519(node_id || timestamp_ms)` at
registration (per ADR-030 §Identity flow) already provides a non-repudiation proof that
the operator intended this registration with this payload. This is sufficient.

---

## 8. Summary: Prioritized Remediation Plan

| Finding | Severity | Phase | Mitigation | Effort |
|---------|----------|-------|------------|--------|
| F1: Region injection | **HIGH** | 5B | IP geolocation cross-check (MaxMind GeoLite2, local DB) | Medium — add to RegisterController |
| F2: Model audit reactive | **MEDIUM** | 5B | Background model probe 60 min post-registration | Medium — extend AuditReportController |
| F4: Available + stale window | **MEDIUM** | 5B | REACH capacity probe (task acceptance test) | Medium — new REACH probe |
| F3: null latency_estimate_ms | **LOW** | 6 | Remove from discover response (spec change + code) | Small |
| F5: Signed payload | **NOT RECOMMENDED** | — | HTTPS + ADR-030 operator_signature is sufficient | — |

**Phase 5B target** (alongside Provider Mode enforcement):
- F1-M1: IP geolocation cross-check at registration
- F2-M1: Background model probe within 60 minutes of registration
- F4-M1: REACH capacity probe

**Phase 5 deferred** (no security urgency):
- F1-M2: ADR-030 DID:web jurisdiction field (document as ADR-030 implementation item)
- F3-R1: Remove null latency_estimate_ms (cosmetic spec tidy)

---

## 9. Spec Impacts

| Spec file | Change | Section |
|-----------|--------|---------|
| `spec/iicp-dir.md` | Add `§Field Integrity and Injection Resistance` | New §5.x |
| `spec/iicp-dir.md` | Remove or sentinel `latency_estimate_ms` field | §3.3 discover response |
| `project/decisions/ADR-030.md` | Add `jurisdiction_cc` to DID:web operator document | §Tier 2 DID:web |

These are informational — spec authors should pull from this document.

---

## 10. References

- `directory/app/Http/Controllers/RegisterController.php` — registration field validation
- `directory/app/Services/NodeScorer.php` — score computation (region diversity)
- `directory/app/Services/ReputationService.php` — DELTA constants (-0.05, -0.05)
- `directory/app/Http/Controllers/AuditReportController.php` — audit pattern reference
- `project/security/THREAT_MODEL.md` — TC-1 through TC-8 threat scope
- `research/credit-economy/02-routing-cost-design.md` — tier_weight table (for F4-M1 p95 thresholds)
- ADR-030 §Tier 2 attestation
- Issue #300 (latency_estimate_ms directory-measured)
