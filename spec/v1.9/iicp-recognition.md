# IICP Operator Recognition Protocol

**Version**: 0.6.2-draft
**Status**: Draft — RECOG-* test IDs registered in `spec/conformance-test-suite.md §15`. API surface §7 + anti-gaming §8 normative. §3 Operator Identity composes on ADR-034 Identity Slot. **§5.4 Founder ordinals (time-gated tiers + lock-in + succession) added 2026-06-05 — parameters maintainer-RATIFIED** (Genesis-50/3mo · Founders-500/6mo · Founders-1000/12mo; transfer-with-signed-succession; rules R1–R7 from `research/gamification-track/08`, #461); the two new signed event types (`FOUNDER_LOCKIN`, `FOUNDER_SUCCESSION`) extend ADR-013 §3.4 and depend on the #458 hash-chain (landed). §12 open questions (seasons/handles/attestation) still carry proposed defaults — v1.0 graduation needs PS to ratify those + #310 directory implementation of §5.4.
**Date**: 2026-06-05 (updated from 2026-05-26)
**Changelog**: 0.6.0 — §5.4 reconciled to the **shipped** #310 lock-in detector (SPEC_UPDATE_PLAN Unit A, D5-A): keyed on `operator_pubkey` (not DID `identity_uri`); **genuine-served-node** gate (operator_verified + public_reachable + active + available) replaces the demand-scaled task-floor; **#1 reserved + 30-day-gate-exempt**; **GENESIS_MS = 2026-06-06** anchor named; FOUNDER_LOCKIN/SUCCESSION ride a **dedicated non-federated** signed chain (DIR-FED-16) with emission a tracked follow-up; §8 rule 8 + RECOG-FND-01/05/06 aligned; RECOG-FND IDs marked pending in conformance-suite. 0.5.0 — §5.4 Founder ordinals + §8 founder hard rules (8–12) + §10 RECOG-FND-01..06 (#309/#461, ratified tiers). 0.4.0 — §12 proposed defaults.
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

**`operator_id` is the operator's ed25519 public key (#464), not an opaque UUID** — i.e. the
same key the directory verifies and stores as `operator_pubkey` via the ADR-045 delegation. It
is therefore **cryptographically verifiable** (the operator proves control by signing; identity
mutations such as a `display_name` rename MUST be operator-signed) and **directory-private**:
public surfaces (node detail, leaderboards) expose only the public `display_name`, never
`operator_id`. The operator's `created_at` is self-attested and bound by
`operator_integrity_hash = SHA256(operator_id ":" created_at)`, which the directory pins on
first-use for tamper-detection; because a self-claimed `created_at` is backdatable, the
**directory-observed** timestamp (the `FOUNDER_LOCKIN` event the directory stamps, §5.4) — never
`created_at` — is authoritative for founder ordinals. `display_name` is the public, mutable
handle (also the community/leaderboard identity); `contact` is private.

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
| 2 | Local Daemon | ≥30 days **cumulative** verified uptime AND ≥1 declared model passing DIR-TRUST-01 | EVICT/REACTIVATE session pairs (#508) + DIR-TRUST-01 result |
| 3 | Intent Weaver | `reputation.completed_tasks_count ≥ 1000` AND ≥3 distinct proxy contributors | reputation + task_events (post G5) |
| 4 | CIP Provider | `cip_conformance_level = 'CIP-Provider'` AND attested operator (Tier 2 per ADR-030) | discover response + operators.attestation_status |
| 5 | REACH Herald | Probed reachable from ≥3 distinct REACH probe origins over 30d rolling | REACH multi-region (G3 dependency) |
| 6 | Mesh Guardian | ≥90 days **cumulative** verified uptime AND ≥99% heartbeat success AND continuous DIR-TRUST-01 pass | combined check (uptime from #508 session pairs) |
| 7 | Forge Baron | `completed_tasks_count ≥ 10000` AND ≥5 distinct models AND ≥3 contributors | reputation + capabilities |
| 8 | Mesh Legend | Top-10 globally by composite rank_score (§5) | hourly leaderboard recompute |
| Zero Kelvin | Permanent founder title | Manual assignment by Genesis Seed maintainer | n/a |

**MUST**: Rank ≥4 (CIP Provider) requires Tier 2 attestation (per ADR-030).
**MUST**: Rank ≥3 (Intent Weaver) requires ≥3 distinct proxy contributors (anti-collusion).
**MUST**: Rank ≥2 (Local Daemon) requires DIR-TRUST-01 pass (anti-fake-backend).
**MUST**: Uptime-duration gates (Tiers 1/2/6) are **cumulative**, not continuous: verified online
time is summed across sessions from the signed EVICT/REACTIVATE event pairs (#508,
`iicp-federated-directory.md` §5.1 uptime tracking events). Downtime never resets accumulated
uptime — it simply does not count. This is deliberate: home-hardware operators (reboots, sleep,
OS updates) accumulate rank progress at the same per-online-hour rate as cloud operators.
Heartbeat-success-rate components (Tier 1 ≥95%, Tier 6 ≥99%) are measured over online time only.

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

### 5.4 Founder ordinals (immutable, time-gated) — normative

Founder ordinals are the **immutable legacy** axis: a permanent, signed-log-provable record of
*who lifted the mesh from the depths*. They are distinct from the mutable ranks (§4) and from
seasonal/yearly badges (§5.2/§5.3). Design + adversarial review: `research/gamification-track/06`,
`07`, and `08` (the anti-gaming re-analysis under the ratified tiers, #461). The maintainer ratified
the parameters below on 2026-06-05.

**5.4.1 Keyed to the cryptographic operator identity, never node_id.** A founder ordinal is bound to the
operator's **active `operator_pubkey`** — the ed25519 operator key (== `operator_id`, #464; §3) that the
directory verifies via the ADR-045 register delegation — not to any node. (This supersedes the earlier
DID `identity_uri` framing for founder keying: the shipped lock-in detector keys on `operator_pubkey`,
which is what reaches the directory.) Nodes are fungible; dev/test churn **MUST** be purged from the
genesis snapshot and **MUST NOT** count toward any ordinal (§8 rule 1, R3).

**Normal key rotation is the sole continuity exception.** A directory MAY move an ordinal to a successor
operator key only after a single-use challenge and proofs of control from both the old and new keys.
The old identity becomes ineligible for new claims; the successor inherits the ordinal exactly once; the
transfer MUST be represented as `FOUNDER_SUCCESSION` on the recognition chain when that anchor is
available. A lost or compromised key MUST NOT receive automatic continuity transfer.

**5.4.2 Earned by serving — provisional → locked (as shipped).** An ordinal is **provisional** at first
appearance and **locks in** when the directory's daily lock-in detector finds the operator has completed:
- **≥ 30 days** since the directory-observed `first_seen_ms` (heartbeat-challenge-verified healthy
  operation, ADR-047 / #411) — the *primary* gate; **and**
- a **genuine served node** — ≥ 1 node bound to this operator that is `operator_verified` (ADR-045
  delegation), `public_reachable` (#326), `active`, and `available`. This unforgeable "real,
  publicly-reachable, verified, live node" check is the as-shipped substitute for a raw task count.

This is rule **R1** (`08`): lock-in is uptime-primary so the earliest founders — who by definition face
the *least* demand — are not locked out by a demand gap they exist to close (caveat N1). A provisional
slot that never locks in is **reclaimable** and holds no number.

**No-reset semantics (normative, as shipped).** The 30-day gate is **calendar-anchored**: it measures
elapsed time since the pinned `first_seen_ms` (`now_ms − first_seen_ms ≥ 30d`), which is set once at
the operator's first registration and **never reset** — not by re-registration, dormancy, reboots, or
outages. The "genuine served node" condition is evaluated by the daily lock-in scan over a **trailing
24-hour window**, not at the scan instant: a node qualifies if it is currently active+available OR its
authenticated `last_seen` falls within the 24 hours before the scan (so a node that sleeps or reboots
at the scan hour — e.g. nightly Windows updates — still counts as serving, provided it heartbeat at any
point that day). An operator whose nodes were offline for the entire window is simply re-evaluated at
the next daily scan, with no penalty and no clock restart. Consequence for self-hosters (home hardware,
Windows/WSL2, sleep/update cycles): downtime **cannot** delay lock-in by more than the downtime itself
plus at most one scan interval. Tier membership (§5.4.3) is computed on the lock-in timestamp against
generous windows (3/6/12 months), so scan-day slippage does not move an operator across tier boundaries
in practice. Implementations MUST NOT impose a continuous-uptime or uptime-percentage requirement on
founder lock-in.

**Founder #1 is reserved** for the maintainer's configured `operator_pubkey` (`iicp_founder_one_pubkey`)
and is minted **immediately, exempt from the 30-day gate** (founder privilege — the genesis operator
lifted the mesh from nothing). Ordinals #2…N obey the gate above, assigned in **first-appearance order**
(`first_seen_ms`).

**GENESIS_MS anchor.** All tier windows (§5.4.3) are measured from the ratified founder-era anchor
**`GENESIS_MS = 1780704000000` (2026-06-06T00:00:00Z)**. It is **permanent** — changing it would
re-tier immutable assignments.

**5.4.3 Ordinal assignment + tiers (window measured on lock-in).** The ordinal `N` = the Nth identity
to **lock in**, ordered by `FOUNDER_LOCKIN` event `seq` (first-REGISTER `seq` breaks ties). Because
provisional/never-locked registrations hold no number, reclaiming one **renumbers nobody** (caveat N4).
Tier membership is computed over the **lock-in timestamp**, not registration (rule **R2**) — serving
cannot be backdated (heartbeat-challenge is live), so a late registrant can never retroactively claim an
earlier tier.

| Tier | Ordinal range | Time window (on lock-in) | Notes |
|------|---------------|--------------------------|-------|
| **Genesis-50** | 1–50 | within **3 months** of genesis | contains the inner pure-ordinal sub-brackets below |
| **Founders-500** | 51–500 | within **6 months** | |
| **Founders-1000** | 501–1000 | within **12 months** | final founder close |

Inside Genesis-50, pure-ordinal **sub-brackets** confer finer prestige: **First 10** (1–10), **First 20**
(11–20), **First 30** (21–30), **First 50** (31–50). **MUST: single-best** — an operator holds **only**
the tightest bracket they qualify for (operator #5 is *First Ten*, not also First 20 / Genesis-50 /
Founders-500). Implementation: `bracket = first threshold ≥ N`.

- **MUST**: a tier requires *both* its ordinal cap *and* its lock-in time window.
- **MUST**: under-fill is valid — if fewer than a tier's cap lock in within its window, the tier is
  simply smaller (scarcity reflecting reality, not an error).
- **MUST**: ordinals and tiers, once assigned (locked), are **immutable** — never re-minted, re-numbered,
  or back-dated.

**5.4.4 Era multiplier — legacy-axis only (R4).** An early-era contribution multiplier MAY weight the
legacy axis (`rank_score` legacy component / ordinal narrative), but **MUST NOT** gate the *mutable*
ranks of §4 — a newcomer MUST still be able to reach the top merit rank on current contribution. The
multiplier **MUST** decay smoothly to ×1.0 on a **published** curve.

**5.4.5 Transferability — provenance immutable, current-holder transferable (R6).** Founder recognition
splits into:
- **Immutable provenance**: the signed log records *who earned* each ordinal. The original earner
  (e.g. genesis operator = founder #1) is recorded **forever** and is never erasable or transferable.
- **Transferable current-holder**: the current holder MAY transfer an *already-locked* ordinal via an
  explicit, identity-signed `FOUNDER_SUCCESSION` event (§5.4.6). **MUST**: succession records the full
  holder **lineage** (genesis earner → … → current) so a buyer is honestly provenanced as
  "current holder, acquired from <earner>"; **MUST**: succession does **not** reset lock-in and **MUST
  NOT** re-open a closed tier; wash-transfers are therefore publicly visible, not hidden. A covert
  off-record private-key sale still passes *control* (inherent to key identity, caveat N-C1) — accepted;
  the protocol protects *provenance*, not control.

**5.4.6 Signed event types (seed-authoritative).** Two new signed event types, emitted **only by the
directory** (DIRECTORY-AUTHORITATIVE), each carrying a per-event Ed25519 signature + `prev_hash` chain
link as §3.4 defines. **They ride a *dedicated, non-federated* signed chain — NOT the federated
`node_events` stream.** Rationale: the federated event set is closed (S.13 `DIR-FED-16` =
`{REGISTER, DEREGISTER, CREDIT_AWARD, REPLICA_REGISTERED, REPUTATION_DECAY, OPERATOR_OBSERVED}`), and
`GET /v1/events` returns all node-events, so emitting founder events there would both violate the closed
list and leak operator references to every replica. **Implementation status:** the shipped detector
persists the immutable `ordinal`/`tier`/`badge` to the authoritative `operators` table (which the
leaderboard serves); the signed-event anchor on the dedicated chain is a **tracked follow-up** (due
before the first external #2 locks in). Payloads are keyed by `operator_pubkey` (never `node_id`):

| Event | Payload (canonical) | Emitted when |
|-------|---------------------|--------------|
| `FOUNDER_LOCKIN` | `{ operator_pubkey, ordinal, tier, badge, locked_at_ms }` | an operator meets the §5.4.2 lock-in conditions (or is the reserved #1); assigns the immutable ordinal |
| `FOUNDER_SUCCESSION` | `{ ordinal, from_operator_pubkey, to_operator_pubkey, succeeded_at_ms }` | the current holder signs a transfer of an already-locked ordinal |

**5.4.7 Canonicality (R7).** Founder ordinals are canonical **only** against the Genesis Seed's signed,
externally-anchored event log (the genesis snapshot root is the chain's anchor block, ADR-013 / `06` §8).
A federated replica **MUST** serve only *derived, verifiable* copies; a replica whose recognition state
diverges from the genesis chain **MUST** raise an alarm (federation cross-check). The directory computes,
verifies, persists, and serves ordinals/tiers; a client (`iicp-node badges --verify`) is an **independent
cross-check**, never the source of truth.

## 6. Leaderboards

Public views of recognition state. Cacheable, anonymous-read.

| Board ID | Title | Order | Window |
|----------|-------|-------|--------|
| `founders` | Founding Cohort | founder ordinal ASC (§5.4) | cumulative |
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

**Implementation status (#310/#463):** `GET /v1/leaderboards/founders` is live (directory PHP + Rust parity) — it reads the operator-keyed record and returns `{board_id, title, count, entries:[{place, display_name, ordinal, tier, badge}]}`, never exposing `operator_pubkey`. Boards ordered by the §5 composite `rank_score` (`living_mesh_lords`, `rising_stars_30d`, `most_reliable_60d`) return `404 IICP-E050` until `rank_score` is computed — they are not fabricated. Visibility opt-out exclusion activates when the visibility column/endpoint lands (no operator can opt out yet).

**Provisional founders — `pending` section (0.6.2, additive).** The founders board response
additionally carries `pending: [{display_name, projected_ordinal, days_remaining, provisional: true}]` —
the §5.4.2 *provisional* state made publicly visible. Inclusion requires a **genuine served node**
(same unforgeable gate as lock-in: `operator_verified` + `public_reachable` + active/available or seen
within the trailing 24h), so registering an identity without serving (name-squatting) does NOT appear.
Ordering is first-appearance (`first_seen_ms`); `days_remaining = ceil((30d − elapsed)/1d)`, with `0`
meaning "eligible at the next daily scan". **Normative constraints**: `projected_ordinal` is an
ESTIMATE and MUST be presented as provisional (ordinals are assigned only at lock-in, §5.4.3 — the
projection shifts if a predecessor drops out or a lapsed predecessor returns); a `pending` entry
confers no rights, is never recorded to the signed chain, and MUST NOT be treated as an assigned
ordinal by any consumer. Purpose: recognition-before-lock-in and a visible race for the next low
ordinal (maintainer directive 2026-06-10).

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
| POST | `/v1/operator/rename` | operator-signed (ed25519, #460) | no-store |

**`POST /v1/operator/rename`** (#460/#463) — change the public, mutable `display_name` (the
universal handle on node detail + leaderboard) without re-registering nodes. Body:
`{ operator_pub, display_name, ts, sig }` where `sig` is the operator's ed25519 signature over
the canonical bytes `json({display_name, operator_pub, ts})` (alphabetical keys, no whitespace,
slashes/unicode unescaped). The directory verifies the signature against `operator_pub`
(== `operator_id`, #464 — proves key-control), rejects a `ts` outside ±300 s (replay), and
updates the single operator-keyed record (reflected on every node + the leaderboard). The
active `operator_id` and any earned founder ordinal stay bound to the key; only the floating
`display_name` changes. The separately defined dual-key rotation flow may transfer the active identity
and its continuity under §5.4.1; rename itself never performs that transfer.

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

Founder-ordinal hard rules (§5.4; sourced from `research/gamification-track/08`, R1–R7):
8. **MUST** (R1/R2): a founder ordinal (≥#2) locks in only after ≥30 **calendar** days since the pinned
   `first_seen_ms` (no-reset semantics, §5.4.2 — the clock never restarts on outage/re-registration)
   **plus** a **genuine served node** at the daily scan (operator_verified + public_reachable + active +
   available, §5.4.2 — a point-in-time check, NOT a continuity requirement); tier membership is computed
   on the **lock-in timestamp** (never registration), and the ordinal is assigned at lock-in
   (first-appearance order) so reclaiming a provisional slot renumbers no one. **#1 is the reserved
   genesis founder** (configured `operator_pubkey`), minted immediately and exempt from the 30-day gate.
9. **MUST** (R6): a `FOUNDER_SUCCESSION` transfer preserves the immutable provenance lineage, does not
   reset lock-in, and cannot re-open a closed tier; the original earner is recorded permanently.
10. **MUST** (R7): founder ordinals are canonical only against the Genesis Seed's signed,
    externally-anchored hash-chained log (#458); a replica diverging from the genesis chain raises an
    alarm. Recognition state is directory-computed; a client is an independent cross-check, not the source.
11. **MUST** (R4): the early-era multiplier weights only the immutable legacy axis and MUST NOT gate the
    mutable ranks of §4; it decays to ×1.0 on a published curve.
12. **MUST** (R5): the renewable recognition engines (seasons §5.2, regional/yearly §5.3, the climbable
    merit ladder §4) MUST be live and visible before the Founders-1000 (12-month) close, so growth has an
    engine after the founder window shuts.

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
| RECOG-FND-01 | Founder ordinal #2+ assigned only after ≥30d healthy + a genuine served node (operator_verified + public_reachable + active + available); #1 reserved + gate-exempt; provisional slots hold no number | MUST |
| RECOG-FND-02 | Tier (Genesis-50/3mo, Founders-500/6mo, Founders-1000/12mo) computed on lock-in timestamp; single-best bracket returned | MUST |
| RECOG-FND-03 | Ordinals are immutable once locked; reclaiming a provisional slot renumbers no locked founder | MUST |
| RECOG-FND-04 | `FOUNDER_SUCCESSION` preserves provenance lineage, does not reset lock-in, cannot re-open a closed tier | MUST |
| RECOG-FND-05 | Founder ordinal keyed to `operator_pubkey` (ed25519 operator_id), never node_id; dev/test identities purged | MUST |
| RECOG-FND-06 | `FOUNDER_LOCKIN` / `FOUNDER_SUCCESSION` events carry valid Ed25519 sig + `prev_hash` on a dedicated non-federated chain (NOT `node_events`, per DIR-FED-16); emission is a tracked follow-up | MUST |

The base RECOG-* IDs are registered in `spec/conformance-test-suite.md §15`; the founder
**RECOG-FND-01..06** IDs are **pending registration** there (tracked — to be added in the
conformance-suite update that accompanies this v0.6.0 reconciliation). REACH probes implementing these
tests will be added to `reach/src/reach/probes/recognition_conformance.py` once G1+G6 gates clear.

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
| 0.6.2-draft | 2026-06-10 | §6 founders board: additive `pending` section — provisional operators (genuine served node, no ordinal) with projected_ordinal (estimate, never authoritative), days_remaining, first-appearance order; anti-squat gate; never on the signed chain. Recognition-before-lock-in + visible ordinal race (maintainer directive). PHP+Rust+website shipped. |
| 0.6.1-draft | 2026-06-10 | **Self-hoster fairness clarifications** (external operator feedback): §5.4.2 gains explicit **no-reset semantics** — the 30-day founder gate is calendar-anchored to the pinned `first_seen_ms` (never resets on outage/reboot/re-registration) and the genuine-served-node condition is a point-in-time daily-scan check, never a continuity or uptime-% requirement (matches the shipped PHP+Rust detector). §8 rule 8 reworded to match. §4.1 Tiers 2/6 uptime gates changed from "continuous" to **cumulative** verified uptime, sourced from the #508 EVICT/REACTIVATE signed session pairs; new §4.1 MUST: downtime never resets accumulated uptime. Aligns spec text with the as-shipped implementation so cloud and home-hardware operators accrue recognition at the same per-online-hour rate. |
| 0.4.0-draft | 2026-05-26 | §12 reformatted: every open question (1, 2, 4-7) now carries a **proposed default** with rationale and an explicit "to override" path for PS. New §12b "Status of v1.0 graduation" table tracks per-question PS-confirmation status. v1.0 unblocks when PS confirms/overrides each row (vs previous "needs full design" framing — now ratification-bounded work). Resolves the spec-graduation-path ambiguity from v0.3.0; PS review surface reduces from "design 6 things" to "confirm 6 defaults". |
| 0.3.0-draft | 2026-05-26 | §3 Operator Identity restructured with layered identity model (Recognition → ADR-030 Operator → ADR-034 Identity Slot → did:web verifier); cross-references S.15 (`spec/iicp-identity-slot.md`) + BC-12. §7 API surface clarifies "operator-signed" means S.15 Identity Slot with verifier dispatch + IICP-IDSLOT-02/04 failure modes. §8 anti-gaming rule 5 (no identity laundering) now cites ADR-034 pin-on-first-use as enforcement mechanism. §12 open question 3 (Operator vs Identity Slot — composed or absorbed?) **resolved**: composed; Identity Slot is foundation. Tracking issue #309 referenced. Resolves 1 of 7 §12 open questions; remaining 6 (1, 2, 4-7) still need PS review before v1.0. |
| 0.2.0-draft | 2026-05-24 | RECOG-* test IDs registered in `spec/conformance-test-suite.md §15` (v4.35.0, iter-976). §10 note updated to reflect cross-spec registration. Status updated to reflect normative bodies in §4/§5/§6/§8/§9 complete; pending PS ratification of §12 open questions before v1.0. |
| 0.1.0-draft | 2026-05-21 | Initial skeleton (iter-302). Sections + test IDs + open questions reserved. Normative bodies preview; final language pending PS review of `research/gamification-track/`. |
