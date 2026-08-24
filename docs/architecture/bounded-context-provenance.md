# Bounded-context and decision provenance

This map explains historical `BC-*` and `ADR-*` references that remain in the
Protocol Suite. Those labels preserve design provenance; they are not a second
source of normative requirements.

## Authority

Current behavior is defined, in order, by the released Core, applicable
Profiles and Bindings, registries and schemas, and their versioned fixtures.
Architecture documents explain why those artifacts have their present shape.
An issue, research note, historical bounded-context label or historical ADR
label cannot override them.

## Historical bounded-context labels

| Label | Durable concern | Current public authority |
| --- | --- | --- |
| BC-8 | Federated directory continuity and independently administered replicas | Federated Directory specification, federation Profiles and fixtures |
| BC-9 | Developer experience and external conformance | Conformance runner, released fixtures and external-evidence guidance |
| BC-11 | Cooperative execution without making one runtime or transport universal | Capability semantics and optional execution Profiles/Bindings |
| BC-12 | Stable identity separated from location, membership and route authority | Identity, security and restricted-trust-domain Profiles and fixtures |
| BC-13 | Candidate future management/policy concern | Research only unless promoted into an approved public contract or architecture record |

A reference to a bounded context identifies the concern that informed a design.
It does not make the original implementation, language, database, transport or
organizational structure part of IICP semantics.

## Historical ADR labels

Historical `ADR-*` references identify the decision lineage behind a released
artifact. A future reader should reconstruct the binding decision from the
current architecture record and the released artifact it governs, not infer
requirements from a missing private or obsolete source file. When a decision
changes, its current architecture record must state the replacement or
supersession relationship; published semantic meaning must not be silently
rewritten.

## Promotion rule

Research becomes project authority only through an explicit reviewed change to
an owning public layer: Core, Profile, Binding, Registry, schema, fixture, or an
implementation-neutral architecture record. Implementation and product choices
remain below that boundary. Release history, immutable tags and compatibility
environment records preserve the meaning of earlier generations.
