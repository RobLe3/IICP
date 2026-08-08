# Architecture decision: portability and non-capture

**Status:** Accepted project principle  
**Recorded:** 2026-08-08  
**Related work:** IICP issues #31, #47, #54, #93 and #99

## Decision

IICP protocol behavior must remain independently implementable from public
specifications, schemas and conformance material. No implementation, hosted
directory, package registry, repository namespace or current steward is part
of the wire protocol's authority.

The control plane may support multiple trust domains and federated directory
operators. Task payloads remain on the execution path between participants and
must not be routed through the directory merely to preserve organizational
control.

Portable identity, policy and evidence formats should use stable public
contracts. Project-specific mechanisms are justified only when an established
standard cannot express the required behavior or security boundary.

Shared stewardship is earned through sustained, reviewable contribution. The
current founder-led model remains legitimate while participation is limited,
but release, recovery and decision procedures must permit responsibility to be
shared when qualified contributors appear.

## Consequences

- Reference implementations cannot redefine protocol semantics.
- Public registries and fixtures require machine-readable authority and
  reproducible releases.
- Migration to another language, operator or repository host must not require
  changes to existing protocol identifiers.
- Federation claims require independently observable interoperability rather
  than multiple processes controlled by one operator.
- Governance must not be presented as distributed before responsibility is
  genuinely shared.

## Non-goals

This decision does not require an immediate foundation, repository transfer,
PHP deprecation, Rust cutover or production federation deployment.
