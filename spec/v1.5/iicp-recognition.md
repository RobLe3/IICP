# IICP Operator Recognition Protocol

**Version**: 0.1.0-draft
**Status**: Draft (skeleton — normative MUST/SHOULD bodies pending PS review of `research/gamification-track/`)
**Date**: 2026-05-21
**Tracking**: #267 (research), #269 (ADR-030 Operator Identity & Anti-Sybil — prerequisite)
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
& Anti-Sybil Layer)**. All rank and badge state is keyed on `operator_id`, never on `node_id`.
A single operator with multiple nodes appears once in leaderboards and rank tables.

`spec/iicp-operator.md` (forthcoming) will hold the normative operator identity spec; until
then this document defers to ADR-030 § Decision.

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
| POST | `/v1/operator/{handle}/visibility` | operator-signed | no-store |
| POST | `/v1/operator/{handle}/handle` | operator-signed | no-store |
| GET | `/v1/operator/{handle}/private_summary` | operator-signed | no-store |

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
   flag) does not restore reputation in the recognition system.
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

REACH probes implementing these tests will be added to
`reach/src/reach/probes/recognition_conformance.py` once implementation is authorized.

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

## 12. Open questions for PS review

These mirror the gamification research open questions; resolution required before v1.0:

1. Season boundary alignment — H1/H2 Jan-Jun / Jul-Dec? Or Q1+Q2 / Q3+Q4?
2. Handle moderation authority — maintainer-only? Community moderation queue (post-#268)?
3. Operator vs Identity Slot (ADR-021) — composed or absorbed?
4. TC-9b operator-scoped rate limit migration — spec impact?
5. Tier 2 attestation expiry — re-attest annually? Permanent once verified?
6. Class of YEAR minimum threshold — ≥7 active days (proposed) or different?
7. Disruption window annotation policy — who flags? Public visibility of the list?

---

## 13. Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.0-draft | 2026-05-21 | Initial skeleton (iter-302). Sections + test IDs + open questions reserved. Normative bodies preview; final language pending PS review of `research/gamification-track/`. |
