# Gamification Track 05 — API Surface

**Status**: Draft (iter-300, 2026-05-21)
**Companion**: `01-design-rationale.md`, `02-metric-mapping.md`, `03-anti-gaming.md`, `04-rollout-gates.md`
**Tracking**: #267

---

## Purpose

Define the directory API extension required to expose ranks, badges, and leaderboards.
Constraint: **minimal surface** — no breaking changes, one new endpoint family, all reads
cacheable through the existing Cloudflare Cache Rule pattern (Cache-Control headers).

## Read-only public endpoints (cacheable, anonymous)

These return computed recognition state. All cacheable per existing Cache-Control discipline
(`s-maxage=120, stale-while-revalidate=60`).

### `GET /api/v1/operator/{handle}/profile`

```http
GET /api/v1/operator/mesh-warrior-42/profile

200 OK
Cache-Control: public, s-maxage=120, stale-while-revalidate=60
Content-Type: application/json

{
  "handle": "mesh-warrior-42",
  "operator_id": "base64url-pubkey-prefix...",
  "first_seen_at": "2026-05-30T12:00:00Z",
  "tenure_days": 145,
  "attestation_status": "attested",
  "attestation_method": "email",
  "rank": {
    "tier": 5,
    "title": "REACH Herald",
    "next_tier": 6,
    "next_tier_title": "Mesh Guardian",
    "progress": { "uptime_days": 67, "next_threshold_days": 90 }
  },
  "badges": [
    {"id": "first_blood", "earned_at": "2026-05-30T12:05:00Z"},
    {"id": "uptime_chad", "earned_at": "2026-07-29T00:00:00Z"},
    {"id": "model_hoarder", "earned_at": "2026-08-12T15:30:00Z"},
    {"id": "h2_2026_mesh_pioneer", "earned_at": "2026-10-15T00:00:00Z", "season": "H2-2026", "expires_after": null},
    {"id": "class_of_2026", "earned_at": "2026-06-01T00:00:00Z", "year": 2026, "expires_after": null}
  ],
  "leaderboard_positions": {
    "living_mesh_lords": 23,
    "regional_champions_DE": 1,
    "model_diversity_hall": 8,
    "reliability_top_50": 12
  },
  "nodes": [
    {"node_id": "uuid-1...", "region": "eu-central", "models": ["llama3.2:1b", "phi3:mini"]},
    {"node_id": "uuid-2...", "region": "eu-central", "models": ["qwen2.5:0.5b"]}
  ],
  "cohort": {
    "year_class": "Class of 2026",
    "founding_cohort": false
  }
}

404 Not Found  — handle not registered
410 Gone       — handle existed but operator opted out of public visibility
```

### `GET /api/v1/leaderboards/{board_id}`

```http
GET /api/v1/leaderboards/living_mesh_lords?limit=50&season=current

200 OK
Cache-Control: public, s-maxage=300, stale-while-revalidate=120
Content-Type: application/json

{
  "board_id": "living_mesh_lords",
  "title": "Living Mesh Lords",
  "season": "H2-2026",
  "computed_at": "2026-05-21T14:00:00Z",
  "next_recompute_at": "2026-05-21T14:30:00Z",
  "entries": [
    {
      "rank_position": 1,
      "handle": "operator-alpha",
      "operator_id_prefix": "AbCdEf...",
      "score": 98.42,
      "score_breakdown": {"uptime": 99, "throughput": 97, "diversity": 100, "cip": 100, "reach": 95},
      "rank_tier": 8,
      "rank_title": "Mesh Legend",
      "country": "DE"
    },
    ...
  ],
  "total_eligible": 247,
  "min_score_for_top_50": 73.5
}
```

**Board IDs**:
- `living_mesh_lords` — top 50 by composite score
- `rising_stars_30d` — fastest growth last 30 days
- `model_diversity_hall` — widest model offerings
- `most_reliable_60d` — best uptime + reachability over 60 days
- `regional_champions_{cc}` — top per country (uses ISO 3166-1 alpha-2)
- `founding_cohort` — permanent, alphabetical by handle
- `season_h{1|2}_{year}_top_50` — closed-season archives

### `GET /api/v1/badges`

```http
GET /api/v1/badges

200 OK
Cache-Control: public, max-age=86400  // badge catalog rarely changes
Content-Type: application/json

{
  "badges": [
    {
      "id": "first_blood",
      "title": "First Blood",
      "description": "Completed your first successfully routed task",
      "category": "core",
      "trigger": "tasks_completed_count >= 1",
      "tier_locked": false,
      "seasonal": false
    },
    {
      "id": "uptime_chad",
      "title": "Uptime Chad",
      "description": "99.5%+ heartbeat success rate over 60 days",
      "category": "core",
      "trigger": "heartbeat_success_rate_60d >= 0.995 AND active_days_60d >= 60",
      "tier_locked": false,
      "seasonal": false
    },
    {
      "id": "h2_2026_mesh_pioneer",
      "title": "H2 2026 Mesh Pioneer",
      "description": "Active node ≥30 days in the second half of 2026",
      "category": "season",
      "trigger": "active_days_in_season >= 30",
      "tier_locked": false,
      "seasonal": true,
      "season_id": "H2-2026",
      "season_start": "2026-07-01T00:00:00Z",
      "season_end": "2026-12-31T23:59:59Z",
      "expired_after_season": false
    },
    ...
  ]
}
```

### `GET /api/v1/seasons/current`

```http
GET /api/v1/seasons/current

200 OK
Cache-Control: public, max-age=3600

{
  "season_id": "H2-2026",
  "title": "H2 2026",
  "start": "2026-07-01T00:00:00Z",
  "end": "2026-12-31T23:59:59Z",
  "days_remaining": 73,
  "badges_available": ["h2_2026_mesh_pioneer", "h2_2026_diversity_champion", "h2_2026_reliability_top_10"],
  "operators_active_in_season": 247,
  "previous_season": "H1-2026",
  "next_season": "H1-2027",
  "next_season_starts_at": "2027-01-01T00:00:00Z"
}
```

## Authenticated write endpoints (operator-owned)

These require operator authentication (Ed25519 signature with `operator_id`'s private key,
per ADR-030).

### `POST /api/v1/operator/{handle}/visibility`

```http
POST /api/v1/operator/mesh-warrior-42/visibility
Authorization: Bearer <operator_jwt or signed_proof>
Content-Type: application/json

{
  "leaderboards_public": true,
  "profile_public": true,
  "handle_in_seasonal_archives": true
}

200 OK
{ "applied": true, "effective_at": "2026-05-21T14:05:00Z" }
```

### `POST /api/v1/operator/{handle}/handle`

Handle change (one-time, requires re-verification if attested).

```http
POST /api/v1/operator/mesh-warrior-42/handle
Authorization: Bearer <operator_jwt>
Content-Type: application/json

{ "new_handle": "danish-mesh-baron" }

200 OK
{ "old_handle": "mesh-warrior-42", "new_handle": "danish-mesh-baron", "effective_at": "..." }

409 Conflict — handle taken
422 Unprocessable Entity — handle violates squatting rules (reserved word, profanity, etc.)
```

---

## Internal computation endpoints (operator dashboard local-only)

Surfaced via the operator's own dashboard at `localhost:8080` (Rust node) — not exposed
publicly. The Rust node fetches its own recognition state from the directory and renders
inline.

### `GET /api/v1/operator/{handle}/private_summary`

Same content as `/profile` but includes:
- `next_rank_eta_days` (computed projection)
- `at_risk_badges` (e.g., uptime_chad at 99.4% — warn at 99.5% threshold)
- `season_progress_detail` (days remaining, current rank in season)
- `flagged_anti_gaming_signals` (sock-puppet heuristic hits — visible only to the operator
  so they can self-correct false-positives)

Requires operator key signature; rate-limited per operator (60/min — operator dashboard
is the only consumer, conservative limit).

---

## Schema implications

Three tables (or migrations to existing tables):

### `operators` (created in ADR-030)

```sql
operator_id        VARCHAR(64)  PK
pubkey             VARCHAR(128) NOT NULL  -- hex Ed25519 public key
handle             VARCHAR(48)  UNIQUE NOT NULL
attestation_status ENUM('pseudonymous', 'attested') DEFAULT 'pseudonymous'
attestation_method ENUM('email', 'did:web', 'github', ...) NULL
first_seen_at      TIMESTAMP
last_active_at     TIMESTAMP
leaderboards_public BOOLEAN DEFAULT true
profile_public     BOOLEAN DEFAULT true
```

### `recognition_badges_earned` (new)

```sql
operator_id        FK operators
badge_id           VARCHAR(48)
earned_at          TIMESTAMP
season_id          VARCHAR(16) NULL    -- for season-exclusive badges
year_class         INT NULL            -- for Class of YEAR
metadata           JSON NULL           -- e.g., country for Country Pioneer
PRIMARY KEY (operator_id, badge_id, season_id)
```

### `recognition_rank_progression` (new)

```sql
operator_id        FK operators
rank_tier          INT  -- 0..8
reached_at         TIMESTAMP
metric_snapshot    JSON  -- frozen evidence of qualifying state
PRIMARY KEY (operator_id, rank_tier)
```

### `node_operators` (created in ADR-030)

```sql
node_id            FK nodes
operator_id        FK operators
linked_at          TIMESTAMP
PRIMARY KEY (node_id)  -- one operator per node; many nodes per operator
```

Recompute jobs:
- **Per-event**: rank tier check on REGISTER, HEARTBEAT, CREDIT_AWARD events (cheap; only
  fires on event types that can trigger a tier-up)
- **Hourly**: leaderboard re-rank (composite score over 247 operators is sub-second)
- **Daily**: season-window aggregations (Class of YEAR, season-exclusive eligibility)
- **On season-close**: freeze season leaderboard archive into `recognition_season_archives`
  (computed once, never recomputed)

---

## OpenAPI fragment

Goes into the existing `directory/openapi.yaml` (or equivalent). One new tag, ~8 operations:

```yaml
tags:
  - name: recognition
    description: Operator recognition (gamification) — ranks, badges, leaderboards

paths:
  /operator/{handle}/profile:
    get:
      tags: [recognition]
      summary: Get operator public profile
      ...
  /leaderboards/{board_id}:
    get:
      tags: [recognition]
      summary: Get leaderboard
      ...
  /badges:
    get:
      tags: [recognition]
      summary: Badge catalog
      ...
  /seasons/current:
    get:
      tags: [recognition]
      summary: Current season info
      ...
  /operator/{handle}/visibility:
    post:
      tags: [recognition]
      security: [operator_signed: []]
      summary: Update visibility preferences
      ...
  /operator/{handle}/handle:
    post:
      tags: [recognition]
      security: [operator_signed: []]
      summary: Change handle (one-time, anti-squatting rules apply)
      ...
  /operator/{handle}/private_summary:
    get:
      tags: [recognition]
      security: [operator_signed: []]
      summary: Operator-only detailed state with projections + warnings
      ...
```

## Cache discipline

All public reads go through the existing Cloudflare Cache Rule pattern (the same rule
deployed for `/api/v1/discover`, `/api/v1/bootstrap`, `/api/v1/node/*`). Add to the rule:

```
(http.request.uri.path matches "^/api/v1/operator/[^/]+/profile$") or
(http.request.uri.path matches "^/api/v1/leaderboards/") or
(http.request.uri.path eq "/api/v1/badges") or
(http.request.uri.path eq "/api/v1/seasons/current")
```

All write endpoints (operator-authenticated) are explicitly `Cache-Control: no-store`.

## Rate limits

Following the existing throttle pattern in `directory/routes/api_protocol.php`:

- Public reads: `throttle:60,1` (60 req/min per IP) — same as discover
- Operator write endpoints: `throttle:operator-write,5,1` (5/min per operator_id)
- `private_summary`: `throttle:60,1` per operator (dashboard polling cadence-friendly)

## Conformance test IDs (for spec/conformance-test-suite.md)

| ID | Requirement | Level |
|---|---|---|
| RECOG-PROF-01 | `GET /v1/operator/{handle}/profile` returns 200 + valid schema | MUST |
| RECOG-PROF-02 | Returns 404 for unknown handle, 410 for opted-out | MUST |
| RECOG-LEAD-01 | `GET /v1/leaderboards/{board_id}` returns sorted entries | MUST |
| RECOG-BADG-01 | `GET /v1/badges` returns complete catalog with stable IDs | MUST |
| RECOG-SEAS-01 | `GET /v1/seasons/current` returns valid season window | MUST |
| RECOG-VIS-01 | `POST /v1/operator/{handle}/visibility` requires operator auth | MUST |
| RECOG-HAN-01 | Handle change blocks reserved words and squatting patterns | MUST |
| RECOG-PRIV-01 | `private_summary` requires operator auth, returns 401 otherwise | MUST |

REACH probes implementing these get added to `reach/src/reach/probes/recognition_conformance.py`
in the implementation phase.

---

## Summary

| Surface area | Endpoints | Tables | Cache rules added |
|---|---|---|---|
| Public reads | 4 | 0 new (reads from operators + earned tables) | 1 (extended) |
| Operator writes | 3 | 0 new | 0 (no-store) |
| Schema additions | — | 2 new (`recognition_badges_earned`, `recognition_rank_progression`) + 2 from ADR-030 (`operators`, `node_operators`) | — |
| Conformance tests | 8 new IDs | — | — |

The total API extension is **7 endpoints + 4 tables**, all in one new `recognition` tag.
Reuses existing auth (operator-signed = ADR-030), existing cache discipline (Cloudflare
Cache Rule), existing throttle middleware. Minimal in the sense the design rationale promised.

---

## Implementation order (post-gates)

When G1..G8 (rollout gates) are clear:

1. Schema migrations (`recognition_badges_earned`, `recognition_rank_progression`) — 1 commit
2. Background recompute jobs (per-event hooks + hourly + daily scheduler) — 2-3 commits
3. Read endpoints (4 public reads with cache headers) — 1 commit per endpoint family
4. Write endpoints (3 operator-authenticated) — 1 commit
5. OpenAPI documentation + conformance test IDs registered — 1 commit
6. REACH probes implementing RECOG-* tests — 1 commit
7. Operator dashboard inline rank/badge rendering in iicp-node — 1 commit

Estimated ~10 commits over 2 weeks once gates clear. Reasonable Phase 5D scope.

---

## End of research track

This is deliverable 5 of 5 (the temporal-cohorts addendum 06 was folded into 01-design-rationale.md
§7 + 02-metric-mapping.md temporal-cohorts section + 04-rollout-gates.md R4 phase). The
research track concludes.

Next steps (separate issues, not part of this track):
- Maintainer review of all 5 deliverables
- PS sign-off on ADR-030 (#269) — needed before G1 opens
- Draft of `spec/iicp-recognition.md` (G6 prerequisite — separate ARCS issue when authorized)
- File implementation tracking issue (Phase 5D scope, gated on G1..G8)
