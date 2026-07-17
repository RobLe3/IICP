# Consumer co-signature profile research

**Status:** pre-normative executable evidence; no settlement or wire behavior
changed.

`urn:iicp:profile:cip:consumer-cosignature:v1` binds provider and consumer
Ed25519 signatures to the same RFC 8785/JCS receipt digest. The receipt includes
task, intent, serving/querying node, response hash, accounting strings,
completion/expiry, and dispatch nonce. Raw prompts and responses are excluded.

The shared fixture defines byte-identical JCS vectors, anti-replay and binding
refusals, key lifecycle, self-dealing exclusions, and terminal settlement
outcomes. Signatures prove attribution, not answer quality.

## Dormant adoption metadata

Providers may explicitly advertise
`supported_receipt_profiles: ["consumer_cosignature_v1"]`. Absence means
unsupported and unknown values are rejected. Directories may persist this list
for migration evidence, but public discovery exposes only
`consumer_cosignature_ready: true|false` and public statistics expose only
anonymous ready/heartbeating counts.

This metadata MUST NOT affect routing, trust, credits, reputation, reservation,
or settlement before a separate normative decision and adoption gate. Legacy
clients remain usable and receive no elevated attribution weight.
