# Pre-normative profile fixtures

These fixtures define the minimum deterministic cases that every future
implementation of the layered profile substrate must evaluate before the
profiles can become normative. They are deliberately independent of a specific
SDK, directory, transport, or database implementation.

`profile-compatibility-v0.json` covers stable and deprecated intents, schema
digests, optional and required extensions, expired experimental extensions,
policy refusal, and MCP/A2A mapping boundaries. Each scenario has an expected
eligibility result and portable reason code; implementations that have not
adopted this draft profile must report the defined
`unsupported_pre_normative_profile` status rather than inventing a different
compatibility rule.

`dispatch-route-ticket-v1.json` covers signed disclosure-only route tickets,
including malformed, tampered, expired, issuer, audience, node and intent
mismatches. It does not imply v1 node admission, single-use redemption or
signer-key revocation.

`selection-v1.json` covers opt-in `weighted_v1` inverse-load selection after
hard eligibility, including stable ordering, bounded load clamping, and the
single-candidate case. It does not alter the default `epsilon` strategy.

`profile-negotiation-v0.json` covers additive directory capability negotiation
for a caller-requested pre-normative profile. No request preserves legacy
discovery; unsupported required requests fail closed, while optional requests
remain advisory.

`cip-consumer-cosignature-v1.json` covers the optional, pre-normative
`consumer_cosignature_v1` profile. It pins RFC 8785 subset bytes, a
domain-separated SHA-256 receipt digest, provider and consumer Ed25519
signatures, anti-replay/binding/key-lifecycle cases, self-dealing exclusions,
and network-isolated reservation/settlement outcomes. It does not enable the
profile or change production credits, reputation, reservation or settlement.

`endpoint-security-v1.json` covers the common public/private address and
hostname policy used by the maintained clients before a provider connection is
pinned. It does not publish resolver output or authorize private routes.

`service-lifecycle-v1.json` covers valid and invalid asynchronous lifecycle,
resume, retry, disconnect, cancellation and privacy behavior. It remains draft
until two independent implementations consume the same digest.

`profile-fixture-manifest-v0.json` pins its declared canonical SHA-256 digests.
Standalone endpoint-security and lifecycle research fixtures are instead
byte-compared with their declared mirrors by dedicated synchronization checks
until their implementation gates are complete.

The fixture set is pre-normative: it does not alter current discovery wire
formats or make profile fields required. Any change must increment the fixture
version, update the manifest digest, retain a migration note, and pass all
maintained implementations.
