# Security, session and receipt crosswalk: September 2026 update

**Verified:** 2026-09-25
**Status:** informative; no protocol adoption or implementation decision.

The [21 August crosswalk](EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-08-21.md)
remains a dated snapshot. The current Datatracker revision of the
[Security Principal and Verifier Binding draft](https://datatracker.ietf.org/doc/draft-bu-agentproto-security-principal-binding/07/)
is `-07` (2026-09-15), rather than `-06`. Its expanded verifier, dependency
and negative-case treatment reinforces the same IICP review question: each
identity, membership, route-authority and receipt claim needs an issuer,
carrier, verifier, freshness condition and failure behavior. It does not
merge those claims into one IICP credential or make the draft an IICP dependency.

The checked [Agent Session Requirements](https://datatracker.ietf.org/doc/draft-feng-agentproto-session-requirements/02/)
remain at `-02` (2026-08-20), and the checked
[SCITT agent-action receipt profile](https://datatracker.ietf.org/doc/draft-noa-scitt-ai-agent-receipt/01/)
remains at `-01` (2026-08-15). Discovery and policy-constrained selection
precede any optional session; a receipt remains evidence of its issuer's
bounded claim, not proof of task correctness. These are individual drafts,
not an adopted session or receipt standard for IICP.

No released IICP field, profile, ticket or receipt changes as a result of
this source update. A future mapping needs a concrete cross-implementation
use case, compatibility review and executable vectors.
