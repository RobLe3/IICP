# Community Platform 04 — Dogfood Angle (Community-on-Mesh)

**Status**: Draft (iter-301, 2026-05-21)
**Companion**: `01-..03-...md`
**Tracking**: #268

---

## The provocation

> **Could the IICP community platform itself run as a service on the IICP mesh?**

If the mesh routes inference tasks, and the protocol is general-purpose enough, then in
principle a federated forum could be served by IICP nodes as a "community" intent type
(`urn:iicp:intent:community:bbs:v1` or similar). Operators don't just contribute compute —
they contribute community hosting.

This is **provocative**, **aspirational**, and **almost certainly premature today**.
This document explores why, what it would take, and when (if ever) it makes sense.

## Why this is appealing

1. **Maximum philosophical alignment**: the protocol that powers the community IS the protocol
   the community discusses. Zero abstraction leak.
2. **Operator incentive amplification (#267)**: nodes that host community traffic earn a new
   badge tier ("Forum Bearer" or similar). Increases participation surface area.
3. **Resilience compounded**: the community is as resilient as the mesh — both federated, both
   operator-sovereign, both protocol-defined.
4. **A signature story**: "the IICP project's discussion forum is decentralized infrastructure
   that ANYONE can run a piece of" is a much more compelling pitch than "we use Discourse".

## Why it's premature today

1. **Intent shape is wrong**: IICP currently routes *inference tasks* (request-response, single
   shot). A forum is a *stateful read-modify-write* application with strong consistency needs
   on threads + comments. The protocol would need a fundamentally new mode.
2. **The CRDT / replication problem**: federated forum state across N operator nodes requires
   a CRDT or similar conflict-free data structure. This is hard. Lemmy + ActivityPub already
   solved it (with caveats). Rebuilding on IICP would be solving the same problem twice.
3. **Latency model mismatch**: inference task latency targets are 100ms–10s. Reading a forum
   thread should be <50ms. Routing every forum read through a node-selection scoring
   algorithm doesn't fit.
4. **No moderation primitive yet**: IICP has reputation (ADR-026 two-sided), credit accounting
   (S.12), trust audit (#118). It does NOT have content moderation primitives (flag, hide,
   move, lock). Adding these to a protocol-as-bbs is a huge spec extension.
5. **Adoption risk**: a custom community protocol means operators can't use existing fediverse
   clients (Jerboa, Mastodon apps, Lemmy web UI). They'd need an IICP-specific reader.
   Friction inversion: a tool meant to attract operators becomes a barrier to participation.

## What "community on mesh" would actually look like (architecture sketch)

If we did pursue this in Phase 6 or beyond, the architectural moves would be:

1. **New intent type**: `urn:iicp:intent:bbs:thread:read:v1`, `bbs:thread:post:v1`,
   `bbs:comment:reply:v1`, etc. Each is a request-response over the existing IICP framing.
2. **State replication**: forum state replicated using the federated event log primitive
   already in place (ADR-013 §5.4 NodeEventLogger). New event types:
   `BBS_POST`, `BBS_COMMENT`, `BBS_MODERATION_ACTION`.
3. **Conflict resolution**: posts/comments are append-only; moderation is a separate event
   stream that nodes can choose to apply or ignore (per-instance moderation policy).
4. **Content addressing**: posts identified by `(operator_id, post_uuid)`. Replicas
   independently verify operator_signature on each post (per ADR-030).
5. **Reads route to "any" replica**: client picks lowest-latency replica from the directory's
   `bbs:replica` capability set; reads served from local replica's materialized view of the
   event log.
6. **Federation gateway**: at least one node runs an ActivityPub bridge so the IICP-native
   community federates with the wider fediverse. This is necessary because operators in the
   wider fediverse won't switch to an IICP-specific client.

## When would this make sense?

**Not before** ALL of these clear:

- ADR-013 federated control plane fully implemented (Phase 6 complete)
- ADR-030 operator identity layer shipped + ≥100 attested operators (rich identity-tied content)
- Gamification (#267) shipped + first season closed (we have season-experienced operators)
- The community on Lemmy reaches the limits of what Lemmy can do for us (signal we'd
  outgrown a generic forum)
- A volunteer operator with strong protocol-design skills champions the spec work (this is
  a multi-month effort)

Even then, the more pragmatic path is **federate FROM Lemmy via ActivityPub** rather than
build a parallel protocol. Lemmy already runs on operator-controlled instances; that's
already mostly the property we wanted.

## What we DO gain from documenting this path

Even if we never build it, the dogfood-angle document serves three purposes:

1. **Anchors aspiration**: the community-on-mesh idea is a north-star that influences
   today's design choices. We prefer Lemmy over Discourse partly because Lemmy's
   ActivityPub-native posture sets up *a future* community-on-mesh as a federation peer.
2. **Acceptance criterion for protocol completeness**: when IICP can plausibly host its own
   community, it's a sign the protocol is general enough to host other applications. That's
   the moment the project graduates from "AI inference mesh" to "generic computational mesh".
3. **Operator narrative**: even today, operators reading `/docs/why-run-a-node` see this
   research and understand the long arc — "your node will eventually host more than inference".

## Recommendation

**Defer.** Use Lemmy now. Revisit community-on-mesh after Phase 6 + ADR-030 ship + gamification
runs one season. File a research-track issue in 2027 to re-evaluate; until then, this is
folklore, not a roadmap item.

The dogfood angle is captured in `project/gamification.md` ("a future operator narrative") and
in `project/ARCHITECTURE.md` future-section as appropriate. No active work item.

---

## Cross-track implications

If we choose Lemmy (per deliverable 02/03), the dogfood angle adds one constraint to the
choice: **prefer Lemmy specifically over its forks**. Lemmy is the implementation most likely
to be the eventual federation peer for an IICP-native BBS. Sharkey / Mbin / Piefed are valid
ActivityPub citizens but less directly aligned with the long-arc bridge story.
