# Community Platform 05 — Final Recommendation

**Status**: Draft (iter-301, 2026-05-21)
**Companion**: 01-requirements, 02-candidates, 03-federation-fit, 04-dogfood-angle
**Tracking**: #268

---

## Top recommendation: **Lemmy**

Rust + Postgres, AGPL, ActivityPub-native, philosophy-aligned, modest hosting cost.

### Why Lemmy wins

1. **Federation is the only candidate that clears the bar today** (deliverable 03). Discourse's
   ActivityPub plugin is beta; Flarum/NodeBB plugins are alpha. Federation is now treated as
   a hard requirement (NFR amendment from deliverable 03), not nice-to-have.
2. **Philosophy alignment** with IICP itself — Rust, federated, operator-sovereign, AGPL.
3. **Hosting cost fits NFR-3** — $5–10/mo on standard VPS, $25/mo at 5k users.
4. **Long-arc compatibility** with future community-on-mesh dogfood angle (deliverable 04) —
   Lemmy is the most likely future federation peer for an IICP-native BBS.
5. **Active maintenance** — weekly commits, recent security audit, mature ecosystem of
   federated instances.

### Acknowledged trade-offs

- Plugin / customization API less mature than Discourse — gamification leaderboard embeds
  (#267) may need a custom static-render path rather than a native Lemmy plugin.
- Mobile UX (Jerboa app + responsive web) is good but not Discourse-level polished.
- AGPL copyleft constraints if we fork — accept the constraint; we're unlikely to ship a
  proprietary modified Lemmy.

## Fallback: **Discourse** (only if Lemmy proves blocking)

Triggers for fallback:
- Gamification integration (#267 leaderboards + badges UI) requires a plugin model Lemmy
  doesn't support and can't be done as a static / API integration.
- Mobile UX quality issues escalate (operator feedback).
- Operational difficulty (a Lemmy instance becomes a recurring maintenance burden beyond
  the 2-4 hr/mo estimated in deliverable 02).

Discourse trade-offs are documented in deliverable 02; the federation gap is the primary
reason it's not the lead pick.

## Rejected: **Flarum, NodeBB, Misskey, GitHub Discussions, Custom**

- **Flarum / NodeBB**: federation gap too large; ActivityPub plugins not production-ready
- **Misskey / Sharkey**: wrong shape (microblog, not BBS)
- **GitHub Discussions**: violates NFR-5 (SSO lock-in) + perpetuates closed-beta posture
- **Custom**: premature; revisit per deliverable 04 (community-on-mesh) after Phase 6

## Rollout plan

### Phase 1 — Stand up community.iicp.network (Week 1)

- Provision $10/mo Hetzner VPS (or use existing if capacity available)
- Install Lemmy 0.20.x via official docker-compose deployment
- Configure: federation enabled, registration mode = "RequireApplication" during closed
  beta (per #260)
- Create initial communities:
  - `!ops` — node operations, configs, troubleshooting
  - `!spec` — protocol discussion
  - `!gamification` — leaderboard / season talk (depends on #267 readiness)
  - `!off-topic` — community lounge
  - `!announcements` — locked, maintainer-only post
- Maintainer + 2-3 early-cohort operators as initial mods

### Phase 2 — Federate (Week 1-2)

- Public ActivityPub endpoint live
- Test federation with hachyderm.io (Mastodon) — subscribe + post propagation
- Test federation with lemmy.world / programming.dev / lemmy.ml — community subscribe + reply
- Document the federation handle (`@iicp@community.iicp.network` for project account;
  `!ops@community.iicp.network` for the ops community)

### Phase 3 — Embed (Week 2-3)

- Add inline community widget to iicp.network homepage (latest 5 posts from `!announcements`)
- Add "Discuss this on community" link to each `/docs` page (links to relevant `!ops` thread
  template)
- Add to `CLAUDE.md` and contributor docs as the official venue for non-issue discussion

### Phase 4 — Migration (Week 3+)

- Migrate any GitHub Discussions that exist (manually crosspost; GH Discussions stays open
  but becomes secondary for code-only topics)
- Announce platform via existing channels (homepage banner, mailto:beta@ replies)
- Continue closed-beta application mode until public-launch gate (#260) clears; then switch
  to open registration

## Decisions deferred to maintainer

1. **Hosting infrastructure**: Hetzner / Vultr / DigitalOcean / DomainFactory? Recommend Hetzner
   (€5/mo Cloud Server CX22, EU jurisdiction matches operator distribution).
2. **Initial mod team**: who are the 2-3 early-cohort operators trusted with mod privileges?
3. **Application form during closed beta**: questions to ask, who reviews, target SLA?
4. **Federation defederation policy**: which fediverse instances to federate with vs.
   defederate (e.g., known spam / hate instances)? Use Fediseer registry as a starting point.
5. **Branding alignment**: should community.iicp.network use the same visual identity as
   iicp.network, or have its own?

## Acceptance criteria for community platform research track

✅ All 5 deliverables drafted (01..05 + 04 dogfood-angle).
- Implementation tracking issue to be filed by maintainer after sign-off.

## Implementation tracking (to be filed when maintainer approves)

Suggested issue title: "[ADOPTION] Deploy community.iicp.network (Lemmy) — Phase 1 stand-up"

Acceptance criteria for implementation issue:
- Lemmy instance live at https://community.iicp.network
- ActivityPub federation working (verified with at least 2 external instances)
- 4 initial communities created with descriptions
- Application-mode registration tied to mailto:zerokelvinmoralist@gmail.com funnel
- Cross-linked from iicp.network homepage + /docs pages
- CLAUDE.md updated to reference as the discussion venue

Estimated effort: 2-3 days standup + 1 week federation validation.

## End of research track

Community platform research track concludes with Lemmy as the recommended choice.

Next: maintainer review + decision; implementation tracking issue filed; gamification (#267)
implementation references this community platform as the leaderboard venue (deliverable 05
of #267 API surface stays independent — leaderboards are rendered on iicp.network with
optional Lemmy crosspost integration).
