# Security-mechanism lifecycle and historical evidence

**Status:** accepted architecture; mechanism assignments remain profile-owned  
**Related:** IICP #55, #160, #161 and #215

## Decision

IICP keeps four decisions separate:

```text
understand an artifact
  -> verify its historical cryptographic statement
  -> trust that mechanism under current policy
  -> authorize the requested action
```

Success at one step does not imply success at the next. In particular, a valid
historical signature proves only the statement defined by its historical
profile. It does not make the signer trusted today and does not authorize an
execution.

Security profiles and registry entries use these lifecycle states:

| State | Meaning under current policy |
| --- | --- |
| `active` | May be considered when all other policy and authorization checks pass. |
| `deprecated` | Meaning remains reconstructable; new use is discouraged and policy may refuse it. |
| `prohibited` | May be parsed or historically verified, but cannot authorize new execution. |
| `replaced` | Historical meaning remains intact and an explicit `replaced_by` relation identifies a successor. |

Deprecation or replacement never rewrites historical meaning. Prohibition does
not require deleting the parser or verification material needed to interpret
old evidence.

## Evaluation and downgrade behavior

The receiver identifies the mechanism and its historical profile, verifies only
the claims that profile actually defines, resolves its current lifecycle entry,
and applies current local policy. Unknown required mechanisms, prohibited
mechanisms and offers that remove a mutually required stronger mechanism fail
closed before dispatch. An implementation must not retry with an older mechanism
merely to obtain interoperability.

Replacement is explicit registry metadata, not an assumption that the two
profiles have identical properties. A current policy may accept the replacement
while refusing the replaced profile. Current policy remains the authority even
when the historical artifact is syntactically valid and cryptographically
verifiable.

## Gateway claim boundary

A compatibility gateway creates a new security boundary. Evidence must name the
party that established each property:

```text
current peer <-> gateway: current profile, established by gateway
gateway <-> historical endpoint: historical profile, established by endpoint
```

The gateway may attest that it translated or verified a historical exchange.
It must not claim that the historical endpoint used the gateway-facing profile,
algorithm or assurance level. Missing issuer or boundary attribution is refused.

## Compatibility catalog

Each coordinated compatibility environment under IICP #55 references the exact
security-profile generation and registry lifecycle data that applied to that
release. Implementation support projections record what an implementation can
parse and verify separately from what current policy permits. This is historical
reconstruction evidence, not a promise that obsolete mechanisms remain usable.

## Non-goals

This decision selects no permanent algorithm, implements no compatibility
gateway or post-quantum mechanism, changes no base wire format, and does not
weaken current authentication, authorization or downgrade requirements.
