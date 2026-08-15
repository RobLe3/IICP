# Gamification Track 04 — Rollout Gates

**Status**: Draft research record (2026-05-21)
**Companion**: `01-design-rationale.md`, `02-metric-mapping.md`, `03-anti-gaming.md`
**Tracking**: no active protocol implementation issue

---

## Purpose

Define the explicit conditions under which the recognition framework is **safe to
ship**. Gates are sequenced: a gate cannot open until all prior gates open. The maintainer is
the sole authority on each gate decision; this document specifies the *evidence* required for
disposition, not the disposition itself.

## Gate stack

Eight gates in order. Each gate is independently observable / verifiable so the maintainer
can disposition without re-investigating prior gates.

### Gate G1 — Identity layer in place

**Required artifact**: a reviewed public operator-identity and anti-Sybil
decision, with its implementation released by the directory owner.

**Evidence**:
- the public decision has accepted status and testable acceptance criteria
- `directory/database/migrations/...operators` migration applied to production
- `POST /v1/operator` returning 201 in live API
- ≥1 attested operator visible via `GET /v1/operator/{handle}/profile`
- DIR-OP-01..08 conformance tests added to REACH

**Why**: Without operator identity, every sock-puppet attack from deliverable 03 succeeds.
Shipping gamification before identity = leaderboards full of phantom operators.

### Gate G2 — Public-launch decision resolved

**Required artifact**: a public launch decision that either:
- Documents the path to public launch with concrete completion criteria, AND those criteria
  are met, OR
- Explicitly documents indefinite closed-beta posture with maintainer rationale (in which
  case gamification rollout is restricted to invited operators only, per Gate G4).

**Evidence**:
- The decision exists in a public operator-facing artifact and is approved by the maintainer
- If "public" path: all checklist items in gate doc are ✅
- If "indefinite closed-beta" path: rationale documented + Gate G4 adjusted

**Why**: Public leaderboards of a closed-invite mesh are weird. Either the network is open
(leaderboards have meaning to outside visitors) or it's gated (leaderboards are an internal
operator tool, not a recruiting amplifier).

### Gate G3 — REACH probe geographic expansion

**Required artifact**: ≥3 distinct probe origins (REACH-EU, REACH-NA, REACH-AS, etc.)
running against production with consistent test cadence.

**Evidence**:
- `/api/v1/stats` exposes per-region probe results
- REACH Herald and Global Node badges from deliverable 02 (currently flagged "partial"
  because only 1 probe location exists) become computable
- Three months of stable multi-region probe data accumulated

**Why**: Geographic-diversity badges are central to the framework. Without multi-region
probing, "Global Node" cannot be earned, and "Diversity Champion" regional tiers cannot
be computed honestly.

### Gate G4 — Minimum external operator threshold

**Required**: ≥10 attested external operators (Tier 2, per ADR-030), distinct from the
IICP working group.

**Evidence**:
- `SELECT COUNT(DISTINCT operator_id) FROM operators WHERE attestation_status='attested' AND operator_id != 'genesis-cohort' ≥ 10`
- A public, content-free operator-count snapshot confirms the threshold

**Why**: Gamifying a single-operator-group mesh is embarrassing. Leaderboards work as a
recruiting tool only when there's a non-trivial population to compete in. The 10-operator
threshold is chosen because it allows:
- A meaningful "top 10" list
- Country pioneers across at least 5 countries (assuming 50% geographic spread)
- Sufficient sample to validate the anti-Sybil heuristics on real data

If closed-beta path was chosen at G2, this threshold can be relaxed to "≥10 invited
operators" — but they still must be distinct from each other (W-016 sock-puppet check
applies regardless of public/private posture).

### Gate G5 — Telemetry extensions ready

**Required**: All "partial" items from deliverable 02 are resolved.

**Evidence**:
- `reputation.first_task_at` column populated (required for Class of YEAR)
- `task_events` table or equivalent per-task records (required for OpenAI Whisperer, Mesh
  Multiplier, Reliable One)
- Region → country lookup table maintained (required for Country Pioneer)
- Model-family classification rules in `spec/iicp-model-families.md` or similar (required
  for Chaos Agent)
- User-Agent capture on REGISTER (required for Rust Enjoyer)
- `mesh_milestones` table seeded with historical markers (required for Early Meshborn)
- `mesh_disruptions` table or maintainer-annotated incident log (required for Reliable One)

**Why**: Don't ship a badge that can't be earned. Every promised badge MUST have a working
computation backing it before launch — otherwise operators lose trust in the system.

### Gate G6 — Spec normative and conformance-tested

**Required artifact**: `spec/iicp-recognition.md` at version ≥ 1.0, with conformance test
IDs registered in `spec/conformance-test-suite.md`.

**Evidence**:
- `spec/iicp-recognition.md` exists, includes normative MUST/SHOULD for: rank thresholds,
  badge eligibility computation, season-window definitions, anti-gaming rules from
  deliverable 03 (the 6 hard rules)
- `RECOG-RANK-01..08`, `RECOG-BADGE-NN`, `RECOG-SEASON-01..02` conformance test IDs registered
- REACH probes implementing the conformance tests added to `reach/src/reach/probes/`

**Why**: Recognition is a permanent identity layer; getting it wrong is expensive to undo.
Normative spec prevents drift between client implementations and the directory.

### Gate G7 — Privacy & moderation policy

**Required artifact**: public recognition privacy and moderation policies.

**Evidence**:
- Privacy policy covers: data retained, what's public, how operators opt out of leaderboards,
  rotation effects, deletion-on-request handling
- Moderation policy covers: handle-squatting rules, flag-and-exclude vs. ban, appeals process,
  who decides edge cases (maintainer? community?)
- Policies cross-referenced from the operator-facing UI (registration flow shows opt-in /
  opt-out for leaderboard visibility)

**Why**: Public recognition is privacy-sensitive. Operators must consent informedly.
Moderation must be predictable so operators don't fear arbitrary deplatforming.

### Gate G8 — Founding Cohort migration plan

**Required artifact**: a public founding-cohort migration policy.

**Evidence**:
- Lists the existing 8 active nodes' `operator_id` assignments (Genesis Cohort)
- Documents the cutoff date for Founding Cohort membership
- Specifies how pre-launch maintainer-only nodes are visible (or hidden) in launch leaderboards
- Defines the "Zero Kelvin" permanent founder title assignment

**Why**: Day-zero recognition state shapes early operator perception. If pre-launch nodes
dominate Day-1 leaderboards by accumulated history, new operators see "no chance of climbing"
and leave. The Founding Cohort migration explicitly addresses this by either separating
pre-launch nodes (own cohort tier) or zeroing their leaderboard contributions while preserving
their badges.

---

## Gate disposition matrix

| Gate | Owner | Disposition trigger | Status check |
|---|---|---|---|
| G1 Identity | protocol and directory owners | Identity decision accepted + schema migrated | public decision status plus released schema evidence |
| G2 Public-launch | Maintainer | Public launch decision approved | public decision plus maintainer approval |
| G3 REACH multi-region | Maintainer + ops | ≥3 probe regions live for ≥90d | `/api/v1/stats` exposes ≥3 region keys |
| G4 External operators | Auto-observed | ≥10 attested distinct operators | `gh issue view 269` comment with operator count snapshot |
| G5 Telemetry | implementation owners | All deliverable-02 partial items resolved | released schema and migration evidence |
| G6 Spec + conformance | protocol owner | `spec/iicp-recognition.md` v ≥ 1.0 + probes registered | public release tag and conformance evidence |
| G7 Policies | Maintainer | Both policies published | stable public policy URLs |
| G8 Founding Cohort | Maintainer | Migration plan published | stable public policy URL |

---

## Rollout schedule (post-gates)

Once all 8 gates open, ship in 4 staged phases over ~6 weeks:

### Phase R1 — Quiet launch (Week 1-2)

- Ranks visible on `/operator/{handle}/profile` (private to operator only)
- No public leaderboards yet
- No badges earned automatically — operators opt in to enable recognition
- Goal: validate the back-end on real data without UI pressure

### Phase R2 — Internal cohort (Week 2-3)

- Public leaderboards visible only to authenticated operators (logged into iicp.network)
- Founding Cohort members visible across the leaderboards
- Goal: stress-test the leaderboard queries; gather operator feedback before public launch
- Anti-pattern guard: this is NOT a closed-beta extension; it's a 1-week internal stress test

### Phase R3 — Public launch (Week 3-4)

- `/registry` and `/stats` pages add inline rank/badge displays
- Public Wall of Fame goes live
- First season (likely H1 or H2 of current year, depending on launch date) starts at the
  end of this phase
- Recruiting flywheel begins: visitors see operators with names, ranks, regions

### Phase R4 — First season close + retrospective (Week 4-6)

- Season closes per schedule
- Season-exclusive badges minted
- Retrospective doc: what worked, what didn't, who gamed (and how detected)
- Adjust rules for Season 2 based on real adversarial data

---

## Failure modes & rollback

If any gate is found to have been opened prematurely, the rollout halts at the current
phase. Specifically:

- **G1 identity layer compromised** (e.g., Ed25519 implementation bug exposed): rotate all
  operator keys; pause Tier 2 attestation acceptance; do not roll back identity layer itself.
- **G4 sock-puppet inflation detected post-launch**: freeze affected leaderboards; investigate;
  apply flag-and-exclude per deliverable 03; do not delete legitimate operators' data.
- **G7 privacy incident**: notify affected operators per policy; pause public leaderboard
  visibility until incident resolved; investigate root cause.

Rollback to "no gamification" is always available but expensive (operator expectations).
Prefer narrow halts (specific badge disabled, season paused) over full rollback.

---

## Cross-references

- `01-design-rationale.md` — principle (earn-by-existing, multi-axis identity)
- `02-metric-mapping.md` — telemetry-readiness verification (16/23 fully computable, 7 partial)
- `03-anti-gaming.md` — threat model + 6 hard normative rules + operator identity as central mitigation
- [`iicp-identity-slot.md`](../../spec/v1.9/iicp-identity-slot.md) — public identity boundary
- [`iicp-recognition.md`](../../spec/v1.9/iicp-recognition.md) — public recognition semantics
- [`privacy-adversary-and-trust-model.md`](../../docs/security/privacy-adversary-and-trust-model.md) — public threat boundary

---

## Next deliverable

`05-api-surface.md` — concrete directory API extension required: endpoint shapes, request /
response schemas, authentication, rate limits, OpenAPI fragments. Keep minimal: the goal is
one new endpoint family, no schema rewrites.
