# Gamification Track 03 — Anti-Gaming Constraints

**Status**: Draft (iter-297, 2026-05-21)
**Companion**: `01-design-rationale.md`, `02-metric-mapping.md`
**Tracking**: #267

---

## Threat model

Any reward system attracts adversarial behavior. For each rank, badge, and leaderboard slot,
we enumerate the gaming attack vector and the detection / mitigation. The goal is not to make
gaming *impossible* — it's to make gaming *cost more than legitimate participation* and *easy
to detect when attempted*.

## Categories of gaming behavior

| Category | Description | Examples |
|---|---|---|
| **Sock-puppet inflation** | One operator runs many nodes to dominate leaderboards | Spinning up 50 cloud nodes from one Stripe account to claim "Diversity Champion" + "Country Pioneer" globally |
| **Metric stuffing** | Pushing one metric high in an unhealthy way | Disabling health checks to fake heartbeats; auto-completing tasks without doing real work |
| **Time-boxing exploits** | Joining/leaving to satisfy thresholds without intent | 31-day uptime followed by deregister to claim "Local Daemon" badge then abandon |
| **Tier-boundary surfing** | Operating just above the threshold needed for next rank | Running exactly the minimum models needed for Model Hoarder, no diversity intent |
| **Identity laundering** | New operator identity to escape reputation history | Bad actor caught spinning up sock-puppets → registers new operator handle, resets to clean slate |
| **Geographic spoofing** | Reporting false region to win regional championships | All nodes claiming `region=eu-central` but actually running in one datacenter |
| **Collusion** | Multiple operators cooperate to game group metrics | Two operators artificially exchange tasks to inflate `completed_tasks_count` for both |

## Per-item attack/mitigation

### Ranks

| Rank | Attack | Mitigation |
|---|---|---|
| Node Initiate | Register and never serve a task — claim the rank trivially | Acceptable: this is the entry rank, low value. No mitigation needed. |
| Mesh Serf (7d heartbeat) | Heartbeats with no real backend (mock /iicp/health) | REACH probes against the node's `/iicp/health` MUST return reachable + valid model list (DIR-TRUST-01 catches divergent model declarations). Without real backend, the trust audit reports a divergence within 1 hour. |
| Local Daemon (30d uptime + models) | Run with 1 trivial model nobody routes to | Genuinely earnable — declaring a model isn't harmful. The badge says "your machine joined", not "your machine matters". Acceptable bar. |
| Intent Weaver (1000 tasks) | Collude with another operator to artificially route to each other | Detection: anomalous task source distribution — if 90% of a node's traffic comes from 1 proxy node_id, flag for review. Mitigation: require ≥3 distinct proxy node_ids contributed traffic to the 1000-task count. |
| CIP Provider | Self-declare `allow_remote_inference=true` without actually serving CIP | REACH conformance probes DIR-CIP-01/02 already verify the field is present + filtering works. Spec says CIP-Provider MUST handle CIP task envelopes — runtime test confirms. |
| REACH Herald | Single VPS in eu-central claiming reachability | Multi-location probes — only counts when ≥3 distinct probe regions confirm reachable. Currently blocked on REACH geographic expansion (deliverable 02 gap). |
| Mesh Guardian (90d + 99% heartbeat) | Same Mesh Serf attack at scale | Same mitigation: REACH trust audit catches degenerate /iicp/health. Adds: declared_models_match flag must remain true throughout the 90d window. |
| Forge Baron (10k tasks + multiple models) | Same as Intent Weaver collusion at scale | Same mitigation: ≥3 distinct proxy contributors required. At 10k scale, organic traffic distribution should easily satisfy. |
| Mesh Legend (top 10) | Sock-puppet army of 50 nodes inflating composite | **Hard mitigation: operator identity layer.** Top-10 is per *operator*, not per *node*. See "Operator identity" section below. |

### Badges

| Badge | Attack | Mitigation |
|---|---|---|
| First Blood | Complete one fake task | Acceptable. Trivial bar; not worth gaming. |
| Uptime Chad (99.5%/60d) | Fake heartbeats with no backend | DIR-TRUST-01 + DIR-FED-07 health checks must pass throughout. Detection: divergent model declarations break Uptime Chad. |
| Model Hoarder (≥5 models) | Declare 5 model_ids without actually serving them | DIR-TRUST-01: `/iicp/health` MUST return all 5 in `models[]`. Trust auditor reports -0.05 reputation if registered_models ⊄ health_models. |
| Chaos Agent (≥3 family-distinct models) | Declare 3 obviously-different model_ids that aren't actually loaded | Same as Model Hoarder — health endpoint must report them. Model-family classification rules (deliverable 02 partial) determine "family distinct". |
| Rust Enjoyer | Spoof `User-Agent: iicp-node/Rust` on a Python adapter | Minor stake. Detection: combined with /iicp/health binary signature (iicp-node returns specific fields the Python adapter doesn't). Mitigation: badge is decorative; if false-positive happens, low harm. |
| Task Gladiator (50k) | Collusion at scale | Same `≥3 distinct contributors` rule (Intent Weaver / Forge Baron). At 50k scale, near-impossible to fake naturally. |
| Diversity Champion (most models in country) | Spin up 10 cloud nodes in `region=eu-central` each declaring 1 model | **Operator identity layer**: same operator's models are deduplicated for the badge — declare the same model_id on 5 nodes still counts as 1 distinct model. |
| Global Node (multiple continents probed) | Run cloud nodes in 3 continents, all same operator | Same operator identity dedup — "global node" of a single operator is acceptable (it really is reachable globally), but it doesn't give that operator the "Founding Cohort" tier of distinct operators. |
| Credit Earner (1000 credits) | Self-fund via collusion | Same collusion mitigation (≥3 distinct paying proxy contributors). |
| Reliable One | Skip operation during marked disruption windows, claim badge | Detection: disruption windows are maintainer-annotated post-incident; only earnable for nodes that *were online* during the window. Heartbeats before/after the window don't count. |
| Country Pioneer | First node from country, gamed by being first to claim a country code | One per identity. If the same operator registers a node from Brazil → claims "Brazilian Pioneer" → claims an Argentinian node → claims "Argentinian Pioneer", that's allowed (genuine multi-country operation) but counted as one *operator*, not two, in operator-diversity metrics. |
| Founding Cohort | Register early under one identity, claim cohort, then run new fake identities | One per identity. Operator-identity is permanent — see below. |

### Temporal cohorts

| Cohort | Attack | Mitigation |
|---|---|---|
| Class of YEAR | Register Dec 31 23:59 and complete one task to claim full-year cohort | Threshold: ≥N days active (suggest ≥7) within the year. Token-effort earned identity. |
| H1/H2 Season exclusive | Register first day of season, abandon | Threshold: ≥30 days active + ≥M tasks served during the season window. Genuine participation required. |

## Operator identity — the crucial layer

The single biggest anti-gaming mechanism is binding nodes to operators. Without this, all
sock-puppet attacks succeed.

### Identity model proposal

Each operator has a **handle** (chosen at first registration) and a **persistent identifier**.
Multiple nodes can register under one handle. Identity creation:

1. **Email-based** (simplest): operator provides an email at registration → directory issues an
   operator_token tied to that email. Anti-gaming: same email can register multiple nodes but
   counts as one operator. Throwaway emails (mailinator, etc.) are filtered.
2. **Ed25519-keyed**: operator generates a key pair locally; public key becomes operator_id.
   No email needed. Anti-gaming: cost of generating arbitrary identities is essentially free
   (no Sybil resistance) — needs to be combined with proof-of-work or reputation lock-in.
3. **Federated via existing accounts**: GitHub OAuth, etc. Strongest Sybil resistance via
   existing platform identity. Reintroduces big-tech lock-in and TOS dependencies — likely
   incompatible with the project's federated-by-design philosophy.
4. **Hybrid**: Ed25519 key + optional email/handle. Anonymity supported; verification optional
   for higher tier participation (e.g., Diversity Champion / Country Pioneer requires email-
   verified identity; Node Initiate / Mesh Serf are key-only).

Recommendation: **Hybrid identity model**. Default to key-based pseudonymous; require an
attested identity (email-confirmed or federated) for ranks ≥4 (CIP Provider and above). This
preserves anonymous participation for new operators while gating high-tier identity
recognition behind anti-sybil checks.

This is a substantial design decision and should be elevated to **ADR-030 (Operator Identity
& Anti-Sybil Layer)** before any gamification ships. Cross-references ADR-021 (identity slot)
and ADR-026 (two-sided reputation).

### Sock-puppet detection (without identity layer)

If identity layer isn't in place by gamification launch, fall back to heuristic detection:

- **Source IP clustering**: nodes registering from the same `/24` block within a short window
  flagged for manual review.
- **Endpoint pattern fingerprinting**: `adapter-llama:8080`, `adapter-phi3:8080`, etc. from the
  same operator have identical container-image style endpoints. Cluster + dedupe.
- **Registration timing**: 10 nodes registering within 5 minutes from adjacent IPs = one
  operator. Group them.
- **Public-key reuse**: Ed25519 nodes presenting the same `signer_did` are the same operator.

These heuristics are weaker than explicit identity but catch the obvious sock-puppet patterns.
W-016's FC-001 finding ("all 8 nodes from one operator group, identical defaults, same region")
is exactly the kind of cluster the heuristics would flag.

## W-016 / FC-001 interaction

The gamification system's "external operator count" metric MUST be consistent with W-016's
finding. If the IICP working group runs 10 nodes:
- Internal accounting: 10 nodes, 1 operator group
- External accounting (for ADOPTION D7): 1 operator group, 0 external operators
- Gamification leaderboards: all 10 nodes can earn badges, but they're all tagged with the
  Genesis Cohort (or Zero Kelvin operator), so a visitor sees "founding team" not "10 different
  operators"

Anti-gaming guarantee: the FC-001 correction (D7 91 → ~60) cannot be defeated by spinning up
more working-group nodes. Operator-diversity ranks need *external* operators by definition.

## Identity laundering — soft mitigation

When a bad actor is caught (sock-puppet detection fires, fraud confirmed), the registered
operator_id can be:
- **Flagged** in the operator profile (visible)
- **Excluded from leaderboards** while keeping access to network operations
- **Capped on future ranks** (cannot exceed rank 2 Local Daemon)

This is preferred over outright bans, which would prompt identity laundering attempts. The
bad actor still has utility (their node serves traffic) but cannot recover their reputation
in the recognition system. New identities can join cleanly — fresh operators shouldn't pay
for someone else's bad behavior — but the original identity is permanently downgraded.

## Hard rules for the gamification spec

When `spec/iicp-recognition.md` is written, these rules MUST be normative:

1. **Same operator nodes do not multiply operator-diversity scores** (Country Pioneer, Diversity
   Champion regional tier, Founding Cohort count).
2. **DIR-TRUST-01 must pass** for any rank ≥ Mesh Serf or any badge with a model-related
   trigger. Trust audit divergence forfeits eligibility.
3. **Collusion-resistant task counts** require ≥3 distinct proxy contributors before the count
   qualifies for any ≥1000-task badge.
4. **Disruption windows are maintainer-annotated post-incident**, not operator-claimed.
5. **Operator identity is permanent**: laundering an identity (re-registering after being
   flagged) does not restore reputation in the recognition system.
6. **Season badges require minimum genuine activity** (≥30d + ≥M tasks) — not just registration
   in the window.

## Next deliverable

`04-rollout-gates.md` — explicit conditions under which gamification is safe to ship. Cross-
references #260 (public-launch), W-016 (operator diversity), ADR-030-proposed (identity layer),
and the bootstrapping plan for the Founding Cohort permanent membership.
