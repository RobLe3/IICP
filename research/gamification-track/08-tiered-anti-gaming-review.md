# 08 — Anti-gaming review under the ratified time-gated tiers (#461)

**Status:** RESA anti-gaming re-analysis (#461), maintainer-directed. Re-examines the `07`
caveats against the **ratified** Founders Circle structure and transferability decision
(maintainer 2026-06-05), and produces the concrete anti-gaming **rules** the `09`/#309
recognition spec MUST encode before #310 mints anything.

**Ratified parameters re-analyzed here:**
- **Founders Circle = nested time-gated tiers** (replaces the single "first 1000 / date-D"
  close): **Genesis-50** = first 50 within **3 months**, **Founders-500** = first 500 within
  **6 months**, **Founders-1000** = first 1000 within **12 months**. A tier requires *both* its
  ordinal cap *and* its time window; **single-best** (a member holds only their tightest tier).
  The inner pure-ordinal sub-brackets (First 10/20/30/50, `06` §5) live *inside* Genesis-50.
- **Transferability = transfer-with-signed-`FOUNDER_SUCCESSION`** on the hash-chained log (#458,
  landed) — from launch, not the `07` "ship non-transferable first" fallback.
- **Rank tone:** hybrid nerdy+business (no anti-gaming impact; cosmetic).

The honesty note from `07`/§E stands: **quantitative** arrival/attrition modelling is still
un-calibratable (prod = 3 active operators, no real arrival data). Everything below is
qualitative re-simulation + design rules; a parameterized RESA run is deferred until real
adoption data exists. No numbers here are measurements.

---

## 1. How the ratified tiers change the `07` findings

| `07` finding | Under a single hard close | **Under the ratified time-gated tiers** |
|---|---|---|
| **E — spike-then-plateau** (High) | One "become a founder" pull that **vanishes overnight** at the close → plateau risk. | **Improved.** Three *staged* closes (3 / 6 / 12 mo) mean the founder pull **steps down**, not off: after Genesis-50 closes at 3 mo, Founders-500 and -1000 still pull through month 12. The cliff is replaced by a ramp. **Residual:** each boundary is still a mini-cliff, and month-12 is the final hard close — the renewable engines (seasons, regional firsts, merit ladder) MUST be live before then (unchanged from `07` §E). |
| **A1 — founder land-grab** (High) | Spread across 1000 slots. | **Concentrated on Genesis-50 / 3 mo** — the tightest, highest-prestige, highest-value tier → the strongest land-grab/Sybil incentive sits here. The lock-in defence (§9a, uptime-primary per N1) must be airtight *specifically* for this tier. **New sharp deadline:** a hard "lock in before month 3" cutoff is itself a land-grab trigger (rush-to-register). |
| **C1/N2 — transferability** | Decision was open; `07` recommended non-transferable-first. | **Decided: transferable-with-signed-succession from launch.** Resale value preserved; the immutable provenance chain (who earned each ordinal) never transfers. **New surface:** succession itself is now a day-one mechanic → wash-transfer / sock-puppet-succession vectors (§3 R6 below). |
| **B1 — snapshot circularity** | Maintainer freezes the #1..C list. | **Unchanged but smaller blast radius:** time-gating + lock-in make the ordering *earned by serving within a window* (log-derived, objective), not a hand-picked list. The external anchor + public-review window (`06` §8) still required for the genesis cohort. |
| A2 / A3 / B2 / B3 / D1 / D2 / N3 / N-C1 | — | **Unchanged residual** — the tiering doesn't touch them; their `06`/`07` mitigations stand and none are made worse. |

**Net:** the ratified structure measurably *improves* the two findings most affected by close-timing
(E, B1) and *concentrates* A1 onto one analyzable tier, at the cost of one genuinely new vector
(succession wash-trades, R6) and one new edge to specify precisely (the time-window reference point, R2).

---

## 2. New findings specific to the time-gated tiers

- **T1 — Which timestamp does the window measure? (must-specify, High).** "First 50 within 3
  months" is ambiguous: 3 months from launch measured on *first-REGISTER* or on *lock-in*?
  Lock-in takes 30 d healthy operation (§9a / N1). If the window is measured on **lock-in**, a
  Genesis-50 aspirant must register early enough to *complete* 30 d by month 3 (≈ register by
  month 2) — and cannot backdate serving, so it is **un-gameable by late rushers**. If measured on
  *register*, a flag-planter can grab a slot at month 2.99 and lock in later → reopens A1.
  → **Rule R2:** the tier window is measured on the **lock-in event timestamp** (the signed
  `FOUNDER_LOCKIN` event on the #458 chain), consistent with N4 (ordinal assigned at lock-in).
- **T2 — Under-fill is fine; over-fill is handled by single-best (Low).** If < 50 identities lock
  in within 3 months, Genesis-50 is simply under-filled (scarcity reflecting reality — correct, not
  a bug). If > 50 try, only the first 50 by lock-in `seq` get Genesis-50; #51–500 (within 6 mo) fall
  to Founders-500. No renumbering (N4). No fix needed; document it.
- **T3 — Staged mini-cliffs invite three rush spikes (Med).** Each window close (3/6/12 mo) is a
  deadline → expect an arrival/lock-in spike just before each. Benign *if* lock-in keeps them real
  (R1) and the renewable engines absorb post-deadline attention (R5). Worth a dashboard watch, not a
  redesign.

---

## 3. Anti-gaming RULES for the #309 spec (the deliverable)

These are the concrete, log-derivable rules the recognition spec MUST encode. Every one reads only
**directory-observed, already-defended signals** (the `03` constraint) and is verifiable against the
#458 hash-chained log — no client-asserted inputs.

- **R1 — Lock-in is uptime-primary, demand-scaled task floor (A1, N1).** A founder ordinal is
  *provisional* at register and locks in only via a signed `FOUNDER_LOCKIN` event after **≥30 days
  healthy operation** (heartbeat-challenge #411 verified) **+** a task floor that **scales down with
  mesh demand** (when there are no consumers, *verified availability to serve* substitutes). Earliest
  founders — who face the least demand by definition — are not punished for the demand gap they exist
  to close.
- **R2 — Tier window measured on lock-in, not register (T1).** Genesis-50 / 500 / 1000 membership is
  computed over the **lock-in timestamp** of the signed event, ordinal = Nth identity to *lock in*
  (first-REGISTER `seq` breaks ties). Backdating serving is impossible (heartbeat-challenge is live);
  late registration can't retroactively claim an early tier.
- **R3 — One identity, one ordinal; anti-self-dealing (A1/A3, Sybil).** Ordinal is keyed to the
  **attested OPERATOR identity** (Tier-2), never node_id; dev/test churn purged and never counted
  (`06` §5). Self-dealing consumer↔provider loops are discounted in the demand/task signal R1 reads
  (defer to `03`'s existing two-sided-reputation defence — recognition adds no new gameable metric).
- **R4 — Era-multiplier is legacy-axis-only, capped, published curve (A2).** The early-task multiplier
  feeds only the *immutable legacy* axis, never the *mutable* merit ranks (a newcomer still reaches
  the top merit rank on current contribution). Decay to ×1.0 on a published curve so it reads fair.
- **R5 — Renewable engines live before month 12 (E).** Seasons, regional/"first-in-country" firsts
  (stay open), and the climbable merit ladder MUST be shipped + visible before the Founders-1000 close
  so post-close growth has its own engine. The staged tiers buy time; they don't remove this need.
- **R6 — Succession is public, signed, provenance-preserving; wash-trades are visible (C1/N2, new).**
  A transfer is an explicit identity-signed `FOUNDER_SUCCESSION` event on the chain. It transfers
  *current-holder* only; the immutable provenance lineage records **every** holder (genesis earner →
  …→ current), so sock-puppet/wash transfers are publicly visible, not hidden. Succession does **not**
  reset lock-in and does **not** re-open a closed tier. Covert off-record key sale still passes control
  (N-C1, inherent to key identity) — accepted; provenance, not control, is what we protect.
- **R7 — Canonical against the genesis-seed chain only (B1/B2).** Badges are canonical against the
  genesis-seed's signed, externally-anchored log; replicas serve *derived, verifiable* copies; a
  replica diverging from the genesis chain = alarm. Gate the public showcase on the federation
  cross-check actually shipping (not assumed).

---

## 4. Verdict + what unblocks #309

The ratified time-gated tiers are **net-positive for anti-gaming**: they convert the single
spike-then-plateau cliff (E) into a staged ramp, make the genesis ordering earned-by-serving rather
than hand-picked (B1), and localize the land-grab incentive to one tier (Genesis-50) where the
uptime-primary lock-in (R1/R2) is strongest. The one genuinely new vector — succession wash-trades —
is contained by the public, provenance-preserving signed-succession chain (R6).

**No blocking anti-gaming objection to proceeding to the #309 spec** with rules R1–R7 encoded.
The only items that remain *gated on shipping* (not on design) are B2 federation cross-check and the
real-data RESA quantitative run — both already tracked, neither blocks writing the spec.

**Honesty note (Fact-Checker discipline):** this is reasoned re-simulation, not measurement. The
spike/rush dynamics (T3), the demand-floor calibration (R1), and the recommended exact task-floor
numbers cannot be calibrated until real adoption data exists (prod = 3 operators). Treat them as
design constraints to encode conservatively, then tune against the parameterized RESA run later.
