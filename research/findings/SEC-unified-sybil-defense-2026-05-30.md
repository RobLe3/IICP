# Unified Sybil Defense — Research Synthesis for RT/Concept Critical+High Findings

**Date**: 2026-05-30
**Track**: Security (red-team #363 follow-up)
**Status**: Research — proposes ADR-030 amendment + phased MVF sequence
**Author**: FORGE iter-1556 deep-research pass (Opus)
**Inputs**: red-team Block 1 (`reports/redteam/01-directory-control-plane.md`), adversarial bypass review (RT-01b/02b/03b/05b), concept review (F1–F10), ADR-030, `research/cryptographic-trustworthiness/`, `research/results/rep/identity_age/`, `research/findings/REP-adversarial-sensitivity-2026-05-18.md`, `research/gamification-track/03-anti-gaming.md`

---

## 1. The one insight

Every critical and high finding from both reviews reduces to a **single root cause**:

> **Identity is free to mint, and every protective gate is keyed on a free-to-mint identifier.**

- RT-02b (CRITICAL credit harvest): gate keyed on `node_id` → mint new `node_id`.
- RT-01b (HIGH reputation inflation): per-node cap → run N nodes.
- RT-03b (HIGH quorum bypass): quorum counts distinct `node_id` → register 3 in 3 seconds.
- RT-05b (HIGH griefing): reporter cap per `node_id` → rotate fresh reporter nodes.
- F1 (CRITICAL self-attestation): reputation derives from operator-controlled inputs.

The corollary that kills the obvious fix: **ADR-030's operator identity does not, by itself, solve this** — because ADR-030 Tier 1 (`operator_id = base64url(Ed25519 pubkey)`) is *also* free to mint (the ADR says so explicitly: "Sybil cost: near-zero"). Relocating gates from `node_id` to `operator_id` moves the bypass up one layer; it does not close it.

So the research question is not "what new mechanism do we invent" but:

> **What resource can an attacker NOT cheaply manufacture, that we can gate high-value operations on, without adding onboarding friction?**

The answer the project's own simulations already validate: **time + sustained good behaviour.** You can mint a keypair in 1 ms and an email in 30 seconds, but you cannot manufacture *"a continuously-operating, well-behaved node with a 30-day clean history"* faster than 30 days of wall-clock time and honest operation. That cost is exactly what honest operators pay anyway — which is the defining property of a sound Sybil defence (cost-to-attack ≈ cost-to-participate-honestly).

---

## 2. What the project already has (inventory — do not rebuild)

| Asset | Status | Closes |
|-------|--------|--------|
| **`response_hash` in CIP receipt** | **SHIPPED** (CreditsController requires it, adapter computes, coordinator verifies) | Concept-review F3 token-inflation/drain — *partially*. Binds receipt to body bytes. Residual: token_count-vs-body-length + escrow. |
| **ADR-030 operator identity** | Accepted, build-deferred behind onboarding | Anti-laundering, operator-diversity honesty, operator-scoped rate limits (designed) |
| **Identity-age gate simulation** | Validated: ~92% whitewash reduction at 720h gate | The core anti-Sybil mechanism — empirically grounded |
| **REP adversarial sweep** | Validated: adversaries converge to ~0.318 rep vs honest ~0.954 *when reputation is transaction-earned* | Confirms reputation works IF inputs are real (red-team attacks the input layer, not the algorithm) |
| **Anti-gaming heuristics** | Designed (IP /24 clustering, registration-timing, pubkey reuse) | Pre-identity-layer sock-puppet detection |
| **Crypto-trustworthiness survey** | 6 approaches evaluated; hash-commitment = "Phase 5 now" | Response integrity (done), TEE/ZK deferred to Phase 6+ |

**Key correction to the concept review**: F3 (credit drain via token inflation) is materially *already mitigated* — `response_hash` is live in production. The reviewer worked from the spec, not the shipped code. The residual F3 gap is escrow (spend-then-confirm) and token_count plausibility, not the full attack.

---

## 3. The smart solution — "time-locked value, free participation"

A three-axis gating model. Each economically-meaningful operation is gated on the *cheapest axis that makes the attack irrational at the scale where the operation has value*. Participation stays free; only value extraction is gated.

### Axis A — Time (identity age). The universal Sybil cost.

Gate high-value operations on `min(node_age, operator_age)`. Empirically (our own sim): a 720h gate cuts platinum-whitewash 92%. The residual is the single first-reach; post-defection re-entry is impossible because a defecting identity cannot stay clean for 30 days.

- **Zero onboarding friction**: a new operator participates *immediately* (registers, serves tasks, earns reputation). They simply cannot reach the highest-value operations (free-credit bonuses beyond a floor, top routing tiers, operator-diversity claims) until their identity has aged. Honest operators don't notice — they age naturally. Attackers pay the full 30 days per Sybil.
- **The attacker's dilemma**: to extract value they must EITHER defect early (caught, never ages) OR behave honestly for 30 days per identity (cost = honest operation, which is the point).

### Axis B — Attestation cost (ADR-030 Tier 2). For operator-diversity claims.

Anything that asserts *"I am a distinct operator"* (diversity badges, the external-operator count, replica trust tier, operator-scoped credit ceilings) requires Tier 2 (email / DID:web). Cost: one domain or one non-throwaway email per claimed-distinct-operator. This is the ADR-030 design; no change needed beyond *enforcing it on the valuable operations*.

### Axis C — External observation. For reputation that affects routing.

Reputation that influences `discover()` ranking must be anchored at least partly in signals the rated node cannot self-produce: proxy-telemetry (counterparty-observed latency/success) and directory-initiated liveness probes. The REP sweep shows the *algorithm* drives adversaries to the floor **when inputs are real**. The red-team shows the *inputs* are forgeable. Axis C closes the input layer by weighting observed signals above self-reported ones, and by requiring the observers themselves to pass Axis A (aged) + Axis B (attested) before their observations count toward quorum.

### The unifying principle

> **Make the cost of faking a high-value signal equal to the cost of earning it honestly.**

Time-gating does this for free (honest operators age; attackers must too). Attestation does it for diversity (one identity per real-world cost unit). Observation does it for routing reputation (you must convince aged+attested counterparties, not yourself). Each axis is individually cheap to implement; together they make every critical/high attack uneconomic *at the scale where the attacked resource has value*.

---

## 4. Per-finding mapping

| Finding | Sev | Smart-solution axis | Mechanism | Effort |
|---------|-----|--------------------|-----------| ------|
| RT-02b credit harvest (fresh id) | CRIT | A + IP heuristic | Free-credit allocation gated on `operator_age ≥ T` AND IP-aggregate ceiling. New ids get a *minimal* floor only; the bonus tier ages in. | S (PHP, ~1 day) |
| RT-01b fleet rep inflation | HIGH | A + C | Self-reported metrics contribute to rep only up to a low cap until the node is aged AND has ≥1 proxy-observed task. Aged+observed unlocks full weight. | M |
| RT-03b quorum ≠ independence | HIGH | A + B | Quorum-contributing proxies MUST be aged (`created_at < now-T`) AND have ≥1 completed task; tighten to attested for diversity-sensitive counts. | S |
| RT-05b griefing + divergence | HIGH | A + C + bugfix | Reporters must be aged+reputable to apply delta; raise cap 2→4; **dual-write `nodes.reputation_score` (correctness bug, fix now)**. | S |
| RT-04 liveness bypass | HIGH | (orthogonal) | Exclude `nat_type="unknown"` from `assertLive()` bypass; only topologies the directory genuinely cannot probe bypass. | XS (~1h) |
| F3 credit drain | HIGH | already mostly closed | `response_hash` shipped. Residual: escrow (hold→release on delivery-confirm) + token_count plausibility check. | M (escrow = protocol msg) |
| F2/F4/F7/F10 trust framing | HIGH/struct | documentation + Rust | `trust_tier` field in NODELIST; threat-model correction; Directory Operator Trust Policy. | S (docs) |

---

## 5. Proportionality — likelihood × scale (the "don't build Fort Knox yet" answer)

| Finding | NOW (3 self-owned nodes, 0 ext ops, credits worthless) | AT GA (≥10 ext ops, credits have value) |
|---------|------|------|
| RT-02b credit harvest | **Negligible** — nothing to steal | **Critical** — direct economic attack |
| RT-01b fleet inflation | **Negligible** — no routing consequence | **High** — script-kiddie tier |
| RT-03b quorum | **Negligible** — no adversaries | **Medium** — needs spec knowledge |
| RT-05b griefing | **Negligible** — no competitors | **Medium** — targeted attacker |
| RT-04 phantom nodes | **Low** — pollutes own REACH probes | **High** — trivial + public spec |
| F3 drain | **Low** (and partly closed) | **Medium** (residual escrow gap) |
| F2/F4/F7/F10 trust | **Low** (operator == maintainer) | **High** (operators depend on honesty) |

**Conclusion**: nothing requires Fort Knox today. But the fixes must land **before the Phase-5D public-launch gate opens external registration**, because every one of these flips from negligible to high/critical the moment there are external operators with something to gain. The trigger is not a date — it is the `≥10 external operators` / `credits-have-value` boundary.

---

## 6. Recommended build sequence

**Tier 0 — now (correctness + trivial, ship regardless of scale):**
1. RT-04: exclude `nat_type="unknown"` from liveness bypass (~1h)
2. RT-05b: dual-write `nodes.reputation_score` in AuditReportController (~30m, pure correctness bug)
3. `trust_basis`/`trust_tier` field design in NODELIST + threat-model "metadata-leak-only" correction (docs)

**Tier 1 — before Phase-5D gate opens (closes the critical/high economic attacks):**
4. **Identity-age gate primitive** (Axis A): add `operator_age` / `node_age` checks; this is the single highest-leverage mechanism (92% validated). Gate free-credit bonus + top routing tier + quorum eligibility on it.
5. RT-02b: IP-aggregate free-credit ceiling + age gate on bonus allocation.
6. RT-03b/RT-05b: aged+reputable requirement for quorum and audit-report weight; raise griefing cap to 4.

**Tier 2 — with ADR-030 implementation (operator layer):**
7. Operator-scoped rate limits (TC-9b extension) — replaces IP heuristics with the correct per-operator gate.
8. Tier 2 attestation enforcement on operator-diversity operations (Axis B).

**Tier 3 — Rust directory / Phase 6 (foundational):**
9. Reputation scoring as an auditable pure function over verifiable inputs (Axis C done right); compile-time operator-power bounds (F7).
10. CBOR strict security profile (concept-review F6); escrow protocol message (F3 residual); consensus-mode minimum-diversity gate (concept-review F8).

---

## 7. PHP-now vs Rust-later vs conceptual (maintainer framing)

- **PHP can fix the symptoms cheaply and should** (Tier 0 + Tier 1) — these are guards on existing endpoints, ~3–5 days total, and they close every *economically rational* attack at the scale we'll hit first.
- **Rust is the right home for the structural fixes** (Tier 3): an auditable scoring function, compile-time bounds on operator power, and a strict CBOR profile are far more defensible in a typed, single-binary, open-sourceable directory than as accreting PHP validation. Use this as a candidate-recruitment hook: "the v2 directory makes operator honesty cryptographically auditable, not a matter of trust."
- **The conceptual issues (F1, F10) are not bugs — they are a design honesty gap.** Self-reported reputation is a *load-balancing heuristic, not a security property.* The fix is to (a) say so explicitly in the spec, (b) add `trust_tier` so the API never overstates what a score means, and (c) commit to Axis C (external observation) as the only path to reputation that can bear security weight. This is the deepest finding: no amount of PHP or Rust closes a logical gap where the trust signal and the thing it claims to measure are produced by the same party. Time-gating + attestation + external observation is the structural answer, and it is the same answer whether implemented in PHP or Rust.

---

## 8. Open questions for maintainer / PS

1. **Age-gate threshold**: 720h (30d) is the simulated value. Confirm, or pick per-operation thresholds (e.g. 72h for routing-tier, 720h for diversity claims)?
2. **Free-credit floor for brand-new operators**: do new ops get a small floor immediately (good UX) with the bonus tier age-gated, or zero until aged? Recommend small floor — preserves onboarding.
3. **Escrow (F3 residual)**: worth the protocol complexity pre-GA, or accept the residual given `response_hash` already blocks the cruder attack?
4. **Does the `trust_tier` field ship in PHP NODELIST now, or wait for the Rust directory API redesign?** Recommend now — it is additive and stops the API from misrepresenting reputation in the interim.
