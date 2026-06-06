# Community Platform 01 — Requirements

**Status**: Draft (iter-301, 2026-05-21)
**Tracking**: #268
**Cross-track**: #267 (gamification leaderboards need a venue)

---

## What we're solving

The IICP project has no community venue. GitHub Issues is the only forum; it's invite-only
(closed beta — #260) and designed for work tracking, not discussion. Operators need a place to:

- **Share configs / setups** (especially for non-obvious cases — port-forwarding, multi-model
  containers, low-resource hardware)
- **Troubleshoot together** (current path: maintainer email → maintainer answers; doesn't scale)
- **Discuss mesh strategy** (which models to run, when to upgrade, how to interpret reputation)
- **See community announcements** (season transitions per #267, deploy windows, spec changes)
- **Post leaderboards / brag rooms** (gamification #267 needs a home for cohort identity)
- **Find collaborators** (operators forming groups for federated replica directories ADR-013)
- **Onboard new operators** (current beta funnel #266 is opaque — community is part of that)

## Functional requirements

| FR | Description | Priority |
|---|---|---|
| FR-1 | **Threaded discussion** — categories + threads + nested replies | MUST |
| FR-2 | **Markdown formatting** + code blocks + syntax highlighting | MUST |
| FR-3 | **Search** — full-text across all threads + filter by category/author/date | MUST |
| FR-4 | **User accounts** — handle + email; no real-name required | MUST |
| FR-5 | **Moderation tools** — flag, lock, move, ban; maintainer-controlled | MUST |
| FR-6 | **Anti-spam** — captcha, rate limits, optional invitation requirement | MUST |
| FR-7 | **Mobile UX** — responsive or PWA; not desktop-only | MUST |
| FR-8 | **Accessibility (WCAG 2.1 AA)** — keyboard nav, screen reader, contrast | MUST |
| FR-9 | **Email notifications** — opt-in per category / per thread | SHOULD |
| FR-10 | **RSS / ATOM feeds** — for ops-style operators who don't want yet another login | SHOULD |
| FR-11 | **API for embedding** — pull recent threads onto iicp.network homepage | SHOULD |
| FR-12 | **OAuth / SSO integration** — optional federated login (GitHub, Mastodon) | NICE |
| FR-13 | **Federation (ActivityPub)** — interop with Mastodon, Lemmy, others | NICE |
| FR-14 | **File attachments** — logs, configs, screenshots; size-limited | NICE |
| FR-15 | **Real-time chat** — IRC/Matrix-style adjacent to async forum | NICE |

## Non-functional requirements

| NFR | Description | Threshold |
|---|---|---|
| NFR-1 | **Free / open-source license** — no per-seat or per-MAU pricing | Must be AGPL/GPL/MIT/Apache |
| NFR-2 | **Self-hostable** — operator or maintainer controls deployment | MUST (no SaaS-only) |
| NFR-3 | **Low ongoing cost** — fits bootstrap budget | Ceiling: ~$20/mo at <500 users |
| NFR-4 | **Operator-sovereign moderation** — no platform TOS overrides | MUST |
| NFR-5 | **No SSO lock-in** — operators don't need GitHub/Google just to post | MUST |
| NFR-6 | **Security track record** — recent audits, no major CVEs in last 12 months | SHOULD |
| NFR-7 | **Active maintenance** — commits in last 90 days | SHOULD |
| NFR-8 | **Reasonable hosting footprint** — runs on a $5/mo VPS at low traffic | SHOULD |
| NFR-9 | **Plugin / customization API** — for the gamification leaderboard embeds (#267) | SHOULD |
| NFR-10 | **Data export** — operators can export their content; we can migrate if needed | MUST |

## Constraints

- **Closed-beta posture (#260)**: until repo is public, the community platform should support
  invitation-only mode. Public-launch enables open registration.
- **No Discord / Slack** — proprietary, vendor lock-in, hostile to long-term data persistence,
  big-tech dependent. Explicitly excluded.
- **No GitHub Discussions for primary venue** — re-reinforces closed-beta posture; operators
  without repo access can't participate.
- **Philosophy alignment**: federated > centralized when feasible; Rust > Ruby/PHP when
  equivalent (mild preference, not blocker).

## Scale assumptions (to size hosting)

- **Year 1**: <500 registered operators (per the gamification target — ≥10 external + ~50
  internal/curious lurkers)
- **Year 2**: 500–5,000 operators
- **Year 5**: aspirational 50,000+ if the protocol takes off

Platform choice must scale from low-hundreds to low-thousands without re-architecting; tens
of thousands can trigger a re-evaluation.

## Out of scope

- Real-time video / voice (out of scope; use Jitsi/BBB if needed for occasional ops calls)
- Wiki-style collaborative docs (covered by `/spec` + GitHub; not a forum concern)
- Code review / PR discussions (covered by GitHub for now; federation TBD)
- Custom protocol design for community-on-mesh (covered separately by deliverable 04)

## Acceptance criteria for deliverable 01

✅ All FR + NFR enumerated above (this document).
Goes into 02-candidates.md to evaluate against each platform.
