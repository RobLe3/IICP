# IICP live-directory deployment provenance

**Status:** Draft implementation profile  
**Version:** 0.1.0  
**Endpoint:** `GET /.well-known/iicp-deployment.json`

This profile lets an operator bind a running directory to a public release
without exposing deployment paths, hostnames, credentials, database details or
private configuration. A valid record proves that the directory signing key
signed the stated metadata. It does not prove that every production setting
matches a reference deployment.

## Record

The response MUST conform to
[`schemas/iicp-deployment-record-v1.json`](../../schemas/iicp-deployment-record-v1.json).
Container-specific fields MUST be `null` for a non-container deployment.

`source_commit` identifies the source revision used to build the artifact.
`build_digest` identifies the deployed runtime artifact. `protocol_min` and
`protocol_max` state the supported protocol-suite range; they do not replace
per-document version negotiation.

The endpoint MUST be available with `GET` and `HEAD`, MUST return
`application/json`, and MUST NOT require browser execution or authentication.
Normal read-rate and abuse controls still apply.

## Signature

The signer removes the top-level `signature` member, serializes the remaining
object as RFC 8785 JSON, and signs these bytes:

```text
ASCII("IICP-DEPLOYMENT-RECORD-V1") || 0x00 || canonical_unsigned_json
```

The signature uses Ed25519 and base64url without padding. The signing key MUST
be the key named by `root_key_id` and MUST be resolvable from the directory DID
document. `signature.purpose` MUST equal `iicp-deployment-record-v1`; signatures
created for events, tickets or other IICP objects MUST NOT be accepted.

Verifiers MUST reject malformed records, unknown purposes, key-ID mismatches,
invalid signatures and records that violate a locally configured freshness
policy. Key rotation does not invalidate a historical record when the verifier
has an authenticated historical key, but the current live endpoint MUST use a
currently authorized directory key.

## Publication procedure

Before publishing a record, an operator MUST:

1. verify the release tag, source revision and artifact digest against immutable
   public release assets;
2. generate the record from the release artifact rather than a mutable source
   checkout;
3. verify the completed record with an independent verifier;
4. retain the prior record and rollback metadata with the deployment evidence.

The conformance fixture
[`fixtures/iicp-deployment-record-v1.json`](../../fixtures/iicp-deployment-record-v1.json)
contains a valid record plus tamper, stale-policy, wrong-purpose and rotated-key
cases.
