# Continuing IICP development

IICP is licensed and documented so that independent parties can review,
implement and continue the protocol without access to the original maintainer's
private development methods or production systems.

## Start here

1. Read [`GOVERNANCE.md`](GOVERNANCE.md), [`SPEC_STATUS.md`](SPEC_STATUS.md) and
   [`VERSIONING.md`](VERSIONING.md).
2. Use [`ecosystem/public-repositories.json`](ecosystem/public-repositories.json)
   to locate the authoritative specification and maintained implementations.
3. Reproduce the checks in [`CONTRIBUTING.md`](CONTRIBUTING.md) and
   [`SPEC_RELEASE_PROCESS.md`](SPEC_RELEASE_PROCESS.md).
4. Use [`research/RESEARCH.md`](research/RESEARCH.md) for product decisions,
   rejected alternatives and open evidence gaps. Research is informative unless
   a specification explicitly makes it normative.
5. Use [`standards/REVIEWING.md`](standards/REVIEWING.md) for an independent
   standards review or Internet-Draft candidate review.
6. Use [`standards/IICP_PROTOCOL_POSITIONING.md`](standards/IICP_PROTOCOL_POSITIONING.md)
   and the dated [protocol comparison](standards/PROTOCOL_COMPARISON_2026-08-15.md)
   before changing IICP's boundary with IAIP, AIDIP, MCP, A2A or discovery
   protocols. The machine-readable facts live in
   `standards/protocol-comparison-v1.json`.

## What an independent implementation needs

The versioned specifications, registries, JSON schemas, fixtures and
conformance runner are the interoperability contract. The Rust, Python and
TypeScript SDKs are useful implementation evidence, but no one implementation
may silently redefine the protocol. The PHP and Rust directory repositories
implement the control plane and have separate release lifecycles.

An implementation should declare the protocol and profile versions it supports,
fail safely on unsupported required behavior and preserve the documented
privacy and security boundaries. Cross-language agreement within this project
is parity evidence, not independent adoption.

## Forks and stewardship

The Apache-2.0 license permits independent use and forks under its terms. A fork
does not automatically become the canonical IICP specification, inherit the
IICP name, control existing package registries or gain access to production
credentials. Those are distinct technical, governance, trademark and account
questions.

While the current repository remains maintained, propose protocol changes in a
public issue and pull request. If it becomes unavailable, a successor effort
should preserve immutable release history, publish its governance and security
contacts, document the divergence point, retain compatibility fixtures and
avoid reusing released version numbers for different semantics. Competing forks
should use explicit implementation or profile identifiers until governance and
interoperability converge.

Maintainer or standards-editor authority should be based on sustained public
review and implementation work, not access to private tools. A governance
transition must identify the repositories, release-signing authority, registry
accounts and security-reporting channel being transferred. No protocol artifact
should contain the credentials or recovery secrets needed for that transfer.

## Standards work

An Internet-Draft contribution is governed by the IETF process and IETF Trust
terms in addition to this repository's license. Building a review bundle or
discussing the protocol does not authorize a submission, create IETF consensus
or request an IANA registration. Any future registration request must identify
the responsible public specification, change controller and review policy.

## Public/private boundary

Technical research that led to a product or protocol decision belongs in the
public record with enough method and evidence to reproduce the conclusion.
Private prompts, orchestration, work-selection systems and personal meta-tools
are not implementation dependencies. The complete boundary is documented in
[`docs/governance/public-artifact-boundary.md`](docs/governance/public-artifact-boundary.md).
