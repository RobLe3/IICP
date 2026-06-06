# REP4 — Two-Sided Feedback Collection: Design Document

**Track**: REP (Reputation & Tiered Access)  
**Issue**: #170 (REP4: Two-sided feedback collection)  
**Date**: 2026-05-18  
**Author**: RESA loop, iter 6  
**Phase**: Design (no simulation required — mechanism design)  
**Related ADRs**: ADR-012 (reputation weight W_REP), ADR-023 (reputation delta rules), ADR-026 (earned signal)

---

## 1. Problem statement

The current reputation model uses proxy-reported telemetry (latency, success/failure) as
the sole exogenous signal. This creates two gaps:

1. **Output quality is invisible**: A provider that returns fast but incorrect or low-quality
   results looks identical to a provider that returns fast and correct results. Latency is
   a proxy for quality but not a measure of it.

2. **Single-source vulnerability**: Telemetry comes only from the proxy node. The §T4 quorum
   gate (≥3 distinct proxies) mitigates Sybil attacks, but a coordinated ring of proxy
   operators can still inflate reputation. Client-side feedback is an independent signal
   that does not depend on the proxy operator.

Two-sided feedback adds a **client quality rating** alongside the existing proxy telemetry.

---

## 2. Feedback schema (proposed)

After task completion, the proxy MAY submit a client quality rating to the directory:

```
POST /v1/feedback
Authorization: Bearer <proxy_token>
```

Request body:
```json
{
  "node_id":       "string (UUID) — provider being rated",
  "task_id":       "string (UUID) — unique task identifier",
  "proxy_node_id": "string (UUID) — rating proxy",
  "quality_score": "integer 1–5 — client-facing quality rating",
  "quality_dims":  {
    "correctness": "integer 1–5 (optional)",
    "relevance":   "integer 1–5 (optional)",
    "completeness":"integer 1–5 (optional)"
  },
  "commit":        "string (32 hex chars) — salted commitment (see §2.1)"
}
```

Response:
```json
{ "recorded": true, "feedback_id": "string (UUID)" }
```

### 2.1 Commit-reveal for rating anti-anchoring

**Problem**: If ratings are submitted immediately after task completion and publicly visible,
providers can condition future behaviour on expected ratings (strategic cooperation with raters).

**Solution**: Two-phase commit-reveal:

1. **Commit phase** (at task completion):
   ```
   commit = sha256(quality_score || task_id || proxy_secret_salt)
   ```
   Proxy submits `commit` immediately — provider sees only the hash, not the score.

2. **Reveal phase** (after 10-minute blind period):
   ```
   POST /v1/feedback/reveal
   { "feedback_id": "...", "quality_score": 3, "salt": "..." }
   ```
   Directory verifies `sha256(quality_score || task_id || salt) == commit`.

**Implementation note**: The 10-minute blind period is a design candidate (PENDING: validate
against typical task completion patterns in live data). The blind period prevents providers
from immediately adapting behaviour to a single rater's preferences.

---

## 3. Identity weighting

Not all feedback carries equal weight. Feedback from a new, unknown proxy should weigh
less than feedback from a long-standing, high-reputation proxy.

**Proposed weight formula**:

```
feedback_weight = min(1.0, identity_age_hours / 720) × reputation_factor(proxy_reputation)

reputation_factor(r):
  if r >= 0.85: 1.0   (platinum proxy)
  if r >= 0.65: 0.8   (gold proxy)
  if r >= 0.40: 0.6   (silver proxy)
  else:         0.3   (bronze proxy)
```

**Rationale**:
- New proxies (identity_age < 720h) are discounted — an attacker creating a fresh Sybil
  proxy to submit fake ratings faces the same identity-age penalty as in REP2
- High-reputation proxies have demonstrated reliable behaviour — their ratings carry more weight
- This creates a virtuous cycle: reliable proxies carry more trust on the feedback channel too

**PENDING**: weight formula parameters are design candidates; feedback weight impact on the
reputation EMA requires simulation (REP4 open question). Marked as pending RESA RS3.

---

## 4. Telemetry corroboration

Feedback ratings SHOULD be corroborated by telemetry to detect anomalous combinations:

| Pattern | Flag |
|---------|------|
| High quality rating + high latency | SUSPICIOUS (provider was slow but rated well — possible collusion) |
| Low quality rating + low latency | ANOMALOUS (fast but poor — investigate; may indicate hallucinated output) |
| Quality rating submitted without prior telemetry | UNVERIFIABLE — exclude from EMA update |

Implementation: The directory checks that `task_id` in the feedback request matches a
prior telemetry record. If no telemetry exists for the task, the feedback is recorded but
NOT applied to the reputation EMA.

This ensures that ratings without a performance record cannot be used to inflate reputation.

---

## 5. Anti-gaming analysis

### 5.1 Sybil feedback farm

**Attack**: Operator creates N proxy nodes that all submit maximum quality ratings to their
own provider nodes.

**Defenses**:
- Quorum gate (T4.2): ≥3 distinct proxies required for EMA update — applicable to feedback too
- Identity weighting: new proxies discounted
- Commit-reveal: prevents pre-arranged rating coordination
- Telemetry corroboration: feedback without telemetry excluded

### 5.2 Competitive sabotage

**Attack**: A proxy operator submits minimum quality ratings to a competitor's provider.

**Defenses**:
- Identity weighting: malicious proxy is discounted if it's new or low-reputation
- Outlier detection (T4.3 / #187): proxies that consistently rate out-of-distribution have weight reduced
- Commit-reveal: sabotage requires committing before seeing the rating — cannot be post-hoc

### 5.3 Rating inflation via coordinated proxies

**Attack**: A group of operators mutually rate each other's providers highly.

**Defenses** (weaker here):
- This requires coordinated operators with high identity_age and high reputation
- The investment required (maintaining high-reputation proxies for 720h+ each) is a significant economic barrier
- Coordinated collusion is modeled in RESA iter7 (RS2→100 work)

---

## 6. Integration with reputation EMA

The feedback signal feeds into the reputation EMA as a parallel channel to telemetry:

```
new_rep = α_tel × telemetry_contribution + α_fb × feedback_contribution + (1 - α_tel - α_fb) × prev_rep

where:
  α_tel = 0.10 (EMA weight for telemetry — from ADR-012, PENDING RS3 validation)
  α_fb  = 0.05 (EMA weight for feedback — PENDING: candidate value, requires simulation)
```

Feedback has a lower EMA weight than telemetry because:
1. Telemetry is objective (measured latency)
2. Feedback is subjective (human-like quality rating, gameable)

**PENDING**: α_fb = 0.05 is a design candidate. RESA RS3 should test feedback weight impact
with coordinated sabotage and Sybil scenarios before finalizing. Tracked in #170.

---

## 7. Spec gap created

This document creates a new spec gap:

```
New endpoint: POST /v1/feedback (proxy authentication, commit-reveal, identity weighting)
New endpoint: POST /v1/feedback/reveal
```

These endpoints are NOT yet defined in `spec/iicp-semantics.md` or `spec/iicp-core.md`.
REP4 issue #170 should remain open until:
- Spec endpoints are defined (blocked on this design doc being reviewed)
- Commit-reveal timing (10 min blind period) is validated
- α_fb parameter is validated by simulation
- The `POST /v1/feedback` AC checklist in #170 is completed

---

## 8. Open questions resolved / created

### Resolved by this document

- Design pattern for commit-reveal (salted sha256, 10-minute blind period)
- Identity weighting approach (identity_age_hours + reputation_factor)
- Telemetry corroboration requirement (no telemetry → no EMA update)

### Open (PENDING simulation / validation)

| Q | Question | Assigned | Status |
|---|---------|---------|--------|
| Q5 | Does α_fb = 0.05 prevent feedback from overwhelming telemetry signal? | REP4 | Not simulated |
| Q6 | Does commit-reveal with 10-min blind period adequately prevent anchoring? | REP4 | Not simulated |
| Q7 | Does coordinated feedback ring (3+ high-rep proxies) significantly inflate provider reputation? | REP4+RS2 | Coordinated collusion model (RESA iter7) |
| Q4 | Does client feedback suppress Sybil rating farms? | REP4 | Partially answered — identity weighting + quorum gate are the primary defenses |
