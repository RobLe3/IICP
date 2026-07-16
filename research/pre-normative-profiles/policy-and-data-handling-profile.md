# Proposal — Policy and Data-Handling Profile

**Status:** fixture-gated pre-normative draft (profile fixture `0.4.0-draft`) · **Depends on:** existing intent-risk taxonomy, policy manifests, DSR/key lifecycle work.

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

## Request and provider declarations

The same schema is used in two roles and implementations MUST preserve the role:

- a **request requirement** states the caller's minimum routing conditions;
- a **provider declaration** states what the provider claims it will do.

A declaration satisfies a requirement only through explicit field rules; missing
values are not treated as permissive. A request may mark individual requirements
critical. An unknown critical field or value fails with
`unsupported_policy_requirement`; an unknown optional value is ignored without
weakening known requirements.

## Field semantics

- `data_class` is caller classification, not content inspection by the Directory.
  Classification SHOULD occur locally. `restricted` is a conservative routing
  class, not a claim that one specific law applies.
- `remote_routing` is a hard caller gate. `local_only` forbids remote
  dispatch; `requires_approval` requires the declared approval event before
  dispatch; `allowed` does not override any other restriction.
- `jurisdiction` and `allowed_regions` describe declared execution/operator
  location constraints. Region is not evidence of legal establishment or legal
  compliance.
- `retention.task_payload`, `training_use` and `subprocessors` are provider
  claims. `unknown` or absent does not satisfy a caller requiring `none`.
  `transient` requires a separately declared bounded operational interval.
- `approval`, `requires_human_review` and `tool_risk` are cumulative. A
  provider cannot downgrade a caller's required approval or tool-risk boundary.
- `requires_encryption` requires a currently usable negotiated confidentiality
  profile/key before dispatch; transport TLS alone does not satisfy an explicit
  payload-confidentiality requirement.
- `requires_receipt` requires a negotiated redacted receipt profile, not an
  arbitrary log statement.

## Evidence and precedence

Provider declarations are not self-authenticating evidence. A decision record
keeps four sources distinct: caller requirement, provider claim, independent
conformance/attestation, and observed operational evidence. A more favorable
claim never overrides a conflicting authenticated manifest or observed hard
failure. Absence of independent evidence is represented as unknown rather than
false certification.

Hard caller requirements, prohibited/high-risk intent policy, authorization,
required confidentiality and local-only routing take precedence over score,
reputation, price, load spreading and fallback. Failure to find a compatible
candidate returns a policy refusal; fallback MUST NOT widen the policy.

## Disclosure and receipts

Public capability output may expose only coarse routing-safe values and a
manifest digest/reference. Authenticated disclosure may provide declared
retention intervals, subprocessors and evidence references to an authorized
caller. Receipts contain requirement/declaration digests, decision reason and
redacted provider reference, but no prompt, response, credential, raw endpoint,
natural-person contact detail or private backend topology.

For ticketed dispatch, a directory MAY bind the public-safe canonical manifest
digest into its signed route ticket as `policy_manifest_sha256`. A client that
receives this claim MUST compare it with the selected route's manifest digest
before dispatch and fail closed on absence from the route, malformed values or
mismatch. Tickets without the additive claim remain compatible and do not make
a policy manifest required. This binding authenticates correspondence between
the ticket and public manifest summary; it does not certify the declaration.

## Evolution

New values require a schema version, compatibility rule, refusal fixture,
cross-SDK implementation evidence and user-facing wording. Existing values are
never silently redefined. This draft remains optional until negotiated; future
ratification must preserve legacy behavior for callers that do not request it.

## Operational evidence boundary

The companion pre-normative operational-evidence fixture distinguishes an
authenticated local verification result from a provider declaration. A caller
may require evidence classes for a retention control, subprocessor disclosure,
or approval event. Each accepted record is bound to the selected manifest
digest, locally verified, and unexpired at evaluation time. Missing, unknown,
unauthenticated, expired, or digest-mismatched required evidence fails closed.

The evaluator does not verify legal compliance and does not prove that a
declared process was followed outside the observed evidence boundary. The
`verified` input is produced by an authenticated verifier; it MUST NOT be copied
from an untrusted provider payload. This additive check is opt-in and does not
change legacy discovery or dispatch.

### Production opt-in and rollback

Operators first publish a signed policy manifest and validate its public digest,
then expose authenticated evidence only to authorized callers. Consumers enable
operational-evidence requirements per request after pinning the fixture/profile
version. Rollback disables the optional requirement and returns to legacy route
evaluation; it never treats failed evidence as permission to widen routing.

## Executable compatibility contract

The pre-normative `fixtures/policy-data-handling-v0.json` fixture separates a
caller `requirement`, provider `declaration`, and locally observed `context`.
The evaluator order is deterministic so all maintained SDKs return the same
portable refusal reason. `accepted_data_classes` is a provider declaration;
`data_class` remains caller classification. A transient-retention declaration
MUST include `max_seconds` when a caller supplies a maximum. Encryption and
receipt readiness are local negotiated/observed context, not inferred from a
provider claim. Unknown optional hints are ignored only after all known hard
gates are evaluated; an unknown field named by `critical_requirements` fails
closed. These evaluators remain opt-in and MUST NOT widen fallback or alter
legacy discovery when the draft profile was not requested.
