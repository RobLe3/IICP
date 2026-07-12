# Proposal — Intent, Capability and Extension Registry Profile

**Status:** fixture-gated pre-normative draft (profile fixture `0.2.0-draft`) · **Depends on:** IICP semantics, node capability format, spec-only sync issue `RobLe3/IICP#2`.

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

The strategic taxonomy simulation covers stable intents, aliases, schema mismatch, optional/required extensions, risk refusal, A2A skill mappings and MCP tool mappings. This proposal cannot become normative until manifest-pinned fixtures are shared across all directory and SDK implementations and the spec-only release records their digest and changelog entry.
