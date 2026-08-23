# IICP federation current-state scaling model

Status: research evidence, 23 August 2026. This is not a protocol profile or a claim of Internet-scale operation.

## Decision

Keep the current full-state federation model for the present beta network. It is simple, preserves exact provider records at every participating directory, and has not reached a measured operational limit.

Do not change Phase 6 wire semantics on the strength of a synthetic capacity model. If independent multi-root operation later demonstrates that full replication is the limiting factor, evaluate an **optional domain-summary federation profile**. A summary would locate an authoritative domain; that domain would still perform exact discovery and current eligibility evaluation. Canonical Intent and Capability identifiers would remain opaque and unchanged.

This decision separates two questions:

* Snapshot plus finite event tail bounds **history growth**.
* Replicating every current provider record still produces **current-state growth proportional to provider population**.

The existing specification solves the first problem. This report measures the second.

## Repeat the model

The model uses only the Python standard library. Its assumptions are embedded in `model.py`, hashed in the generated result, and deliberately conservative rather than calibrated as production forecasts.

```bash
python3 research/federation/state-scaling/model.py --json \
  > research/federation/state-scaling/results-v1.json
python3 -m unittest discover \
  -s research/federation/state-scaling -p 'test_*.py'
```

Assumption digest: `cf4960820db3f983add4a82b7033ee51de48024d99e3d0413c86cc51b9f12a35`.

Important inputs include a 4 KiB provider record, 25% local index overhead, 1 KiB state-change events, 0.5% provider-state change per hour, 64 capability-prefix summaries per domain, and 60- or 300-second summary refresh intervals. Heartbeats remain local, consistent with the current federation specification; they are not counted as federated events.

The distribution is intentionally uneven. The largest domain contains 25% of providers in the 1,000-provider case, tapering to 1% in the 100-million-provider thought experiment. This exposes a weakness hidden by even-shard averages.

## Equations

For provider count `N`, domain count `D`, provider-record size `R`, index factor `I`, summary entries per domain `C`, summary-entry size `S`, and state changes per provider-hour `U`:

```text
full state per directory = N × R × I
full state across D directories = D × N × R × I
local shard per directory = ceil(N / D) × R × I
domain summaries per directory = D × C × S
state-change traffic per directory-hour = ceil(N × U) × event size
worst summary staleness = configured refresh interval + transport delay
partition recovery lower bound = changes missed during the partition
partition recovery upper bound = a fresh authoritative snapshot
```

The model does not predict database compression, protocol framing, query caches, cryptographic overhead, retries, or real workload skew. Results are capacity bounds for comparing architectures, not deployment sizing guidance.

## Results

| Providers | Domains | Full state/directory | Even local shard | Largest skewed shard | Local shard + all summaries | Full-state event traffic/directory-hour |
|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 10 | 4.88 MiB | 540 KiB | 1.26 MiB | 700 KiB | 5 KiB |
| 100,000 | 100 | 488.28 MiB | 5.27 MiB | 49.22 MiB | 6.84 MiB | 500 KiB |
| 1,000,000 | 1,000 | 4.77 GiB | 8.79 MiB | 248.05 MiB | 24.41 MiB | 4.88 MiB |
| 100,000,000 | 10,000 | 476.84 GiB | 87.89 MiB | 4.81 GiB | 244.14 MiB | 488.28 MiB |

The last row is a stress thought experiment, not a target or support claim. At that size, the assumptions yield 500,000 global state changes per hour and as many as 41,667 changed providers during a five-minute summary window. That illustrates why a summary can become stale; it does not establish a safe operating threshold.

## Architecture comparison

| Property | Full current state | Domain/shard ownership | Hierarchical/domain summaries |
|---|---|---|---|
| State at each directory | Exact record for every provider | Exact local records plus domain descriptors | Exact local records plus bounded capability summaries |
| Update traffic | Every relevant state change reaches every replica | Local changes remain local; descriptors change infrequently | Local changes remain local; summaries refresh or change incrementally |
| Freshness | Limited by federation convergence | Exact locally; remote candidates require a domain query | Summary may be stale until refresh; exact domain query remains required |
| Partition behavior | Replica can select from its last known global state | Remote domains become unavailable or last-known | Summary can direct a query but cannot prove present availability |
| Recovery | Event-tail replay or snapshot | Reconcile local shard and domain descriptors | Reconcile local state and refresh summaries; snapshot remains fallback |
| Selection accuracy | Highest candidate visibility, subject to stale state | Exact within the authoritative domain | False-positive candidate domains are possible; false negatives depend on summary design |
| Policy fidelity | Full advertised metadata is locally available | Policy checked by the authoritative domain and requester | Summary may prefilter only; authoritative policy and eligibility checks remain mandatory |
| Complexity | Lowest | Requires domain ownership and query routing | Highest; also requires aggregation, freshness, and downgrade rules |

Aggregation weakens global, immediately queryable visibility. It must not weaken these guarantees:

1. A summary is not endpoint authentication.
2. A summary is not a dispatch ticket or execution authority.
3. A summary is not proof of current reachability, availability, policy compliance, or eligibility.
4. The authoritative domain must revalidate exact constraints before returning an eligible provider.
5. The caller and endpoint retain their existing authentication and authorization decisions.
6. Unknown optional summaries may be ignored. An unsupported required profile must fail closed through existing profile negotiation.

## DRISAC crosswalk

The comparison uses the primary text of `draft-wang-dmsc-drisac-01` (18 August 2026). It is an individual Internet-Draft, expires 19 February 2027, requests no IANA action, and is not an adopted standard.

| DRISAC concept | Comparable IICP concern | Boundary for IICP |
|---|---|---|
| Agent Capability Access Server keeps locally attached agent records | Authoritative directory/domain owns exact local provider records | A later profile could preserve this locality without adopting DRISAC messages |
| Agent Capability Management Servers exchange aggregated capability tables | Federated directories could advertise bounded domain summaries | Summary syntax and hierarchy are unresolved research, not current IICP behavior |
| Hierarchical capability classification | IICP needs a scalable candidate-domain index | IICP Intent and Capability identifiers remain canonical opaque values; no forced hierarchy |
| Intent is mapped to a capability vector for forwarding | IICP discovers against an Intent, constraints, policy, and effective capabilities | Mapping must not discard policy or convert a candidate hint into eligibility |
| Capability-aware forwarding reaches a local access server | Summary directs an exact query to the authoritative domain | Existing session, endpoint-authentication, dispatch, and execution layers remain separate |

Primary source: <https://www.ietf.org/archive/id/draft-wang-dmsc-drisac-01.txt>

## Security and privacy

A future summary design would need explicit defenses and conformance cases for:

* **summary poisoning:** a domain advertises capabilities it cannot provide;
* **capability suppression:** an intermediary omits legitimate domains or capabilities;
* **stale availability:** old summaries continue to attract queries during outage or revocation;
* **domain capture:** one authority controls a disproportionately important branch;
* **Sybil amplification:** many cheap domains inflate apparent coverage or routing weight;
* **enumeration:** aggregation exposes provider classes, demand, or sensitive capabilities;
* **private topology leakage:** restricted-domain membership or structure crosses its policy boundary;
* **downgrade:** a peer substitutes weaker summary behavior for required full-state semantics.

Signed summaries can identify the issuer and protect integrity, but cannot prove the truth of the advertised capability. Bounded validity, sequence/epoch handling, policy-scoped disclosure, authoritative re-query, and independently verifiable execution evidence would still be required.

## Threshold for revisiting the decision

Open a separate protocol-profile issue only after operational evidence shows that current-state replication, convergence traffic, or recovery time is a material blocker in independently administered multi-root operation. That issue must define fixtures, privacy rules, security properties, required/optional negotiation, downgrade behavior, and the accuracy loss accepted by aggregation.

Until then, public material should say that IICP bounds federation history. It should not describe current-state federation as Internet-scale.
