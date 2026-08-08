# IICP intent registry

`intents.json` is the canonical vocabulary of standard IICP intent URNs. It is
not a live inventory of providers. A directory may report only the subset that
its currently registered nodes advertise.

Registry 1.4 adds executable JSON Schema 2020-12 input and output references,
content digests, lifecycle history, ownership, review dates, compatibility
declarations, fixtures and released-implementation evidence. It remains at the
existing `registry/intents.json` and `/.well-known/iicp-intents.json` paths.
Existing URNs and the descriptive `payload_schema` field remain available for
pre-1.4 consumers.

## Current lifecycle meanings

- `active`: defined for current use. This status does not prove live provider
  availability. Active entries cite a shared payload fixture and at least one
  released implementation.
- `experimental`: the identifier and draft schema are available for testing,
  but released intent-specific interoperability evidence is incomplete.
- `reserved`: the identifier is held for a named profile but is not an active
  interoperability claim.
- `deprecated`: retained for compatibility; `deprecated_by` identifies the
  replacement.
- `withdrawn`: no longer available for new use. A retained record explains the
  disposition and prevents accidental identifier reuse.

Implementation-defined intents use a separately governed custom namespace and
must not be added to this file merely because they appear in an example or
test. Proposed standard intents require public specification review, schemas,
fixtures and implementation evidence.

`source-classification.json` is a dated audit of intent-like strings in the
public repositories. Negative tests, policy examples, custom namespaces and
unregistered candidates remain visible there without gaining canonical status.
Run `python3 tools/audit_intent_sources.py --check` from a full workspace to
detect new, undispositioned observations.
