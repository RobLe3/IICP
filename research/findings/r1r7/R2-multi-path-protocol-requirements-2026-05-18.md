# R2 — Multi-Path Inference: Protocol Requirements and Threat Model

**Track**: R1R7 — Provider Selection & Multi-Path Routing  
**Issue**: #174 (R2: Multi-path inference requirements and threat model)  
**Date**: 2026-05-18  
**Author**: RESA loop, FORGE iter82  
**Depends on**: R1 (#173) — protocol/policy boundary complete  
**Length**: ≈1950 words (within ≤2000 limit)  
**ADR impact**: Proposes ADR-029 (multi-path envelope extension); flags ADR-024 and ADR-019 updates needed.

---

## 1. Use Cases: When Is Multi-Path Warranted?

Multi-path inference means the client sends the same task to N providers and reconciles
their responses. The R1 protocol boundary established that multi-path declaration is a
protocol substrate field (Gap 4), not client-internal. This document specifies what the
protocol must carry for each use case.

| Use Case | N | Reconciliation strategy | Warranted when |
|----------|---|------------------------|----------------|
| **Quality comparison** | 2–3 | Best response (client scores quality) | Client prefers highest quality over cost |
| **Byzantine-tolerant execution** | 3–5 | Majority vote or quorum | High-value tasks where any single provider might be adversarial or misconfigured |
| **Verification (1+verify)** | 2 (1 executor + 1 verifier) | Verifier checks executor's output | Deterministic tasks (code, math, structured data) — verifier is cheap |
| **Fallback resilience** | 2 (primary + standby) | First success wins | Reliability-critical tasks where p99 latency matters more than cost |
| **Consolidated multi-path** | N+K (N inference + K consolidators) | Consolidators synthesize fragments | Non-deterministic tasks requiring coherent synthesis (see MESH4) |

**Cost reality**: Multi-path is never free. At N=3, the client pays 3 task prices (all N
providers get paid — see §4 Settlement). This means multi-path is economically rational
only when the value increment exceeds N×cost. For most tasks, single-provider routing is
correct. Multi-path should be a client option, not a default.

---

## 2. Protocol Requirements

### 2.1 Multi-Path Declaration in Task Submission

Per R1 Gap 4, providers need to know if they are in a multi-path set. This affects:
- **Pricing**: a provider in a multi-path set may choose to charge less, knowing that
  payment is guaranteed (the client pays all N) but bearing lower responsibility (failure
  is mitigated by other providers). Protocol MUST allow providers to declare a multi-path
  discount; clients MUST declare whether a task is multi-path.
- **Behavior**: a provider in a multi-path set MUST NOT suppress or delay its response
  to coordinate with other providers in the set. Multi-path coordination attacks are the
  primary threat (§5.2).
- **Fragment identity**: when a task is part of a multi-path set, the provider's response
  should carry a fragment identifier linking it to the task and the set (so the client can
  match received responses to outstanding fragments).

**Required new protocol field in task submission**:

```json
{
  "task_id": "...",
  "intent": "...",
  "payload": "...",
  "multi_path": {
    "enabled": true,
    "set_id": "<client-generated UUID for this fan-out>",
    "position_in_set": 2,
    "set_size": 3,
    "strategy": "quality_comparison | byzantine_tolerant | verification | fallback | consolidated"
  }
}
```

The `set_id` allows correlation across fragments. The `strategy` field is informational
for the provider (affects pricing decisions) but does not mandate provider behavior.

### 2.2 Fragment Identity in Task Response

Each provider response in a multi-path set MUST carry the `set_id` and
`position_in_set` from the task submission. This allows the client's receive window
(architecture §9) to match responses to fragments and detect duplicates or substitutions.

**Required response field addition** (extends ADR-024 signed envelope):

```json
{
  "task_id": "...",
  "multi_path_fragment": {
    "set_id": "<same as task submission>",
    "position_in_set": 2,
    "fragment_hash": "<SHA-256 of payload content>"
  },
  "signed_by": "...",
  "signature": "..."
}
```

The `fragment_hash` enables the client to detect tampering without comparing full
payloads in memory.

### 2.3 Receive Window Completion Criteria

The client's receive window (architecture §9) must handle partial returns. Protocol
carries: all N `set_id` submissions are paired with N `multi_path_fragment` responses.
The client decides completion policy (all N, quorum, timeout — CLIENT-INTERNAL per R1).
Protocol does not dictate completion criteria; it provides the fragment identity substrate.

### 2.4 Signed Envelope Extension (ADR-024)

ADR-024's signed envelope currently signs: task payload, node identity, timestamp,
intent URI. For multi-path, the envelope must additionally sign `set_id` and
`position_in_set`. This prevents a provider from claiming a different position in the set
(which would allow a malicious provider to substitute another provider's fragment).

**Required ADR-024 update**: add `multi_path_fragment` to the signed fields set. If
`multi_path.enabled = false`, these fields are absent (no backward-compat break).

---

## 3. Settlement Model

Multi-path raises an immediate settlement question: if the client fans out to 3 providers
and uses 2 responses, does the third provider (whose response was discarded) get paid?

**Principle (extends ADR-019)**: All N providers in a multi-path set get paid the declared
price for the task they executed, regardless of whether their fragment was selected by
the reconciliation policy. A provider cannot know in advance whether its fragment will
be selected; holding back payment based on selection would create perverse incentives
(providers coordinate to produce "winning" responses rather than honest responses).

**Settlement fields required**:
- Client declares `multi_path.set_size = N` at task submission time.
- Each provider holds a signed receipt showing it was position K in set S.
- Settlement occurs per-provider based on task completion, not on fragment selection.
- If a provider times out (no response within deadline), it is not paid. Timeout is not
  provider fault; deadline enforcement is client policy.

**Cost model**:

| Strategy | N | Settlement multiplier | Notes |
|----------|---|----------------------|-------|
| Quality comparison (3) | 3 | 3× single task price | All 3 paid, best selected |
| Byzantine-tolerant (3-of-5) | 5 | 5× | All 5 paid, quorum wins |
| 1+verify | 2 | 2× (executor price + verifier price) | Verifier may charge less (lighter work) |
| Fallback (primary+standby) | 2 | 1× if primary succeeds; 2× if standby activated | Primary success → standby not invoked, not paid |
| Consolidated (N+K) | N+K | N× inference + K× consolidation | Consolidators charge higher rate |

**Fallback settlement nuance**: the client MUST commit to paying the standby at
task-dispatch time if the standby is invoked. The client cannot decide mid-flight
that the standby should not be invoked and then refuse payment. Task dispatch is the
commitment point.

---

## 4. Threat Model — New Attacks from Multi-Path

### 4.1 Collusion Coordination Attack (HIGH RISK)

**Threat**: N providers in a multi-path set coordinate to produce a specific response
that wins the reconciliation (majority vote). A quorum of colluding providers can determine
the client's output.

**Mitigation**:
- Provider diversity selection (operator, region, model) reduces probability of colluding
  providers being in the same set — client policy, MESH4/MESH5 design scope.
- `set_id` and `position_in_set` must be included in the signed envelope (§2.4). Providers
  cannot learn which other providers are in the set without coordination.
- **Protocol protection**: the client MUST NOT reveal the full multi-path set to any
  individual provider. Each provider knows its own `position_in_set` and `set_size` but
  NOT the identity of other providers in the set. This is a protocol MUST requirement.

### 4.2 Time-Correlation Attack (MEDIUM RISK)

**Threat**: An observer who can time-correlate task submissions can infer which providers
are in the same multi-path set by observing simultaneous task arrivals at multiple providers.

**Mitigation**:
- Jitter at client dispatch: the client SHOULD introduce random jitter (50–200ms) between
  dispatches to the N providers. Protocol MUST NOT enforce simultaneous submission.
- Jitter implementation is CLIENT policy; the protocol requirement is that providers MUST
  NOT assume synchronized receipt of tasks in a multi-path set.
- Note: jitter increases latency of the first-fragment arrival. For verification (1+verify),
  this may be acceptable; for fallback-resilience, it's counterproductive. Client strategy determines jitter policy per use case.

### 4.3 Sybil Provider Pool Corruption (HIGH RISK)

**Threat**: A Sybil attacker registers N provider identities and wins multiple positions
in the same multi-path set. A single operator controls the consensus result.

**Mitigation**:
- Identity-age gate for provider roles (per REP2 design, tier structure) — ensures
  newly registered identities cannot immediately appear as providers in high-trust roles.
- Operator diversity selection in consolidator pool (MESH2 design scope).
- The directory MUST NOT return providers from the same operator (same identity key
  shard) for the same multi-path set. This is a new directory requirement — currently
  not specified. Flagged as Gap in §6.

### 4.4 Fragment Substitution Attack (MEDIUM RISK)

**Threat**: A malicious provider substitutes another provider's signed fragment with its
own, or modifies a fragment in transit.

**Mitigation**:
- `fragment_hash` in signed envelope (§2.2) — client can verify each fragment's content
  was not modified in transit.
- `position_in_set` is signed — a provider cannot claim another position.
- Relay nodes (if any) cannot modify fragments without invalidating the provider's
  signature, since the full fragment is signed.

---

## 5. Contradictions with Existing ADRs

| Existing ADR | Contradiction | Resolution |
|-------------|---------------|-----------|
| ADR-024: signed envelope fields | Does not include `set_id`, `position_in_set`, `fragment_hash` | Extend ADR-024 with multi-path fields (conditional, absent for single-path tasks) |
| ADR-019: declarative pricing | Does not address per-position settlement within a multi-path set | Extend ADR-019 §settlement with multi-path settlement model (all N pay rule) |
| ADR-013: federated directory | Does not specify diversity constraints for multi-path set composition | Add multi-path diversity requirement to ADR-013 §node selection |

No outright contradictions — all three are extensions, not incompatibilities.

---

## 6. Proposed Follow-Up ADR

**ADR-029: Multi-Path Inference Protocol Extension**

Scope:
- Define `multi_path` field in task submission (§2.1)
- Define `multi_path_fragment` in task response (§2.2)
- Extend ADR-024 signed fields to include multi-path fields
- Extend ADR-019 settlement to cover multi-path set payment model
- Define operator-diversity requirement for multi-path set composition (Threat 4.3)

This ADR is blocked on MESH4 (consolidator pattern specifics) and R6 (N-of-M strategy
simulation results). ADR-029 should be drafted after R6 simulation completes.

**Interim protocol stub** (safe to add now): add `multi_path.enabled` boolean to task
submission schema as an OPTIONAL field. When absent or `false`, single-path behavior.
This forward-compatible addition lets REACH add a probe for the field without waiting for
the full ADR-029 specification.

---

## 7. Acceptance Criteria Verification

| AC | Requirement | Status |
|----|-------------|--------|
| Research document covers all 6 topic areas | Use cases (§1), protocol req (§2), settlement (§3), threat model (§4), cost model (§3 table), relationship to ADR-024 (§2.4, §5) | ✓ |
| At least one follow-up ADR stub proposed | ADR-029 (§6) | ✓ |
| Settlement model is concrete (who pays, how much) | §3: all N pay; fallback nuance; per-strategy table | ✓ |
| Threat model includes at least 3 adversarial scenarios | §4.1 collusion (HIGH), §4.2 time-correlation (MEDIUM), §4.3 Sybil pool (HIGH), §4.4 fragment substitution (MEDIUM) — 4 scenarios | ✓ |
