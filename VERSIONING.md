# IICP Versioning Canon

**One source of truth. Six independent version axes. Never conflate them.**

---

## 1. IICP Protocol Suite Version (public-facing)

**Format**: `MAJOR.MINOR.PATCH` (semver)  
**Source of truth**: `spec/v1.9/VERSION` in the [`RobLe3/IICP`](https://github.com/RobLe3/IICP) spec repo  
**Displayed as**: `IICP v1.9.0` or `IICP Protocol v1.9.0`  
**Changelog**: `CHANGELOG.md` in the IICP spec repo

This is the version that external implementers, operators, and IETF reviewers see. It covers
the entire IICP specification suite (core, CIP, framing, identity, telemetry, etc.).

| Version | Date | Milestone |
|---------|------|-----------|
| v1.4.2 | 2024 | Historical — deprecated (inflated performance claims; corrected in v1.5) |
| v1.5.0-draft | 2026-05-15 | Spec corrections applied; methodology disclosure; v1.4.2 claims moved to non-normative appendix |
| v1.6.0 | 2026-05-23 | Phase 5 CIP spec added; binary framing stubs; recognition, telemetry, MCP binding, billing extension |
| v1.7.0 | 2026-05-24 | §5.1.1 tier structure and §5.1.2 bootstrap floor ratified; all 13 Phase-5 research tracks closed |
| v1.8.0 | 2026-05-25 | S.13 ephemeral-by-design federation (ADR-033); snapshot+event-tail bootstrap |
| v1.9.0 | 2026-05-30 | RT-01/RT-05 reputation caps and directory drift closeout |
| v1.9.1 | 2026-07-30 | Status/version governance and transport/IANA errata; superseded because its bundled implementation index was stale |
| v1.9.2 | 2026-07-30 | Corrective immutable release with synchronized implementation/package references and a version-truth gate |
| **v1.10.12** | **2026-08-09** | **Current** — profile-only lifecycle-envelope correction, strict Registry 1.4 evidence validation, and updated conformance fixtures; no base-wire change |
| v1.10.11 | 2026-08-08 | Additive evidence-linked intent registry 1.4 and PHP/Rust reputation parity; no base-wire change |
| v1.10.10 | 2026-08-08 | Consolidated rate-limit correctness, registry validation and negotiated streaming clarification; no base-wire change |
| v1.10.9 | 2026-08-05 | Recorded PHP directory 1.10.87 security-patch currency; no wire change |
| v1.10.8 | 2026-08-02 | Added a content-free, loopback-only authenticated directory lifecycle profile; no wire change |
| v1.10.7 | 2026-08-02 | Reconciled conformance-suite authority and added a loopback-only dispatch-safety profile; no wire change |
| v1.10.6 | 2026-08-02 | Generated current-version projection and prose-quality tooling; no normative wire change |
| v1.10.5 | 2026-08-02 | Records browser node 0.2.3; no normative wire change |
| v1.10.4 | 2026-08-02 | Separate provider implementation identity from SDK compatibility |
| v1.10.3 | 2026-08-01 | Dual-era MCP profile and coordinated SDK 0.7.101 currency |
| v1.10.2 | 2026-08-01 | Additive discovery evidence explanations |
| v1.10.1 | 2026-07-31 | Corrective structured-release metadata pin; no wire change |
| v1.10.0 | 2026-07-31 | Authenticated replica decommissioning, signed lifecycle propagation and same-DID reactivation |
| v1.9.3 | 2026-07-31 | Records the Rust directory v0.1.4 snapshot-bootstrap correction; no wire change |

**Rules:**
- Bump MINOR for new normative content (new sections, new specs added to suite)
- Bump PATCH for corrections, ratifications, clarifications to existing normative content
- Bump MAJOR for breaking wire-format changes (none in IICP history yet)
- Update both the IICP repo `VERSION` file and `CHANGELOG.md` when bumping

---

## 2. Sub-Spec Document Version (internal editorial)

**Format**: `MAJOR.MINOR.PATCH[-draft]`  
**Scope**: Per-document, for tracking editorial changes within a specific spec file  
**Displayed as**: `S.12 v0.6.13` (always with the spec number prefix)

Sub-spec documents have their own internal versioning for fine-grained editorial tracking.
**These are NOT the IICP Protocol Suite version.** They exist so spec editors can track
which version of a sub-document contains which normative text.

| Sub-spec | Current internal version | Notes |
|----------|--------------------------|-------|
| S.12 `iicp-cooperative-inference.md` | 0.6.13 | CIP — Phase 5 |
| `iicp-core.md` | follows iicp-core section versioning | Core protocol |
| `iicp-framing.md` | 0.1.x | Binary framing — Phase 4 stub |

**Rules:**
- Sub-spec versions are for editors. End users see the Protocol Suite version.
- When displaying both: `IICP v1.10.12 · S.12 CIP v0.6.13` (suite first, sub-spec second)
- Never use a sub-spec version alone as "the" IICP version on public-facing surfaces

---

## 3. OpenAPI Contract Version

The OpenAPI `info.version` versions one HTTP contract projection. It is not the
Protocol Suite version and it is not a directory release number. An OpenAPI
document MUST state the protocol compatibility range and implementation
releases MAY implement the same OpenAPI version.

---

## 4. Reference Implementation Version (software)

**Format**: `vMAJOR.MINOR.PATCH`  
**Scope**: Each software component has its own version  
**Source**: `directory/config/app.php iicp_version` (directory service)

The reference implementation version tracks software releases, not protocol releases.
A software version can be ahead of or behind the spec version (e.g., directory v1.10.x
implements Protocol Suite v1.9.0).

| Component | Current version | Location |
|-----------|----------------|----------|
| Directory (PHP Genesis) | Check `IMPLEMENTATIONS.md` and the release registry | Current Genesis implementation |
| Directory (Rust preview) | Check `IMPLEMENTATIONS.md` and the release registry | Official second flavour; operator preview |
| Adapter (Python) | v1.x — check adapter/VERSION or pyproject.toml | |
| Proxy (Python) | v1.x | |
| Rust node | v0.x | `iicp-node/Cargo.toml` |

**Rules:**
- Never use the directory software version as "the" IICP version on public surfaces
- When citing implementation evidence: `directory v1.9.19` (always include "directory")
- Website asset version (`version-info.json`) is a build artifact version — never display as protocol version

---

## 5. Package Version

SDK and tool packages use their own semantic versions. A package release MUST
declare its supported Protocol Suite range; matching package versions across
languages indicate a coordinated release, not protocol ratification.

---

## 6. Deployment Version

A website build or deployed directory instance has a deployment/build
identifier. It MUST be labelled as a build or deployment version and MUST NOT
be displayed as the Protocol Suite, OpenAPI or package version.

---

## 7. Display Rules (website, docs, PRs)

| Surface | What to display | Example |
|---------|----------------|---------|
| Research page badge | Protocol Suite version | Use `spec/v1.9/VERSION` and label the axis |
| Spec references in page body | Suite + sub-spec | `IICP v1.10.12 · S.12 v0.6.13` |
| Implementation evidence | Software version | `directory v1.9.19` |
| PR commit messages | Component + software version | `[directory] v1.9.19` |
| IICP repo CHANGELOG | Protocol Suite version | `## v1.7.0 — 2026-05-24` |
| Spec file headers | Sub-spec version | `**Version**: 0.6.13` |

**Never do:**
- Use a made-up page version (e.g., "v1.3.0") on public surfaces
- Use the S.12 internal version as the IICP Protocol Suite version badge
- Use the directory software version as the protocol version
- Mix version axes in the same badge without labeling them

---

## 8. Version Update Procedure

When making spec changes that warrant a version bump:

```bash
# 1. Update the IICP spec repo (via GitHub API or clone)
#    - Update spec/v1.9/VERSION
#    - Add entry to CHANGELOG.md

# 2. Update the sub-spec document version header
#    - File: spec/iicp-cooperative-inference.md (or other sub-spec)
#    - Field: **Version**: x.x.x
#    - Add changelog entry in the document's own changelog table

# 3. Update website badge
#    - File: website/app/research/page.tsx
#    - Badge: "IICP vX.Y.Z · Updated YYYY-MM-DD"
#    - Footer: "Spec: S.12 vA.B.C"

# 4. Update directory software version (only when shipping directory changes)
#    - File: directory/config/app.php
#    - Field: iicp_version

# 5. Update website asset version (only when doing a full website deploy)
#    - File: website/public/assets/json/version-info.json
```

The IICP spec repo version and the directory software version update on independent schedules.
