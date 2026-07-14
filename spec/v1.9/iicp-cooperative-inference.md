# S.12 — IICP Cooperative Inference Protocol (CIP)

**Status**: Draft (active — normative text in §2–§7, §10; §4 wire format normative per 0.4.0-draft)  
**Version**: 0.6.13
**Phase**: 5 (Cooperative Inference)  
**Authors**: Protocol Steward  
**Linked ADR**: ADR-012 (Phase 5 CIP Scoring Formula), ADR-019 (Declarative Node Pricing)  
**GitHub**: Issues #67 (spec), #68 (policy block), #69 (TOML config), #84 (security), #149 (BC-11)  
**RFC 2119**: The key words "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", and "MAY" in this document are to be interpreted as described in RFC 2119.

---

## 1. Purpose

The Cooperative Inference Protocol (CIP) extends IICP to allow a single task to be
executed across multiple nodes simultaneously. This enables:

- **Best-of-N**: Fan out to N peers; return the highest-quality result.
- **Majority vote**: Fan out to N peers (typically odd); return the result that ≥ ⌈N/2⌉ peers agree on.
- **Map-reduce**: Split a large task into subtasks, distribute across peers, aggregate.

CIP is a Phase 5 feature. It requires the Phase 4 Rust node and Phase 3 reputation
scoring to be deployed first.

---

## 2. Roles

| Role | Description |
|------|-------------|
| **Coordinator** | The node that receives the original task. Fans out to Worker nodes. |
| **Worker** | A peer node that executes a subtask or a full-task copy. |
| **Aggregator** | Function (or node) that combines Worker results into the final response. |

In Phase 5, the Coordinator and Aggregator roles are always the same node (the proxy
or the node that received the original client task).

### 2.1 Provider Opt-In (Phase B)

A node participates in CIP as a Worker only when it has explicitly opted in via its registration policy block.

**Normative requirements for Provider nodes:**

- A node MUST include `"policy": {"allow_remote_inference": true}` in its REGISTER payload to be eligible for CIP worker selection. Absence of the `policy` block or `allow_remote_inference: false` means the node MUST NOT be assigned cooperative sub-tasks.
- A provider node MUST enforce its configured `minimum_reputation` floor. If the requesting coordinator's reputation score is below this floor, the provider MUST reject the sub-task with error code `IICP-E020` (reputation threshold not met).
- A provider node MUST NOT exceed its configured `max_concurrent_remote` limit. If the limit is reached, the provider MUST return `IICP-E021` (capacity exhausted) — NOT silently queue or delay.
- A provider MUST include `"cip_role": "worker"` in the RESPONSE `trace` object when executing a CIP sub-task.
- A provider node MUST NOT modify the intent URN of a CIP sub-task — it MUST execute the exact intent received from the coordinator.
- A provider SHOULD report actual token usage in the RESPONSE `metrics.tokens_used` field, accurate to within 5%.

**Policy block discovery:** The directory MUST surface `policy.allow_remote_inference` in `GET /v1/discover` responses. Clients MAY filter CIP-eligible nodes by including `filter.cip_capable=true` in the discovery request. The directory MUST treat absence of the `policy` block as `allow_remote_inference=false`.

#### 2.1.1 REGISTER policy block schema (#68 — CIP-S2)

The `policy` block is an optional object in the REGISTER request body. All fields are optional; omitting the block is equivalent to all fields at their defaults.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `allow_remote_inference` | bool | `false` | Node participates as CIP Worker |
| `allow_tool_execution` | bool | `false` | Node accepts tasks with tool-execution intent domain |
| `allow_file_access` | bool | `false` | Node accepts tasks requiring filesystem reads/writes |
| `minimum_reputation` | float [0.0–1.0] | `0.0` | Minimum coordinator reputation score required; coordinators below this threshold receive IICP-E020 |
| `max_concurrent_remote` | int ≥ 1 | `2` | Maximum simultaneous CIP sub-tasks accepted; excess receives IICP-E021 |

Backward-compatibility: nodes omitting the `policy` block are treated as `allow_remote_inference=false` by the directory. Phase 1–4 nodes are unaffected.

**Provider adapter.toml schema** (#69 — CIP-S3 provider side):

```toml
[cooperative_inference]
enabled = false                  # MUST default false
allow_remote_inference = false   # mirrors REGISTER policy block
allow_tool_execution = false     # mirrors REGISTER policy block
allow_file_access = false        # mirrors REGISTER policy block
minimum_reputation = 0.0         # coordinator reputation floor (0.0 = accept all)
max_concurrent_remote = 2        # MUST be ≥ 1
```

### 2.2 Consumer Activation (Phase A)

A consumer proxy enables CIP by setting `cooperative_inference.enabled = true` in `proxy.toml`. All CIP behavior is off by default.

**Normative requirements for Consumer nodes:**

- A consumer MUST NOT dispatch CIP sub-tasks to remote workers unless `cooperative_inference.enabled = true` in the active proxy configuration.
- A consumer MUST evaluate the estimated credit cost before dispatching any CIP sub-task. If `estimated_credits > max_credits_per_task`, the consumer MUST fall back to local execution and MUST NOT dispatch to remote workers.
- A consumer SHOULD call `GET /v1/credits/quote` before dispatching any CIP sub-task. The directory response includes `consumer_balance` (caller's node-local balance), `effective_balance`, `balance_scope` (`"node"` or `"operator_wallet"`), optional `operator_wallet_balance`, and `balance_sufficient` (boolean: `effective_balance ≥ estimated_credits`). If `balance_sufficient = false`, the consumer MUST fall back to local execution.
- A consumer MUST NOT dispatch a task to remote workers when:
  - The task has `constraints.sensitivity = "high"` AND `privacy.send_sensitive_prompts = false` (the default). The consumer MUST execute locally in this case.
  - The consumer has no reachable workers with `policy.allow_remote_inference = true` in the current discovery cache.
- When `trusted_peers` is non-empty, a consumer SHOULD prefer workers in that allow-list over unlisted nodes at equivalent quality scores.
- A consumer SHOULD implement the `local-first` strategy by default: attempt local execution first; fall back to remote workers only if local execution fails or no local model is available for the requested intent.
- A consumer that cannot complete a task locally AND has no eligible remote workers MUST return a structured error (code `IICP-E022`: no CIP workers available) rather than silently failing.

**Consumer configuration schema** (#69 — CIP-S3, canonical — `proxy.toml`):

```toml
[cooperative_inference]
enabled = false                        # MUST default false
strategy = "local-first"               # local-first | remote-first | balanced
max_credits_per_task = 10.0            # MUST be > 0; reject at startup otherwise
min_reputation = 0.0                   # minimum worker reputation (0.0 = no filter)
trusted_peers = []                     # empty = open (any CIP-capable node)

[cooperative_inference.privacy]
send_sensitive_prompts = false         # MUST default false; never forward sensitive tasks
```

---

## 3. CIP Execution Modes

### 3.1 Best-of-N

```
Client → Coordinator → [Worker1, Worker2, ... WorkerN]
                              ↓ all results
Coordinator ← ResultAggregator (picks highest-score result by intent-specific criterion)
Client ← Coordinator
```

**Configuration**: `cip_policy = "best_of_n"`, `cip_replicas = N`  
**Scoring criterion**: Lowest perplexity for language tasks; most complete for structured output tasks.  
**N**: 2–5 recommended; > 5 requires explicit operator opt-in.

**Normative requirements — Best-of-N:**

- A Coordinator MUST fan out to exactly `cip.replicas` Worker nodes. If fewer than `cip.replicas` eligible workers are available at dispatch time, the Coordinator MUST fall back to local execution or return `IICP-E022` (no CIP workers available); it MUST NOT dispatch to a reduced replica count.
- `cip.replicas` MUST be in the range [2, `cooperative_inference.max_replicas`]. The coordinator MUST reject configurations with `cip.replicas < 2` or `cip.replicas > max_replicas` at startup and MUST NOT allow runtime override.
- The Coordinator MUST issue all worker subtask requests concurrently (not sequentially) and MUST wait up to `worker_timeout` (see §6) before aggregating.
- If at least one worker responds within `worker_timeout`, the Coordinator MUST select the result with the highest quality score computed by an intent-specific criterion (see §3.1.1 below). The Coordinator MUST NOT return an unscored result.
- If zero workers respond within `worker_timeout`, the Coordinator MUST fall back to local execution if a local model is available; otherwise MUST return a structured error `IICP-E024` (all workers timed out).
- The Coordinator MUST record the number of responding workers and the selected worker's ID in the response `trace.cip_aggregation` object.

**§3.1.1 Quality scoring criterion:**

| Intent category | Criterion |
|-----------------|-----------|
| `urn:iicp:intent:llm:*` (text generation) | Lowest perplexity score. If no perplexity is available, prefer the longest non-truncated response. |
| `urn:iicp:intent:llm:structured:*` | Most fields populated in the declared output schema; fewest null/missing fields. |
| All other intents | First response received within worker_timeout (latency-first fallback). |

### 3.2 Majority Vote

```
Client → Coordinator → [Worker1, Worker2, Worker3]
                              ↓ all results
Coordinator ← ResultAggregator (majority vote: ≥ 2/3 agreement)
Client ← Coordinator
```

**Configuration**: `cip_policy = "majority_vote"`, `cip_replicas = 3` (must be odd)  
**Agreement criterion**: Semantic equivalence (embedding cosine similarity ≥ 0.95).  
**Tie-break**: Lowest-latency result wins.

**Normative requirements — Majority Vote:**

- `cip.replicas` MUST be an odd integer ≥ 3. A Coordinator MUST reject a `majority_vote` request with even `cip.replicas` at parse time (before dispatch) with a client error `IICP-E025` (invalid replica count for majority_vote).
- The Coordinator MUST aggregate responses using semantic equivalence: two responses are considered equivalent when their embedding cosine similarity is ≥ 0.95. Implementations without embedding capability MUST fall back to exact-match string equivalence on the first 512 characters of the response.
- A majority is reached when ≥ `cip.quorum` workers agree. If `cip.quorum` is null, the Coordinator MUST compute the strict-majority quorum as `floor(N / 2) + 1`. Because `majority_vote` requires odd `N`, this is equivalent to `ceil(N / 2)` for every valid request. Implementations MUST NOT add another `+ 1` after applying `ceil(N / 2)`.
- If a quorum is reached within `worker_timeout`, the Coordinator MUST return the majority result. Among the agreeing responses, the Coordinator MUST select the one from the worker with the lowest `metrics.latency_ms`.
- If no quorum is reached within `worker_timeout`, the Coordinator MUST fall back per §6 fallback rules. The Coordinator MUST NOT synthesize or blend non-majority results.
- The Coordinator MUST include the quorum vote tally (`cip_vote_count`, `cip_quorum_threshold`) in the response `trace.cip_aggregation` object for auditability.

### 3.3 Map-Reduce (Phase 5+)

Splits long documents or large prompt batches into independent chunks, distributes to
workers, and concatenates results. Requires the task payload to declare a
`split_strategy` field.

**Status**: Planned for Phase 5 implementation. Coordinator-side split and aggregation logic is not yet implemented in iicp-node.

**Normative requirements — Map-Reduce (planning normative — binding on Phase 5 implementations):**

- Each subtask produced by the split MUST be independently executable: a subtask MUST NOT reference or depend on the output of any sibling subtask in the same batch.
- The Coordinator MUST validate that `split_strategy` produces non-overlapping, complete coverage of the input before dispatching. If coverage gaps are detected, the Coordinator MUST abort and return `IICP-E026` (incomplete map split).
- Workers MUST NOT be aware that they are processing a map-reduce subtask — the subtask MUST be a valid standalone IICP CALL with the original intent URN.
- The Coordinator MUST perform concatenation/aggregation of results in the order defined by the `split_strategy.chunk_index` field, not in arrival order.
- If any subtask fails and no fallback value is defined for that chunk, the Coordinator MUST fail the entire map-reduce task (partial results MUST NOT be returned to the client).

---

## 4. Wire Format

### 4.1 CIP CALL extension fields

CIP extends the IICP CALL message (see IICP-core Phase 1 conformance profile) with
optional fields in the `constraints` object:

```json
{
  "task_id": "uuid-v4",
  "intent": "urn:iicp:intent:llm:chat:v1",
  "payload": { "messages": [...] },
  "constraints": {
    "timeout_ms": 30000,
    "cip": {
      "policy": "best_of_n",
      "replicas": 3,
      "quorum": null
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `cip.policy` | string | `best_of_n` \| `majority_vote` \| `map_reduce` |
| `cip.replicas` | integer | Number of worker nodes to fan out to (2–5) |
| `cip.quorum` | integer\|null | Minimum agreeing workers for majority_vote (null → `floor(N/2)+1`; equivalently `ceil(N/2)` for valid odd N) |

**Normative requirements — CIP CALL field validation:**

- A Coordinator MUST validate `cip.policy` before dispatching. Valid values are `"best_of_n"`, `"majority_vote"`, and `"map_reduce"`. Any other value MUST be rejected with `IICP-E028` (invalid CIP field value).
- `cip.replicas` MUST be a positive integer in the range [1, 10]. A Coordinator MUST reject requests with `cip.replicas` outside this range with `IICP-E028`. For `"majority_vote"`, `cip.replicas` MUST additionally be odd (see §3.2; rejection error: `IICP-E025`).
- `cip.quorum` MUST be `null` or a positive integer ≤ `cip.replicas`. A non-null `cip.quorum` that exceeds `cip.replicas` MUST be rejected with `IICP-E028`.
- A Coordinator MUST NOT process a CIP CALL where the `cip` object is present but `cip.policy` is absent. Such requests MUST be rejected with `IICP-E028`.
- All four validation checks MUST occur at parse time, before any worker selection or dispatch.

### 4.2 Subtask CALL (Coordinator → Worker)

Workers receive a standard IICP CALL with an additional `cip_role` field:

```json
{
  "task_id": "uuid-v4",
  "intent": "urn:iicp:intent:llm:chat:v1",
  "payload": { "messages": [...] },
  "constraints": { "timeout_ms": 15000 },
  "trace": {
    "trace_id": "propagated-from-client",
    "origin_node": "coordinator-node-id",
    "cip_role": "worker",
    "cip_parent_task_id": "parent-uuid-v4"
  }
}
```

Workers MUST respond with a standard IICP RESPONSE. Workers MUST NOT further fan out
(no recursive CIP — a Worker receiving a CIP-tagged task with `cip_role = worker`
MUST execute locally and return).

**Normative requirements — Subtask trace fields:**

- A Coordinator MUST set `trace.cip_role = "coordinator"` in its own CALL `trace` when initiating CIP dispatch. A Worker MUST set `trace.cip_role = "worker"` in its RESPONSE `trace` when executing a CIP sub-task.
- A CALL with `trace.cip_role` set to any value other than `"coordinator"` or `"worker"` MUST be rejected with `IICP-E028` (invalid CIP role).
- `trace.cip_parent_task_id` MUST be a valid UUID v4 string. A Worker that receives a sub-task with a malformed `cip_parent_task_id` (not matching UUID v4 format) MUST reject the request with `IICP-E028`.
- A Coordinator MUST include `trace.cip_session_key` in every sub-task CALL dispatched to Workers. Workers MUST echo the received `cip_session_key` unchanged in their RESPONSE `trace` (see §10.4). A Worker MUST NOT modify or omit the `cip_session_key` it received.

### 4.3 Response — CIP Aggregation Object

Coordinator RESPONSES MUST include a `cip_aggregation` object within `trace` whenever a CIP policy was activated (at least one sub-task was dispatched):

```json
{
  "trace": {
    "trace_id": "...",
    "cip_aggregation": {
      "policy": "best_of_n",
      "replicas_dispatched": 3,
      "replicas_responded": 2,
      "selected_worker_id": "node-uuid-v4",
      "aggregation_latency_ms": 45,
      "cip_vote_count": null,
      "cip_quorum_threshold": null
    }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `policy` | string | MUST | The `cip.policy` value used for this aggregation |
| `replicas_dispatched` | integer | MUST | Number of worker nodes contacted |
| `replicas_responded` | integer | MUST | Number of workers that returned a result within `worker_timeout` |
| `selected_worker_id` | string\|null | MUST | Node ID of the worker whose result was returned; `null` if zero workers responded |
| `aggregation_latency_ms` | integer | SHOULD | Elapsed time from last worker response received to aggregation complete |
| `cip_vote_count` | integer\|null | MUST for majority_vote | Number of workers in the agreeing majority |
| `cip_quorum_threshold` | integer\|null | MUST for majority_vote | Strict-majority quorum required (`floor(N/2)+1`, or explicit `cip.quorum`) |

**Normative requirements — CIP aggregation object:**

- A Coordinator MUST include `cip_aggregation.replicas_dispatched` and `cip_aggregation.replicas_responded` in every CIP RESPONSE. These fields are required for coordinator-level auditability and credit accounting.
- For `majority_vote` mode, `cip_vote_count` and `cip_quorum_threshold` MUST be populated with non-null values.
- If zero workers responded (`replicas_responded = 0`), the Coordinator MUST still include the `cip_aggregation` object with `selected_worker_id = null` and `replicas_responded = 0`. Omitting the object when dispatch failed is a protocol violation.

---

## 5. Node Selection for CIP

CIP uses the ADR-008 scoring formula (with Phase 5 price + model_match terms from
ADR-012) to select Worker nodes from the peer list. Additional CIP-specific constraints:

- Workers MUST support the requested intent (model_match = 1.0 preferred).
- Workers MUST NOT be the Coordinator itself.
- Workers MUST have `available = true` and `load < 0.8` at selection time.
- Coordinator MUST select Workers from known peers (not via directory discovery) to
  avoid adding directory latency to the critical path.

### 5.1 Reputation-Aware Routing

Worker eligibility is gated on a minimum reputation score that decays over time when
a node is inactive (no completed tasks) and recovers as the node completes tasks
successfully.

**Reputation decay function:**

```
R_effective(t) = R_base × decay(t)
decay(t) = max(R_floor, 1.0 - λ × idle_hours(t))
```

Where:
- `R_base` — the node's current reputation score (range [0.0, 1.0])
- `λ` — decay rate, default `0.005` per idle hour (decays ~50% after 100h idle)
- `idle_hours(t)` — hours since last successful task completion, capped at 200h
- `R_floor = 0.3` — minimum decay floor; reachable-but-idle nodes are never scored below 0.3

**Normative requirements:**

- A Coordinator MUST NOT select a Worker whose `R_effective` is below the Coordinator's configured `min_reputation` threshold (default: 0.0 = no filter).
- A Worker that has `allow_remote_inference = true` but has been idle for > 200 hours MUST be scored at `R_effective = R_base × 0.3` (full decay floor), not removed from the eligible pool.
- The reputation score used for CIP routing MUST be the directory's most recently observed `reputation_score` for the node — the Coordinator MUST NOT compute a local reputation estimate from peer observations alone.

**Recovery**: Each successfully completed CIP sub-task increments the node's reputation by `+0.05 × (1 - R_base)` (bounded at 1.0). Failed or timed-out sub-tasks apply a `−0.15` penalty (per spec §3.3 consensus outlier rule).

### 5.1.1 Tier Structure — RATIFIED 2026-05-24

> **Status**: RATIFIED. REP1 and REP2 research tracks (16 independent simulation runs,
> #168 #171 #172 closed 2026-05-24) confirm these values. The decay floor (0.30),
> tier thresholds (0.40/0.65/0.85), and identity-age gate (720h) are now normative.
> Implementation verified in directory v1.9.19 (ReputationDecayCommand, NodeScorer).

The following tier thresholds are used for routing priority and service eligibility.
A node's **effective tier** for routing is determined by BOTH reputation score AND identity age:

| Tier | Reputation threshold | Identity-age requirement | Routing priority |
|------|---------------------|--------------------------|-----------------|
| Bronze | ≥ 0.00 | None | Lowest — fallback only |
| Silver | ≥ 0.40 | None | Standard routing |
| Gold | ≥ 0.65 | None | Preferred routing |
| Platinum | ≥ 0.85 | ≥ 720 hours (30 days) | Highest priority routing |

**Identity-age conjunctive gate**: A node whose reputation score is ≥ 0.85 but whose
`identity_age_hours` is < 720 is routed as Gold, not Platinum. This prevents whitewash
attacks where an agent quickly builds reputation and then resets identity.

- Demotion does NOT reset `identity_age_hours` — only a whitewash (identity reset) does.
- `identity_age_hours` is tracked by the directory from node registration onward.
- Starting credit for new nodes is 0.50 (places new nodes at Silver tier from registration).

**NODELIST surface**: The directory's `GET /v1/discover` response MUST include a
`reputation_tier` field in each node record. The field value MUST be one of:
`"bronze"` (floor tier, reputation ≥ 0.00 — the value the directory emits for
sub-Silver nodes, including probation nodes), `"silver"`, `"gold"`, or `"platinum"`.
The platinum gate uses node registration age (`created_at`) as the identity-age proxy.

> **Enum note (reconciled 2026-05-30)**: Earlier drafts named the floor tier `"none"`.
> The shipped directory (`NodeScorer`) emits `"bronze"` for the floor tier, matching the
> tier table above. Clients MUST treat `"bronze"` as the floor; `"none"` is retired.

**General reputation update rules** (normative — ratified 2026-05-24, separate from CIP-specific
adjustments above):

| Event | Δ reputation |
|-------|-------------|
| Task success | +0.01 (+quality×0.005 bonus) |
| Task failure | −0.05 |
| CIP sub-task success | +0.05 × (1 − R_base) (CIP-specific, more verifiable) |
| CIP sub-task failure | −0.15 (CIP-specific, consensus-backed evidence) |

The CIP-specific adjustments are more aggressive than general task adjustments because
CIP consensus provides stronger evidence of node quality or failure.

---

### 5.1.2 Bootstrap Traffic Floor — RATIFIED 2026-05-24

> **Status**: RATIFIED. RS6-F1 cold-start finding confirmed by REP6 live-readiness
> assessment (#168 #172 closed 2026-05-24). Bootstrap floor is now normative.
> Implementation in Coordinator routing logic is a Phase 5 deliverable.

**Problem**: A node whose reputation score falls below the Silver threshold (0.40) is
excluded from standard routing. With no traffic, it cannot accumulate successful tasks,
so it cannot recover its score. This is structurally identical to the cold-start problem
but in reverse — a **floor trap**.

The bootstrap floor breaks this cycle by guaranteeing a minimum amount of exploration
traffic to recovering nodes.

**Floor rule** (normative):

A Coordinator MUST route at least one sub-task per session to a node in the **bootstrap
pool** when the following conditions are jointly met:

1. The node's reputation score is ≥ `R_floor` (0.30 — below this, the node is effectively
   suspended) AND < Silver threshold (0.40), OR the node's reputation score is ≥ Silver
   AND `lifetime_jobs < 100`.
2. The node has been seen within the last 90 seconds (last heartbeat within liveness window).
3. The Coordinator's pool for the current task has ≥ 3 eligible Silver-or-above nodes
   (the floor MUST NOT degrade pool quality when the pool is thin).

**Rationale**: Condition 3 ensures the floor does not force low-quality results on clients
with small pools. The floor fires only when the Coordinator has enough good alternatives
to absorb one exploration slot without material quality loss.

**Session floor count**: Exactly 1 bootstrap slot per session (defined as: per unique
`coordinator_node_id` within a 30-minute rolling window). This limits the floor's cost
impact: at 30-minute cadence, a new node reaches 100 lifetime jobs in ≈ 50 days.

**Directory signal**: The NODELIST response MUST include `lifetime_jobs` (integer) and
`status` (string: "active" | "dormant") so Coordinators can evaluate bootstrap pool
eligibility without a separate lookup.

**Interaction with §5.1.1 tier thresholds**: The bootstrap floor applies to nodes at
Silver tier with `lifetime_jobs < 100` AND to nodes in the recovery band (0.30 ≤ score < 0.40).
Once `lifetime_jobs ≥ 100`, standard ε-greedy routing governs without the floor guarantee.

---

## 5.2 Conformance Levels

CIP defines three conformance profiles. Implementations declare at most one profile.

| Profile | Required Capabilities | Exclusions |
|---------|----------------------|------------|
| **CIP-None** | Phase 1–4 behavior: no CIP capabilities declared. Default for nodes that do not opt in. | Cannot participate in CIP fan-out or credit settlement. |
| **CIP-Consumer** | Can send CIP CALL messages (§4.1). Enforces `max_credits`, `max_multiplier`, `min_quality_score`. Supports `local-first` strategy. Does NOT fan out. | Cannot act as Coordinator. No worker selection. |
| **CIP-Provider** | Can receive and execute CIP sub-tasks (§4.2). Enforces `max_concurrent_remote`, `minimum_reputation`. Returns `cip_role = worker` in trace. | Cannot initiate fan-out. No aggregation logic. |
| **CIP-Full** | All of CIP-Consumer + CIP-Provider + full Coordinator/Aggregator. Supports best_of_n, majority_vote, and map_reduce. Handles credit settlement (§7) and consensus fallback (§6). | — |

Nodes declare their profile in the REGISTER payload via:

```json
{
  "cip_conformance_level": "CIP-None | CIP-Consumer | CIP-Provider | CIP-Full"
}
```

`"CIP-None"` means Phase 1–4 behavior: no CIP capabilities. Directory surfaces
`cip_conformance_level` in NODELIST with `"CIP-None"` as the default when a node
has not opted into any CIP role. Nodes declaring `CIP-Full` MUST satisfy ALL
normative requirements in §2–§10 of this document. Partial implementations MUST
declare the most restrictive matching profile.

---

## 6. Coordinator Timeout Budget

```
coordinator_timeout = task.timeout_ms
worker_timeout = coordinator_timeout × 0.6   (60% — leaves time for aggregation)
aggregation_budget = coordinator_timeout × 0.3
```

If fewer than `cip.quorum` Workers respond within `worker_timeout`, the Coordinator
MUST fall back to its own local result (if available) or return a structured error.

---

## 7. Credit Accounting

In CIP mode, each Worker node earns credits for the tokens it processed. The
Coordinator earns a coordination fee:

```
coordinator_credits = Σ(worker_tokens) × 0.05   (5% of total)
worker_credits[i] = worker_tokens[i] × 1.0
```

All credit reports include `cip_parent_task_id` for auditability.

**Rate parity — no CIP premium.** CIP tasks are priced on the **same** schedule as
standard routed tasks: `routing_cost = ceil(output_tokens/1000) × tier_weight ×
credit_cost_multiplier` (iicp-billing-extension §10.1/§10.2). There is **no CIP-specific
rate premium** (#305). The `× 1.0` worker rate and `× 0.05` coordination fee above are the
*split* of that cost, not a surcharge — CIP's HMAC/settlement overhead is protocol cost,
not routing cost. A premium would break the credit-neutrality invariant and reward faking
CIP compliance; CIP providers compete on reputation, not price. (An operator MAY still set
a higher `credit_cost_multiplier` per ADR-019 as market positioning — node-declared, not a
protocol CIP differential.)

**Normative requirements — Credit Accounting:**

- Every Worker MUST report its actual token usage in `metrics.tokens_used` in the RESPONSE, accurate to within 5% of the model's reported token count. Estimates MUST NOT be substituted for actual counts when actual counts are available from the inference backend.
- The Coordinator MUST NOT award credits to a Worker whose response was not used in the final aggregation result (e.g. a non-majority result in majority_vote mode or a lower-scoring result in best-of-N). Credits MUST be awarded only to the Worker(s) whose response was selected or contributed to the final result.
- The Coordinator MUST compute `coordinator_credits = Σ(selected_worker_tokens) × 0.05`. The coordination fee MUST NOT exceed the coordinator's own local processing cost for an equivalent task (cost floor invariant).
- All credit settlement messages generated for a CIP task MUST include the `cip_parent_task_id` field, populated with the `task_id` of the original client CALL. Absence of this field MUST cause the directory to reject the credit award request.
- The Coordinator MUST generate a signed `CIPReceipt` (§10.3) for each Worker whose credits are awarded. The `CIPReceipt.worker_id` MUST match the Worker's registered node ID. Coordinators MUST NOT batch multiple Workers into a single receipt.
- A Worker MUST NOT self-report credit awards. Credit awards MUST originate exclusively from the Coordinator of the session in which the Worker participated.
- The directory MUST validate the `CIPReceipt` signature (HMAC-SHA256, §10.3) before processing any credit award. An invalid or absent signature MUST result in rejection with `IICP-E027` (invalid receipt signature).

### 7.1 Free Evaluation Allocation

To enable new operators to try the mesh before earning or purchasing credits, the
directory MUST implement a free credit allocation for any registered node with a
zero balance:

- **Allocation amount**: 5 credits per allocation period.
- **Period**: 6 hours. A node is eligible for a fresh allocation when its credit
  balance is zero AND at least 6 hours have elapsed since its last free allocation
  (or it has never received one).
- **Eligibility**: any registered `node_token` (worker nodes and pure proxy/client
  registrations). Eligibility is per `node_token`, not per IP address.
- **Trigger**: the directory MAY allocate lazily (on the first credit balance query
  or at registration). The directory MUST NOT accumulate un-dispensed credits across
  periods — if a node's balance remains zero across multiple periods, it receives
  only one period's worth (5 credits) on the next query, not multiples.
- **Anti-Sybil**: the registration rate limit (`IICP-E034`, §8 registration) bounds
  abuse at the network level. Per-IP Sybil resistance (ADR-030) is a Phase 6
  hardening concern and does not block this mechanism.

**Normative requirements — Free Evaluation Allocation:**

- The directory MUST award exactly 5 credits per eligible period. It MUST NOT award
  partial allocations or accumulate across missed periods.
- The directory MUST log each allocation with event type `CREDIT_ALLOCATION` in the
  node lifecycle event log. The log entry MUST include `amount`, `reason`, and
  `period_h` fields.
- The directory MUST NOT award a free allocation when the node's balance is greater
  than zero, even if the 6-hour period has elapsed.

---

## 8. Conformance Requirements (Deferred — Phase 5)

The following conformance requirements are defined here for Phase 5 implementation.
Test marks: `@pytest.mark.phase5`. All IDs map to `spec/conformance-test-suite.md §12`.

### 8.1 Coordinator Behaviour

| ID | Requirement | Test file |
|----|-------------|-----------|
| CIP-01 | Coordinator MUST fan out to exactly `cip.replicas` worker nodes. | `tests/integration/test_cip_coordinator.py` |
| CIP-02 | Worker receiving `cip_role = worker` MUST NOT further fan out. | `tests/integration/test_cip_coordinator.py` |
| CIP-03 | Coordinator MUST fall back to local result if quorum not met within `worker_timeout`. | `tests/integration/test_cip_fallback.py` |
| CIP-04 | All credit reports in CIP mode MUST include `cip_parent_task_id`. | `tests/integration/test_cip_credits.py` |
| CIP-05 | `map_reduce` split MUST produce independently-executable subtasks (no cross-subtask dependencies). | `tests/integration/test_cip_map_reduce.py` |

### 8.2 Worker Behaviour

| ID | Requirement | Test file |
|----|-------------|-----------|
| CIP-W01 | Worker MUST return standard IICP RESPONSE with `cip.role = worker`. | `tests/integration/test_cip_coordinator.py` |
| CIP-W02 | Worker MUST NOT accept tasks with `cip.replicas > 1` (no cascading). | `tests/integration/test_cip_coordinator.py` |

### 8.3 Policy Enforcement

| ID | Requirement | Test file |
|----|-------------|-----------|
| CIP-P01 | Adapter MUST enforce `cooperative_inference.max_replicas` from config. | `tests/integration/test_cip_policy.py` |
| CIP-P02 | Consumer proxy MUST respect `credit_spending_limit` before CIP routing. | `tests/integration/test_cip_credits.py` |

---

## 9. Phase Readiness

| Prerequisite | Status |
|-------------|--------|
| Phase 4 Rust node (iicp-node) | Implemented — pending Milestone 1 gate |
| Phase 3 reputation scoring | Specced (ADR-008 Phase 3 weights) |
| ADR-012 accepted (price + model_match terms) | Proposed — needs PS + SA sign-off |
| S.12 conformance test suite additions | Pending (spec/conformance-test-suite.md §12) |

**CIP implementation gate**: ADR-012 must be Accepted (not just Proposed) and Phase 4
Milestone 1 gate must be closed before any CIP code is written.

---

## 10. Safety Boundaries and Forbidden Operations

This section defines MUST NOT constraints that apply to all CIP roles regardless of operator configuration. These rules enforce the data sovereignty invariant (ADR-001) in a multi-node execution context and mitigate the TC-9a..d abuse vectors defined in the IICP threat model.

### 10.1 Data Sovereignty (TC-9b mitigation)

- Workers MUST NOT execute operating system shell commands, file system read/write operations, or outbound network requests on behalf of a coordinator. The task payload is the sole input; the result is the sole output.
- Workers MUST NOT log, cache, or forward the coordinator's system prompt, conversation history, user identity, or any field not explicitly included in the submitted task payload.
- Coordinators MUST NOT include the client's full conversation history in CIP sub-task payloads — only the minimal context required for the sub-task intent SHOULD be forwarded.
- Implementations MUST NOT use CIP to forward credentials, API keys, access tokens, or any material that grants authority beyond the current task.

### 10.2 Sensitive Task Protection (TC-9a mitigation)

- A consumer MUST NOT dispatch a task with `constraints.sensitivity = "high"` to remote CIP workers when `privacy.send_sensitive_prompts = false`. This check MUST occur before worker selection — not as a post-selection gate.
- If a task's intent URN is in a category that the operator has designated as locally-only (configurable via `trusted_peers = []` with `strategy = "local-first"`), the consumer MUST NOT fall back to remote workers for that task category even if local execution fails.
- A provider MUST NOT accept a CIP sub-task whose intent URN is not in the provider's declared `capabilities` list, even if the request includes a valid node_token.

### 10.3 Credit Receipt Integrity (TC-9c mitigation)

- Every credit settlement receipt generated for a CIP task MUST include a `receipt_nonce` (cryptographically random, ≥ 128 bits) and an `expires_at` timestamp (ISO-8601, ≤ task completion time + 300s).
- The directory MUST reject any credit award request whose `receipt_nonce` has been seen before (replay protection). Nonce storage MUST be maintained for at least 24 hours after `expires_at`.
- Coordinators MUST NOT reuse a `receipt_nonce` across multiple CIP sessions or task IDs.

**Canonical message format for CIPWorkerReceipt HMAC-SHA256 (Phase 5):**

The HMAC-SHA256 signature MUST be computed over the following canonical message (UTF-8 encoded, colon-delimited fields):

**Without `querying_node_id`** (legacy, backwards-compatible):
```
{task_id}:{tokens_used}:{cip_parent_task_id}:{cip_session_key}:{nonce}:{response_hash}
```

**With `querying_node_id`** (v0.7.50+, preferred — required for credit spending):
```
{task_id}:{tokens_used}:{cip_parent_task_id}:{cip_session_key}:{nonce}:{response_hash}:{querying_node_id}
```

The directory determines which form to reconstruct based on whether `querying_node_id` is present and non-empty in the receipt body. Implementations MUST NOT include a `querying_node_id` in the canonical message unless it is also present in the receipt body — mixing the extended canonical with a missing body field is a signature mismatch.

Where:
- `task_id`: The Worker's sub-task UUID (not the parent coordinator task UUID)
- `tokens_used`: Integer token count as reported by the inference backend (actual, not estimated)
- `cip_parent_task_id`: The coordinator's parent task UUID, or the empty string `""` if absent
- `cip_session_key`: The session key received from the Coordinator (see §10.4), or `""` if absent
- `nonce`: The `receipt_nonce` value (hex-encoded, ≥ 32 hex characters = 128 bits)
- `response_hash`: SHA-256 hex digest (64 lowercase hex characters) of the canonical JSON encoding of the task `result` field — `sha256(json.dumps(result, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()`. For a null/empty result, use SHA-256 of zero bytes (`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).
- `querying_node_id` (optional today; see evolution below): The `node_id` of the consumer node that dispatched the original task, forwarded from the task body `source_node_id` field. Including this field in the HMAC canonical message is REQUIRED when `querying_node_id` is present in the receipt body — it prevents a malicious serving node from fabricating or substituting a foreign `querying_node_id` to drain that operator's credit balance (TC-9e). **Note**: because it is optional and the serving node is the receipt's author, a self-dealing serving node can OMIT it to skip the self-query-neutrality exclusion (`CreditsController`); TC-9e protects *foreign* balances, not against self-dealing.

> **Anti-self-deal evolution (future profile, #525)**: a future CIP minor MAY (a) make `querying_node_id` **REQUIRED** for any credit/reputation gain, and (b) require the receipt to be **consumer co-signed** — the querying node signs an attestation that it received `result` for `task_id` from the serving node — so the serving node can neither omit nor fabricate the counterparty. The directory verifies BOTH signatures. This closes self-dealing at the root and is rolled out as an iicp-dir §6.1 capability migration (additive co-signature → measured adoption → hard-require), never a silent break.

**`response_hash` requirement (Phase 5)**: The Worker MUST include `response_hash` in every `CIPWorkerReceipt`. A receipt without `response_hash` MUST be rejected by the Coordinator (hash check fails) and by the directory (returns `IICP-E027`). The Coordinator MUST verify `compute_response_hash(received_result) == receipt.response_hash` BEFORE returning the response to the end client AND BEFORE submitting the credit award. Hash mismatch MUST result in the Coordinator discarding the response and trying the next eligible Worker.

**Signing key**: The Worker's `node_hmac_key` as provisioned by the directory at registration (UTF-8 encoded string used directly as the HMAC key).

**Algorithm**: HMAC-SHA256 with `hmac.compare_digest` (constant-time) for verification.

**Directory verification (IICP-E027)**: To validate a CIPWorkerReceipt, the directory MUST:
1. Look up the Worker's registered `node_hmac_key` by `worker_id` from the receipt. If the node has no `node_hmac_key` provisioned, the directory MUST return `IICP-E027` (422 Unprocessable Entity) with message `"Node HMAC key not provisioned"`. The node MUST re-register to obtain a fresh key.
2. Reconstruct the canonical message from the receipt's `task_id`, `tokens_used`, `cip_parent_task_id`, `cip_session_key`, `nonce`, `response_hash`, and — if `querying_node_id` is present and non-empty in the receipt body — `querying_node_id` appended as the 7th colon-delimited field.
3. Compute `HMAC-SHA256(node_hmac_key, canonical_message)` and compare with `receipt.signature` using constant-time comparison.
4. If `response_hash` is absent or not a valid 64-character lowercase hex string: return `IICP-E027` (422) with message `"CIPWorkerReceipt missing response_hash"`.
5. If the signature is absent, malformed, or does not match: return `IICP-E027` (422 Unprocessable Entity). The directory MUST NOT credit the Worker in this case.

**Credit debit after award**: After successfully crediting the Worker (step 5 passed), the directory SHOULD attempt to debit the querying node when `querying_node_id` is present. This debit is **best-effort**: if the querying node has insufficient balance, the Worker's award MUST still proceed and the directory MUST log a `CREDIT_SPEND_INSUFFICIENT` event. The `amount` debited MUST equal the `amount` awarded to the Worker. The response SHOULD include a `spent` field (float, credits debited from querying node) and a `spend_reason` field (string, set to `"insufficient_balance"` when the debit was attempted but rejected by an insufficient-balance guard).

**Credit amount ceiling (anti-inflation, TC-9c)**: The directory MUST reject any credit award request where `amount` exceeds the authorized ceiling:

```
ceiling = ceil(tokens_used / 1000) × credit_cost_multiplier × 1.1
```

Where `credit_cost_multiplier` is the node's registered pricing multiplier (default 1.0). The 10% tolerance (`× 1.1`) accommodates rounding in the Worker's billing calculation. The ceiling check MUST occur **before** the nonce lock is acquired — a rejected inflated receipt MUST NOT consume the nonce, so the Worker may resubmit with a corrected amount. Return `IICP-E027` if the ceiling is exceeded.

**Nonce lock atomicity**: The directory MUST acquire the nonce lock using an atomic set-if-not-exists operation (e.g., `Cache::add()` in Laravel, Redis `SETNX`, or equivalent). A non-atomic check-then-set (`has()` + `put()`) introduces a TOCTOU race that allows concurrent duplicate submissions to both pass the uniqueness check. Implementations MUST NOT use a two-step check-then-set for nonce replay protection.

### 10.4 Session Binding (TC-9d mitigation)

- Each CIP sub-task dispatched by a coordinator MUST include a `cip_session_key` derived from the coordinator's `task_id` and a per-session random salt. Workers MUST include this `cip_session_key` in their RESPONSE.
- Coordinators MUST validate that every incoming worker RESPONSE includes the correct `cip_session_key` for the current aggregation session. A RESPONSE with a mismatched or absent `cip_session_key` MUST be discarded and MUST NOT contribute to the aggregation result.
- This prevents a malicious worker from injecting a pre-computed response into a different coordinator's aggregation session.

### 10.5 Policy Denial Rate Limiting (TC-9b/resource protection)

- A provider SHOULD rate-limit incoming CIP policy evaluation requests from a single source. A provider MAY respond with `IICP-E023` (rate limit exceeded) after N consecutive policy evaluation calls (N configurable, SHOULD default 100/minute per source).
- A provider MUST NOT expose detailed rejection reasons that reveal internal capacity or policy configuration to untrusted requesters. The error response SHOULD contain only the error code and a generic message.

### 10.6 Credit Award Rate Limiting (TC-9b: anti-laundering)

Colluding nodes can inflate credit balances by routing tasks between coordinating pairs — one node dispatches CIP tasks to a partner, which earns credits and transfers them back. A per-node hourly award cap bounds the practical benefit of this attack.

- The directory MUST enforce a per-`node_id` credit award rate limit of **1 000 credits per rolling hour** (configurable; default MUST be 1 000).
- If crediting `amount` to a node would cause the node's cumulative award total within the current hour to exceed the limit, the directory MUST reject the request with `IICP-E027` (422 Unprocessable Entity) and the message `"Credit award rate limit exceeded (max 1000 credits/hour per node)"`.
- The rate limit check MUST occur **before** the nonce lock is acquired — a rejected award MUST NOT consume the receipt nonce. This guarantees that a legitimate Worker can resubmit the same receipt after the rate window resets without being blocked by a burned nonce.
- The hourly counter MUST be incremented **only on successful award** — rejected requests (for any reason, including rate-limit rejection) MUST NOT increment the counter.
- The rate limit counter is scoped to the `node_id` field from the credit award request (the Worker's ID). Coordinators are not subject to the award rate limit — they spend credits, they do not earn them.

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.6.13 | 2026-07-14 | Corrected the default `majority_vote` quorum to the strict-majority formula `floor(N/2)+1` (equivalent to `ceil(N/2)` for the required odd replica count) and explicitly prohibited the erroneous double increment. No wire-shape change. |
| 0.6.12 | 2026-06-30 | Credit quote/debit alignment with operator wallet: quote responses include `effective_balance`, `balance_scope` and optional `operator_wallet_balance`; `balance_sufficient` is computed against the effective balance. Award settlement debits operator-bound consumers from their pooled wallet while preserving per-node ledger rows. |
| 0.6.11 | 2026-06-09 | §10.3 HMAC canonical message: extended form `{…}:{response_hash}:{querying_node_id}` when `querying_node_id` is present in receipt body — REQUIRED to prevent a malicious serving node from substituting a foreign `querying_node_id` to drain foreign operator balances (TC-9e, #490). Backwards-compatible: receipts without `querying_node_id` use the 6-field form. §10.3 Credit debit: after awarding the Worker, directory SHOULD best-effort debit the querying node by the same amount; `CREDIT_SPEND_INSUFFICIENT` logged on failure; response includes `spent` + `spend_reason`. Implementation: directory v1.10.25, all 3 SDKs v0.7.50. |
| 0.6.10 | 2026-06-06 | §7 Credit Accounting: added **rate-parity** clause — CIP tasks price on the same schedule as standard routing (no CIP premium, #305); the ×1.0 worker / ×0.05 coordinator rates are the *split* of `routing_cost`, not a surcharge. Cross-refs iicp-billing-extension §10.1–§10.3 (credit schedule + economy fold). |
| 0.6.9 | 2026-05-30 | §5.1.1 reputation_tier enum reconciled (#384): floor tier is `bronze` (matches shipped NodeScorer + the tier table); `none` retired. |
| 0.6.8 | 2026-05-24 | §5.1.1 Tier Structure: RATIFIED — tier thresholds (Silver ≥ 0.40, Gold ≥ 0.65, Platinum ≥ 0.85), identity-age gate (≥ 720h), decay floor (R_floor = 0.30), general reputation update rules. §5.1.2 Bootstrap Traffic Floor: RATIFIED — floor rule normative. PENDING markers removed from both sections. Evidence: REP1/REP2/REP5/REP6 research tracks, #168 #171 #172 closed. Implementation: directory v1.9.19 (ReputationDecayCommand DECAY_FLOOR=0.30, NodeScorer tier thresholds). |
| 0.6.7 | 2026-05-20 | §10.6 Credit Award Rate Limiting: normative per-node hourly cap (1 000 credits/hour, configurable). Directory MUST enforce before nonce lock (rejected awards MUST NOT consume nonce). Counter increments only on successful award. Error: IICP-E027. Closes TC-9b directory-level spec gap. |
| 0.6.6 | 2026-05-20 | §5.2 Conformance Levels: added `CIP-None` as explicit profile for nodes that have not opted into any CIP role. Updated profile table and REGISTER example to use `"CIP-None"` instead of `null`. Consistent with implementation (RegisterController, NodeScorer) — `null` is no longer emitted by the directory. |
| 0.6.5 | 2026-05-19 | §10.3 Directory verification: added HMAC key not provisioned sub-case — if `node_hmac_key` absent from directory record, MUST return IICP-E027 with message "Node HMAC key not provisioned"; node must re-register. Corrected key reference from `node_token` to `node_hmac_key` (implementation uses a dedicated HMAC key issued at registration, not the node auth token). |
| 0.6.4 | 2026-05-19 | §2.2 Consumer: quote pre-flight normative note — directory MUST return `consumer_balance` (caller's credit balance) and `balance_sufficient` (bool: balance ≥ estimated_credits) in `GET /v1/credits/quote` response; consumer MUST fall back to local execution when `balance_sufficient = false`. §5.1.1 NODELIST surface note: `reputation_tier` field MUST appear in each discover node record (`"none"\|"silver"\|"gold"\|"platinum"`); platinum gate uses `created_at` as identity-age proxy. |
| 0.6.3 | 2026-05-19 | §10.3: credit amount ceiling rule — `ceil(tokens_used/1000) × multiplier × 1.1` anti-inflation ceiling (TC-9c); ceiling check MUST precede nonce lock so rejected receipts do not consume nonces. Nonce lock atomicity requirement — MUST use atomic set-if-not-exists (TOCTOU-safe); two-step check-then-set explicitly prohibited. |
| 0.6.2-draft | 2026-05-18 | §5.1.2 Bootstrap Traffic Floor (PENDING ratification): floor-trap problem definition, 1-job-per-session minimum for Silver nodes with <100 lifetime_jobs and recovery-band nodes (0.30≤score<0.40), session definition (30-min rolling window), pool-size guard (≥3 Silver+ nodes required), NODELIST signal requirements. Motivated by RS6-F1 cold-start finding. Tracked in #168. |
| 0.6.1-draft | 2026-05-18 | §5.1.1 Tier Structure (PENDING ratification): REP2 simulation-validated tier thresholds (silver=0.40, gold=0.65, platinum=0.85), identity-age conjunctive gate (≥720h for platinum), starting credit 0.50, general vs CIP-specific delta comparison. Tracked in #168. |
| 0.6.0-draft | 2026-05-17 | §5.1 Reputation-Aware Routing: decay function (λ=0.005/hr, R_floor=0.3, 200h cap), recovery +0.05×(1-R_base) per success, −0.15 outlier penalty. §5.2 Conformance Levels: CIP-Consumer, CIP-Provider, CIP-Full profiles with REGISTER declaration field `cip_conformance_level`. ROADMAP S.12 spec normative content complete; closes #67 spec track. |
| 0.5.0-draft | 2026-05-17 | §2.1.1 REGISTER policy block schema (CIP-S2 #68): normative field table (allow_remote_inference, allow_tool_execution, allow_file_access, minimum_reputation, max_concurrent_remote) with types, defaults, backward-compat guarantee. Provider adapter.toml schema. §2.2 consumer schema: min_reputation field added (CIP-S3 #69). |
| 0.4.0-draft | 2026-05-17 | §4 Wire Format: normative field validation requirements for §4.1 CIP CALL fields (cip.policy enum, cip.replicas range, cip.quorum), §4.2 subtask trace fields (cip_role MUST values, cip_parent_task_id UUID v4, cip_session_key echo), §4.3 new CIP aggregation response object schema + normative requirements. §10.3: canonical HMAC-SHA256 message format for CIPWorkerReceipt (colon-delimited task_id:tokens_used:parent:session:nonce) + directory verification procedure for IICP-E027. IICP-E028 defined (invalid CIP field value). |
| 0.3.0-draft | 2026-05-17 | §3 CIP Execution Modes: normative MUST/SHOULD requirements for Best-of-N (fan-out, quality scoring, timeout), Majority Vote (odd replica, quorum, cosine similarity, tie-break), Map-Reduce (subtask independence, coverage completeness). §7 Credit Accounting: normative MUST rules (actual token count, non-majority no credit, receipt per worker, directory validation of CIPReceipt signature). Error codes IICP-E024..E027. |
| 0.2.0-draft | 2026-05-17 | Added RFC 2119 status; §2.1 Provider Opt-In (normative); §2.2 Consumer Activation (normative); §10 Safety Boundaries (TC-9a..d mitigations). Linked ADR-019 pricing. |
| 0.1.0-draft | 2026-05-15 | Initial stub — wire format, execution modes, node selection, timeout budget, credit accounting |

---

## Sign-off

**Protocol Steward**: S.12 normative content complete (§2–§10, §5.1 reputation decay,
§5.2 conformance levels). Wire format aligns with IICP CALL extension model. Binding
on CIP-Full implementations; CIP-Consumer and CIP-Provider may implement subsets per §5.2.
ADR-012 must be Accepted before CIP coordination code ships. Draft — PS sign-off ✓.
