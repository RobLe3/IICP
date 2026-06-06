# Community Platform 02 — Candidates Evaluation

**Status**: Draft (iter-301, 2026-05-21)
**Companion**: `01-requirements.md`
**Tracking**: #268

---

## Evaluation matrix

Eight candidates evaluated against the requirements from deliverable 01. Each platform scored
1-5 per category; "—" = not applicable / unknown / out of scope.

| Candidate | Stack | License | Federation | Forum FR | Mobile UX | Security | Maint | Self-host cost | Plugin API | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| **Lemmy** | Rust + Postgres | AGPL | ActivityPub ✓ | 4/5 (threaded comments, categories=communities) | 4/5 (Jerboa app, responsive web) | 4/5 (audited 2024; no major CVEs 12mo) | 5/5 (active) | $5/mo VPS ok | 3/5 (plugin system maturing) | **Top pick — philosophy aligned** |
| **Discourse** | Ruby + Postgres | GPL | ActivityPub via plugin | 5/5 (best-in-class threaded discussions) | 5/5 (excellent mobile, PWA) | 5/5 (mature, regularly audited) | 5/5 | $20+/mo Discourse-recommended | 5/5 (extensive plugin ecosystem) | **Strong contender — high overhead** |
| **Flarum** | PHP + MySQL | MIT | Limited (ActivityPub plugin alpha) | 4/5 (modern UI, less mature than Discourse) | 4/5 | 3/5 (smaller community, less audit coverage) | 4/5 | $5/mo shared hosting works | 4/5 (extension ecosystem) | **PHP-aligned; modest fit** |
| **NodeBB** | Node.js + Mongo/Redis | GPL | Limited (ActivityPub plugin beta) | 4/5 | 4/5 | 3/5 (regular updates, smaller audit footprint) | 4/5 | $10/mo VPS | 5/5 (plugins easy to write) | **Reasonable but no federation** |
| **Misskey / Sharkey** | TypeScript + Postgres | AGPL | ActivityPub ✓ (native) | 2/5 (microblog, not forum-structured) | 4/5 | 3/5 (newer, less battle-tested) | 4/5 | $10/mo VPS | 3/5 | **Wrong shape — microblog, not BBS** |
| **Cactus Comments + static** | JS + Matrix | AGPL | Matrix federation | 2/5 (comments on pages, not forum) | 3/5 | 4/5 | 4/5 | depends on Matrix infra | 3/5 | **Wrong shape — comments only** |
| **GitHub Discussions** | Closed SaaS | proprietary | none | 3/5 | 4/5 | n/a (managed) | n/a | free | none | **Excluded — reinforces closed-beta posture; FAILS NFR-5 (SSO lock-in)** |
| **Custom (gemini / native IICP)** | — | n/a | none initially | — | — | — | — | high build cost | — | **Premature — research deliverable 04 may revisit if Phase 6 community-on-mesh path opens** |

## Top 3 deeper dive

### 1. Lemmy — federated, Rust-native, philosophy fit

**Pros**:
- ActivityPub federation native — operators with Mastodon, Lemmy, Sharkey accounts can follow
  iicp.network communities without creating new accounts
- Rust stack — matches iicp-node implementation language; familiar to project contributors
- Communities-as-categories model fits multi-track structure (operators, spec, gamification,
  governance, off-topic)
- AGPL aligns with operator-sovereign philosophy
- Active development (commits weekly; v0.20 released 2024)
- Lightweight footprint — runs comfortably on $5/mo VPS

**Cons**:
- Plugin / customization API less mature than Discourse — gamification leaderboard embeds may
  need a separate static-export approach
- Mobile experience via Jerboa app + responsive web — slightly less polished than Discourse
- Less battle-tested under heavy moderation load
- AGPL has copyleft constraints if we modify and host

**Hosting estimate**: $5–10/mo on Hetzner / Vultr; +$3 for backup; +$0 for domain (use iicp.network/community).

### 2. Discourse — mature, polished, plugin-rich

**Pros**:
- Best-in-class forum UX; mobile PWA exceptional
- Mature moderation tools (TL trust-level system, automatic spam detection)
- Plugin ecosystem covers everything we'd want (leaderboards, polls, badges natively!)
- Excellent search; ATOM/RSS first-class
- Discourse already implements a "badge + trust level" system — would compete with #267
  gamification but could potentially align

**Cons**:
- Ruby/Rails — heavier hosting requirement (recommended 4 GB RAM); $20+/mo realistic
- Federation via ActivityPub plugin only (not native)
- GPL has copyleft constraints
- Operationally heavier (database migrations, postgres tuning, redis, sidekiq)

**Hosting estimate**: $20–40/mo realistic; Discourse-managed hosting starts at $100/mo (excluded
per NFR-3).

### 3. Flarum — lightweight, PHP-aligned

**Pros**:
- PHP/MySQL — aligns with directory service stack; can co-locate on shared hosting (the same
  DomainFactory account that hosts `iicp.network` could host `community.iicp.network`)
- Lowest hosting cost ($5/mo shared hosting)
- Modern UI; better than its mature competitors (phpBB, vanilla MyBB)
- Extension ecosystem; some federation work in progress

**Cons**:
- Smaller community than Discourse/Lemmy; less battle-tested
- ActivityPub support alpha-stage
- Plugin ecosystem less rich; gamification integration would be custom work

**Hosting estimate**: $5/mo on existing shared hosting; zero new infra.

## Excluded with rationale

- **Misskey / Sharkey**: shape is wrong. They're microblog platforms. Operators discussing
  "should I run Llama 70B or Qwen 7B for my hardware" need threaded forum structure, not
  algorithmic feeds. Better to federate FROM a forum into the fediverse than to host the
  community on a microblog.
- **Cactus Comments**: only useful as a comment widget on static pages, not a primary forum.
  Could be used adjunct (e.g., comments on /docs pages) but not the main community venue.
- **GitHub Discussions**: explicitly excluded — perpetuates the closed-beta posture and
  forces GitHub SSO (NFR-5 violation). May be useful for code-related discussions but not
  for operator community.
- **Custom build**: premature. Deliverable 04 evaluates the "community-on-mesh" path as a
  future Phase 6+ possibility (federated forum nodes implementing a community protocol on
  top of IICP itself).

## Cost-of-life comparison

| Platform | Setup time | Monthly cost (Y1) | Monthly cost (Y2 — 5k users) | Admin hours/mo (est) |
|---|---|---|---|---|
| Lemmy | 1 day | $8 | $25 | 2-4 |
| Discourse (self-hosted) | 2-3 days | $25 | $80 | 4-8 |
| Flarum | 0.5 day | $5 | $15 | 1-3 |
| GitHub Discussions | 1 hour | $0 | $0 | 0-1 (but FAILS NFR-5) |

## Initial recommendation (refined in 05-recommendation.md)

**Lead with Lemmy** as the primary community platform. Philosophy alignment is strongest
(federated, Rust, AGPL, operator-sovereign). Hosting cost fits NFR-3. ActivityPub federation
opens future composition with other fediverse communities — a long-term strategic asset that
neither Discourse nor Flarum provides natively.

**Fallback to Discourse** if Lemmy's plugin / customization limitations prove blocking for
gamification integration (#267). Trade-off: higher operational overhead, but mature mobile
UX and badge-native ecosystem.

**Reject Flarum** despite lowest hosting cost — federation gap is too large, and Phase 6
ADR-013 federated control plane benefits significantly from a federated community platform.

Federation gap deep-dive in `03-federation-fit.md`.
