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

## Compatibility transition states

Implementations evaluating this proposal use three named transition states:

- `legacy`: current additive behavior; a missing co-signature remains compatible
  and receives no elevated trust.
- `observe`: validate a supplied profile receipt and retain aggregate outcome
  counts, but do not change credits, reputation, routing or task delivery.
- `required`: refuse economic or reputation gain when the required receipt is
  missing or invalid. Task-result delivery remains independent of settlement.

`legacy` is the only production-authorized state. `observe` and `required` are
research/conformance terms until the receipt-return and settlement exchange is
specified, implemented across maintained clients, and approved through the gate
below. An advertised profile never proves that a receipt was co-signed.

## Preregistered enforcement gate

Changing the production default requires all of the following:

1. At least 90% of active heartbeating nodes advertise the profile for a fixed,
   continuous 14-day window with at least 48 successful observations and no gap
   above 12 hours.
2. At least two independently operated participants complete valid cross-operator
   receipts through the maintained exchange path.
3. A fixed content-free economic observation window contains modern attributed,
   debit-bearing receipts and no growth in forbidden attribution, ledger mismatch,
   spend mismatch or duplicate settlement.
4. PHP and Rust directories pass the same valid, missing, malformed, replay,
   same-operator, insufficient-balance and duplicate-settlement fixtures.
5. An isolated canary proves enablement, mixed-client failure behavior and
   rollback. Security, privacy, compatibility, economic and compliance reviews
   pass afterward.
6. A separate maintainer decision explicitly authorizes production enforcement.

The public adoption window measures only an anonymous capability claim. It cannot
satisfy items 2-6 and cannot authorize deployment or enforcement by itself.
