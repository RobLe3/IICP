# 07 — Adversarial design review: blind spots, caveats, and a growth simulation

**Status:** adversarial review of `06-recognition-design.md` (maintainer-directed, 2026-06-05:
"simulate the effect and decisions to find blind spots and caveats"). Findings carry a
**severity** (High = could undermine the goal or create real harm; Med; Low) and a proposed
**mitigation**. Same posture as the FRAME8 transport review.

---

## A. Perverse incentives

**A1 — Founder land-grab of inactive nodes (High).** Ordinals reward *registration order*, not
contribution. With a 1,000-slot prize, the rational play is to attest + register *immediately*
to grab a low ordinal, then never serve. Result: the first-1000 could be dominated by inactive
"flag-planters," and the badge that's meant to honor "those who lifted the mesh" instead honors
people who showed up and left.
→ **Mitigation:** an ordinal does not *lock in* until the identity has done real work — e.g. ≥N
tasks served and ≥D days of healthy uptime within the founder window. Until locked, the slot is
*provisional* and reclaimable. The founder badge then means "early **and** real," not "early."

**A2 — Era-weighting discourages the majority (Med).** If a task at 10 nodes is worth 3× one at
1,000 nodes, every operator who joins after the bootstrap feels they're playing a rigged game
("I can never catch the early cohort"). 01 explicitly flags "exclusivity that locks out late
joiners" as an anti-pattern — era-weighting is a soft version of it.
→ **Mitigation:** cap era-weighting's influence to the *legacy* axis only (it must not gate the
*mutable* merit ranks — a newcomer can still reach Luminary on current contribution). Decay the
multiplier smoothly to 1.0 and publish the curve so it feels fair, not rigged.

**A3 — Ranks amplify gaming of the underlying signals (High).** The merit ladder reads
reputation, tasks-served, uptime — already gameable (two-sided reputation, Sybil, self-dealing
consumer↔provider loops). Today gaming buys a marginal routing edge; with ranks + public
leaderboards it also buys *status*, raising the payoff and attracting more sophisticated gaming.
→ **Mitigation:** ranks must ship *after* 03's anti-gaming is hardened, not before — the stakes
rise the moment status is attached. Treat rank as a *derived view* of already-defended signals,
never a new gameable surface (no rank-only metrics).

## B. Trust & centralization

**B1 — Genesis-snapshot circularity (High).** The snapshot that fixes #1–#1000 is frozen by the
maintainer — who is #1. "The founder defined who the founders are, and put themselves first" is a
legitimate trust objection if IICP ever matters.
→ **Mitigation:** publish the candidate genesis ordering **publicly for a review window** before
freezing; anchor the frozen root **externally** (git commit hash + RFC-3161 timestamp + ideally a
public chain) so it can't be silently re-cut; and document #1 = genesis operator *by definition*
(transparency, not a grant). The external anchor is what converts "trust the maintainer" into
"verify the timestamp."

**B2 — Federation canonicality (High, deferred).** Directory-authoritative is clean with one
directory. Post-federation (#437/ADR-013), *which* directory's badge is canonical? A rogue replica
can serve different ordinals. The design leans on "federated cross-check," but that check is not
yet implemented.
→ **Mitigation:** canonical badges are defined against the **genesis-seed's** signed log only;
replicas serve *derived, verifiable* copies; the cross-check (replicas diverging from the genesis
chain = alarm) must actually ship with federation, not be assumed. Badge canonicality is a
federation-trust problem — gate the public showcase on it.

**B3 — Hash-chain retrofit gap (Med).** #458 chains *future* events, but the genesis cohort
predates the chain (and #271 prod-signing). So #1–#N rest on the snapshot's integrity (B1), not an
unbroken chain from event #1.
→ **Mitigation:** the genesis snapshot root *is* the chain's anchor block; everything after links
to it. Accept that pre-anchor ordering is "maintainer-attested + externally-timestamped," and say
so plainly.

## C. Identity, transferability, legal

**C1 — Key-portability = badge-transferability → a secondary market (High).** ADR-030 identity is
**portable** (key-based, migratable). So "founder #1" travels with the private key — meaning it's
*de-facto sellable* (sell the genesis key, sell the badge). Combined with the maintainer's own
"might have value later," this risks (a) a market in founder identities, (b) the prestige decoupling
from the actual person who built the mesh, (c) securities-like / collectible regulatory questions if
badges trade for money.
→ **Mitigation (decision needed):** declare founder badges **non-transferable recognition bound to
identity** and design against key-sale — e.g. recognition references the *continuous operating
history* of the identity (a sold key with no operating history doesn't carry the legacy), or an
explicit "non-transferable, revoked on key transfer" policy. Decide deliberately: is founder #1 a
*person's* honor (non-transferable) or a *key's* asset (tradeable)? They can't be both.

**C2 — "Value later" expectation (Med).** Framing recognition as financially valuable invites
speculation and disappointment, and edges toward "we issued you something with monetary upside"
(reputational/legal exposure).
→ **Mitigation:** keep the public framing as *recognition/legacy*, never investment; no promises of
monetary value; badges are status, not equity.

## D. UX & adoption

**D1 — Attestation friction vs the adoption funnel (High).** Founder ordinals + Provider+ ranks
require Tier-2 attestation. If attestation feels like KYC, it suppresses exactly the early adoption
the founder badges exist to drive. Tension: strong anti-Sybil ↔ low-friction onboarding.
→ **Mitigation:** Tier-2 = **domain control / did:web / a tweet-proof**, never identity documents;
the *pseudonymous* Tier-1 path must reach the early merit ranks so onboarding stays frictionless;
attestation is a one-time, minutes-long step gating only the prestige tiers.

**D2 — Demotion churn (Med).** Even with hysteresis, dropping a rank after an outage can make an
operator quit (loss aversion > gain).
→ **Mitigation:** display **highest-ever rank** alongside current ("Vanguard · currently Sustainer");
generous outage grace tied to the heartbeat-challenge signal; never demote >1 tier per step.

## E. Growth-dynamics simulation (reasoned; needs a parameterized RESA run later)

**The decision under test:** does a hard "first 1,000" founder close produce *steady growth* (the
stated goal) or **spike-then-plateau**?

Reasoned model (no real adoption data yet, so this is qualitative — see honesty note):
- **Phase 1 (window open):** scarcity + "be a founder" drives an arrival spike. *Risk A1* inflates
  it with flag-planters.
- **Phase 2 (window closes at 1,000 / date D):** the single strongest pull ("become a founder")
  **vanishes overnight**. If nothing replaces it, arrivals drop sharply → *plateau*. This is the
  central caveat: a hard close optimizes the bootstrap and then *removes its own growth engine*.
- **Phase 3 (post-close):** growth must come from utility + the *additive* mechanics (seasons,
  climbable merit ranks, regional "first-in-country" badges that stay open). If those aren't
  compelling, the curve flattens after the circle closes.

→ **Mitigations:** (1) the A1 lock-in keeps Phase-1 arrivals real; (2) keep **uncapped, renewable**
recognition (seasons, country/region firsts, merit ladder) so Phase-3 has its own engine; (3)
consider a **date-fallback that closes the circle by time, not just count**, so the close is
predictable and the post-close mechanics are live before it hits; (4) the era-multiplier already
gives late joiners *some* of the early-cohort feeling without a hard cliff.

**Honesty note (Fact-Checker discipline):** a *quantitative* simulation (arrival rate λ, attrition,
close-timing) would be **assumption-driven garbage today** — there is no real adoption rate to
calibrate against (prod = 3 active operators). Flag a **parameterized RESA simulation** to run once
there's ≥a few weeks of real arrival data; until then, treat the spike-then-plateau risk as a
*design constraint* (keep renewable engines live), not a measured result.

## F. Governance / optics

**F1 — Founder #1 = maintainer (Med).** Natural (they are the genesis) but optically loaded and a
mild governance-incentive bias if badges gain value (the rule-maker holds the most valuable badge).
→ **Mitigation:** transparency (it's #1 *by definition of being the genesis operator*, externally
timestamped per B1), and keep recognition decisions (close condition, rank criteria) on the record
(GOVERNANCE.md) rather than maintainer discretion.

---

## Top blind spots, ranked

1. **A1** founder land-grab of inactive nodes → require lock-in (early **and** real).
2. **C1** key-portability makes founder #1 de-facto sellable → decide transferability now.
3. **A3** ranks amplify metric-gaming → harden 03 anti-gaming before attaching status.
4. **E** hard close removes its own growth engine → keep renewable recognition live.
5. **B1/B2** snapshot circularity + federation canonicality → external anchor + cross-check.
6. **D1** attestation friction vs adoption → did:web-grade Tier-2, frictionless Tier-1 funnel.

## Decisions this surfaces for the maintainer — RATIFIED 2026-06-05 (see `08`, #461)

- **Lock-in rule** (A1): ✅ uptime-primary, 30 d healthy + demand-scaled task floor (`08` R1).
- **Transferable or not** (C1): ✅ **transferable with signed `FOUNDER_SUCCESSION`** from launch —
  immutable provenance + transferable current-holder (`08` R6). (Not the non-transferable-first fallback.)
- **Close by count, date, or milestone** (E): ✅ **nested time-gated tiers** — Genesis-50/3 mo,
  Founders-500/6 mo, Founders-1000/12 mo (`06` §5a, `08` §1). Staged closes replace the single cliff;
  renewable engines still required before the 12-mo close (`08` R5).
- **Sequencing** (A3, B2): unchanged — ranks only after `03` anti-gaming hardening; public showcase
  only after the federation cross-check ships. Still gated on shipping, not design.

Full re-analysis under the ratified structure + the rules R1–R7 for the `09`/#309 spec:
**`08-tiered-anti-gaming-review.md`**.

---

## Re-review after the §9 mitigations (2026-06-05) — does it fix the caveats?

Re-simulated each finding against 06 §9 (lock-in / transferability decision / identity protection):

| 07 finding | Status after §9 | Note |
|---|---|---|
| **A1** land-grab | ✅ **Fixed** | §9a: ordinal is provisional, locks only after 30d healthy + real tasks; abandoned slots reclaimed → "early **and** proven." |
| **C1** key-sale | ✅ **Mostly fixed** | §9b splits immutable provenance from transferable current-holder (signed succession only). *Residual:* a covert key handoff still passes *control* — see N-C1 below. |
| **B1** snapshot circularity | �︎ **Improved** | §9a makes the genesis ordering *earned by serving* (objective, log-derived) rather than a hand-picked list — but the maintainer still freezes the window; §8 external-anchor + public-review still required. |
| **E** spike-then-plateau | 🟡 **Improved** | Lock-in by *30d-served* (not registered) **slows + smooths** the close (a slot takes ≥30d to lock; reclaims keep it live longer). Hard-close growth-engine loss still needs renewable engines (06 §E). |
| **C2** securities framing | 🟡 **Reduced** | "Recognition, on-record succession, no monetary promise" + "ship non-transferable first." Any transferability keeps *some* exposure. |
| **A2** era-weighting / **A3** rank-gaming / **B2** federation / **B3** chain / **D1** attestation friction / **D2** demotion churn | ⬜ **Unchanged residual** | §9 didn't touch these; their 06/§8 mitigations stand and none were made worse. |

### New issues introduced by §9 (the cost of the fixes)

- **N1 — Task-count lock-in is *unmeetable in a low-demand bootstrap* (High, new).** The earliest
  founders join when there are almost no consumers → they may be unable to serve a "minimum task
  count" through no fault of their own. The people *lifting the mesh from the depths* face the
  **least** demand — so a hard task threshold could lock out exactly the genuine founders it's
  meant to honor. → **Fix (applied to §9a): make lock-in uptime-PRIMARY** (30d healthy, heartbeat-
  challenge-verified) with tasks as a **low floor that scales down with mesh demand** (or "verified
  *availability* to serve" when demand is absent). Don't punish early operators for the demand gap
  they exist to close.
- **N2 — A successor needn't serve (Med, by-design).** A transferred (already-locked) founder badge
  carries to a buyer who never served. Acceptable — that's the point of *transferable current-holder*
  (a collectible). Decision: once **locked**, a badge is a permanent collectible; no ongoing-operation
  requirement on successors. The *provenance* still shows the original earner. (Documented, no fix.)
- **N3 — Password-protected key vs headless 24/7 operation (Med, new).** §9c key-at-rest encryption
  conflicts with unattended server nodes that must auto-restart + re-register (and *must* stay up to
  meet the 30d lock-in). A password prompt on every restart breaks headless operation. → **Fix (applied
  to §9c): password protection is OPTIONAL and headless-compatible** — unlock via env/keyring/agent or
  a cached/derived *operational* key separate from the cold master identity key; never a mandatory
  interactive prompt for a serving node.
- **N4 — Reclaimed provisional slots must not renumber anyone (Med, new).** If ordinals were assigned
  at *registration* and a provisional slot is reclaimed, everyone behind it shifts — breaking
  immutability (you were #6, now #5). → **Fix (applied to §9a): assign the ordinal at LOCK-IN** —
  #N = the Nth identity (in first-REGISTER `seq` order) to *lock in*. Provisional/never-locked
  registrations hold no number, so reclaiming one renumbers nobody. The bracket is computed over
  *locked* founders only.
- **N-C1 — Covert key sale still passes control (Low, inherent).** Key-based identity = whoever holds
  the key can operate as it; you cannot *prevent* an off-record private-key sale. §9b ensures the
  immutable **provenance** (who built it) never transfers covertly and legitimate transfers are
  on-record — that's the best achievable for a cryptographic identity. Honest framing: **control is
  inherently sellable; prestige-provenance is not.** Password-at-rest (§9c) only reduces *accidental*
  leak, not intentional sale.

### Honesty note (unchanged)
A *quantitative* growth/attrition simulation still cannot be calibrated (prod = 3 active operators,
no real arrival data). The above is reasoned re-simulation; a parameterized RESA run is flagged for
when real adoption data exists. §9 measurably closes the two highest-severity findings (A1, C1) and
improves three more; the new N1 is the one that needs a design fix *before* lock-in ships (applied).
