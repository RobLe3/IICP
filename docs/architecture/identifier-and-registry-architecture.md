# Architecture decision: identifier and registry architecture

**Status:** Accepted project identifier boundary; external registration pending  
**Recorded:** 2026-08-14  
**Machine-readable contract:**
[`identifier-registry-v1.json`](identifier-registry-v1.json)  
**Related work:** IICP #40, #43, #47, #55, #160 and #161

## Decision

Strings beginning with `urn:iicp:` are stable IICP project identifiers. They
remain byte-for-byte compatible and are compared as opaque, case-sensitive
values. They are not described as identifiers in an already registered formal
URN namespace: the IANA URN Namespace registry contained no `iicp` namespace
identifier when checked on 2026-08-14.

IICP will prepare a formal `iicp` Namespace Identifier registration under RFC
8141. Submission requires the authorship, change-control, contact and succession
authority tracked by IICP #47. This decision does not submit or claim that
registration. If registration cannot preserve the deployed identifier form,
the project must publish a separately reviewed alias and migration plan;
released identifiers are never silently rewritten or reassigned.

Implementations must stop deriving protocol meaning through scattered string
construction. Public interfaces continue to accept strings for compatibility,
but internal `IntentId`, `CapabilityId`, `ProfileId`, `BindingId` and `SchemaId`
types should validate once and otherwise preserve opaque bytes. Typed wrappers
are implementation hardening, not a wire change.

## Namespace allocation

The existing hierarchy is retained pending registration:

```text
urn:iicp:intent:...
urn:iicp:capability:...
urn:iicp:profile:...
urn:iicp:binding:...
urn:iicp:evidence:...
urn:iicp:schema:...
```

Public assignments require a stable specification and registry entry. The
`x.<label>` intent subdomain remains an IICP Private Use convention for
operator-controlled identifiers. `x.exp` is the IICP Experimental Use area.
Neither convention is presented as IETF practice or as a separate URN
namespace. Private identifiers cannot later acquire public meaning without a
new public identifier and an explicit relationship record.

Identifiers are persistent names, not locators. No identifier requires online
resolution. Registry documents may provide current schemas, lifecycle and
documentation links, but failure to reach such a document does not invalidate
an otherwise valid cached identifier or signed artifact.

## Registry policy

IICP uses the RFC 8126 policy vocabulary internally so later external review
does not require a new governance model:

| Registry | Public assignment policy | Private/experimental space |
| --- | --- | --- |
| Intent namespaces and canonical intents | Specification Required with designated review | `x.<label>` Private Use; `x.exp` Experimental Use |
| Capability identifiers | Specification Required | vendor-qualified Private Use |
| Profiles | Specification Required with interoperability and security review | vendor-qualified Experimental Use |
| Bindings | Specification Required with compatibility and downgrade analysis | vendor-qualified Experimental Use |
| Frame and message types | Expert Review plus a stable specification | explicitly reserved private-use range only |
| Error codes | Specification Required; Expert Review for security-sensitive errors | reserved private-use range only |
| Security mechanisms and evidence profiles | Expert Review plus a stable public specification | no private assignment may claim general interoperability |
| Schema and conformance identifiers | Specification Required | local schemas use implementation-qualified identifiers |

The least restrictive policy that protects interoperability should be used.
Registry review does not certify security, quality, legal compliance or
deployment fitness.

## Lifecycle and compatibility

Each public entry records its identifier, kind, status, introduced version,
owner, specification, compatibility information and review date. Deprecated
entries remain resolvable and keep their meaning. Replacement uses an explicit
`replaced_by` relationship. Removed or revoked security material is distinct
from deprecated semantic identifiers.

Unknown identifiers remain opaque. An unknown required Profile, Binding or
security mechanism fails closed. An unknown optional identifier may be retained
or ignored only when every required constraint remains satisfied. Identifier
spelling alone never grants authorization, capability, trust or routing
eligibility.

## Current implementation inventory

All maintained SDKs, both directories and browser surfaces contain prefix
regular expressions or constructors for `urn:iicp:` intent values. The
machine-readable contract records the owned source locations and required
hardening direction. No bulk wrapper migration is authorized in this decision;
each component should adopt opaque wrappers when it next changes its public
identifier handling, using shared compatibility fixtures.

## Non-goals

This decision does not register the `iicp` NID, create an online resolver,
rename released identifiers, change registry version 1.4, submit an IANA
request, or authorize a standards claim. Port and media-type registrations
remain owned by IICP #43.
