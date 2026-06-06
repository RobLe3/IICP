# REP4 — Two-Sided Feedback Collection

**Track**: REP (Reputation & Tiered Access)  
**Issue**: #170 (REP4: Two-sided feedback collection)  
**Date**: 2026-05-18  
**Status**: Design complete — schema stub at `spec/schemas/feedback-envelope.json`  
**Author**: RESA loop, iter93  
**Depends on**: REP1 (`reputation-mechanics.md`), ADR-026  
**Schema draft**: `spec/schemas/feedback-envelope.json`

---

## 1. Purpose

Task outcomes alone (success/failure) are coarse signals. Two-sided feedback adds
counterparty-rated quality and compliance dimensions, making the reputation signal
more informative:

| Signal direction | What it measures |
|-----------------|-----------------|
| Client → Node | Output quality: did the response match the intent? |
| Node → Client | Request compliance: was the request protocol-compliant? |

Both directions use different vocabularies because they measure different things.
Payment behavior is explicitly excluded (ADR-019 concern — separate settlement track).

---

## 2. Feedback Envelopes

### 2.1 Client → Node Quality Feedback

Submitted by the requesting client (proxy) after receiving task output.

```
quality_feedback {
  task_id          : string (UUID — must match a completed task)
  rater_id         : string (client node_id or identity token)
  rated_node_id    : string (node that executed the task)
  intent_match     : integer 1..5 (did output match the stated intent?)
  output_useful    : integer 1..5 (was output practically useful?)
  would_route_again: boolean
  reason_codes     : [string]? (optional; see §2.3 quality reason codes)
  comment          : string? (≤ 500 chars; private to node operator — not disclosed)
  timestamp        : string (ISO 8601)
  signature        : string (HMAC-SHA256 over canonical envelope bytes)
}
```

**Score semantics** (1–5):

| Score | intent_match | output_useful |
|-------|-------------|---------------|
| 1 | Completely missed intent | Unusable |
| 3 | Partially satisfied intent | Marginally useful |
| 5 | Precisely matched intent | Excellent |

Reputation impact (REP1 integration): quality_bonus = (avg_intent_match − 3) × 0.001 per
confirmed feedback unit. This adds ≤ ±0.002 per task at extremes — enough to differentiate
consistent quality without dominating the ±0.01/−0.05 task-outcome path.

### 2.2 Node → Client Compliance Feedback

Submitted by the executing node (adapter) after completing a task.

```
compliance_feedback {
  task_id             : string (UUID — must match a completed task)
  rater_id            : string (node_id of rating node)
  rated_client_id     : string (client that submitted the task)
  request_well_formed : boolean (request parsed and validated without errors)
  compliance_status   : string (enum; see §2.4)
  violation_codes     : [string]? (required if compliance_status ≠ "compliant")
  would_serve_again   : boolean
  timestamp           : string (ISO 8601)
  signature           : string (HMAC-SHA256 over canonical envelope bytes)
}
```

Reputation impact: a `protocol_violation` or `abusive` compliance status triggers an
additional −0.03 penalty on the client identity's reputation **only if**
telemetry-corroborated (§4). `minor_issue` triggers no reputation change — recorded
for pattern analysis only.

### 2.3 Quality Reason Codes

Enumerated quality signals from client → node:

| Code | Meaning |
|------|---------|
| `output_truncated` | Response cut off mid-sentence or incomplete |
| `wrong_format` | Format did not match the declared output schema |
| `factually_wrong` | Output contained verifiable factual errors |
| `refused_valid_request` | Node refused a protocol-compliant request without basis |
| `hallucination_detected` | Output invented non-existent references or facts |
| `excellent_quality` | Positive signal — unusually high accuracy or utility |
| `other` | Catch-all; `comment` field should contain details |

### 2.4 Compliance Status Enum (Node → Client)

| Value | Meaning | Reputation action |
|-------|---------|-----------------|
| `compliant` | Request fully met all protocol rules | None |
| `minor_issue` | Minor format or field anomaly; request still processable | Record only |
| `protocol_violation` | Clear rule breach (see violation_codes) | −0.03 if corroborated |
| `abusive` | Systematic or coordinated abuse pattern | −0.05 if corroborated |

### 2.5 Compliance Violation Codes

Used when `compliance_status` is `protocol_violation` or `abusive`:

| Code | Meaning | Testable? |
|------|---------|-----------|
| `malformed_intent` | Intent URN malformed or unregistered | Yes (URI parse + registry check) |
| `prompt_injection_attempt` | Intent payload contains injection markers | Yes (pattern match) |
| `rate_limit_evasion` | Request rate exceeded declared limits | Yes (sliding window) |
| `signature_invalid` | HMAC verification failed | Yes (cryptographic) |
| `payment_protocol_violation` | Payment signal absent or invalid (ADR-019) | Yes (schema check) |
| `spec_violation_other` | Other spec rule breach; `comment` required | Partial |

**Testability constraint**: violation codes must be falsifiable against observable request
data. Codes that require interpretation of intent or subjective judgment are NOT included
in this enum; they belong in free-text commentary.

---

## 3. Mutual Blinding — Commit-Reveal Scheme

To prevent strategic voting (rater sees the other side's rating and adjusts), both
parties commit before revealing:

```
Phase 1 — Commit (T_commit = 30 min after task completion):
  Both parties submit: commit = SHA-256(rating_json || nonce)
  Directory stores: (task_id, rater_id, commit, commit_timestamp)

Phase 2 — Reveal (T_reveal = 24 h after T_commit deadline):
  Both parties submit: (rating_json, nonce)
  Directory verifies: SHA-256(rating_json || nonce) == stored commit
```

**Non-reveal defaults**:
- If one party commits but does not reveal within T_reveal: rating counted as **abstain**
  (neutral; no reputation change). Non-reveal is not penalised — the commit is discarded.
- If one party does not commit at all: they waive feedback rights for that task.
  
**Why abstain, not punish**: Punishing non-reveal creates an incentive to use non-reveal
strategically (commit, observe the counterparty's reveal timing, then abstain). The correct
incentive is to always reveal honestly — which requires that reveal is free.

**Centralization consideration**: The directory holds commits and verifies reveals. This
is a centralization pressure point. For Phase 5, the single-directory architecture makes
this pragmatic. Phase 6 (federated directory) will need to distribute commit storage —
see ADR-013 and research/federated-directory-design notes.

---

## 4. Identity-Weighting

Higher-reputation identities produce more informative ratings (demonstrated
compliance track record). Weighted feedback impact:

```
effective_weight(rater) = clamp(rater_reputation / SILVER_THRESHOLD, 0.5, 2.0)
```

Where `SILVER_THRESHOLD = 0.40` (from REP2 design).

| Rater tier | reputation | effective_weight |
|-----------|-----------|-----------------|
| Recovery | 0.30 | 0.75 |
| Silver | 0.40 | 1.00 (baseline) |
| Gold | 0.65 | 1.625 |
| Platinum | 0.85 | 2.00 (cap) |

The 0.5 floor prevents recovery-band identities from being completely ignored — they
can still contribute, but with reduced signal weight.

Weighted quality bonus formula:
```
quality_delta = Σ(quality_weight_i × (intent_match_i − 3) × 0.001) / Σ(quality_weight_i)
```

Applied once per task, after all commits are revealed within T_reveal.

---

## 5. Anti-Sybil Measures

Feedback from coordinated Sybil identities should not sink a competitor's reputation.
Three layers of protection:

**Layer 1 — Credibility floor**:
Rating counts only if `rater_reputation ≥ R_FLOOR (0.30)`. Freshly registered
identities (sc=0.50 but no task history) are accepted but at minimum weight (0.75).

**Layer 2 — Independent agreement**:
A compliance violation rating triggers reputation action only if:
- Single rater: telemetry corroboration required (§5 below), OR
- Three or more independent raters (different `identity_age_hours`) agree on the
  same `compliance_status` and overlapping `violation_codes` within a 7-day window.

**Layer 3 — Creation-time clustering**:
If more than 50% of ratings in any 48-hour window for a single target come from
identities created within the same 24-hour span, the entire cluster is discounted:
their ratings contribute at 0.1× weight. This detects Sybil farms without requiring
identity linkage.

---

## 6. Telemetry Corroboration

A compliance violation (`protocol_violation` or `abusive`) advances to reputation update
only if at least one observable signal corroborates it:

| Violation code | Corroboration signal |
|---------------|---------------------|
| `signature_invalid` | Directory signature verification failure (recorded in task log) |
| `malformed_intent` | URI parse failure (logged at intake) |
| `rate_limit_evasion` | Rate counter exceeded threshold (logged by rate limiter) |
| `prompt_injection_attempt` | Detection pattern match (logged by intake filter) |
| `payment_protocol_violation` | Payment schema validation failure (logged) |
| `spec_violation_other` | Requires ≥2 corroborating raters (peer agreement as proxy) |

**Why corroboration is load-bearing**: Without it, a competitor can file `protocol_violation`
with violation code `spec_violation_other` for any task, imposing −0.03 with only a signed
envelope as evidence. Corroboration ensures the rating aligns with the directory's own
observable record, not just a claim.

---

## 7. Directory API Integration Points

Feedback submission does not require new endpoints at this stage — it piggybacks on
the existing heartbeat/event-log path. Recommended implementation approach:

```
POST /api/v1/feedback
  body: feedback_envelope (see spec/schemas/feedback-envelope.json)
  auth: Bearer node_token
  returns: 202 Accepted + commit_id
           400 Bad Request (schema validation failure)
           409 Conflict (duplicate feedback for task_id + rater_id)
           422 Unprocessable (reveal before commit phase complete)
```

Feedback state machine per task:
```
NEW → COMMIT_PENDING (both sides within T_commit)
    → PARTIAL_COMMIT (one side committed, other didn't)
    → REVEAL_PENDING (both committed, awaiting reveal)
    → COMPLETE (both revealed — reputation update applied)
    → EXPIRED (T_reveal passed — abstain rule applied, reputation unchanged)
```

---

## 8. Reputation Update Integration with REP1

REP1 delta table (base outcome path):

| Outcome | Δ |
|---------|---|
| Successful task | +0.01 |
| Failed task | −0.05 |

REP4 adds feedback modifier applied after task Δ:

| Condition | Additional Δ (node reputation) |
|-----------|-------------------------------|
| Quality feedback, avg_intent_match = 5 | +0.002 (max bonus) |
| Quality feedback, avg_intent_match = 3 | ±0.000 (neutral) |
| Quality feedback, avg_intent_match = 1 | −0.002 (max penalty) |
| Compliance violation (corroborated, protocol_violation) | −0.03 on client rep |
| Compliance violation (corroborated, abusive) | −0.05 on client rep |

The feedback modifier is intentionally small relative to the task-outcome Δ. It should
not dominate; it should differentiate nodes that are consistently excellent from those
that are consistently mediocre within the same success/failure tier.

---

## 9. Open Questions (deferred to REP5/REP6)

- **Client reputation decay**: S.12 §5.1 currently models only node reputation. Does
  client reputation need a separate decay function, or does the same λ=0.005/hr apply?
  Recommendation: same decay model, separate track (deferred to REP6 live readiness).

- **Commit storage for federated architecture**: Phase 6 federated directory needs
  distributed commit storage. The current design centralizes this at the directory — a
  follow-up ADR stub is warranted when Phase 6 design begins.

- **Full simulation**: How does the feedback modifier interact with adversarial strategy?
  (deferred to REP6 simulation harness)

- **Commit-reveal liveness**: What happens if the directory is unreachable during T_reveal?
  Should feedback be accepted after T_reveal with proof of network partition? Deferred.

---

## 10. Cross-References

- **ADR-026**: Two-sided reputation as earned signal — establishes the symmetric
  reputation framework that this document implements
- **REP1** (`reputation-mechanics.md`): Base delta values (+0.01/−0.05) that feedback
  modifiers stack on top of
- **REP2** (`tier-structure.md`): Silver threshold (0.40) used in identity-weighting formula
- **§5.1** (spec/iicp-cooperative-inference.md): Decay model (λ=0.005, R_FLOOR=0.30)
- **ADR-019**: Declarative pricing — payment is orthogonal to feedback
- **ADR-021**: Identity slot — durable identity binding ensures feedback is attributable
- **#170**: REP4 tracking issue
- **#187**: T4.3 outlier detection (related anti-gaming mechanism)
