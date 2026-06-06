# 06 — Recognition Design: ranks, alignment, and legacy

**Status:** design proposal (maintainer-directed, 2026-06-05). Feeds the `iicp-recognition.md`
spec (#309) and the #310 implementation. Builds on 01–05 + ADR-030 (identity tiers).

**Maintainer brief (2026-06-05):**
1. Build now; ranks in the spirit of a **"Founders Circle"** with **slight Rebel-Alliance**
   references; research the right *number* of ranks, promotion/demotion, and the blend of
   **"nerdy vs business-acceptable."**
3. An **alignment mechanism** that rewards both those who *lift IICP out of obscurity* (early
   growth) and those who *keep it what it is* (long-term stewards).
4. A **durable legacy**: drives adoption now, and in ~10 years lets newcomers see who built
   IICP "from the depths of the internet to a commodity."

---

## 1. Tone — "nerdy vs business-acceptable"

Design rule: **a rank must read fine on a company's "we operate IICP infrastructure" page,
and still make an insider smile.** The existing draft names (`Uptime Chad`, `Model Hoarder`)
are too memey for the rank ladder. Resolution:

- **Ranks = business-clean** (a CTO can put "Vanguard operator, IICP mesh" on a slide).
- **Badges = where the nerd lives** (optional flair, opt-in display) — that's where the
  Rebel-Alliance Easter eggs and the playful names go, so they never block business adoption.
- **Subtlety over cosplay:** the Rebel-Alliance thread is *thematic* (a decentralized mesh
  is the scrappy alliance vs centralized Big-Inference), surfaced through one or two names —
  not a Star Wars skin.

## 2. The two axes (why one ladder isn't enough)

Per 01's anti-Goodhart principle, recognition is **multi-axis** and a *side-effect of operating
well* — never a separate grind. Two distinct things deserve recognition:

- **Merit (mutable):** how much useful capacity you're contributing *right now* — climbs and
  falls. This is the rank ladder.
- **Legacy (immutable):** *when* you showed up and *how long* you've stewarded — never falls.
  This is the Founders Circle + cohort/tenure track.

## 3. Merit ladder (mutable, promote/demote) — 6 ranks

Research note on count: 5–7 is the engagement sweet spot (Duolingo leagues=10 feels grindy;
GitHub has none; SO's are too many). The draft's 8 is slightly long — **6** gives a visible
climb without diluting each step. Names are business-clean with one subtle Alliance nod
(`Vanguard`):

| # | Rank | Earn (starting recipe — tune in 02) | Tier (ADR-030) |
|---|------|-------------------------------------|----------------|
| 1 | **Initiate** | registered, ≥1 successful task served | Tier 1 (pseudonymous OK) |
| 2 | **Operator** | ≥100 tasks · ≥7d uptime · reputation ≥ Bronze | Tier 1 |
| 3 | **Provider** | CIP-Provider conformance · ≥1k tasks · reputation ≥ Silver | **Tier 2 (attested)** |
| 4 | **Sustainer** | ≥90d sustained healthy uptime · reputation ≥ Gold | Tier 2 |
| 5 | **Vanguard** | top ~10% by era-weighted contribution · Platinum | Tier 2 |
| 6 | **Luminary** | top ~10 globally by composite (the old "Mesh Legend") | Tier 2 |

Attestation gate (ADR-030): ranks ≥ **Provider** require Tier-2 attestation, so the prestige
ranks can't be sock-puppeted.

### Promotion / demotion mechanics (research)

- **Promotion** on a **7-day sustained** crossing of a threshold (not a single good hour).
- **Demotion is slow + asymmetric** (the key UX finding): use **hysteresis** — promote at
  threshold `T`, demote only below `T − margin` *and* sustained ≥14 days. Prevents rank
  "flapping" that kills motivation. Reputation decay (λ=0.005/hr, floor 0.30) already feeds
  this; rank reads a smoothed 7/14-day contribution signal, not the instantaneous score.
- **One-rank-at-a-time** demotion (never drop two tiers in one step).
- **Grace on outage:** a planned/short outage inside the SLA window doesn't demote (ties to
  the heartbeat-challenge liveness signal, #411).
- **Legacy ranks never demote** (§5).

## 4. Alignment mechanism — early growth × long-term stewardship

The brief's tension: reward those who *lift IICP from obscurity* **and** those who *keep it*.
Three levers, all anti-Sybil by construction:

1. **Era-weighting (rewards lifting-from-the-depths).** A contribution made when the mesh was
   small counts more. Define an **era multiplier** `w(t) = 1 + k · clamp(1 − active_nodes(t)/N₀, 0, 1)`
   (e.g. N₀=500, k=2 → a task served at 10 nodes is worth ~3×, at 500+ nodes worth 1×). Early
   operators climb the era-weighted ranks (Vanguard) faster *because their help mattered more
   when it was scarce*. The weight is computed from the **signed event log** (active_nodes at
   the event's `ts_ms`), so it's auditable and not back-datable.
2. **Tenure-compounding stewardship (rewards keeping-it).** A separate, **non-resetting**
   stewardship score accrues with sustained healthy operation: `steward += days_healthy`, with
   a mild compounding bonus for unbroken multi-year tenure. This is what makes a 5-year quiet
   reliable operator outrank a flashy newcomer on the *legacy* axis even if merit is equal.
3. **Side-effect-of-real-work (the alignment guarantee).** Both levers read only
   directory-observed, mesh-health-correlated signals (tasks served, uptime, quality tier,
   relay-hosting for CGNAT peers) — never a grindable vanity metric. **What's good for your
   standing is exactly what's good for the mesh.** Operator-diversity recognition requires
   Tier-2 attestation (ADR-030 §Tier 2), so it can't be farmed.

> Anti-gaming detail lives in 03; this section only adds the era-multiplier (new) and the
> stewardship accumulator (new) — both must pass 03's sock-puppet review before ship.

## 5. Legacy — the 10-year "built it from the depths" credential

The durable payoff. Design goals: **drive adoption now** (scarcity/urgency) and be **provable
and meaningful in a decade** (when IICP is, hopefully, a commodity).

- **Pioneer ordinals — the rarest tier (maintainer-directed 2026-06-05):** ultra-scarce
  badges for the **first 10 / 20 / 30 / 50** members in the *whole mesh*, anchored by
  **registration order**. The signed event log assigns every REGISTER a strictly-monotonic
  `seq` (ADR-013), so "mesh member #7" is an **objective, cryptographically-verifiable fact**
  forever — there is exactly one #1, and the brackets can never be re-minted or back-dated.
  - **One unified ordinal ladder, 8 brackets** (maintainer 2026-06-05): **First 10** (members
    1–10), **First 20** (11–20), **First 30** (21–30), **First 50** (31–50), **First 100**
    (51–100), **First 200** (101–200), **First 300** (201–300), **First 500 / Founders Circle**
    (301–500). Member 501+ → no ordinal badge, just the additive "Class of YYYY" cohort.
  - **Single best badge — you hold exactly ONE.** A member displays only the **tightest
    bracket they made**, never the wider ones it implies. Member #5 is **"First Ten"** — *not*
    also First 20 / First 50 / Founders Circle. (Implementation: `bracket = first threshold ≥
    ordinal`; store/show only that. The wider memberships are logically implied, never
    awarded.) This keeps each badge meaningful and the inner sanctum unambiguous.
  - **The ordinal axis is the OPERATOR IDENTITY, not the node (maintainer 2026-06-05).** What
    earns a founder ordinal is the **attested `operator_id` (the user)** — *not* `node_id`.
    Nodes are **interchangeable/fungible** (an operator swaps hardware, runs many, retires
    some); the durable, valuable thing is the *person/identity* behind them. So:
    - Ordinal #N = the Nth distinct **attested operator identity** to appear in the genesis
      window, anchored by the `seq` of its first operator-bound REGISTER in the signed log.
    - **`node_id` is explicitly NOT a founder axis.** (The earlier "node-id series" idea is
      dropped — it would reward fungible machines + dev churn, which is meaningless.)
    - Tier-2 attestation is mandatory for a founder ordinal (so #1–#50 "people" can't be
      sock-puppeted, and the identity is real and portable across the operator's nodes).
    - **Test/dev nodes and their IDs are purged and never count.** Per §5 dev-churn exclusion,
      the genesis count begins only over real attested operators; test registrations are
      removable and carry no ordinal. The badge survives node churn because it's bound to the
      identity, not any machine.
  - Determinism: ties broken by `seq` (the log is totally ordered), so the ranking is
    unambiguous and auditable by anyone replaying the signed log — no directory discretion.
  - **Provenance caveat (honest):** the *cryptographic* ordinal proof holds only from the
    point **signed REGISTER emission is live in production** (prod genesis-key signing = #271,
    pending). Members who registered *before* that have an authoritative ordinal from the
    directory's `nodes.created_at` (recorded, attestable by the maintainer) but not yet
    signed-log-provable. Mitigation: fix the close of the inner brackets to the signing
    go-live (or anchor a one-time signed "genesis ledger" snapshot of the existing order when
    #271 ships) so the #1–50 ordinals become cryptographically frozen from a known point.
  - **DEV-CHURN EXCLUSION (critical — found 2026-06-05):** prod already shows **89 distinct
    registered node_ids but only 3 active** — i.e. ~86 are development/test registrations from
    the build period, not founders. Assigning ordinals by *raw* historical registration order
    would award "first 10" to **test nodes**, defeating the purpose. Therefore the ordinal
    counter MUST start from a **clean genesis snapshot at public launch** (or the first
    Tier-2-attested operator), explicitly excluding pre-launch dev/test node_ids. This is the
    decisive reason the meaningful series is the **operator-ordinal (attested)** one — node-id
    ordinals over the raw log are noise until the dev nodes are fenced off. "Member #1" must
    be the first real founding operator, by construction.
- **Founders Circle = the outermost ordinal bracket, immutable + time-boxed.** It closes when
  the ladder fills (the first *C* attested operators) OR at a date D, whichever first — after
  which no ordinal founder badge is earnable again. The inner brackets (#1–50) are the prestige
  core; the cap *C* sets only *how long the founder on-ramp stays open*, not the prestige (that
  lives in the low brackets). All brackets share the immutable, signed-log-anchored,
  single-best-badge mechanics above.

### 5a. Sizing the Founders Circle cap *C* (researched, maintainer 2026-06-05)

The cap is a **growth lever, not a prestige lever** — prestige is carried by the tight inner
ordinals (First 10/50/100), so *C* can be generous without diluting the elite tiers. What *C*
controls is how long "join the founders" pulls new operators. Comparables:

| Reference | Early-cohort size | Lesson |
|-----------|-------------------|--------|
| Hacker News / Reddit cake-day | uncapped; **low user-ID** = the prestige | Ordinal scarcity beats a hard cap — exactly our inner-bracket model |
| Kevin Kelly **"1,000 True Fans"** | ~1,000 | The empirically-cited size of an early base that makes a project self-sustaining |
| Bitcoin / Ethereum early adopters | uncapped, organic | "Early" is self-evident from the chain — value accrues to *provable* earliness, not a badge cap |
| Y Combinator batch | ~100–400 | Small cohorts feel elite but don't reach network-effect scale alone |
| Tesla Founders Series | hundreds | Very exclusive, but a luxury good, not a network that needs coverage |
| Founding-member DAO/NFT drops | 1k–10k | Capped drops over-mint and dilute fast; the cap rarely correlates with utility |

**Why not 50:** a 50-operator mesh isn't viable (no multi-region coverage, no redundancy) — the
founder incentive would expire *before* the network is useful, starving the growth it's meant to
drive. 50 is right as the *inner prestige bracket*, wrong as the whole circle.

**RATIFIED (maintainer 2026-06-05): nested time-gated tiers, NOT a single cap.** The Founders
Circle is three nested tiers, each requiring *both* an ordinal cap *and* a time window (single-best;
window measured on **lock-in**, see `08` R2):

| Tier | Ordinal cap | Time window | Contains |
|---|---|---|---|
| **Genesis-50** | first 50 | within **3 months** | the inner pure-ordinal sub-brackets First 10/20/30/50 |
| **Founders-500** | 51–500 | within **6 months** | — |
| **Founders-1000** | 501–1000 | within **12 months** | — |

Rationale (supersedes the earlier single "C = 1,000 / date-D" recommendation): time-gating rewards
genuinely **early** adoption (not just a low node number a latecomer could grab), and three *staged*
closes convert the single spike-then-plateau cliff into a ramp (`08` §1 / `07` E). Prestige still lives
in the inner ordinals (First 10/50); the outer caps stay ultra-scarce against an eventual commodity.
Anti-gaming under this structure is reviewed in `08` (#461) — proceed to the `09`/#309 spec with rules
R1–R7. Brackets: 10 / 20 / 30 / 50 *(= Genesis-50 close, 3 mo)* / 100 / 200 / 300 / 500 *(6 mo)* /
**1000 (12-mo close)**.
Fallback options if a tighter feel is wanted: **C = 500** (more exclusive, still coverage-viable)
or **C = pegged to a milestone** (e.g. "until 3 regions × 90 days of healthy mesh," tying the
close to real viability rather than a round number). Maintainer picks *C* + *D*.

### 5b. Founder #1 — reserved + backed up (maintainer directive 2026-06-05)

The maintainer (**RobLe3**) is **user & founder #1 — the genesis operator**, to be anchored as
**ordinal #1** in the genesis snapshot (§5 dev-churn cutoff). This is recorded here and in the
agent's persistent project memory so it is not lost across sessions. When the genesis snapshot
is frozen (post dev-churn exclusion, at the #271 signing go-live), position #1 of both ordinal
series (operator-identity and node-id) is the maintainer's genesis identity, cryptographically
anchored in the signed event log — the highest-value, never-reissuable badge in the mesh.
- **Cryptographically anchored, not a database flag.** An operator's *first REGISTER* lives in
  the directory's **Ed25519-signed, federatable, append-only event log** (ADR-013 — the same
  log `iicp-node credits --verify` audits). So "this operator was here in the genesis era" is
  **independently verifiable from the signed log in 10 years**, even against a different
  directory operator — like an early on-chain address, but provable via the signed history,
  not trust. This is the part that makes the legacy *real* rather than marketing.
- **Cohort identity (additive, never resets):** "Class of 2026", plus regional "Country
  Pioneer / Outer-Rim" (first attested operator in a country/region — the subtle Alliance nod,
  kept as a badge not a rank). Additive seasons (per 01) mean late joiners always have *new*
  legacy to earn, but the genesis cohorts stay scarce.
- **Display, build later (per maintainer #4):** the founder/legacy *recognition mechanics* are
  designed now and the genesis event-anchoring is captured the moment operators register
  (it's already in the signed log) — but the public "hall of builders" surface ships once the
  mechanisms are waterproof (Tier-2 attestation live + the alignment levers passed anti-gaming
  review). The data is being recorded from day one; the showcase is the deferred piece.

## 6. What ships now vs later

- **Now (decision 1 "build"):** rank ladder (§3) over existing directory-observed metrics +
  Founders-Circle genesis cohort *capture* (it's already in the signed log — just needs the
  threshold defined + the read endpoint). No new telemetry (per 01 constraint).
- **Before public showcase (decision 4 "waterproof"):** era-multiplier + stewardship
  accumulator pass 03 anti-gaming review; Tier-2 attestation live (ADR-030); G3/G4 rollout
  gates (≥3 probe regions 90d, ≥10 attested operators) — i.e. an actual operator base to
  recognize.

## 7. Open decisions for the maintainer

- **Founders-Circle close condition:** first N attested operators (suggest 500) and/or a date?
- **Era-multiplier constants** (N₀, k) — suggest N₀=500, k=2; confirm or tune.
- **Rank names:** sign off the 6 (Initiate/Operator/Provider/Sustainer/Vanguard/Luminary) or
  adjust the nerdy↔business dial.
- **Badge flair latitude:** how far to lean into the Rebel-Alliance theme in *badge* names
  (ranks stay business-clean regardless).

---

## 8. Anti-spoof — how to make badges unforgeable (maintainer-directed 2026-06-05)

**Core principle: badges are PROVEN, not GRANTED.** A badge is a deterministic function of the
public, signed event log — never a directory-asserted flag a profile "carries." Anyone can
recompute it. So the security question isn't "can someone claim a badge?" (they can claim
anything; nobody believes a claim) — it's **"can the underlying log be forged or rewritten?"**

### Threat model (four adversaries)

| Adversary | Goal | Current defense | Gap |
|-----------|------|-----------------|-----|
| **A node/operator** | Claim a badge it didn't earn (fake "First Ten") | Badge derived from signed log; directory assigns `seq` + Ed25519-signs each event — a node cannot forge a lower seq or self-sign | **None** — strong today |
| **Sybil farmer** | Register 50 nodes at genesis to grab all founder slots | Operator-ordinals require **Tier-2 attestation** (one real identity per slot); node-id ordinals are dev-churn noise | Cost = N real attestations; acceptable |
| **The directory itself** | Rewrite history — insert/reorder a friend into "#3" | Per-event Ed25519 sig proves *attestation* of each event | **Real gap:** no hash-chain → the key-holder could re-issue a different ordered log; per-event sigs don't bind position |
| **A rogue federated directory** (Phase 6) | Mint fake founders on its replica | Badges scoped to the **canonical genesis-seed log**, not any replica | Needs the genesis anchor (below) |

### The algorithm — three upgrades, smallest-effort-first

1. **Hash-chain the event log (the single biggest win).** Add `prev_hash` to each event and
   include it in the signed message: `sign( event_id : event_type : seq : ts_ms :
   sha256(canonical_json(payload)) : prev_hash )`, where `prev_hash = sha256(prev event's full
   signed record)`. Now the log is **tamper-evident**: inserting, deleting, or reordering *any*
   event breaks every subsequent link, so a post-hoc rewrite is detectable by anyone holding an
   earlier copy. This closes the "directory rewrites history" gap — positions become immutable
   even against the key-holder, *given* at least one honest earlier copy exists. (Schema add:
   one `prev_hash` column; back-compat — chain starts at the migration's first event or a
   genesis-snapshot root.)
2. **Signed, externally-anchored genesis Merkle root.** At the dev-churn cutoff (§5), freeze the
   ordered list of the first-N attested operators into a **Merkle tree**, sign the root with the
   genesis Ed25519 key, and anchor it *outside* the directory's control — e.g. publish the root
   in a **git commit** (immutable history) and/or a public timestamp authority (RFC 3161) and/or
   the chain head. A badge proof is then a **Merkle inclusion proof**: `{ operator_id, ordinal,
   bracket, merkle_path, genesis_root, root_sig }` — verifiable fully offline against the frozen
   signed root, with **zero trust** in the directory's *current* state. The directory cannot
   move a position after the root is published.
3. **Federated replica cross-check (trust-minimization, Phase 6).** Once replicas tail the
   signed/chained log (ADR-013), multiple independent parties hold the same history. A directory
   that rewrites diverges from the replicas' chains → **detectable by consensus**. This is the
   real long-run defense: no single party — not even the genesis operator — can rewrite the
   founder ordering once it's replicated.

### Verification surface — DIRECTORY-AUTHORITATIVE, never a client-only flag (maintainer 2026-06-05)

The badge is **computed, verified, persisted, and served by the directory** — it is the
authoritative party, and the badge is a **server-side fact derived from the directory's own
signed event log**, not something a client can self-assert. Concretely:

1. **Directory (authoritative):** computes each operator's ordinal from the signed (hash-chained)
   log over real attested operators, persists it (e.g. `operator_recognition.ordinal/bracket`),
   and serves it on the authenticated profile + public read endpoints. A node/client **cannot**
   set or inflate it — it is never accepted from the client; it is *derived* by the directory.
   Spec it as a normative directory behavior (DIR-RECOG-* conformance), so any directory
   (PHP/Rust, #385) must compute it identically. This is the leg that makes it real — not a
   "client said so" flag.
2. **Client (independent cross-check, defense-in-depth):** `iicp-node badges --verify` (sibling
   of `credits --verify`) re-derives the ordinal from the public signed log + Merkle proof and
   verifies the hash-chain + genesis-root signature against the published genesis key
   (`/.well-known/did.json` / externally-anchored root). This lets *anyone* confirm the
   directory computed honestly — it does **not** replace the directory's authority; it audits it.

So: the directory enforces (server-side, spec-conformant, federation-cross-checked), and the
client can independently verify — **both legs, never client-only**. Output of `--verify`: ✓
*cryptographically confirmed: operator X is mesh member #5 (First Ten), anchored to genesis root
`abc…`, matching the directory's served badge* — or a loud ✗ on any chain break / mismatch /
directory-vs-log disagreement (which would itself flag a misbehaving directory).

### Net posture

- **Faking a badge you don't hold:** impossible (derived + recomputed; no claim is trusted).
- **Forging your ordinal upward:** impossible (directory assigns + signs `seq`; with the
  hash-chain, even the directory can't reorder post-hoc undetected).
- **Sybiling the founder slots:** bounded by Tier-2 attestation cost (one real identity each).
- **Directory/rogue-replica rewrite:** defeated by hash-chain + externally-anchored signed
  genesis root + federated cross-check.

**Build order:** the hash-chain (#1) is a small, high-value directory change worth doing before
any founder badge is minted (so the ordinal substrate is immutable from day one); the genesis
Merkle anchor (#2) lands at the dev-churn cutoff; federated cross-check (#3) rides Phase-6
federation. Filed as a follow-up so #310 doesn't mint badges on an un-chained log.

---

## 9. Lock-in, transferability, and identity protection (maintainer decisions 2026-06-05)

### 9a. Lock-in — a founder ordinal is earned by *serving*, not by registering (anti-fraud)

Closes blind-spot A1 (07). A registration only **provisionally** reserves an ordinal; it
**locks in** as a permanent founder badge only after the *identity* has demonstrably served:

- **≥ 30 days of healthy operation** (maintainer-set threshold), measured by the **heartbeat-
  challenge** cryptographic liveness signal (#411) — so uptime cannot be faked or self-reported.
  Continuity required: a sustained-health rolling window, not 1 day up / 29 down.
- **Uptime is the PRIMARY signal; tasks are a demand-scaled floor (closes N1, 07 re-review).**
  The earliest founders face the *least* consumer demand (they exist to close that gap), so a
  hard task quota would lock out exactly the genuine founders. Lock-in is therefore 30d healthy
  *availability* (heartbeat-challenge-verified) **plus** a **low task floor that scales down with
  mesh demand** — when there are few consumers, verified availability-to-serve suffices; the floor
  rises only as organic demand exists. Never punish an early operator for the demand gap.
- **Ordinal is assigned at LOCK-IN, not at registration (closes N4).** #N = the Nth identity, in
  first-REGISTER `seq` order, to *lock in*. Provisional/never-locked registrations hold no number,
  so reclaiming an abandoned slot renumbers nobody; brackets are computed over *locked* founders
  only. (Order is still by genuine earliness — `seq` — among those who proved themselves.)
- **Anti-self-dealing:** tasks where the consumer and provider resolve to the *same* operator
  identity are discounted (no farming your own slot). Ties to the two-sided-reputation /
  03 anti-gaming defenses — the lock-in reads only signals those already defend.
- **Tier-2 attestation** (one real identity) is a precondition, so 30-day Sybil farming costs N
  real attested nodes running real work for a month each — economically unattractive.
- **Provisional → locked → reclaimable:** until locked, the slot is provisional; if the identity
  abandons before meeting the threshold, the slot is **reclaimed** and the next real operator
  takes that ordinal. So the final #1–#1000 are *early **and** proven*, never flag-planters.

This dovetails with the **existing 720h (30-day) identity-age gate for Platinum** (S.12 §5.1.1) —
"30 days of real operation" is already a ratified maturity bar; founder lock-in reuses it.

### 9b. Transferability — DECISION: immutable provenance, transferable current-holder

Maintainer delegated this ("if I sell my founder id for $1M… that is a decision you have to
make"). **Decision:** split the badge into two layers, both on the signed log:

- **Provenance (immutable, never transferable):** the signed event log records *who earned each
  ordinal* — forever. That RobLe3 was the **original** founder #1 can never be erased, sold, or
  rewritten. The "who built IICP from the depths" record is permanent.
- **Current-holder (transferable, but only by explicit on-the-record succession):** holding an
  ordinal *may* be transferred — so it can carry real value (sellable) — **but only via an
  explicit, identity-signed `FOUNDER_SUCCESSION` event** recorded in the signed log, never via a
  covert private-key handoff. A transfer appends to the provenance chain
  (`#1: earned by RobLe3 (genesis) → transferred to X, 2030-… (signed)`), so a buyer gets a
  *verifiable, honestly-provenanced* "current holder of founder #1, acquired from the genesis
  operator" — valuable, but it can never let them claim they *built* it.

**Why this resolves C1:** it gives the badge tradeable value (the maintainer's interest) while
(i) keeping the legacy honest (provenance is immutable), (ii) avoiding the covert-key-sale grey
market (transfers are explicit + visible + signed), and (iii) staying recognition-not-equity
(an on-the-record collectible succession, no monetary promise from the project).

**RATIFIED (maintainer 2026-06-05): allow succession from launch** — `FOUNDER_SUCCESSION` ships
with the recognition system, not as a later add-on (the maintainer chose transfer-with-signed-record
over the ship-non-transferable-first fallback). Wash-transfer / sock-puppet-succession is the new
day-one vector this opens; it is contained because every transfer is public + signed and the
provenance lineage records **every** holder (genesis earner → … → current), so wash-trades are
visible, succession never resets lock-in, and it cannot re-open a closed tier (`08` R6, #461).

### 9c. Identity protection — password-at-rest + mutable nickname

Extends ADR-030's wallet model (#307). The cryptographic identity is permanent; its *ergonomics*
are not:

- **Password-protected key (wallet-style, client-side) — OPTIONAL + headless-compatible (closes
  N3).** The operator's identity key in `~/.iicp` *may* be **encrypted at rest with a passphrase**
  (KDF → symmetric encrypt, like a crypto wallet). Because a serving node must auto-restart + stay
  up 24/7 to meet the 30d lock-in, encryption must **never** force an interactive prompt on a
  headless node: unlock via env var / OS keyring / a running agent, or a cached/derived
  *operational* key kept separate from the cold master identity key. Default off; recommended for
  interactive/cold-storage use. Reduces *accidental* leak — not a defense against an intentional
  key sale (see 07 N-C1). Pairs with the chmod-600 storage already used for `node_token`.
- **Mutable nickname over an immutable ID:** the `operator_id` / pubkey is the **permanent,
  cryptographic** identity; a human-readable **nickname/display name is a mutable attribute** the
  operator can change anytime via an authenticated, directory-recorded update (the badge, ordinal,
  and provenance all stay bound to the *key*, not the nickname). So "RobLe3" is a renameable label
  on the immutable founder-#1 key; on a succession (9b), the new holder sets their own nickname
  while the provenance log still shows the genesis operator. Directory-authoritative (the served
  profile reflects the current nickname; history is in the log).
