# R3 — Discovery Layer: Centralized Directory vs. DHT

**Track**: R1R7 — Provider Selection & Multi-Path Routing  
**Issue**: #175 (R3: Discovery layer — centralized directory vs. DHT)  
**Date**: 2026-05-18  
**Author**: RESA loop, FORGE iter82  
**Depends on**: R1 (#173) — protocol/policy boundary complete  
**Length**: ≈1900 words (within ≤2000 limit)  
**Recommendation**: **Stay centralized through Phase 5; begin federated substrate with ADR-013; DHT gated on concrete trigger (§5).**

---

## 1. The Question

IICP currently runs a single centralized directory at iicp.network. Should this
architecture persist into Phase 5+ and beyond? What are the concrete trade-offs, and at
what trigger does decentralization become warranted?

Note: ADR-013 (federated control plane) is already in progress, introducing a hierarchy
of Genesis Seed / Replica / Gossip nodes. This design does not evaluate ADR-013 — it
already represents a strong intermediate answer. The question here is whether to go
further (full DHT-based discovery) and under what conditions.

---

## 2. What the Centralized Directory Does Well

**Simplicity and debuggability.** A single authority means a single source of truth for
node membership, reputation, and capability declarations. When a client cannot find a
provider for a given intent, the failure mode is unambiguous: either no nodes have
registered the capability, or the directory is unreachable. There is no consistency
puzzle (different nodes seeing different membership lists), no convergence wait, and no
routing-table churn to diagnose.

**Shared-hosting deploy substrate.** `iicp.network` runs on DomainFactory shared hosting
via LFTP/FTPS. This is intentional — it demonstrates that IICP's control plane does not
require cloud infrastructure to operate. A DHT requires nodes running continuously,
maintaining routing tables, and responding to membership probes. That is fundamentally
incompatible with shared-hosting operation. As long as the Genesis Seed must be operable
on low-cost infrastructure, centralized (or lightly federated) is the correct architecture.

**Zero bootstrap cost for new nodes.** Registration is a single POST to a known URL.
The node is immediately discoverable. DHT join requires contacting a bootstrap node,
computing a node ID, inserting key/value pairs, and waiting for the routing table to
stabilize. This represents 10–100× more operational complexity for new node operators.

**Sybil surface is contained.** The centralized directory controls admission: a node
can register only if it passes the registration check (identity proof, capability
declaration, challenge). In a pure DHT, Sybil attacks are structurally harder to contain
because any node can join and claim any content. Combined with reputation and
identity-age mechanisms from REP track, the centralized model is well-equipped for
adversarial environments at current scale.

---

## 3. What the Centralized Directory Does Poorly

**Single point of failure.** If `iicp.network` is unreachable, client discovery is
blocked entirely. The network can still route tasks to previously-discovered providers
(clients can cache; REACH probes confirm the live network is operational), but new
intents against undiscovered providers will fail. ADR-013's Replica tier partially
mitigates this — a Replica can serve discover requests independently — but the Genesis
Seed remains authoritative for registration.

**Censorship surface.** A single operator controls who is discoverable. This is
acceptable when the operator is the protocol designer and the network is small (7 nodes,
all known participants). It becomes a design liability when the network grows to hundreds
of operators who may have adversarial relationships with each other or with the directory
operator. The protocol's privacy properties (task payloads never touch the directory)
mitigate this, but exclusion from discovery is still a censorship vector.

**Scaling ceiling (soft, not hard).** The current directory architecture can handle
tens of thousands of registered nodes (PHP + MySQL on shared hosting is adequate for
that load at infrequent heartbeat cadence). The scaling ceiling is not a near-term
concern. However, at 100,000+ nodes, a centralized directory with real-time heartbeats
becomes an operations challenge. This is a 5–10 year problem, not a Phase 5 problem.

**Operator trust requirement.** Clients must trust the directory operator to accurately
report reputation scores, tier classifications, and capability declarations. ADR-013's
Replica system introduces independent verification of role assignments, which partially
breaks this trust requirement. A DHT would make node membership self-verifiable without
trusting any operator.

---

## 4. What DHT-Based Discovery Would Add and Cost

**What it adds:**

- *Censorship resistance*: No single operator can block a node from being discoverable.
  A node that publishes its capability key to the DHT is reachable regardless of any
  one operator's decision.
- *Structural decentralization*: Network membership is verifiable from the DHT without
  trusting a central party. This is the strongest argument for DHT, but it requires the
  threat model to actually include a hostile directory operator.
- *Operator diversity at scale*: DHT is self-governing above some participation
  threshold. At 10,000+ nodes with diverse operators, no single party controls routing.

**What it costs:**

- *Capability-key complexity*: The current directory indexes nodes by intent URN, which
  is a well-defined namespace. A DHT requires a capability-key construction: something
  like `hash(intent_urn | context_window | modality | privacy_class)`. The key space
  must be sized correctly — too coarse and lookups return too many candidates; too fine
  and popular intents are split across many unrelated DHT regions. IICP's multi-dimensional
  capability space makes this non-trivial (see §4.1 below).
- *Reputation integration*: The centralized directory is the natural place to maintain
  reputation scores (it sees all heartbeats and registration events). In a DHT, reputation
  aggregation requires a separate mechanism — either a centralized reputation oracle
  (defeating part of the point) or a distributed reputation protocol (very hard to make
  adversarially robust; the REP track simulation findings show how hard reputation is
  even in the simplified centralized model).
- *Bootstrap complexity*: DHT membership requires a bootstrap node list. Without a
  well-known bootstrap node, new participants cannot join. This simply pushes the
  centralization problem one level down (from the directory to the bootstrap list).
  Ethereum, IPFS, and similar networks all require maintained bootstrap node lists.
- *Gossip and churn handling*: DHT routing tables must be maintained under continuous
  churn (nodes register/deregister). At 7 nodes, churn is negligible. At 10,000 nodes
  with typical cloud-VM lifetimes (hours to days), churn is significant. Handling churn
  in a Kademlia-style DHT requires continuous background gossip and repair.
- *Harder debugging*: When a client cannot find a provider in a DHT, the failure could
  be: key not published, key published but not yet propagated, routing table stale,
  the specific DHT region unavailable. Diagnosing this requires DHT-specific tooling
  (equivalent to `dig`, `traceroute`, `mtr` — but for DHT routing). Currently absent.

### 4.1 Capability-Key Construction Assessment

The current directory indexes by intent URN. A client queries `GET /v1/discover?intent=urn:iicp:intent:llm:chat:v1` and receives nodes matching that intent. The directory filters by additional capability fields (context window, modality, privacy class) server-side.

A DHT requires a routing key. Options:

| Option | Key shape | Problem |
|--------|-----------|---------|
| Intent URN only | `hash(intent_urn)` | Too coarse — all nodes for `llm:chat` in one key; privacy class not encoded |
| Full capability tuple | `hash(intent | context | modality | privacy)` | Combinatorial explosion — n intents × m context sizes × k modalities × j privacy classes → too many keys |
| Hierarchical DHT | Separate key spaces per dimension | Complex; no standard DHT supports this natively |
| Directory overlay | DHT for membership + centralized for capability filtering | Hybrid; complexity without full decentralization benefit |

None of the key shapes is clean for IICP's capability space. The multi-dimensional filtering that the centralized directory does server-side (and does well) is genuinely hard to replicate in a pure DHT. This is the strongest technical argument against a DHT transition before the capability namespace is proven stable.

---

## 5. Recommendation: Stay Centralized; Federate via ADR-013; DHT Gated on Trigger

**Recommendation**: V1 stays centralized (with the ADR-013 federated extension already
in progress). Full DHT-based discovery is gated on the following trigger condition:

> DHT evaluation warranted when **all three** hold simultaneously:
> 1. Active node count ≥ 10,000 (DHT routing tables need minimum viable size; below this, overhead dominates benefit)
> 2. A concrete, documented case of directory-operator censorship has been observed or credibly threatened
> 3. The reputation aggregation problem for a DHT has a proposed solution — either a distributed reputation protocol with adversarial guarantees, or acceptance of a reputation oracle that clients can swap

None of these conditions is met in Phase 5 or any foreseeable Phase 6 planning horizon
at current growth rate.

**ADR-013 federation satisfies the Phase 5+ need.** The Genesis Seed / Replica / Gossip
hierarchy:
- Breaks single-operator dependency for discover requests (Replicas can serve independently)
- Introduces independent verification of role assignments
- Allows geographic distribution of directory capacity
- Does not require solving the capability-key construction problem or the distributed reputation problem

This is the correct level of decentralization for current scale and threat model.

**Implication for ADR-003 (centralized directory).** ADR-003 does not need to be
superseded. It should be annotated: "Valid for Phase 1–5. ADR-013 extends with
federation. DHT gated on §5 trigger (R3 finding, 2026-05-18)."

---

## 6. Acceptance Criteria Verification

| AC | Requirement | Status |
|----|-------------|--------|
| Trade-off analysis covers both directions fairly | §2 (centralized strengths), §3 (weaknesses), §4 (DHT trade-offs) | ✓ |
| Trigger condition for decentralization is concrete and verifiable | §5: 3-condition trigger | ✓ |
| Capability-key construction assessed | §4.1: 4 options analyzed; none clean | ✓ |
| Clear recommendation with justification | §5: stay centralized, federate via ADR-013, DHT gated | ✓ |
