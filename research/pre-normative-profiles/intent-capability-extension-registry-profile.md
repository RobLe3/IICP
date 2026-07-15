# Proposal — Intent, Capability and Extension Registry Profile

**Status:** fixture-gated pre-normative draft (profile fixture `0.4.0-draft`) · **Depends on:** IICP semantics, node capability format, spec-only sync issue `RobLe3/IICP#2`.

## Purpose

Separate what a participant wants from what a provider can do and under what
conditions it may do it.

## Proposed layers

1. **Core intent** — stable, outcome-level URN.
2. **Capability profile** — input/output schema URI and digest, modalities, limits, backend/tool binding and pricing hints.
3. **Policy profile** — data class, retention/training claim, jurisdiction, approval and tool-risk requirement.
4. **Evidence profile** — key readiness, conformance, observed health, receipt support and attestation references.
5. **Extension declaration** — versioned URI with `required` boolean and parameters.

## Compatibility rules

- Existing active URNs remain valid.
- Deprecated URNs may provide an explicit successor mapping only when their schemas remain compatible.
- A provider is ineligible when intent, schema digest, or a required extension is incompatible.
- Unknown optional extensions do not change core compatibility.
- Experimental extensions require an owner, review/expiry date and no interoperability guarantee. A required experimental extension past its review expiry is rejected with `experimental_extension_expired`.
- Compatibility uses the released fixture digest and portable reason codes. An
  implementation that has not adopted this draft profile returns
  `unsupported_pre_normative_profile`; it does not silently reinterpret a
  required extension.

## Evidence gate

The strategic taxonomy simulation covers stable and unknown intent versions, deprecated aliases, schema digest match/mismatch, optional and required extensions, risk refusal, A2A skill mappings and MCP tool mappings. This proposal cannot become normative until manifest-pinned fixtures are shared across all directory and SDK implementations and the spec-only release records their digest and changelog entry.

## Registry entry contract

Each registered intent or extension entry defines:

| Field | Requirement | Meaning |
|---|---|---|
| `id` | MUST | Stable intent URN or extension/profile URI. |
| `kind` | MUST | `intent`, `capability_profile`, `policy_profile`, `evidence_profile`, `binding`, or `subprotocol`. |
| `version` | MUST | Semantic version of this declaration; intent major remains in the URN. |
| `status` | MUST | `proposed`, `experimental`, `active`, `deprecated`, or `withdrawn`. |
| `owner` | MUST | Accountable registry steward or external standards authority. |
| `created_at` / `updated_at` | MUST | RFC 3339 registry timestamps. |
| `review_at` | MUST for experimental | Date by which continuation, promotion, or expiry is decided. |
| `input_schema` / `output_schema` | MUST for executable intent | JSON Schema 2020-12 URI plus SHA-256 digest. |
| `compatibility` | MUST | Compatible predecessor versions and explicit breaking boundaries. |
| `successor` | MUST when deprecated | Replacement identifier or explicit `none`. |
| `references` | SHOULD | Conformance fixture, binding and change record references. |

The URI locates a schema; the digest identifies the exact reviewed content.
Resolvers MUST verify the digest before using fetched schema content. A changed
schema digest under the same active declaration is a registry error rather than
a silent update.

## Lifecycle and version rules

- `proposed` entries are discussion artifacts and MUST NOT be required for
  interoperability.
- `experimental` entries may be negotiated only by explicit opt-in and MUST
  carry an owner and review date. Expiry makes a required use ineligible with
  `experimental_extension_expired`.
- `active` entries have released schemas, conformance vectors, implementation
  evidence and a recorded change decision.
- `deprecated` entries remain resolvable for their announced migration window.
  An alias is valid only where schema and lifecycle semantics are compatible.
- `withdrawn` entries MUST NOT be selected for new work. Historical receipts
  may continue to resolve their immutable registry record.
- A breaking payload or lifecycle change requires a new intent major/identifier.
  Additive optional fields may use a declaration minor version only when old
  receivers preserve their prior semantics.
- Unknown required profiles/extensions fail closed. Unknown optional declarations
  are ignored and MUST NOT weaken intent, policy or security requirements.

## Disclosure boundary

Public discovery exposes only the stable identifier, declaration version,
schema URI/digest, modalities, coarse limits and public policy/evidence claims
needed for eligibility. Authenticated manifests may disclose additional
processor, attestation or operational detail. Neither surface contains prompts,
responses, credentials, private endpoints or backend topology.

## Governance and release

Registry promotion is one-way and reviewed: working proposal, deterministic
fixtures, cross-implementation evidence, spec-only digest/changelog update, then
normative release. Implementation repositories cannot silently overwrite the
spec-only registry. Emergency withdrawal preserves the immutable historical
entry and adds a signed status change rather than deleting evidence.
