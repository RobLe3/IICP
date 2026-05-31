# S.14 — IICP Conformance Badge System

**Version**: 0.1.0 (Draft)  
**Date**: 2026-05-15  
**Status**: draft  
**Authority**: Protocol Steward + Developer Advocate  
**Linked ADR**: ADR-016 (SDK Interface Contract); ADR-010 (scoring formula)  
**Prerequisite**: S.10 (conformance test suite) extended with SDK-01–06, DIR-FED-01–08  
**Relation to**: BOUNDED_CONTEXTS.md BC-9 (Developer Experience); spec/conformance-test-suite.md

---

## 1. Purpose

Conformance badges allow node operators and SDK authors to publicly signal that their implementation has passed the IICP conformance test suite at a stated tier. They are machine-verifiable trust signals embedded in documentation, dashboards, and the public node registry.

Badges do not replace real-time health monitoring. They attest to a point-in-time test run. The badge system is designed to:

- Give operators a low-friction way to communicate interoperability compliance
- Give clients a signal when choosing between nodes in the public registry
- Create a feedback loop that pulls implementations toward spec compliance
- Enforce that badge claims are tied to verifiable test results

---

## 2. Badge Tiers

| Tier | Requirements | Badge label |
|------|-------------|-------------|
| **Core Compliant** | Passes all `MUST` requirements in S.1–S.6 (Phase 1 conformance profile) | `iicp:core:v1` |
| **Mesh Compliant** | Core + S.7 (mesh/gossip) MUST requirements | `iicp:mesh:v1` |
| **SDK Compliant** | SDK-01 through SDK-06 (ADR-016 §5) | `iicp:sdk:v1` |
| **Federated Compliant** | DIR-FED-01 through DIR-FED-08 (S.13) | `iicp:federated:v1` |
| **Full Compliant** | All above tiers | `iicp:full:v1` |

Badge tiers are additive — a `full` badge implies all lower tiers.

---

## 3. Badge Attestation Record

A badge is represented as a signed JSON record:

```json
{
  "badge_id": "uuid-v4",
  "tier": "iicp:core:v1",
  "subject_did": "did:web:node.example.com",
  "subject_component": "adapter | proxy | sdk | replica",
  "suite_version": "1.0.0",
  "passed_at": "2026-05-15T12:00:00Z",
  "test_results_url": "https://node.example.com/iicp-conformance/results-20260515.json",
  "issuer_did": "did:web:iicp.network",
  "sig": "base64url-ed25519-signature"
}
```

**Signature input**: `Ed25519Sign(genesis_key, SHA256(badge_id + ":" + tier + ":" + subject_did + ":" + passed_at + ":" + SHA256_hex(canonical_json(test_results))))`

The `test_results_url` MUST be a publicly accessible endpoint that returns the full conformance test output in the format defined in §5.

---

## 4. Badge Lifecycle

```
1. Run:    Operator runs conformance suite locally or via CI
2. Submit: POST /v1/conformance/submit with test_results + subject_did
3. Verify: Genesis Seed re-runs a subset of tests against live endpoint (online verification)
4. Issue:  Genesis Seed signs and returns badge attestation record
5. Publish: Operator embeds badge in README, docs, public registry listing
6. Expire:  Badge expires 90 days after issue; operator must re-run to renew
```

**Self-attestation (offline mode)**: For SDK badges that cannot be verified against a live endpoint, the operator signs the test results with their subject DID. The badge is labeled `self-attested` in the public registry — weight 0.7× vs Genesis Seed-verified badges.

---

## 5. Test Results Format

The conformance suite (S.10 extension) MUST produce results in this format:

```json
{
  "suite_version": "1.0.0",
  "run_id": "uuid-v4",
  "started_at": "ISO-8601",
  "completed_at": "ISO-8601",
  "subject": {
    "did": "did:web:node.example.com",
    "component": "adapter",
    "version": "1.2.0"
  },
  "results": [
    {
      "test_id": "CORE-01",
      "spec_ref": "S.1 §3.2",
      "description": "REGISTER response contains node_id and node_token",
      "status": "pass | fail | skip",
      "duration_ms": 45,
      "error": null
    }
  ],
  "summary": {
    "total": 42,
    "passed": 42,
    "failed": 0,
    "skipped": 0
  }
}
```

---

## 6. Badge Display

### 6.1 SVG Badge URL

```
GET https://iicp.network/badge/{tier}?did={subject_did}
```

Returns an SVG badge image. Color and label per tier:

| Tier | Color | Label |
|------|-------|-------|
| `iicp:core:v1` | `#2563EB` (blue) | `IICP Core v1` |
| `iicp:mesh:v1` | `#16A34A` (green) | `IICP Mesh v1` |
| `iicp:sdk:v1` | `#9333EA` (purple) | `IICP SDK v1` |
| `iicp:federated:v1` | `#DC2626` (red) | `IICP Federated v1` |
| `iicp:full:v1` | `#CA8A04` (gold) | `IICP Full v1` |

Status-aware: if badge is expired, SVG shows `IICP Core v1 · expired` with gray background.

### 6.2 Markdown Embed

```markdown
[![IICP Core Compliant](https://iicp.network/badge/iicp:core:v1?did=did:web:node.example.com)](https://iicp.network/conformance/verify?did=did:web:node.example.com)
```

---

## 7. Conformance API

### 7.1 Submit Results

```
POST /v1/conformance/submit
Content-Type: application/json

{
  "subject_did": "did:web:node.example.com",
  "tier": "iicp:core:v1",
  "test_results": { "...S.14 §5 format..." },
  "subject_sig": "base64url-ed25519-signature"
}
```

**Response** (on success):
```json
{
  "badge_id": "uuid-v4",
  "tier": "iicp:core:v1",
  "status": "verified | self-attested | pending-online-check",
  "badge_url": "https://iicp.network/badge/iicp:core:v1?did=...",
  "expires_at": "ISO-8601",
  "attestation": { "...§3 badge attestation record..." }
}
```

### 7.2 Verify Badge

```
GET /v1/conformance/verify?did={subject_did}&tier={tier}
```

Returns the current badge status for a given DID and tier. Used by clients, dashboards, and the public registry to check validity without downloading the full attestation record.

**Response**:
```json
{
  "subject_did": "did:web:node.example.com",
  "tier": "iicp:core:v1",
  "status": "valid | expired | not-found",
  "issued_at": "ISO-8601",
  "expires_at": "ISO-8601",
  "verification_mode": "genesis-verified | self-attested"
}
```

### 7.3 List Badges for DID

```
GET /v1/conformance/badges?did={subject_did}
```

Returns all active badges for a subject DID. Used by the public node registry.

---

## 8. Conformance Requirements

| ID | Requirement | Who |
|----|------------|-----|
| BADGE-01 | Badge attestation MUST be signed by Genesis Seed DID | Genesis Seed |
| BADGE-02 | Operators MUST NOT claim tiers their test results do not cover | Operator |
| BADGE-03 | Genesis Seed MUST expire badges older than 90 days | Genesis Seed |
| BADGE-04 | Badge SVG endpoint MUST reflect current expiry status in real time | Genesis Seed |
| BADGE-05 | Self-attested badges MUST be labeled as such in all public displays | Registry / Dashboard |
| BADGE-06 | Test results URL in attestation record MUST remain accessible for 90 days | Operator |

---

## 9. Phase Readiness

| Component | Change required |
|-----------|----------------|
| Directory (PHP) | Add `/v1/conformance/{submit,verify,badges}` endpoints; Ed25519 signing of attestation records |
| Public Registry | Display badge status per node; differentiate genesis-verified vs self-attested |
| Conformance suite (S.10) | Add test result output in §5 format; publish suite_version |
| `iicp.network` website | `/conformance` page; SVG badge endpoint; badge embed docs |
| SDK | `IicpClient.conformance_check()` convenience method (optional) |

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.0 | 2026-05-15 | Initial draft — badge tiers, attestation record, lifecycle, conformance API, 6 MUST requirements (BADGE-01–06) |
