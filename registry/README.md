# IICP intent registry

`intents.json` is the canonical vocabulary of standard IICP intent URNs. It is
not a live inventory of providers. A directory may report only the subset that
its currently registered nodes advertise.

The current document is the compatibility registry. IICP issue #99 tracks a
strict v2 registry with executable input/output schemas, lifecycle ownership,
review dates, compatibility declarations and evidence links. Existing URNs and
the current `payload_schema` field remain stable while that additive migration
is reviewed.

## Current lifecycle meanings

- `active`: defined for current use. This status does not prove live provider
  availability.
- `reserved`: the identifier is held for a named profile but is not an active
  interoperability claim.
- `deprecated`: retained for compatibility; `deprecated_by` identifies the
  replacement.

Implementation-defined intents use a separately governed custom namespace and
must not be added to this file merely because they appear in an example or
test. Proposed standard intents require public specification review, schemas,
fixtures and implementation evidence.
