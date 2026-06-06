# Gamification Track 01 — Design Rationale

**Status**: Draft (iter-294, 2026-05-21)
**Tracking**: #267 (research) | gated on #260 (public-launch) for implementation
**Author**: FORGE-5 iter-294 ADOPTION work, maintainer concept

---

## 1. The principle in one sentence

Convert **passive operational telemetry the directory already collects** into **intrinsic motivators**
that recognize, differentiate, and amplify operator contributions to the mesh — without requiring any
extra work from the operator and without inventing new metrics that would have to be gamed against.

## 2. The problem this solves

The IICP mesh has a chicken-and-egg adoption problem (W-016, FC-001, ADOPTION D7 partially supported):

- ADOPTION D7 score is 91 internally but FC-001 found real ≈ 55–65 because there are zero
  confirmed external operators (all 8 active nodes belong to the IICP working group).
- The "join the mesh" docs are polished (D1–D6, D8 all at 100), yet no external operator
  has joined since launch.
- The structural blocker is **invisibility of contribution** — operators get a node_id
  and a heartbeat counter, nothing that says "you matter to this network".

A node operator running on their hardware, paying their electricity bill, debugging port-forwarding,
expects *something* in return. Credits are part of that. But credits alone are utilitarian — they
don't create identity, belonging, or social proof. Without those, the operator population stays at
0 and the mesh remains a single-operator demo.

## 3. Why "earn-by-existing" recognition

Many gamification systems fail because they invent a parallel metric ("post-count", "engagement
score") that distorts the underlying behavior. Our framework deliberately avoids this:

- Every signal already exists in the directory or REACH probe data.
- The same actions that make the mesh *work* (heartbeats, task completions, model diversity,
  reachability) are the actions that earn recognition.
- No extra "do X to get badge Y" — earning is a side-effect of operating well.

This is the **earn-by-existing** principle. It aligns operator effort with mesh health; the only
way to climb is to participate genuinely.

## 4. Multi-axis identity (not one number)

A single score (e.g. "reputation") forces operators into one ranking and creates Goodhart-style
gaming pressure. Multi-axis recognition spreads identity across orthogonal dimensions:

- **Reliability** (uptime, heartbeat success rate)
- **Throughput** (tasks completed, credits earned)
- **Diversity** (number of distinct models, variety of intents handled)
- **Reach** (probe-reachability from multiple geographic locations)
- **Conformance** (CIP level, advisory capability declarations)
- **Tenure** (days since first registration)

Each operator has their own profile shape. The "Diversity Champion" of country X is a different
operator than the "Uptime Chad" of region Y. This removes single-winner-take-all dynamics and
creates multiple ladders to climb.

## 5. Social proof as a recruiting mechanism

The public-facing parts (leaderboards, Wall of Fame, regional champions, founding cohort) serve a
specific marketing function: **prove the mesh is real to people who haven't joined yet**.

A prospective operator visits iicp.network and sees:
- A list of 200 active nodes (not 8) — *the mesh is alive*
- Recognizable operators with names, regions, ranks — *people like me are here*
- A "Class of 2026" cohort that's closed but a "Class of 2027" they could still join —
  *there's a window of opportunity*
- Their potential rank progression mapped out — *I can see myself in this*

The leaderboards don't exist to flatter top operators. They exist to convert visitors into
operators.

## 6. Community narrative (titles, cohorts, founding stories)

Named ranks ("Node Initiate" → "Mesh Legend") and cohort identities ("Class of 2026", "Danish
Pioneer", "H2 2026 Mesh Pioneer") create **belonging**. Belonging is what makes operators stay
through the inevitable boring middle period (months 2–6 of operation, after the novelty wears off
but before serious credits roll in).

Counter-narratives to avoid:
- **Exclusivity that locks out late joiners** — every joiner should see badges they can still earn.
- **Vanity metrics with no mesh-health signal** — every badge should correlate with something
  that benefits the mesh.
- **Resets that destroy long-term identity** — season badges are additive (you collect them),
  never replacements for permanent identity.

## 7. Temporal dimension — seasons + yearly classes (maintainer addendum)

Add to the multi-axis identity:

- **Seasons (2/year — H1, H2)**: each season has exclusive badges that can never be earned
  again once it closes. Creates FOMO + urgency + renewal mechanic.
- **Yearly classes (Class of 2026, 2027, ...)**: permanent cohort identity for operators
  active in that calendar year. Cohort solidarity without locking out late joiners (they get
  their own class).

Why seasons matter psychologically:
1. **Urgency**: "5 days left to earn the H1 2027 Diversity Champion badge" creates engagement spikes.
2. **Renewal**: every season is a fresh start. Even operators who missed early ranks have new
   things to chase.
3. **Cohort pride**: "I'm Class of 2026" is a permanent identity that can never be back-earned.
4. **Leaderboard rhythm**: season leaderboards reset; cumulative leaderboards persist.

Anti-pattern guard: avoid seasons that *punish* steady operators. Always keep cumulative
leaderboards alongside season-specific ones.

## 8. Prior art and what we learn from it

| System | What worked | What didn't |
|---|---|---|
| **StackOverflow reputation + badges** | Multi-axis (rep, gold/silver/bronze badges, tags); badges trigger spike behavior (Q&A bursts) | Gaming-resistant only because the underlying signal (peer votes) is hard to game — IICP has the same advantage with directory-observed metrics |
| **GitHub achievements** | Simple, side-effect of normal use; cohort identity (Pull Shark, Quickdraw) | Mostly decorative; not connected to leaderboards or community identity |
| **Foldit** | Massive community engagement around a niche technical task | Required custom client; deep onboarding curve. IICP avoids this by piggybacking on already-installed adapter/node binaries |
| **Folding@home / BOINC** | Team-based competition, donation cohorts, points | Single metric (points); led to GPU arms races. IICP multi-axis prevents this |
| **Strava** | Segments (location-specific leaderboards), kudos, club memberships | Subscription model — we won't replicate that |
| **The Internet Archive's contributor recognition** | Quiet but persistent — librarian-style. Right tone for a research-flavored network | Doesn't drive viral growth on its own |

Takeaway: **piggyback on existing operator behavior** (StackOverflow / Strava model), **avoid
single-metric optimization** (BOINC failure mode), **build cohort identity** (Folding@home team
model), **keep it free** (no subscription tier).

## 9. Constraints that the design must respect

1. **No new telemetry collection** — research deliverable 02 must verify every rank/badge is
   computable from data the directory or REACH already stores.
2. **Anti-sock-puppet** — operator diversity check must distinguish "10 nodes from one person"
   from "10 nodes from 10 people". Same operator running multiple nodes is fine (encouraged for
   model diversity) but shouldn't dominate the "external operators" count for D7.
3. **No public PII** — operator identity can be a chosen handle, not real name. Geographic info
   is region-level, not GPS.
4. **Implementation gated on #260** — gamifying a single-operator mesh would be embarrassing.
   Wait until ≥10 confirmed external operators OR explicit maintainer waiver.
5. **No new spec until rationale stable** — `spec/iicp-recognition.md` is a downstream artifact
   created only after this research track produces stable recommendations.

## 10. Success criteria for this research track

- Every rank/badge proposed has an unambiguous, observable trigger.
- Every trigger uses data already collected (verified in deliverable 02).
- Anti-gaming constraints are explicit (deliverable 03).
- Rollout gates prevent shipping while the mesh is still single-operator (deliverable 04).
- Directory API extension is minimal — ideally one new endpoint (deliverable 05).
- The framework feels *fun* to a node operator without feeling silly or condescending.

## 11. Open questions for follow-up deliverables

- How are season boundaries determined? (Calendar Q1+Q2 vs Q3+Q4? Or fixed Jan 1 / Jul 1?)
- Who decides badge eligibility edge cases? Maintainer? Community vote? Algorithmic only?
- Do operators get a publicly-visible handle (chosen at registration) or is identity by node_id?
- Does the gamification system require its own bounded context (BC-13?) in DDD terms, or fold
  into BC-4 (Directory)?
- Interaction with ADR-026 (two-sided reputation as earned signal) — is rank a derived view of
  the underlying reputation, or a separate axis?

---

## Next deliverable

`02-metric-mapping.md` — concrete mapping from each rank/badge in the maintainer's Nerd Legacy
concept to the underlying telemetry source (NodeEventLogger event types, REACH probe results,
heartbeat success calculation). Must verify all are computable without schema changes.
