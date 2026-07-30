# IICP specification status

IICP uses the following status terms. They describe different kinds of
evidence and must not be treated as synonyms.

| Status | Meaning |
| --- | --- |
| **Project-normative** | Binding for implementations claiming conformance to the named IICP Protocol Suite release. |
| **Stable** | Project-normative behavior protected by the compatibility and deprecation policy. |
| **Active draft** | Reviewed work under development. It is not required for suite conformance unless a released profile explicitly incorporates it. |
| **Experimental** | Research or implementation work without enough interoperability and operational evidence for normative promotion. |
| **Externally ratified** | Approved by the named external standards body. IICP uses this label only with a public external reference. |

“Implemented,” “deployed,” and “project-normative” are separate claims.
Deployment by the Genesis Seed does not ratify protocol text. A reference
implementation cannot silently redefine a released specification.

## Compatibility policy

- Patch releases correct or clarify existing requirements without intentionally
  breaking conforming implementations.
- Minor releases may add project-normative behavior. New mandatory behavior
  requires migration notes and conformance evidence.
- Breaking wire changes require a major release or a separately negotiated
  versioned profile.
- Stable behavior receives a documented deprecation window before removal.
  Security fixes may shorten that window, but the release notes must say so.
- Unknown optional fields and extensions are handled according to the relevant
  profile; this document does not create a universal ignore rule.

## Authority

The immutable specification release, its schemas, registries, conformance
identifiers and integrity manifest form the citable release set. OpenAPI
documents are machine-readable projections. Software and live deployments are
evidence, not normative authority.
