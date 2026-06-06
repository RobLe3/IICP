# Gamification Track 02 — Metric Mapping

**Status**: Draft (iter-296, 2026-05-21)
**Companion**: `01-design-rationale.md`, `project/gamification.md`
**Tracking**: #267

---

## Purpose

For every rank and badge in the Nerd Legacy concept, identify the **underlying telemetry source**
and verify it's **computable from existing data** without new collection scope. If any item
requires telemetry the directory or REACH doesn't already capture, flag it for a separate
"telemetry extension" research deliverable.

## Data sources available today

| Source | Where it lives | What it captures |
|---|---|---|
| **Directory: `nodes` table** | `directory/database/migrations/...nodes` | node_id, endpoint, region, public_endpoint, available, last_seen, observed_source_ip, max_concurrent, tokens_per_min |
| **Directory: `capabilities` table** | `...capabilities` | intent, model_family, model_id, quantization, inference_engine, max_tokens, attested (per-node, multi-row) |
| **Directory: `node_events` table** | `NodeEventLogger` writes here | seq, event_id, event_type ∈ {REGISTER, HEARTBEAT, SCORE_UPDATE, REPUTATION_UPDATE, CREDIT_AWARD, DEREGISTER}, payload (JSON), ts_ms, signature, signer_did |
| **Directory: `reputation` table** | `Reputation` model | node_id, score, tasks_total, tasks_failed, completed_tasks_count, avg_latency_ms |
| **Directory: `credit_events` table** | TelemetryController + CreditsController writes | node_id, amount, nonce, parent_task_id, awarded_at |
| **REACH: probe results** | `/api/v1/stats` aggregate + raw probe stream pushed by daemon | per-probe pass/fail, latency_ms, region origin, test_id |
| **Cloudflare logs** (out of band) | CF dashboard | request count by path — not currently piped into directory |

## Ranks — telemetry mapping

| Rank | Trigger | Source | Computable today? | Notes |
|---|---|---|---|---|
| 0 Node Initiate | First REGISTER event | `node_events.event_type='REGISTER'` | ✅ yes | Emit on first registration acknowledgement |
| 1 Mesh Serf | 7 days of successful heartbeats | `node_events.event_type='HEARTBEAT'` over 7d rolling, success ratio ≥ N | ✅ yes | Need to define "successful heartbeat" — probably any HEARTBEAT row counted as ok unless preceded by REPUTATION_UPDATE drop |
| 2 Local Daemon | 30 days uptime + ≥1 model | `min(last_seen) > 30d ago` + `capabilities WHERE node_id=X COUNT ≥ 1` | ✅ yes | Uptime = days since first REGISTER without intervening DEREGISTER |
| 3 Intent Weaver | 1,000 tasks completed | `reputation.completed_tasks_count ≥ 1000` | ✅ yes | Counter already exists |
| 4 CIP Provider | Full CIP conformance | `nodes` field `allow_remote_inference=true` AND CIP-Provider in capabilities | ✅ yes | Already surfaced as `cip_conformance_level` in /v1/discover |
| 5 REACH Herald | Reachable from multiple locations | REACH probe stream — count distinct `region_origin` with PASS for this node's `/iicp/health` over 30d | ⚠ partial | REACH currently 1 probe location (EU-DE-Cologne). Need geographic probe expansion before this is meaningful |
| 6 Mesh Guardian | 90+ days uptime + 99%+ heartbeat success | uptime calc above + heartbeat-success rolling 90d | ✅ yes | Threshold tuning open; spec the rate carefully |
| 7 Forge Baron | 10,000+ tasks + multiple models | `reputation.completed_tasks_count ≥ 10000` + `capabilities COUNT(DISTINCT model_id) ≥ N` | ✅ yes | |
| 8 Mesh Legend | Top 10 nodes globally | ranked composite score (next deliverable defines formula) | ✅ yes once formula defined | Risk: definition will be contentious; treat as living recipe |
| Zero Kelvin | Manual — Genesis Seed maintainer | `signer_did = did:web:iicp.network` permanent assignment | ✅ trivial | |

**Verdict**: 9/10 ranks computable today. **REACH Herald** needs probe-location expansion (currently 1 location); flag as a downstream dependency.

## Badges — telemetry mapping

### Core badges

| Badge | Trigger | Source | Computable today? |
|---|---|---|---|
| First Blood | First task successfully routed | `reputation.completed_tasks_count` transitions 0→1 | ✅ yes |
| Uptime Chad | 99.5%+ heartbeat success / 60d | rolling 60d HEARTBEAT success ratio | ✅ yes |
| Model Hoarder | ≥5 distinct models | `capabilities COUNT(DISTINCT model_id) WHERE node_id=X ≥ 5` | ✅ yes |
| Chaos Agent | ≥3 very different models concurrently | model family classification (model_family field exists) — heuristic: ≥3 distinct family_classes | ⚠ partial | Needs "model family classification" rules — may belong in spec, not data |
| Rust Enjoyer | Running official Rust iicp-node | nodes.user_agent field? | ⚠ partial | The Rust node identifies itself via User-Agent on register; ensure directory stores it (low effort) |
| Task Gladiator | 50,000+ tasks | `reputation.completed_tasks_count ≥ 50000` | ✅ yes |
| Diversity Champion (per country) | Most distinct models in nodes.region=country | `RANK() OVER (PARTITION BY region ORDER BY COUNT(DISTINCT model_id) DESC) = 1` | ✅ yes |
| Global Node | Probed from multiple continents | Geographic probe-location aggregation | ⚠ partial | REACH Herald dependency — same blocker |
| Credit Earner | First 1,000 credits | `SUM(credit_events.amount WHERE node_id=X) crosses 1000` | ✅ yes |
| Reliable One | High success across multiple network disruptions | Heuristic: > N HEARTBEAT events within 60d of a known mesh-wide disruption window | ⚠ partial | Needs "disruption window" definition — may be a manual annotation by maintainer, like marking known incident periods |

### Special badges

| Badge | Trigger | Source | Computable today? |
|---|---|---|---|
| Country Pioneer (Danish Pioneer, etc.) | First node from a given country | `MIN(REGISTER ts) PARTITION BY country` | ✅ yes if we map region → country (region field is "eu-central" not "DE" — need lookup table) |
| Early Meshborn | Joined when <100 nodes existed | `REGISTER ts < ts_when_total_active_nodes_first_hit_100` | ✅ yes — but requires a precomputed historical milestone marker |
| Potato Compute | Strong performance on low-resource hardware | `max_concurrent ≤ 2 AND completed_tasks_count ≥ N` | ✅ yes |
| OpenAI Whisperer | High success on OpenAI-compat requests | Requires intent classification at task level (currently aggregate `reputation.tasks_total`); needs per-intent breakdown | ⚠ partial | Currently directory doesn't store per-intent task success — would need `task_events` table or per-intent reputation. Open scope. |
| Mesh Multiplier | Served 100+ distinct clients | `COUNT(DISTINCT proxy_node_id FROM task_events WHERE provider_node_id=X) ≥ 100` | ⚠ partial | Same blocker — per-task records aren't surfaced in directory state today |

## Temporal cohorts — telemetry mapping

| Badge | Trigger | Source | Computable today? |
|---|---|---|---|
| Class of YEAR | ≥1 successful task in calendar year | `EXISTS(reputation.completed_tasks_count > 0 AND first_task_ts in year)` — need to capture first-task-ts | ⚠ partial | `reputation` doesn't track first task timestamp; need to derive from `credit_events.awarded_at MIN` or store explicitly |
| H1/H2 SEASON badge | Active ≥N days in season window | HEARTBEAT events filtered by ts within season window | ✅ yes |
| Season-Top-N badge | Top N by metric within season window | Standard window-function queries | ✅ yes |

## Composite "rank score" formula (for Mesh Legend / Living Mesh Lords)

Proposal (open for iteration in deliverable 03 anti-gaming):

```
rank_score = 0.30 * uptime_pct
           + 0.25 * task_throughput_norm
           + 0.20 * model_diversity_norm
           + 0.15 * cip_conformance_bonus  (0 / 50 / 100 for None / Provider / Full)
           + 0.10 * reach_diversity_norm   (gated on REACH expansion)
```

Where each `*_norm` is min-max normalized to [0, 100] across the active operator population.
The formula is deliberately weighted toward reliability + diversity over raw throughput to
prevent single-machine-with-fastest-GPU dominance.

## Summary — telemetry readiness

| Verdict | Count | Items |
|---|---|---|
| ✅ Fully computable today | 16 | Most ranks, most core badges, season windows |
| ⚠ Partial (data exists but schema/aggregation gap) | 7 | REACH Herald, Global Node, Chaos Agent, Rust Enjoyer, Reliable One, OpenAI Whisperer, Mesh Multiplier, Class of YEAR |
| ❌ Not computable today | 0 | None |

**Telemetry extensions needed before launch** (priority order):

1. **REACH probe geographic expansion** (high) — REACH Herald + Global Node require ≥2 probe regions; currently 1. Needs maintainer infra setup (e.g. Cloudflare Workers as probe origins, or volunteer operators running REACH instances).
2. **Per-task / per-intent records** (medium) — OpenAI Whisperer, Mesh Multiplier, Reliable One need finer-grained task records. Could be a new `task_events` table with `proxy_node_id`, `provider_node_id`, `intent`, `result`, `ts_ms`. Storage scope: 1 row per dispatched task, indexed by provider_node_id.
3. **First-task timestamp on reputation row** (low) — `reputation.first_task_at` column added at next migration; populated lazily from credit_events MIN.
4. **User-Agent capture on REGISTER** (trivial) — RegisterController logs `user_agent` field if present; Rust node's reqwest sends a recognizable UA.
5. **Region → country mapping table** (trivial) — static lookup; `eu-central` → `DE`, `eu-west` → `IE`/`FR`, etc.
6. **Model family classification rules** (open) — likely a JSON file or spec section; this is also useful for routing heuristics.
7. **Historical milestone markers** (low) — `mesh_milestones` table: `(milestone_name, reached_at_ts)`; populated by maintainer (e.g., "100th node registered: 2026-XX-XX").
8. **Disruption windows** (low) — `mesh_disruptions` table or annotated incident log; manual entry by maintainer.

None of these require novel infrastructure — they're modest schema additions and lookup tables.
The total telemetry-extension scope is bounded and matches the maintainer's intent of
"recognition flows from existing operation, no new tracking".

## Next deliverable

`03-anti-gaming.md` — for each rank and badge, define the gaming attack vector and the
detection / mitigation. Includes the sock-puppet operator-diversity check that interacts with
W-016 / FC-001 (multiple nodes from one person shouldn't satisfy "external operator" tier).
