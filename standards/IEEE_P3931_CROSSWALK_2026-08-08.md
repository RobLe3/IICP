# IICP-DIR / IEEE P3931 crosswalk — 2026-08-08

**Status:** research note for IICP issue #105. It is not an IEEE submission,
endorsement, implementation claim, or compatibility assertion.

## Source boundary

This note compares public IICP material with the IEEE P3931 public project page,
*Standard for Agent Description, Discovery, and Registry (ADDR)
Interoperability*, checked 2026-08-08. The page describes an **Active PAR**,
approved 2026-03-26; it is not a published IEEE standard. Its public scope
covers description metadata, lifecycle APIs, discovery/matching, federation,
access control, rate limiting, validation, and conformance. It explicitly puts
identity frameworks, trust scoring, collaborative governance, and domain
business semantics outside scope. Source: <https://standards.ieee.org/ieee/3931/12499/>.

| Mechanism | Public P3931 PAR scope | IICP evidence | Difference / risk | Disposition |
|---|---|---|---|---|
| Description and capabilities | Metadata, I/O types, bindings, version and runtime/resource constraints | `node-capability-format.md`, `registry/intents.json`, directory OpenAPI | P3931 data model text is not public here; no field-level compatibility claim is possible | defer pending standard text |
| Lifecycle | Registration, update, revocation, signatures, timestamps and integrity | `iicp-dir.md`; lifecycle conformance profile | IICP heartbeat and signed event behavior may be an extension, not a conflict | align terminology |
| Discovery and matching | Query, filter, rank, negotiate using semantic tags, performance and compatibility | `iicp-dir.md`, discovery fixtures | IICP distinguishes eligibility and route authorization from discovery | profile |
| Health and freshness | Performance metrics plus fallback/degradation | telemetry and discovery-evidence profiles | Reputation/trust must not be presented as P3931 behavior; P3931 excludes trust scoring | retain distinct |
| Federation | Synchronization, caching and conflict resolution | `iicp-federated-directory.md`, replica lifecycle contract | Public PAR does not expose consistency algorithms or failure semantics | defer pending standard text |
| Access and abuse controls | Access control, rate limiting, validation/security | directory specification and conformance | IICP policy eligibility and dispatch tickets extend registry admission | extend |
| Conformance | Test suites, compliance assertions and plugfests | `conformance-runner/`, directory profiles | Internal fixtures do not yet prove cross-organization interoperability | contribute implementation experience |
| Execution selection and receipts | Not stated in public PAR scope | dispatch tickets, policy manifests, receipts | IICP control-plane selection is intentionally outside a generic registry description | retain distinct |

## Positioning conclusion

IICP should describe itself as a protocol-neutral intent-resolution and
execution-selection control plane, not as a replacement for a prospective
registry interoperability standard. If P3931 publishes usable normative text,
map description/lifecycle/discovery terminology before claiming a profile. Keep
live operational eligibility, policy filtering, short-lived route authorization,
and redacted execution evidence as candidate IICP extensions. No contact,
submission, normative promotion, wire change, release, or deployment follows
from this note.
