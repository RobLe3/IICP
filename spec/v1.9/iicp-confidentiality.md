# IICP Confidentiality Extension (IICP-CX)

**Spec ID**: S.16
**Version**: 0.3.2-draft
**Date**: 2026-07-10
**Status**: Draft — **Tier 1 mandatory-posture (#360, privacy-first): encryption is on by default,
no opt-out.** CX-Consumer encrypt is implemented in all three SDKs + CX-Provider decrypt/advertise in
the adapter (round-trip verified); both default ON; rollout is migration-sequenced (#532) to fail-closed.
Forward-secrecy claim corrected (#539 — Tier 1 has no FS vs node-key compromise; Tier 2 target).
Previously — **Tier 1 partially implemented** (CX-Provider decrypt path + directory cx_public_key
storage live). Reconciled after the 2026-06-21 key-alias hotfix: the CX key is `cx_public_key` at
REGISTER/storage and `cx_public_key` is the sole discover/NODELIST CX field. The deprecated CX
`public_key` output alias was retired after the SDK adoption window (§3.2); shipped error codes are
`IICP-E050` (collapsed decrypt/no-support) + `IICP-E049` (cx_public_key update auth) — see §6
implementation status. Full E060–E064 model is the Tier-2 target. (#360)
**Tracking**: #360 (E2E payload confidentiality), #361 (privacy threat model)
**Foundation**: `project/SECURITY.md §Privacy Adversary Model` (PA-1..PA-4),
`spec/iicp-core.md §8 Security` (SEC-PRIV-04/05/09)

---

## 1. Purpose

IICP-CX defines **mandatory** End-to-End Confidentiality for IICP task payloads (privacy-first,
#360). In Tier 1, request task payloads are encrypted between the client and the
inference-executing node such that relay nodes, the directory, and any intermediate infrastructure
receive only ciphertext for the request — they cannot read prompt content or task context.
Tier 1 responses are **not** E2E encrypted; bidirectional response encryption is a Tier 2 target (§5a.3).

**Privacy goals (first-class, not an optional extension):**
- A conformant CX-Consumer **MUST** encrypt task payloads to any node advertising a `cx_public_key`.
- A node serving inference **MUST** be CX-capable (advertise a key + decrypt).
- **No opt-out.** Encryption is not a user toggle; there is no plaintext path for an adversary or
  operator to coerce a downgrade to. Once the mesh is key-ready, a client with no verified recipient
  key **fails closed** (refuses) rather than sending plaintext.
- **The honest boundary:** the executing node necessarily decrypts to run the model — IICP-CX
  protects the payload from the directory, relays, and the network, **not from the node you chose**.
  For data no party should ever see, run the model locally (on-device). Executor-blind remote
  inference (TEE attestation) and metadata privacy are separate, tracked work (P2 / #361).

This specification directly addresses Privacy Adversary classes PA-2 and PA-3 from
`project/SECURITY.md`:
- **PA-2** (relay operator coercion): relay sees ciphertext only
- **PA-3** (directory operator coercion): directory never sees task payloads (preserved from ADR-001/003)

IICP-CX properties:
- **On by default, no opt-out**: clients always encrypt to key-advertising nodes; nodes advertise a key by default.
- **Migration-sequenced** (#532): during rollout, a not-yet-CX-capable node receives a loud plaintext
  warning; this transitional path is removed (fail-closed) once the mesh carries keys.
- **Relay-transparent**: the relay forwarding protocol does not need modification.

---

## 2. Conformance levels

| Level | Description |
|-------|-------------|
| **CX-Consumer** | Client implementation that can generate ephemeral key pairs, discover node public keys, and encrypt task payloads |
| **CX-Provider** | Node implementation that advertises a public key, maintains the corresponding private key, and can decrypt CX-encrypted payloads |
| **CX-Relay** | Relay implementation that can forward CX-encrypted task envelopes without modification (opaque forwarding) |

A conformant CX-Relay MUST NOT attempt to decrypt or inspect the `encrypted_body` field.
This is the primary security property of the relay confidentiality model.

---

## 3. Node Key Advertisement

### 3.1 Registration and NODELIST

Nodes that support CX-Provider MUST include a `cx_public_key` object in their REGISTER
payload and HEARTBEAT updates:

```json
"cx_public_key": {
  "algorithm": "X25519",
  "encoding": "base64url",
  "key": "<32-byte X25519 public key, base64url-encoded, no padding>",
  "key_id": "<sha256 of DER-encoded key, first 8 hex bytes>",
  "not_after": "<ISO 8601 UTC expiry — SHOULD be ≤ 90 days from registration>",
  "hybrid_pq": null
}
```

`hybrid_pq` is reserved for Kyber-768 post-quantum KEM hybrid (Phase 4+); set to `null` in
Tier 1 implementations.

### 3.2 Discovery response

The `/v1/discover` (and NODELIST) response exposes the registered key under the canonical field name
**`cx_public_key`** (`null` when the node advertised no CX key). This keeps the field name identical
on the way **in** (REGISTER/HEARTBEAT) and the way **out** (discover/NODELIST), and avoids confusing
the CX X25519 key with other protocol keys such as DID, gossip or directory-signing public keys.

The 2026-06-21 compatibility window permitted the directory to duplicate this object under
`public_key`. That output alias is retired by #557 after maintained SDKs adopted canonical
`cx_public_key`. Consumers MAY retain read fallback for one further release when interoperating with
older directories, but new directories MUST emit only `cx_public_key`. Missing or malformed key
material remains equivalent to no CX key and MUST fail closed before task submission. This cutover
does not affect node-detail or peer-exchange `public_key`, which is a separate Ed25519 gossip key.

```json
{
  "node_id": "...",
  "endpoint": "...",
  "cx_public_key": { ... }, // the node's registered cx_public_key object, or null
  "capabilities": [ ... ]
}
```

Nodes without a `cx_public_key` MUST NOT receive CX-encrypted payloads.

### 3.3 Conformance requirements

| ID | MUST/SHOULD | Requirement |
|----|-------------|-------------|
| CX-NODE-01 | MUST | CX-Provider nodes MUST rotate their key pair at least every 90 days |
| CX-NODE-02 | MUST | CX-Provider nodes MUST NOT reuse key pairs across node_id registrations |
| CX-NODE-03 | SHOULD | CX-Provider nodes SHOULD use ephemeral session sub-keys derived from the long-term key for individual task decryption |

---

## 4. Confidentiality Envelope

When a CX-Consumer sends a task to a CX-Provider, the IICP `payload` field is replaced
with a confidentiality envelope:

### 4.1 HTTP transport

The task request body wraps the normal `POST /v1/task` payload:

```json
{
  "task_id": "...",
  "intent": "urn:iicp:intent:llm:chat:v1",
  "iicp_conf": {
    "version": 1,
    "recipient_key_id": "<8-hex-byte key_id from the node's cx_public_key in discover (§3.2)>",
    "kem_ciphertext": "<base64url — X25519 ephemeral public key used in HKDF>",
    "encrypted_body": "<base64url — AES-256-GCM ciphertext of the normal payload JSON>",
    "nonce": "<base64url — 12-byte random nonce>",
    "aad": "<base64url — task_id + intent concatenated, UTF-8>",
    "plaintext_size": 1234
  }
}
```

The `payload` field MUST be absent when `iicp_conf` is present.

### 4.2 IICP TCP transport

For native IICP TCP (port 9484), a new message flag `0x04` (`CONF_ENCRYPTED`) is defined.
When this flag is set on a CALL message, the CBOR `payload` field contains the
confidentiality envelope map:

```
{
  1: 1,                    ; version
  2: h'<key_id bytes>',   ; recipient_key_id (8 bytes)
  3: h'<kem_ct>',         ; kem_ciphertext (32 bytes, ephemeral X25519 pubkey)
  4: h'<encrypted_body>', ; encrypted payload
  5: h'<nonce>',          ; 12-byte nonce
  6: h'<aad>',            ; task_id + intent
  7: 1234                  ; plaintext_size
}
```

---

## 5. Key Exchange Protocol (Tier 1 — X25519 + AES-256-GCM)

**Algorithm**: X25519-HKDF-SHA256 + AES-256-GCM (IETF HPKE, RFC 9180 compatible)

**Client-side (CX-Consumer) steps**:

1. Retrieve node's X25519 public key from `/v1/discover` response
2. Generate ephemeral X25519 key pair (client_ephem_priv, client_ephem_pub)
3. Perform ECDH: `shared_secret = X25519(client_ephem_priv, node_pub_key)`
4. Derive encryption key via HKDF-SHA256:
   ```
   info = "IICP-CX-v1" || task_id || intent
   key_material = HKDF(ikm=shared_secret, salt=nonce, info=info, length=32)
   ```
5. Encrypt payload:
   ```
   aad = UTF8(task_id + "|" + intent)
   (ciphertext, tag) = AES-256-GCM(key=key_material, nonce=nonce, plaintext=payload_json, aad=aad)
   encrypted_body = ciphertext + tag
   ```
6. `kem_ciphertext` = base64url(client_ephem_pub)

**Node-side (CX-Provider) decryption steps**:

1. Receive task with `iicp_conf` envelope
2. Look up private key matching `recipient_key_id`
3. Recover `client_ephem_pub` from `kem_ciphertext`
4. Perform ECDH: `shared_secret = X25519(node_priv_key, client_ephem_pub)`
5. Derive decryption key using the same HKDF derivation as step 4 above
6. Decrypt: `plaintext = AES-256-GCM-Decrypt(key, nonce, encrypted_body, aad=UTF8(task_id+"|"+intent))`
7. Process decrypted payload normally

**Security properties**:
- Ciphertext binding: AAD ties the ciphertext to the specific task and intent — prevents ciphertext from being replayed against a different task.
- Relay opacity: relay only sees `kem_ciphertext` (client ephemeral pubkey) and `encrypted_body` — no plaintext.
- **Forward secrecy — Tier 1 is LIMITED (correction, #539).** The client ephemeral key is single-use,
  so compromising a *client* does not expose other sessions. However, the **node key is static
  (long-term)** and the client ephemeral *public* key travels in `kem_ciphertext` in the clear —
  therefore compromise of a node's long-term private key **DOES** allow decryption of past sessions
  recorded to that node. **Tier 1 does NOT provide forward secrecy against node-key compromise.**
  Mitigation today: mandatory key rotation (CX-NODE-01, ≤90 days) bounds the exposure window. Full
  forward secrecy (ephemeral-ephemeral via published node prekeys) is the **Tier 2** target.
- **Request-only (Tier 1).** Only the request payload is encrypted; the response is returned over the
  transport (TLS), not E2E. Bidirectional (response) encryption is a **Tier 2** target (§9 Q2).

---

## 5a. Tier 2 — Authenticity, forward secrecy, bidirectional (normative design)

Tier 2 closes the three Tier-1 gaps without changing the one-shot request model. It is additive:
a Tier-2 CX-Consumer negotiates Tier-2 when the node advertises the capabilities below, else falls
back to Tier-1. All Tier-2 elements build on the Tier-1 AEAD construction (§5).

### 5a.1 Operator-signed keys + key transparency (authenticity)
The directory advertises a node's `cx_public_key`; on its own that means a client trusts whatever
the directory reports. Tier 2 removes that trust dependency:

- The node **operator** signs the binding `op_sig = Sign_opIdentity( "IICP-CX-KEYBIND-v1" || node_id || key_id || cx_public_key || not_after )` with the **operator identity key** (the same Ed25519 identity used for operator delegation). `op_sig` + the operator identity public key (or its fingerprint) are advertised alongside `cx_public_key` and included in REGISTER.
- The directory **anchors** the binding in its signed, append-only event log as a `CX_KEY_BIND` event (so rotation/revocation is publicly auditable) and serves `op_sig` in discover.
- A Tier-2 CX-Consumer **MUST** verify `op_sig` under the operator identity key **before encrypting**; an absent/invalid signature → reject with **`IICP-E065`** (do not fall back to an unverified key). The client **SHOULD** pin the operator→key binding (TOFU) and warn on unexpected change.
- **Security note:** operator-identity signing makes the *directory* unable to substitute a key it controls (it cannot forge the operator's signature). Full equivocation detection (a directory presenting different logs to different clients) additionally requires **independent log monitors**, which depend on directory **federation** (Phase 6); until then, key transparency provides auditability + pinning, not split-view detection.

### 5a.2 Forward secrecy via node prekeys
To remove Tier-1's dependence on the node's static key, the node publishes a rotating set of
**one-time ephemeral X25519 prekeys**, each signed by the node's long-term CX key:
`prekey_sig = Sign_cxKey( "IICP-CX-PREKEY-v1" || prekey_id || prekey_pub || not_after )`. Prekeys are
refreshed via heartbeat; the directory serves the current set (with `prekey_id`s).

- The CX-Consumer selects an **unused** prekey and performs **ephemeral-ephemeral** ECDH:
  `shared_secret = X25519(client_ephem_priv, node_prekey_pub)`; the envelope carries the chosen
  `prekey_id`. Because both sides of the agreement are ephemeral, compromise of the node's long-term
  key does **not** decrypt past sessions → forward secrecy.
- **Depletion:** if no unused prekey is available, the consumer MAY fall back to the static-key Tier-1
  agreement and MUST mark the session `fs=false` (caller-visible) — never silently. Nodes SHOULD
  publish enough prekeys (and refresh promptly) that depletion is rare.
- The node verifies `prekey_id` maps to a prekey it still holds the private half for; expired/unknown
  → `IICP-E060`.

### 5a.3 Bidirectional (response) encryption
The node encrypts its response under a key derived from the **same established shared secret**, with a
distinct label so request and response keys differ:
`resp_key = HKDF(ikm=shared_secret, salt=resp_nonce, info="IICP-CX-RESP-v1" || task_id, length=32)`.
The client already holds `shared_secret` and decrypts. The response envelope mirrors `iicp_conf`.

Implementations MAY deploy this element before the complete Tier-2 bundle by advertising
`cx_public_key.features: ["response_encryption_v1"]`. A consumer that selects such a node sends
`cx_response_encryption: "required"` in the task envelope. The provider then MUST return
`iicp_conf_resp` and omit the plaintext result. A consumer MUST reject a plaintext response after
that negotiation. This granular feature does **not** authorize advertising `cx_tier: 2`; that field
remains reserved for implementations that also satisfy §5a.1, §5a.2 and all applicable §5a.3
conformance requirements. Nodes and consumers that do not advertise/understand the feature retain
the Tier-1 response behavior.

- **Streaming (SSE):** each streamed chunk is an independent AEAD frame; the per-frame AAD includes a
  **monotonically increasing sequence number** (`task_id || "|" || seq`) so dropped, reordered, or
  replayed frames are detected. The final frame sets an `end` marker; the client MUST verify
  sequence continuity and the terminal marker.

### 5a.4 Negotiation & conformance
A node advertises Tier-2 support via a `cx_tier: 2` field (and the prekey set) in discover. Tier-2
consumers prefer it; absent it, Tier-1 applies. Tier 2 makes the granular `IICP-E060..E065` error
model (§6) fully emittable. New conformance IDs: **CX-T2-01** (operator-sig verified before encrypt),
**CX-T2-02** (prekey ephemeral-ephemeral FS; `fs=false` surfaced on depletion), **CX-T2-03**
(response + streaming frames authenticated and sequence-checked).

`response_encryption_v1` is therefore an additive, independently negotiable confidentiality
feature and not a synonym for `cx_tier: 2`. Unknown `cx_public_key.features` entries MUST be ignored.

---

## 6. Error Handling

| Code | Condition | HTTP status |
|------|-----------|-------------|
| `IICP-E060` | `recipient_key_id` / `prekey_id` not found for this node | 422 |
| `IICP-E061` | `iicp_conf.version` not supported | 422 |
| `IICP-E062` | Decryption failed (wrong key, tampered ciphertext) | 400 |
| `IICP-E063` | CX-Provider capability advertised but key has expired | 422 |
| `IICP-E065` | Operator key-binding signature missing or invalid (Tier-2, client-side; client refuses to encrypt to an unverified key) | n/a (client) |

Nodes that do not support CX MUST return `IICP-E064` when they receive a request
with `iicp_conf` present (target Tier-2 error model). Current privacy-first SDKs
MUST NOT automatically downgrade to plaintext after any CX error. They skip or
refuse keyless nodes by default; plaintext is a transitional debugging escape
hatch only when an implementation exposes an explicit opt-in override such as
`IICP_CX_ALLOW_PLAINTEXT=1`.

**Implementation status (Tier-1, as shipped — normative for current conformance).** The full
`IICP-E060..E064` set above is the *target* error model. The shipped Tier-1 implementation is coarser:
- the CX-Provider adapter returns **`IICP-E050`** (422) for **both** decryption failure (target E062)
  **and** a request bearing `iicp_conf` to a node with `cx_enabled = false` (target E064) —
  i.e. E050 currently collapses E062 + E064 (`adapter/src/adapter/handlers/task.py`);
- the directory returns **`IICP-E049`** (422) when a `cx_public_key` update is presented without a valid
  `current_node_token` (register-time key-update auth — a code with no equivalent in the target set).

The granular `IICP-E060` (unknown key_id), `IICP-E061` (version), and `IICP-E063` (expired key) are
**not yet emitted**. Until Tier-2, a conformant CX-Provider MUST emit `IICP-E050` on the collapsed
decrypt/no-support condition; CX-04/CX-05 (§8) reference the target codes and are Tier-2 gated.

---

## 7. Session Negotiation (optional)

Clients MAY include an `X-IICP-Require-E2E: 1` HTTP header or equivalent IICP TCP header
flag to require E2E encryption. The privacy-first client posture treats this as
the default for remote mesh dispatch. If the node does not support CX, it MUST
return `IICP-E064` in the target Tier-2 model (or `IICP-E050` in the current
collapsed Tier-1 provider implementation) rather than accepting the unencrypted
payload. This prevents silent downgrade.

---

## 8. Conformance test IDs

| ID | Level | Description |
|----|-------|-------------|
| CX-01 | MUST | CX-Provider advertises its CX key as `cx_public_key` at REGISTER and in NODELIST/discover (§3.2); directory output MUST NOT overload `public_key` for CX material |
| CX-02 | MUST | CX-Provider decrypts CX envelope and returns correct response |
| CX-03 | MUST | CX-Relay forwards CX-encrypted task envelope unmodified |
| CX-04 | MUST | CX-Provider returns IICP-E060 for unknown key_id |
| CX-05 | MUST | CX-Provider returns IICP-E062 for tampered ciphertext (AES-GCM tag failure) |
| CX-06 | SHOULD | CX-Consumer rotates ephemeral key on every task |
| CX-07 | SHOULD | CX-Provider rotates long-term key every 90 days |

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.3.2-draft | 2026-07-10 | #557 retires the deprecated CX `public_key` directory-output alias after the compatibility window. Canonical `cx_public_key` is now the sole CX discovery/dispatch field; consumer read fallback may remain for one further release. |
| 0.3.1-draft | 2026-06-28 | §6–§7 remove the stale automatic plaintext fallback wording. Current SDK posture is fail-closed/keyless-skip by default, with plaintext only via an explicit transitional debug override; E060–E064 remain the Tier-2 target while shipped Tier-1 providers collapse errors to E050. |
| 0.3.0-draft | 2026-06-13 | Tier-1 privacy-first confidentiality draft with canonical `cx_public_key`, static X25519 request encryption, fail-closed migration posture, and Tier-2 targets for forward secrecy, response encryption and granular errors. |

---

## 9. Open Questions

1. **Key rotation continuity**: How should clients cache node public keys to avoid a round-trip to `/v1/discover` on every task? Suggest 5-minute TTL with background refresh.
2. **Response encryption**: Should the node also encrypt its response back to the client? (Phase 2 of this spec.) In Tier 1, only the request payload is encrypted.
3. **Multi-hop CIP**: In CIP fan-out (#360 follow-up), the originating client encrypts to each CIP sub-node's key individually. The CIP orchestrator sees only the intent routing, not the payloads. Spec coordination needed with `spec/iicp-cooperative-inference.md`.
4. **Relay worker decrypt**: A relay worker receiving a RELAY_BIND connection on behalf of a CGNAT node — should the relay decrypt on behalf of the node? This would require the node to share its decryption key with the relay, which breaks PA-2. Preferred: relay passes ciphertext through unmodified; CGNAT node decrypts locally via its relay connection.
