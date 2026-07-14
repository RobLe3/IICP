# Proposal — Additive Profile Negotiation v0

**Status:** pre-normative, additive draft · **Depends on:** profile fixture
`0.4.0-draft` and `fixtures/profile-negotiation-v0.json`.

## Contract

A discovery caller may send `profile_id`, `profile_version`,
`profile_fixture_sha256`, and `profile_required` query parameters. They ask a
directory whether it recognizes the named pre-normative profile fixture; they
do not carry task content, provider credentials, endpoints, or policy details.

Once `profile_id` is present, the version and 64-character fixture digest are
also required. This prevents an implementation from accepting a profile name
while silently evaluating a different fixture revision.

When no profile fields are sent, the discovery request and response preserve
the legacy contract. During a draft fixture revision, an implementation MAY
recognize the immediately preceding manifest-pinned identity as well, so an
explicit required request does not break solely because peers upgraded at
different times. When a request is sent, the response includes a redacted
`profile_negotiation` object with the requested identity, status, fixture
digest, and portable reason. A compatible directory returns `compatible`.

An unknown, mismatched, or incomplete **required** request is rejected before
candidate dispatch with `unsupported_pre_normative_profile`. An unsupported
optional request returns ordinary candidates plus an `unsupported` negotiation
result. Clients still perform their native candidate-policy evaluation; this
v0 contract only establishes a shared fixture interpretation.

## Boundaries

This does not make draft profiles required, change stable URNs, register a
provider profile, or alter default routing. It is a directory-capability
negotiation step. Provider-level profile declarations and normative profile
ratification require separate evidence.
