# Proposal — Policy and Data-Handling Profile

**Status:** fixture-gated pre-normative draft (profile fixture `0.3.0-draft`) · **Depends on:** existing intent-risk taxonomy, policy manifests, DSR/key lifecycle work.

## Purpose

Make policy-aware routing machine-readable without promising anonymity,
executor-blind inference, legal compliance, or universal jurisdictional
coverage.

## Proposed fields

- data class and remote-routing eligibility;
- allowed region/jurisdiction constraints;
- retention, training/use and subprocessors claims;
- tool-risk and required approval level;
- encryption/key requirement;
- receipt and human-review requirement;
- public versus authenticated extended-manifest disclosure.

The companion `schemas/policy-and-data-handling-profile-v0.schema.json` is an
additive draft schema. `remote_routing=local_only` is a caller-side exclusion,
not a claim that a provider cannot be contacted by other policy contexts.
Public views may expose only routing-safe profile claims. Any richer operator
or processor detail belongs to authenticated disclosure and remains a provider
claim unless independently evidenced.

## Routing rule

A client excludes a candidate before dispatch when its policy profile conflicts
with the request. A client may accept a compatible profile only as a provider
claim unless conformance, attestation or observed evidence says otherwise.
Absence of this additive draft profile preserves current routing behaviour;
unknown critical requirements fail closed only when a caller explicitly asks
for this profile.

## Evidence gate

The canonical risk-taxonomy parity check must remain green across Python,
TypeScript, Rust and browser consumers. New policy values need corresponding
schema fixtures, refusal tests and user-facing wording before ratification.
Fixture results use the shared manifest digest and portable reason codes so a
provider cannot substitute a weaker local policy interpretation.
