# Community Platform 03 — Federation Fit

**Status**: Draft (iter-301, 2026-05-21)
**Companion**: `01-requirements.md`, `02-candidates.md`
**Tracking**: #268

---

## Why federation matters for IICP specifically

IICP is, by design, a **federated protocol**. ADR-013 establishes a Genesis Seed + Replica
Directory model. The roadmap (Phase 6) culminates in a fully federated control plane.

A *centralized* community platform on top of a federated protocol is a contradiction. It
creates a single point of moderation control, a single point of data loss risk, and
philosophically signals that "operators are first-class but discussion is centralized" —
which undercuts the project's stated values.

Federation also addresses concrete risks:
- **Moderation pluralism**: if the IICP working group's moderation choices conflict with a
  sub-community's preferences, that sub-community can federate elsewhere without losing
  identity / posts.
- **Disaster resilience**: a federated community survives the main instance going dark.
- **Adjacent community visibility**: AI / decentralized-ops / Rust communities on Lemmy /
  Mastodon can subscribe to IICP communities without crossing platforms.

## ActivityPub support per candidate

| Platform | ActivityPub native | Federation maturity | Cross-platform composability |
|---|---|---|---|
| **Lemmy** | ✅ native, since v0.10 | Mature; battle-tested across hundreds of instances | Subscribe-from-Mastodon, cross-instance posts, federated comments — all work today |
| **Discourse** | ⚠️ via plugin (Discourse ActivityPub plugin v1.x) | Beta-quality; not yet stable across major Discourse versions | Limited — can publish posts as fediverse notes but federated commenting is shaky |
| **Flarum** | ⚠️ alpha plugin only | Pre-release; not production-ready | Effectively none today |
| **NodeBB** | ⚠️ alpha plugin only | Pre-release | Effectively none today |
| **Misskey/Sharkey** | ✅ native | Mature (Misskey predates Mastodon's ActivityPub in some respects) | Excellent — but shape is microblog, not BBS |
| **GitHub Discussions** | ❌ none | n/a | n/a |
| **Custom** | depends on build | depends on build | depends on build |

## What "federated" buys us in practice

Concrete scenarios where federation pays off:

### 1. Operator already in fediverse — zero new account friction

A Rust dev with a `@dev@hachyderm.io` account can follow `!iicp@community.iicp.network`
without creating a new account. They get IICP announcements in their existing feed.
Lower friction = more attention.

### 2. Cross-pollination with adjacent communities

`!iicp@community.iicp.network` can federate with `!selfhosted@lemmy.world`,
`!rust@programming.dev`, `!ai@lemmy.ml`. Mutually relevant posts surface in both directions.
Recruiting flywheel.

### 3. Replica community model (#268 + ADR-013 alignment)

A federated replica directory operator (per ADR-013) can naturally also run a federated
community instance for their region. `community.iicp.eu`, `community.iicp.asia` etc. all
federate back to `community.iicp.network` (Genesis Seed for community as well as for
directory).

This is a strong narrative for the project: **the community is structurally homologous to the
mesh itself** — federated, operator-sovereign, no central authority. The two patterns reinforce.

### 4. Moderation portability

If maintainer makes an unpopular moderation choice (banning a controversial topic), affected
operators can fork their sub-community to a different Lemmy instance and keep federating.
This is healthy. Centralized platforms (Discord, Slack, Discourse without federation) make
this impossible — leaving = losing all history.

## Federation quality bar

The bar isn't "ActivityPub-compatible" — it's **federation that works for our use case
without ongoing maintenance burden**. Lemmy clears this bar; Discourse's plugin does not.

Specifically, the federation tests we'd want passing:

1. **Subscribe-from-Mastodon**: a Mastodon user can follow an IICP community and see posts
   in their home timeline.
2. **Federated comments**: a Lemmy user on a different instance can reply to an IICP post
   and the reply appears in both instances' threads.
3. **Cross-instance post visibility**: posts originating on IICP community surface in
   federated instances' All / Local-but-federated views.
4. **Block / moderation propagation**: instance-level blocks propagate; user-level moderation
   stays per-instance.

Lemmy: 4/4 ✓ today.
Discourse plugin: 1/4 (partial subscribe-from-Mastodon, no federated comments yet).
Flarum / NodeBB: 0/4.

## Federation security considerations

Federation isn't free — it introduces attack surface:
- **Spam from federated instances**: standard fediverse defense is instance-level blocklists
  (e.g., the Fediseer registry) and user-level blocks. Lemmy has this.
- **Moderation arbitrage**: bad actor on instance X publishes to IICP community via federation.
  Lemmy supports community-level moderation that applies to federated posts.
- **Cross-instance impersonation**: handles like `mesh-warrior-42@some-rando-instance.tld` can
  imitate IICP operators. Mitigation: operator handles tied to ADR-030 operator_id; community
  platform handles separately scoped (community handle != operator handle).

These are tractable; Lemmy's moderation tooling is adequate.

## Recommendation

**Federation should be a hard requirement, not a "nice-to-have"** — this is a soft
amendment to deliverable 01's FR matrix (where federation was listed as NICE rather than MUST).

Lemmy is the only candidate that satisfies hard-federation today. Discourse + plugin is a
plausible Phase 2 path if Lemmy proves blocking for gamification integration. Flarum / NodeBB
fail this gate.

Promote federation to **MUST** in the final recommendation: deliverable 05.
