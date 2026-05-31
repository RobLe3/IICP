# S.15 — IICP Identity Slot Protocol

**Version**: 0.1.0-draft
**Date**: 2026-05-26
**Status**: Draft
**Authority**: Protocol Steward
**Linked ADRs**: ADR-034 (this slot; Proposed), ADR-019 (declarative pricing), ADR-020 (reputation stub), ADR-018 (federation), ADR-024 (signed message envelope; pending), ADR-030 (operator identity & anti-Sybil)
**Tracking issues**: #150 (Identity Slot work package), #151 (this spec — D1)
**Bounded context**: BC-12 (Identity Context — see `project/ddd/BC-12-identity.md`)

---

## 1. Purpose

IICP carries cryptographic identity through a **slot** — a designated set of fields
in every relevant message type — rather than through a built-in identity system.

The protocol defines *where* identity goes, *how* it is signed, and *how* signatures
are canonicalised. The protocol does **NOT** define *which* identity schemes are
valid; that is delegated to implementation-supplied **verifiers** dispatched by
URI scheme.

This separation is deliberate. Identity schemes evolve faster than wire protocols.
By treating identity as an extension point, IICP can carry `did:web`, `did:key`,
`did:plc`, X.509 cert subjects, or future post-quantum schemes without a protocol
revision.

## 2. Slot Model

### 2.1 Slot Definition

The Identity Slot consists of two paired fields in every IICP message that carries
or asserts identity:

| Field | Type | Purpose |
|-------|------|---------|
| `identity` | string (URI, RFC 3986) | The identity URI being asserted by the message sender |
| `identity_signature` | string (hex) | Detached signature over the canonical message bytes |

Both fields are **OPTIONAL** at the protocol layer. Whether a specific message
type *requires* identity is determined by:

1. The message-type-specific spec (e.g. `iicp-federated-directory.md` §7.1 requires
   `did` in `POST /v1/replicas/register`)
2. The deployment's conformance level (CIP-None / CIP-Provider / CIP-Full)
3. Phase-gated protocol requirements (e.g. Phase 4+ may require all CALL messages
   to be identity-signed; Phase 1 does not)

### 2.2 Slot Is Not An Identity System

The protocol layer:
- **MUST NOT** enumerate valid `identity` URI schemes
- **MUST NOT** issue identity URIs
- **MUST NOT** maintain a registry of valid identities
- **MUST NOT** adjudicate disputes between identity claims

The protocol layer **DOES**:
- Define exactly where the slot fields live in each message
- Define the canonical bytes the signature covers
- Define the signature algorithm and encoding
- Define error codes for slot-related failures (IICP-IDSLOT-01..09)

## 3. Identity Field Placement

The slot appears in the following IICP message types. Other message types
(PONG, ACK, CLOSE) MAY carry the slot but are NOT REQUIRED to.

### 3.1 INIT (Node → Directory; `POST /v1/register`)

The slot fields appear at the **top level** of the request body:

```json
{
  "endpoint": "https://node.example.com",
  "region": "eu-central",
  "capabilities": [...],
  "limits": {...},
  "identity": "did:web:operator.example.com",
  "identity_signature": "<hex>"
}
```

When present, `identity` declares the operator identity registering this node.
ADR-030 (operator identity layer) requires this for participation in anti-Sybil
gates (diversity badges, regional pioneer status).

### 3.2 PING (Node → Directory; `POST /v1/heartbeat`)

The slot fields appear at the **top level**:

```json
{
  "load": 0.42,
  "active_jobs": 2,
  "available": true,
  "identity": "did:web:operator.example.com",
  "identity_signature": "<hex>"
}
```

If `identity` is present, the directory verifies it matches the identity recorded
at INIT for this `node_id`. Mismatch → IICP-IDSLOT-04 (identity drift).

### 3.3 CALL (Proxy → Adapter; `POST /v1/task`)

The slot fields appear at the **top level** alongside the task envelope:

```json
{
  "task_id": "uuid",
  "intent": "urn:iicp:intent:llm:chat:v1",
  "payload": {...},
  "cip": {...},
  "identity": "did:key:z6Mk...",
  "identity_signature": "<hex>"
}
```

When present, `identity` asserts the *client* identity for the call. This is
distinct from `proxy_token` (which authenticates the proxy itself to the
adapter) — `identity` is the upstream party the proxy is acting on behalf of.

### 3.4 RESPONSE (Adapter → Proxy)

The slot fields appear at the **top level**:

```json
{
  "task_id": "uuid",
  "status": "success",
  "result": {...},
  "identity": "did:web:node-operator.example.com",
  "identity_signature": "<hex>"
}
```

When present, `identity` asserts the node-operator identity that produced the
result. This is what makes credit settlement (CIPWorkerReceipt) cryptographically
attributable — see ADR-019.

### 3.5 DISCOVER Response (Directory → Proxy)

In replica directories (Phase 6), the slot fields appear in **response headers**,
not the body:

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-IICP-Replica-DID: did:web:replica.example.com
X-IICP-Replica-Sig: <hex>
X-IICP-Snapshot-Seq: 42891
```

`X-IICP-Replica-DID` is the `identity` slot value; `X-IICP-Replica-Sig` is the
`identity_signature` slot value. This is the **reference verifier** mapping for
`did:web` (see §8). The seed itself does NOT sign — TLS+DNS provides the trust
anchor — but replicas MUST sign per S.13 §6.5 / DIR-FED-20.

### 3.6 Event Log Entries (Genesis Seed → Replicas)

Event log entries in `GET /v1/events` use a per-event variant:

```json
{
  "event_id": "uuid",
  "event_type": "REGISTER",
  "seq": 42,
  "ts_ms": 1700000000000,
  "node_id": "...",
  "payload": {...},
  "signer_did": "did:web:iicp.network",
  "sig": "<hex>"
}
```

Here `signer_did` is the `identity` slot field and `sig` is the
`identity_signature` slot field, named for historical reasons (predates this
spec). Spec v0.2.0 will normalise the names; v0.1.0-draft retains compatibility.

### 3.7 REPLICA_REGISTER (Replica → Genesis Seed; `POST /v1/replicas/register`)

Slot fields at the **top level**:

```json
{
  "did": "did:web:replica.example.com",
  "endpoint": "https://replica.example.com",
  "identity_signature": "<hex>"
}
```

Here `did` is the `identity` slot field (named for the §7.1 wire-format
compatibility with S.13 v0.2.0). The directory MUST resolve the `did` to a DID
document, extract the Ed25519 verification method, and verify
`identity_signature` over the canonical request bytes before issuing a
`replica_token` (IICP-IDSLOT-02 on verify failure).

## 4. Identity URI Format

The `identity` field is a URI conforming to RFC 3986. Verifier dispatch uses
the URI **scheme** (the substring before the first `:`):

- `did:web:...` → dispatch to the W3C DID v1 + DID Method `web` verifier
- `did:key:z6Mk...` → dispatch to the W3C DID v1 + DID Method `key` verifier
- `did:plc:...` → dispatch to AT Protocol DID-PLC verifier
- Future schemes → defined by their respective specs

The protocol layer MUST treat unrecognised schemes as a **verifier dispatch
failure** (IICP-IDSLOT-05). It MUST NOT silently accept or reject the message
based on the scheme alone.

URIs MUST be ≤ 256 characters. Implementations MAY enforce shorter limits per
their verifier's requirements.

## 5. Identity Signature Field

`identity_signature` is a hex-encoded detached signature, length determined by
the signature algorithm:

| Algorithm | Hex length | Bytes |
|-----------|-----------|-------|
| Ed25519 (default) | 128 | 64 |
| Secp256k1 | 128 | 64 |
| PQ schemes | varies | varies (≥ 256 hex) |

The signature algorithm is **NOT carried in the protocol message**. It is
determined by the verifier dispatched from the URI scheme. For `did:web` and
`did:key`, the verifier reads the `publicKeyJwk.crv` field of the resolved
verification method to determine the algorithm.

## 6. Canonical Serialization

Signatures cover the **canonical serialization** of the message **excluding** the
`identity_signature` field (and excluding the `Authorization` header for HTTP
transports).

### 6.1 JSON Canonicalisation (Default)

For JSON-bodied messages, canonical serialization MUST follow **RFC 8785 (JSON
Canonicalization Scheme — JCS)**. Implementations MAY use simpler subset rules
where the message structure is constrained (see §6.2).

### 6.2 Simplified Canonical Form (S.13 §3.4 Compatibility)

For protocol-internal messages where field types are constrained (no floats with
ambiguous representations, no Unicode normalisation surprises), implementations
MAY use the simpler canonical form already in use by `NodeEventLogger`:

```
canonical_input = SHA256_bin(
  field_1 + ":" + field_2 + ":" + ... + ":" + SHA256_hex(canonical_json(payload))
)
```

This is the form used by:
- Event log signing (S.13 §3.4)
- Replica response signing (S.13 §6.5)
- This form is **NOT** suitable for messages containing user-supplied content
  with arbitrary Unicode or floats — those MUST use full RFC 8785.

### 6.3 HTTP Transport Specifics

When the slot fields are carried in HTTP headers (as in §3.5 replica discover
responses), the canonical input is:

```
SHA256_bin(METHOD + ":" + PATH + ":" + canonical_query + ":" + SNAPSHOT_SEQ + ":" + SHA256_hex(BODY_BYTES))
```

per S.13 §6.5. The `identity_signature` (`X-IICP-Replica-Sig`) is computed over
this canonical input.

## 7. Verifier Dispatch

A receiver of a message bearing the slot fields MUST:

1. Parse `identity` as a URI; extract the scheme
2. Look up a registered verifier for that scheme; if none → IICP-IDSLOT-05
3. Hand `identity`, `identity_signature`, and the canonical input to the verifier
4. The verifier returns `{ verified: bool, public_key_fingerprint: string }`
5. On `verified: false` → IICP-IDSLOT-02 (signature invalid); reject the message
6. On `verified: true` → message is identity-asserted; downstream logic MAY
   bind decisions to `public_key_fingerprint`

Verifiers MUST be deterministic — the same `(identity, signature, canonical_input)`
triple MUST always return the same verdict. Verifiers SHOULD cache resolved
identity-to-key mappings (see ADR-030 for operator-identity caching).

## 8. Reference Verifiers

Phase 6 deployed `did:web` verification at two surfaces:

### 8.1 `did:web` for Replicas (S.13 §6.5)

The replica's `did:web:<domain>` URI resolves to `https://<domain>/.well-known/did.json`.
The verifier:
1. HTTPS GET to that URL
2. Parses the DID document; finds the first `verificationMethod` with `publicKeyJwk.kty = "OKP"` and `publicKeyJwk.crv = "Ed25519"`
3. Base64url-decodes `publicKeyJwk.x` → 32-byte raw Ed25519 public key
4. Calls `sodium_crypto_sign_verify_detached(sig, canonical_input, pub_key)`

Implementation: `directory/app/Services/SeedDidResolver.php` (PHP) +
`proxy/src/proxy/clients/did_resolver.py` (Python).

### 8.2 `did:web` for Event Log Signers (S.13 §3.4)

Same verifier as §8.1; the `signer_did` field of each event log entry is the
identity URI, and `sig` is the identity signature over the canonical input
defined in §6.2.

### 8.3 Future Verifiers

- `did:key` — pure self-contained URI; verifier extracts key from URI fragment;
  no network fetch. Recommended for Phase 4 client identity (CALL messages).
- `did:plc` — AT Protocol identifier; resolved via `https://plc.directory/<did>`.
- `urn:iicp:operator:<hex>` — internal operator identity per ADR-030; resolved
  via the genesis seed's operator registry.

Each verifier is specified in a separate document under `spec/verifiers/`.
The Identity Slot spec itself does not specify any.

## 9. Conformance Test IDs

Registered in `spec/conformance-test-suite.md §11.10` (to be added when this
spec graduates from Draft):

| Test ID | Requirement | Level |
|---------|-------------|-------|
| `IDENTITY-01` | A message with `identity` field MUST include `identity_signature` (or both absent) | MUST |
| `IDENTITY-02` | Verifier rejects a message whose `identity_signature` does not verify against `identity` | MUST |
| `IDENTITY-03` | Verifier dispatch on unrecognised URI scheme returns IICP-IDSLOT-05 | MUST |
| `IDENTITY-04` | URI longer than 256 chars is rejected (IICP-IDSLOT-06) | MUST |
| `IDENTITY-05` | `identity_signature` length matches algorithm (128 hex for Ed25519) | MUST |
| `IDENTITY-06` | Canonical input excludes the `identity_signature` field | MUST |
| `IDENTITY-07` | RFC 8785 canonicalisation produces stable bytes across re-serialisation | MUST |
| `IDENTITY-08` | `did:web` reference verifier extracts only Ed25519 OKP keys (skips other curves) | MUST |
| `IDENTITY-09` | Verifier dispatch is deterministic — same inputs always return same verdict | MUST |

## 10. Error Codes

Reserved in the `IICP-IDSLOT-NN` namespace:

| Code | Meaning |
|------|---------|
| `IICP-IDSLOT-01` | identity field missing when required by message-type spec |
| `IICP-IDSLOT-02` | identity_signature verification failed |
| `IICP-IDSLOT-03` | identity_signature length does not match expected algorithm |
| `IICP-IDSLOT-04` | identity drift — claimed identity differs from previously-recorded identity for this principal |
| `IICP-IDSLOT-05` | unrecognised URI scheme — no verifier dispatched |
| `IICP-IDSLOT-06` | identity URI exceeds 256-char limit |
| `IICP-IDSLOT-07` | DID document fetch failed (network error or 4xx/5xx) |
| `IICP-IDSLOT-08` | DID document missing required verification method |
| `IICP-IDSLOT-09` | canonical serialization produced non-deterministic bytes (JCS violation) |

## 11. Threat Model Summary

See `project/security/THREAT_MODEL.md §TC-10` for federation-specific threats.
Slot-specific threats:

- **Signature replay across messages**: mitigated by including message-specific
  fields (`task_id`, `seq`, `snapshot_seq`) in the canonical input. Replays
  outside the original message context fail verification.
- **DID document tampering**: see TC-10e (HTTPS + registry pin-on-first-use is
  the partial mitigation; full mitigation needs DNSSEC-pinned trust).
- **Verifier confusion**: a message claiming `identity: "did:web:..."` but
  signed by a `did:key` key fails verification because the dispatcher uses
  scheme to select the verifier; mismatched key/scheme always fails.
- **Algorithm downgrade**: the verifier reads the algorithm from the DID
  document, not from the message. Attackers cannot downgrade by claiming a
  weaker algorithm in the message itself.

## 12. Backwards Compatibility

Implementations conforming to S.5 v1.2.x (Phase 1) MUST continue to accept
messages without slot fields. The slot is **additive**: presence of the slot
adds verification; absence is allowed where the message-type spec permits.

Specific compatibility notes:
- **Event log entries** already use `signer_did` and `sig` (S.13 §3.4); this
  spec adopts those names retroactively as the slot fields for that message
  type. v0.2.0 of this spec MAY introduce canonical names with `signer_did →
  identity` aliasing.
- **Replica response headers** already use `X-IICP-Replica-DID` and
  `X-IICP-Replica-Sig` (S.13 §6.5); ditto.
- **No existing v1.2.x-compliant deployment is broken** by this spec —
  conformance is asserted only when the slot fields are present.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.0-draft | 2026-05-26 | Initial draft per Phase 5 charter #150–#154 / D1 (issue #151). Renumbered from original-plan ADR-021 to ADR-034 (ADR-021 was repurposed for multi-model node registration in commit `f213553`, 2026-05-17). |
