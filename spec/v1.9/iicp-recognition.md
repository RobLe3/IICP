# IICP Operator Recognition Protocol

**Version**: 0.4.0-draft
**Status**: Draft — RECOG-* test IDs registered in `spec/conformance-test-suite.md §15`. API surface §7 + anti-gaming §8 normative. §3 Operator Identity composes on ADR-034 Identity Slot. §12 open questions now carry **proposed defaults** with rationale — PS review reduces to confirm/override per question (was "needs full design"). v1.0 unblocks when PS ratifies §12 defaults.
**Date**: 2026-05-26 (updated from 2026-05-24)
**Tracking**: #309 (this spec graduation), #267 (research), #269 (ADR-030 — closed 2026-05-26, file exists at Proposed)
**Foundation**: ADR-034 (Identity Slot), S.15 (`spec/iicp-identity-slot.md`), BC-12 (`project/ddd/BC-12-identity.md`) — operator identity composes on top of the Identity Slot
**Companion**: `project/gamification.md` (project-level concept), `research/gamification-track/` (rationale, metric mapping, anti-gaming, rollout gates, API surface)

---

## 1. Scope

This document specifies the IICP Operator Recognition Protocol: ranks, badges, leaderboards,
and seasonal cohorts that convert passive operational telemetry the directory already collects
into intrinsic motivators for node operators.

**This is a skeleton spec.** Each section reserves space for normative MUST/SHOULD language
that will be filled in after PS review of the research deliverables. Until that review
completes, treat statements in this document as **informative** (preview of the normative
content) rather than binding.

## 2. Conformance levels

| Level | Description |
|-------|-------------|
| RECOG-Aware | Implementation surfaces operator ranks and badges in its UI / API responses. Read-only. |
| RECOG-Provider | Directory implementation that computes and serves rank / badge / leaderboard state per this spec. |
| RECOG-Federated | Directory replica that consumes recognition state from the Genesis Seed's federated event log (per ADR-013) and serves locally-computed views. |

Phase 5D launch: only RECOG-Provider (Genesis Seed) initially. RECOG-Federated unblocked when
ADR-013 replicas are operational + replica trust tiers settled (per ADR-030 attestation gates).

## 3. Operator Identity (normative reference)

This protocol depends on the operator identity layer defined by **ADR-030 (Operator Identity
& Anti-Sybil Layer)**, which itself sits on top of the **Identity Slot** foundation
(ADR-034, `spec/iicp-identity-slot.md`, BC-12). All rank and badge state is keyed on
`operator_id`, never on `node_id`. A single operator with multiple nodes appears once in
leaderboards and rank tables.

**Layered identity model** (resolves open question 3 from v0.2.0-draft):

```
Recognition Protocol (this spec)
        ↓ keyed on operator_id
ADR-030 Operator Identity & Anti-Sybil
        ↓ uses identity primitives from
ADR-034 / S.15 Identity Slot (Identity URI + Identity Signature, verifier dispatch)
        ↓ first reference verifier
did:web verifier (Phase 6 SeedDidResolver / DidResolver / replica_sig_verifier)
```

This composes — it does NOT absorb. The Identity Slot is general (any signed message);
operator identity (ADR-030) adds operator-grouping semantics on top (one operator may
run multiple nodes; sock-puppet detection; attestation tiers). Recognition (this spec)
adds rank/badge semantics on top of operator identity.

`spec/iicp-operator.md` (forthcoming) will hold the normative operator identity spec,
specifying how `operator_id` maps to Identity URIs (e.g. `urn:iicp:operator:<hex>` or
external `did:web:<operator-domain>`) and how the verifier dispatch from S.15 §7 applies
when a CALL or RESPONSE message carries an operator identity claim. Until that spec
lands, this document defers to ADR-030 § Decision for `operator_id` semantics and to
ADR-034 / S.15 for the underlying cryptographic primitives.

## 4. Ranks

Ranks are progression tiers earned by sustained participation. Each rank has an unambiguous
trigger computed from data the directory collects.

### 4.1 Rank table

| Tier | Title | Trigger (normative — TBD final tuning) | Telemetry source |
|------|-------|----------------------------------------|------------------|
| 0 | Node Initiate | First successful `POST /v1/register` | `node_events.event_type='REGISTER'` |
| 1 | Mesh Serf | ≥7 days of HEARTBEAT events with success rate ≥ 95% | rolling 7d HEARTBEAT aggregation |
| 2 | Local Daemon | ≥30 days continuous uptime AND ≥1 declared model passing DIR-TRUST-01 | uptime calc + DIR-TRUST-01 result |
| 3 | Intent Weaver | `reputation.completed_tasks_count ≥ 1000` AND ≥3 distinct proxy contributors | reputation + task_events (post G5) |
| 4 | CIP Provider | `cip_conformance_level = 'CIP-Provider'` AND attested operator (Tier 2 per ADR-030) | discover response + operators.attestation_status |
| 5 | REACH Herald | Probed reachable from ≥3 distinct REACH probe origins over 30d rolling | REACH multi-region (G3 dependency) |
| 6 | Mesh Guardian | ≥90 days uptime AND ≥99% heartbeat success AND continuous DIR-TRUST-01 pass | combined check |
| 7 | Forge Baron | `completed_tasks_count ≥ 10000` AND ≥5 distinct models AND ≥3 contributors | reputation + capabilities |
| 8 | Mesh Legend | Top-10 globally by composite rank_score (§5) | hourly leaderboard recompute |
| Zero Kelvin | Permanent founder title | Manual assignment by Genesis Seed maintainer | n/a |

**MUST**: Rank ≥4 (CIP Provider) requires Tier 2 attestation (per ADR-030).
**MUST**: Rank ≥3 (Intent Weaver) requires ≥3 distinct proxy contributors (anti-collusion).
**MUST**: Rank ≥2 (Local Daemon) requires DIR-TRUST-01 pass (anti-fake-backend).

### 4.2 Rank advancement

**MUST**: Ranks advance automatically when triggers are satisfied — no operator action required.
**MUST**: Once earned, a rank persists for the operator's lifetime even if triggers later fail
(e.g., uptime drops). Only Mesh Legend (top-10) is recomputed dynamically; all others ratchet.
**SHOULD**: The directory MAY notify the operator via webhook or email when a rank is reached.

### 4.3 Composite rank_score formula (§5 — for Mesh Legend / Living Mesh Lords)

```
rank_score = 0.30 × uptime_pct
           + 0.25 × task_throughput_norm
           + 0.20 × model_diversity_norm
           + 0.15 × cip_conformance_bonus
           + 0.10 × reach_diversity_norm
```

Where `*_norm` is min-max normalized to [0, 100] across active operators. Recomputed hourly.

## 5. Badges

Discrete recognitions for specific achievements. Each badge has a stable identifier and is
permanently associated with the operator once earned.

### 5.1 Core badges (subset — full table in §5.x)

| Badge ID | Title | Trigger | Source |
|----------|-------|---------|--------|
| `first_blood` | First Blood | First successfully routed task | reputation count 0→1 |
| `uptime_chad` | Uptime Chad | ≥99.5% heartbeat success / 60d | rolling aggregation |
| `model_hoarder` | Model Hoarder | ≥5 distinct models, all passing DIR-TRUST-01 | capabilities + trust audit |
| `task_gladiator` | Task Gladiator | ≥50,000 tasks with ≥3 distinct contributors | reputation + collusion check |
| `diversity_champion_{cc}` | Diversity Champion (per country) | Most distinct models in region=cc (attested operators only) | partitioned ranking |
| `credit_earner` | Credit Earner | First 1,000 credits earned | credit_events sum |

### 5.2 Seasonal badges

**MUST**: Each season has a defined window (H1: Jan 1 – Jun 30; H2: Jul 1 – Dec 31).
**MUST**: Season-exclusive badges cannot be earned after the season closes.
**MUST**: Once earned, season-exclusive badges persist permanently on the operator profile.
**MUST**: Season badges require ≥30 days active AND ≥M tasks served within the season window.

Examples:
- `h2_2026_mesh_pioneer` — Mesh Pioneer for H2 2026 (active ≥30d in window)
- `h1_2027_diversity_champion` — Diversity Champion for H1 2027 (most distinct models in window)

### 5.3 Yearly class badges

**MUST**: `class_of_YYYY` is earned by any operator with ≥7 days active AND ≥1 successful task
within calendar year YYYY.
**MUST**: Class badges are permanent. Late joiners earn future-year classes; no back-earning.

## 6. Leaderboards

Public views of recognition state. Cacheable, anonymous-read.

| Board ID | Title | Order | Window |
|----------|-------|-------|--------|
| `living_mesh_lords` | Living Mesh Lords | composite rank_score DESC | cumulative |
| `rising_stars_30d` | Rising Stars | growth in rank_score over last 30d | rolling 30d |
| `model_diversity_hall` | Model Diversity Hall | distinct models DESC | cumulative |
| `most_reliable_60d` | Most Reliable Nodes | uptime + reachability composite | rolling 60d |
| `regional_champions_{cc}` | Regional Champions | top per country | cumulative, per region |
| `founding_cohort` | Founding Cohort | alphabetical | pre-public-launch operators only |
| `season_h{1|2}_{YYYY}` | Season archive | season composite | closed-season frozen |

**MUST**: Leaderboards exclude operators who have opted out via `POST /v1/operator/{handle}/visibility`.
**MUST**: Leaderboards exclude operators flagged for sock-puppet violations.
**MUST**: Cumulative leaderboards persist across seasons; seasonal leaderboards freeze at season close.

## 7. API Surface

See `research/gamification-track/05-api-surface.md` for full endpoint specifications. Brief
inventory:

| Method | Endpoint | Auth | Cache |
|--------|----------|------|-------|
| GET | `/v1/operator/{handle}/profile` | none (public) | `s-maxage=120` |
| GET | `/v1/leaderboards/{board_id}` | none | `s-maxage=300` |
| GET | `/v1/badges` | none | `max-age=86400` |
| GET | `/v1/seasons/current` | none | `max-age=3600` |
| POST | `/v1/operator/{handle}/visibility` | operator-signed (S.15 slot) | no-store |
| POST | `/v1/operator/{handle}/handle` | operator-signed (S.15 slot) | no-store |
| GET | `/v1/operator/{handle}/private_summary` | operator-signed (S.15 slot) | no-store |

"Operator-signed" means the request body carries the Identity Slot (`identity` +
`identity_signature` per S.15 §3) with `identity_uri` matching the operator's published
DID. The directory MUST verify the slot via the configured verifier dispatcher (S.15 §7)
before accepting the mutation; failure → IICP-IDSLOT-02 (signature invalid) or
IICP-IDSLOT-04 (identity drift if operator claims different DID than registered).

## 8. Anti-gaming Hard Rules (normative)

The following MUST be enforced by RECOG-Provider implementations. Sourced from
`research/gamification-track/03-anti-gaming.md` §"Hard rules for the gamification spec":

1. **MUST**: Same operator's multiple nodes do not multiply operator-diversity scores
   (Country Pioneer, Diversity Champion regional, Founding Cohort).
2. **MUST**: DIR-TRUST-01 must pass for any rank ≥ Mesh Serf or any badge with a model-related
   trigger. Divergence forfeits eligibility.
3. **MUST**: Collusion-resistant task counts require ≥3 distinct proxy contributors before the
   count qualifies for any badge with task threshold ≥1000.
4. **MUST**: Disruption windows are maintainer-annotated post-incident, not operator-claimed.
5. **MUST**: Operator identity is permanent — laundering an identity (re-registering after
   flag) does not restore reputation in the recognition system. Identity continuity is
   enforced via ADR-034 / S.15 Identity Slot: the `identity_uri` of an operator is pinned-on-
   first-use; re-registration with a *different* `identity_uri` creates a new operator
   (rank-zero, no prior reputation), and re-registration with the *same* `identity_uri`
   after a flag does NOT clear the flag.
6. **MUST**: Season badges require minimum genuine activity (≥30d + ≥M tasks) — not just
   registration in the window.

Additional MUST from the rank table (§4):
7. **MUST**: Rank ≥4 (CIP Provider) requires Tier 2 attested operator identity.

## 9. Privacy

**MUST**: Operator handle is chosen at registration, never a real-name binding.
**MUST**: Operator geographic info is region-level only (no GPS, no precise location).
**MUST**: Operators MAY opt out of public leaderboard visibility via API; private profile
remains for the operator themselves.
**MUST**: Opt-out is honored within 5 minutes of API call (cache invalidation).
**SHOULD**: Recognition data deletion-on-request — operator can request hard-delete of all
recognition state (badges, ranks, leaderboard positions) per local privacy regulations.

## 10. Conformance Test IDs

The following test IDs are reserved for `spec/conformance-test-suite.md` §X (Recognition):

| Test ID | Requirement | Level |
|---------|-------------|-------|
| RECOG-PROF-01 | `GET /v1/operator/{handle}/profile` returns valid schema | MUST |
| RECOG-PROF-02 | 404 for unknown handle, 410 for opted-out | MUST |
| RECOG-LEAD-01 | `GET /v1/leaderboards/{board_id}` returns sorted entries | MUST |
| RECOG-BADG-01 | `GET /v1/badges` returns complete catalog with stable IDs | MUST |
| RECOG-SEAS-01 | `GET /v1/seasons/current` returns valid season window | MUST |
| RECOG-VIS-01 | `POST /v1/operator/{handle}/visibility` requires operator auth | MUST |
| RECOG-HAN-01 | Handle change blocks reserved words / squatting patterns | MUST |
| RECOG-PRIV-01 | `private_summary` requires operator auth (401 otherwise) | MUST |
| RECOG-RANK-01 | Rank advancement persists once earned (except top-10) | MUST |
| RECOG-RANK-02 | Rank ≥4 requires Tier 2 attestation | MUST |
| RECOG-ANTI-01 | Same operator nodes do not multiply operator-diversity scores | MUST |
| RECOG-ANTI-02 | Big-N task badges require ≥3 distinct contributors | MUST |
| RECOG-SEAS-02 | Season-exclusive badges cannot be earned after window closes | MUST |
| RECOG-OPT-01 | Opt-out applied within 5 minutes | MUST |

These test IDs are now registered in `spec/conformance-test-suite.md §15` (v4.35.0, iter-976) for cross-spec traceability. REACH probes implementing these tests will be added to `reach/src/reach/probes/recognition_conformance.py` once G1+G6 gates clear.

## 11. Implementation gates

Per `research/gamification-track/04-rollout-gates.md`, this spec MUST NOT have any
RECOG-Provider implementation deployed to production until ALL of these gates clear:

- **G1**: ADR-030 Accepted + operator identity implementation shipped
- **G2**: `project/gates/CLOSED_BETA_TO_PUBLIC_GATE.md` resolved (either path)
- **G3**: REACH geographic expansion to ≥3 probe origins
- **G4**: ≥10 attested external operators in production
- **G5**: All "partial" telemetry items from gamification deliverable 02 resolved
- **G6**: This spec at v1.0 + conformance test IDs registered in test suite
- **G7**: Privacy + moderation policy documents committed
- **G8**: Founding Cohort migration plan committed

## 12. Open questions for PS review — with proposed defaults

These mirror the gamification research open questions. Each now carries a
**proposed default** with rationale; PS review reduces to confirm or override
per question. Question 3 already resolved in v0.3.0.

### Q1 — Season boundary alignment

**Proposed default**: **H1/H2 (Jan-Jun / Jul-Dec)**.

**Rationale**: Two 6-month seasons match the "Class of YEAR" annual rhythm
(2 mid-year checkpoints + 1 year-end) and align with most operators' fiscal/
ops planning cycles. Quarterly seasons would create 4× the leaderboard reset
ceremony churn for marginal additional motivation surface. Operators already
report monthly metric checkpoints; H1/H2 cadence keeps it stable.

**To override**: PS confirms quarterly preferred + writes `season_boundaries:
["Q1","Q2","Q3","Q4"]` into recognition config.

### Q2 — Handle moderation authority

**Proposed default**: **Maintainer-only at launch; community queue post-#268**.

**Rationale**: Phase 5D launches with N=1 maintainer; a community-moderation
queue requires meaningful moderator pool (≥3 attested operators per ADR-030
Tier 2) which isn't available pre-public-beta. Maintainer-only is the only
viable initial state. The community-queue model from #268 activates when the
mesh has enough attested operators to sustain it (target: 10+ Tier-2 operators).

**To override**: PS confirms maintainer-only is permanent (close #268) OR
defines an earlier community-queue trigger condition.

### Q4 — TC-9b operator-scoped rate limit migration

**Proposed default**: **Spec impact = NONE for recognition; TC-9b stays
node-scoped (per existing implementation)**.

**Rationale**: Recognition is keyed on `operator_id` for rank/badge state, but
the underlying rate limit (TC-9b: 1000 credits/hour) is enforced at the credit
ledger layer which already operates on `node_id`. An operator with multiple
nodes effectively gets a multiplied rate budget — that's a credit-economy
design question (ADR-031 / research/credit-economy/), not a recognition design
question. Recognition consumes credit events; it does not enforce rate limits.

**To override**: PS confirms a hard cap should be applied at the operator level
(e.g. 1000 credits/hour PER OPERATOR regardless of node count) — would require
parallel ADR + credit-economy redesign, OUT OF SCOPE for this spec.

### Q5 — Tier 2 attestation expiry

**Proposed default**: **Annual re-attestation required** (365-day TTL).

**Rationale**: Tier 2 attestation depends on operator-supplied evidence (KYC-
adjacent or community vouching per ADR-030). Operators change companies, lose
key control, exit the mesh. A permanent attestation creates stale-trust risk —
an operator attested in 2026 might be a different person in 2028 with the same
node identity (key transfer / corporate change). Annual re-attestation forces
liveness check on the operator identity itself. Cost to operator: ~10 minutes
once per year.

**To override**: PS confirms permanent-once-verified is acceptable for the
mesh size (e.g. with ≤100 operators the trust web is small enough to detect
breaches socially) OR a different TTL (e.g. 2 years, 5 years).

### Q6 — Class of YEAR minimum threshold

**Proposed default**: **≥7 active days within the cohort year** (as
originally proposed).

**Rationale**: 7-day floor filters out operators who registered + ran one
single uptime burst then abandoned. It allows part-time / hobbyist operators
(weekend-only, monthly burst) to qualify. A higher threshold (e.g. 30 days)
excludes the long tail; a lower threshold (e.g. 1 day) trivializes the
recognition. 7 is the documented research finding; preserve unless PS has a
specific counter.

**To override**: PS provides a different threshold (e.g. 14 days for stricter
filter, 3 days for inclusive cohort).

### Q7 — Disruption window annotation policy

**Proposed default**: **Maintainer-flags; public list visible on
`/recognition/disruptions` with redacted operator names**.

**Rationale**: Disruptions (network outages, deploy windows, force-majeure
events) reset operator uptime counters in ways that aren't the operator's
fault. SOMEONE has to annotate them or operators get penalized for outages
they didn't cause. Maintainer-flagged is the only viable initial state (N=1
operator). Public visibility (with redaction) provides accountability for
why a leaderboard reset happened. Full operator-name visibility opens
gaming surface (operator submits false disruption claim to evade a
penalty); redaction balances transparency vs gaming defense.

**To override**: PS confirms full-public-with-operator-names OR
maintainer-only-private (no public visibility), OR delegates to a community
moderation queue (composes with Q2).

---

## 12b. Status of v1.0 graduation

When PS confirms/overrides Q1, Q2, Q4-Q7, the spec promotes to v1.0:

| Question | Status |
|----------|--------|
| Q1 season boundaries | Proposed default H1/H2 — awaits PS |
| Q2 moderation authority | Proposed default maintainer-only-launch — awaits PS |
| Q3 identity composition | ✅ Resolved v0.3.0 |
| Q4 TC-9b operator-scoped rate limit | Proposed default NONE (out of scope) — awaits PS |
| Q5 Tier 2 attestation expiry | Proposed default 365-day TTL — awaits PS |
| Q6 Class of YEAR threshold | Proposed default ≥7 days — awaits PS |
| Q7 disruption annotation | Proposed default maintainer-flag + redacted-public — awaits PS |

Each confirmation closes one row; full confirmation removes the `-draft`
suffix and bumps to `v1.0`. The G6 gamification gate prerequisite is then
satisfied.

---

## 13. Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.4.0-draft | 2026-05-26 | §12 reformatted: every open question (1, 2, 4-7) now carries a **proposed default** with rationale and an explicit "to override" path for PS. New §12b "Status of v1.0 graduation" table tracks per-question PS-confirmation status. v1.0 unblocks when PS confirms/overrides each row (vs previous "needs full design" framing — now ratification-bounded work). Resolves the spec-graduation-path ambiguity from v0.3.0; PS review surface reduces from "design 6 things" to "confirm 6 defaults". |
| 0.3.0-draft | 2026-05-26 | §3 Operator Identity restructured with layered identity model (Recognition → ADR-030 Operator → ADR-034 Identity Slot → did:web verifier); cross-references S.15 (`spec/iicp-identity-slot.md`) + BC-12. §7 API surface clarifies "operator-signed" means S.15 Identity Slot with verifier dispatch + IICP-IDSLOT-02/04 failure modes. §8 anti-gaming rule 5 (no identity laundering) now cites ADR-034 pin-on-first-use as enforcement mechanism. §12 open question 3 (Operator vs Identity Slot — composed or absorbed?) **resolved**: composed; Identity Slot is foundation. Tracking issue #309 referenced. Resolves 1 of 7 §12 open questions; remaining 6 (1, 2, 4-7) still need PS review before v1.0. |
| 0.2.0-draft | 2026-05-24 | RECOG-* test IDs registered in `spec/conformance-test-suite.md §15` (v4.35.0, iter-976). §10 note updated to reflect cross-spec registration. Status updated to reflect normative bodies in §4/§5/§6/§8/§9 complete; pending PS ratification of §12 open questions before v1.0. |
| 0.1.0-draft | 2026-05-21 | Initial skeleton (iter-302). Sections + test IDs + open questions reserved. Normative bodies preview; final language pending PS review of `research/gamification-track/`. |
