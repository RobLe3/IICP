# Phase 5 Implementation Proposal — Response Hash Commitment

**Research track**: W-031 / GitHub issue #301  
**Date**: 2026-05-22  
**Status**: Proposed — pending Protocol Steward review  
**Scope**: Spec change to `spec/iicp-cooperative-inference.md` §10.3 and implementation changes across adapter, proxy, and directory

---

## 1. Spec Change: `spec/iicp-cooperative-inference.md` §10.3

### 1.1 Current Canonical Message (§10.3)

```
{task_id}:{tokens_used}:{cip_parent_task_id}:{cip_session_key}:{nonce}
```

### 1.2 Proposed Canonical Message

```
{task_id}:{tokens_used}:{cip_parent_task_id}:{cip_session_key}:{nonce}:{response_hash}
```

Where `response_hash` is the SHA-256 hex digest of the response body bytes, as defined below.

### 1.3 New Field Definition

**Add to §10.3** after the existing field table:

---

**`response_hash`**: `string` (SHA-256 hex, 64 lowercase hex characters)

The SHA-256 digest of the exact response body bytes delivered by the worker to the coordinator. Used to cryptographically bind the credit receipt to the specific response content.

**Computation rules (normative)**:

1. The worker MUST compute `response_hash = sha256(response_body_bytes).hex()` where `response_body_bytes` is the raw bytes of the response body AFTER any Content-Encoding is stripped (i.e., the decompressed, decoded bytes).
2. For JSON responses: hash the raw UTF-8-encoded JSON string as returned by the inference backend. DO NOT normalize keys, whitespace, or field order before hashing.
3. For streaming SSE responses: the worker MUST accumulate all SSE chunk data fields into a single concatenated byte sequence `body = b"".join(chunk.data for chunk in events)`, then hash the accumulated sequence. The `response_hash` MUST be placed in the final SSE event (see §10.3.1 below).
4. For empty responses (e.g., error cases where no content body is present): the worker MUST use `response_hash = "e3b0c44298fc1c149afbf4c8996fb924" + "27ae41e4649b934ca495991b7852b855"` (SHA-256 of empty byte string).
5. The worker MUST NOT include any HTTP framing bytes (headers, chunk-length prefixes, trailers) in the hash input. Only the application-layer body content is hashed.

**Phase 5 conformance requirement**:

- In Phase 5: `response_hash` is REQUIRED in the `CIPWorkerReceipt` for all CIP worker sub-tasks. A coordinator MUST NOT submit a credit award for a receipt missing `response_hash`. A coordinator MUST verify `sha256(received_body_bytes) == receipt.response_hash` before submitting the credit award and before returning the response to the client. Mismatch MUST result in receipt rejection (coordinator discards the response and marks the worker as having violated the integrity contract — see §10.3.2).
- The directory MUST include `response_hash` in the canonical message reconstruction when verifying receipts. A receipt missing `response_hash` MUST be rejected with `IICP-E027` (422 Unprocessable Entity) with message `"CIPWorkerReceipt missing response_hash"`.

---

### 1.4 New Section 10.3.1 — Streaming Response Hash

**Add new subsection §10.3.1** to spec:

---

**§10.3.1 Streaming Response Hash (SSE)**

When the adapter returns an SSE stream (`Content-Type: text/event-stream`), the response body cannot be hashed at response initiation time. The worker MUST follow this procedure:

1. Buffer all SSE events internally as inference proceeds.
2. Upon completion of inference (the final token has been generated), compute `response_hash = sha256(accumulated_body_bytes).hex()`.
3. Emit all buffered SSE data events to the coordinator.
4. Emit a final SSE event of the form:
   ```
   event: cip_receipt
   data: {"response_hash": "<64-char hex>", "signature": "<receipt.signature>", "nonce": "<nonce>"}
   
   ```
5. The coordinator MUST receive and parse the `cip_receipt` event. If the event is absent or malformed, the coordinator MUST treat the response as lacking a valid receipt and MUST NOT submit a credit award.
6. The coordinator MUST verify `sha256(accumulated_received_bytes) == cip_receipt.response_hash` where `accumulated_received_bytes` is the concatenation of all received SSE data payloads excluding the `cip_receipt` event itself.

**Note on buffering latency**: Because the worker buffers internally before emitting, streaming response latency to the coordinator is equal to non-streaming response latency (inference must complete before emission begins). In Phase 5, IICP does not offer true streaming integrity guarantees (chunk-by-chunk hash verification). Phase 6+ may introduce Merkle-tree-based streaming integrity (see `research/cryptographic-trustworthiness/04-phase6-plus-roadmap.md`).

---

### 1.5 New Section 10.3.2 — Misbehavior Flagging

**Add new subsection §10.3.2**:

---

**§10.3.2 Response Hash Mismatch — Coordinator Protocol**

When a coordinator detects `sha256(received_body) != receipt.response_hash`:

1. The coordinator MUST NOT submit a credit award for this receipt.
2. The coordinator MUST NOT return the received response body to the end client. The coordinator MUST fall back to local execution or return `IICP-E024` (all workers failed) if no local fallback is available.
3. The coordinator SHOULD log the mismatch event with the worker's `node_id`, `task_id`, and the two differing hashes for auditability.
4. The coordinator MAY submit a misbehavior report to the directory (endpoint TBD in Phase 5.1) to trigger reputation penalty application.

---

### 1.6 New HTTP Header (Optional in Phase 5, MUST in Phase 6)

**Add to §10.3:**

---

**`X-IICP-Response-Hash` header**

Workers SHOULD include the response hash as an HTTP response header for non-streaming responses, enabling early verification before the body is fully received:

```
X-IICP-Response-Hash: <64-char lowercase SHA-256 hex>
```

- In Phase 5: OPTIONAL. Coordinators MAY use this header for early validation. If present and the final body hash does not match, the coordinator MUST reject the receipt as per §10.3.2.
- In Phase 6: REQUIRED for non-streaming CIP worker responses. Absence MUST result in a warning-level audit log entry and MAY trigger a probation status update.

The header value MUST match `receipt.response_hash`. If the values differ, the coordinator MUST treat the response as if the hash was absent and apply §10.3.2 protocol.

---

## 2. Implementation Changes Required

### 2.1 `adapter/src/adapter/services/cip_receipt.py`

**Change 1: Add `response_hash` parameter to `_canonical_message()`**

Current:
```python
def _canonical_message(
    task_id: str,
    tokens_used: int,
    parent_task_id: str | None,
    session_key: str | None,
    nonce: str,
) -> bytes:
    return (
        f"{task_id}:{tokens_used}:{parent_task_id or ''}:{session_key or ''}:{nonce}"
    ).encode()
```

Proposed:
```python
def _canonical_message(
    task_id: str,
    tokens_used: int,
    parent_task_id: str | None,
    session_key: str | None,
    nonce: str,
    response_hash: str,
) -> bytes:
    return (
        f"{task_id}:{tokens_used}:{parent_task_id or ''}:{session_key or ''}:{nonce}:{response_hash}"
    ).encode()
```

**Change 2: Add `response_body` parameter to `build_worker_receipt()` and compute the hash internally**

Current signature:
```python
def build_worker_receipt(
    task_id: str,
    tokens_used: int,
    node_hmac_key: str,
    *,
    worker_node_id: str | None = None,
    cip_parent_task_id: str | None = None,
    cip_session_key: str | None = None,
) -> CIPWorkerReceipt:
```

Proposed signature:
```python
import hashlib as _hashlib

def compute_response_hash(response_body: bytes | str) -> str:
    """Compute SHA-256 hex digest of response body bytes (TC-9c integrity).

    Accepts bytes or str. If str, encodes to UTF-8 before hashing.
    Strips no framing. Caller is responsible for decompressing Content-Encoding.
    Empty input returns the SHA-256 of zero bytes (not an error).
    """
    if isinstance(response_body, str):
        response_body = response_body.encode("utf-8")
    return _hashlib.sha256(response_body).hexdigest()


def build_worker_receipt(
    task_id: str,
    tokens_used: int,
    node_hmac_key: str,
    *,
    response_body: bytes | str,
    worker_node_id: str | None = None,
    cip_parent_task_id: str | None = None,
    cip_session_key: str | None = None,
) -> CIPWorkerReceipt:
    """Build and sign a CIPWorkerReceipt (TC-9c).

    `response_body`: the exact response bytes that were (or will be) delivered
    to the coordinator. The SHA-256 of this value is included in the canonical
    message and the resulting CIPWorkerReceipt. Coordinator verifies this hash
    before submitting the credit award.

    Caller must pass raw decompressed bytes — do not pass gzip-encoded bytes.
    """
    nonce = secrets.token_hex(16)
    response_hash = compute_response_hash(response_body)
    msg = _canonical_message(
        task_id, tokens_used, cip_parent_task_id, cip_session_key, nonce, response_hash
    )
    signature = hmac.new(node_hmac_key.encode(), msg, hashlib.sha256).hexdigest()
    now = datetime.now(timezone.utc)
    return CIPWorkerReceipt(
        task_id=task_id,
        worker_node_id=worker_node_id,
        tokens_used=tokens_used,
        cip_parent_task_id=cip_parent_task_id,
        cip_session_key=cip_session_key,
        nonce=nonce,
        issued_at=now.isoformat(),
        expires_at=(now + timedelta(seconds=300)).isoformat(),
        signature=signature,
        response_hash=response_hash,
    )
```

**Change 3: Update `verify_worker_receipt()` to include `response_hash`**

```python
def verify_worker_receipt(receipt: CIPWorkerReceipt, node_hmac_key: str) -> bool:
    msg = _canonical_message(
        receipt.task_id,
        receipt.tokens_used,
        receipt.cip_parent_task_id,
        receipt.cip_session_key,
        receipt.nonce,
        receipt.response_hash,  # new
    )
    expected = hmac.new(node_hmac_key.encode(), msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, receipt.signature)
```

**Where in the adapter call flow does `build_worker_receipt()` get called?** The adapter's task handler (wherever it dispatches to the inference backend and constructs the response) must accumulate the full response body before calling `build_worker_receipt()`. For streaming responses, this means the adapter MUST complete inference and buffer the body before signing. The response body is then emitted to the coordinator after signing.

### 2.2 `adapter/src/adapter/models.py`

**Change: Add `response_hash` field to `CIPWorkerReceipt`**

Current:
```python
class CIPWorkerReceipt(BaseModel):
    task_id: str
    worker_node_id: str | None = None
    tokens_used: int
    cip_parent_task_id: str | None = None
    cip_session_key: str | None = None
    nonce: str
    issued_at: str
    expires_at: str | None = None
    signature: str
```

Proposed:
```python
import re as _re

_SHA256_HEX_RE = _re.compile(r'^[0-9a-f]{64}$')


class CIPWorkerReceipt(BaseModel):
    task_id: str
    worker_node_id: str | None = None
    tokens_used: int
    cip_parent_task_id: str | None = None
    cip_session_key: str | None = None
    nonce: str
    issued_at: str
    expires_at: str | None = None
    signature: str
    response_hash: str  # SHA-256 hex of response body; required in Phase 5

    @field_validator("response_hash", mode="before")
    @classmethod
    def validate_response_hash(cls, v: Any) -> str:
        if not isinstance(v, str) or not _SHA256_HEX_RE.match(v):
            raise ValueError(
                "response_hash must be a lowercase SHA-256 hex string (64 characters)"
            )
        return v
```

**Backward compatibility note**: This field is required (no default). Existing code that constructs `CIPWorkerReceipt` without `response_hash` will fail validation at the Pydantic layer. All callers of `build_worker_receipt()` must pass `response_body`. This is a breaking change within the adapter — acceptable since Phase 5 CIP code is not yet deployed to production.

### 2.3 Proxy — Receipt Verification Before Award Submission

**Location**: `proxy/src/proxy/routing/fallback.py`, function `_schedule_award()` and the call site in `execute()`.

**Current behavior** (from code inspection): The proxy receives the response, checks session key binding, then calls `_schedule_award()` which fires a background `_fire_award()` coroutine. The `_fire_award()` function constructs a `CIPWorkerReceipt` from the raw response dict and calls `submit_award()`. The `submit_award()` function checks nonce replay and session binding, then POSTs to the directory. **Neither `_fire_award()` nor `submit_award()` verify that `sha256(received_body) == receipt.response_hash`.** This verification must be added.

**Change: Add response body hash verification before award submission**

In `proxy/src/proxy/routing/fallback.py`, modify `execute()` to extract and verify the hash:

```python
async def execute(self, nodes, task_id, intent, payload, timeout_ms,
                  cip_envelope=None, cip_policy="best_of_n",
                  cip_replicas=1, cip_quorum=None):
    # ... existing code ...
    for node in nodes:
        node_id = node.get("node_id", "unknown")
        try:
            response = await self._router.route(
                node, task_id, intent, payload, timeout_ms, cip_envelope=cip_envelope
            )
            # ... existing session key binding check ...

            if cip_envelope is not None:
                # TC-9c response integrity: verify response_hash before accepting
                raw_receipt = response.get("cip_receipt")
                if raw_receipt:
                    receipt_hash = raw_receipt.get("response_hash")
                    response_body = _extract_response_body(response)
                    if receipt_hash is not None:
                        import hashlib
                        actual_hash = hashlib.sha256(
                            response_body if isinstance(response_body, bytes)
                            else response_body.encode("utf-8")
                        ).hexdigest()
                        if actual_hash != receipt_hash:
                            logger.warning(
                                "node %s returned response_hash mismatch — discarding (TC-9c §10.3.2)",
                                node_id,
                            )
                            last_error = "response_hash_mismatch"
                            continue  # try next node, do NOT submit award
                    else:
                        # Phase 5: missing response_hash is a protocol violation
                        logger.warning(
                            "node %s CIPWorkerReceipt missing response_hash — discarding (Phase 5 §10.3)",
                            node_id,
                        )
                        last_error = "response_hash_missing"
                        continue

                # ... existing cip_aggregation building and award scheduling ...
```

Where `_extract_response_body(response)` is a new helper that extracts the response body as bytes from the IICP RESPONSE dict. This requires agreement on the canonical field path — likely `response["result"]["content"]` or `response["result"]["text"]` depending on the intent domain. The helper must handle the case where the body is embedded in different result schemas.

**Important ordering constraint**: The hash verification MUST happen BEFORE `_schedule_award()` is called. The current architecture fires the award in a background task after the response is returned to the client. This must change: the proxy MUST verify the hash synchronously before returning the response to the end client (to prevent the client receiving garbage) AND before scheduling the award (to prevent paying for garbage).

### 2.4 Directory — `CreditsController.php`

**Location**: `directory/app/Http/Controllers/CreditsController.php`, `award()` method.

**Change 1: Add `response_hash` to validated fields**

In the `$request->validate([...])` block:
```php
'response_hash' => ['required', 'string', 'regex:/^[0-9a-f]{64}$/'],
```

**Change 2: Include `response_hash` in canonical message reconstruction**

Current canonical construction (line 105–111):
```php
$canonical = implode(':', [
    $validated['task_id'],
    (string) $validated['tokens_used'],
    $validated['cip_parent_task_id'] ?? '',
    $validated['cip_session_key'] ?? '',
    $validated['nonce'],
]);
```

Proposed:
```php
$canonical = implode(':', [
    $validated['task_id'],
    (string) $validated['tokens_used'],
    $validated['cip_parent_task_id'] ?? '',
    $validated['cip_session_key'] ?? '',
    $validated['nonce'],
    $validated['response_hash'],  // new — Phase 5
]);
```

**Change 3: Include `response_hash` in event log**

In the `$this->eventLogger->log(...)` call, add `'response_hash' => $validated['response_hash']`.

**Change 4: Backward-compatible validation rule**

For the migration period (Phase 5.0), make `response_hash` conditionally required:
```php
'response_hash' => ['sometimes', 'nullable', 'string', 'regex:/^[0-9a-f]{64}$/'],
```

But then check: if absent and the node's registered `cip_version >= "5.1"`, reject with IICP-E027. If absent and `cip_version == null | "5.0"`, accept but log a warning. This allows Phase 5.0 → 5.1 migration without immediately breaking existing receipts.

**Important**: The directory does NOT have access to the actual response body. The directory cannot independently verify that `response_hash` matches the actual response that was delivered. The directory's verification is: (a) the receipt signature is valid (proving the adapter signed THIS hash), and (b) the coordinator submitted the request (claiming it verified the hash matches). This is trust-in-the-coordinator for hash verification at the directory layer — acceptable given that the coordinator is the direct recipient of the response.

---

## 3. Edge Cases With Solutions

### 3.1 Streaming Responses

**Problem**: In SSE mode, the adapter cannot sign a hash until inference completes, but SSE is designed to stream incrementally.

**Solution** (Phase 5): Adapter buffers SSE chunks internally. After inference completes, computes `response_hash = sha256(b"".join(chunks))`, includes hash in the `cip_receipt` SSE event. Coordinator accumulates received chunks, verifies hash on `cip_receipt` event receipt. Latency impact: zero additional latency beyond inference time (inference must complete before the last token is emitted anyway).

**Implementation detail**: The body to hash is the concatenated SSE `data:` field values (excluding `event:` and empty lines). The adapter and coordinator must agree on exactly which bytes constitute the "body" for hashing. Recommended: use the concatenated text content of all `data:` fields in chronological order, encoded as UTF-8. Exclude the `event:` field names and delimiter whitespace.

**What if the stream is interrupted mid-transmission?** The coordinator will have accumulated a partial body. Its hash will not match `receipt.response_hash` (which was computed over the full body). The coordinator MUST reject the receipt. This is correct behavior — the adapter did not deliver what it signed for.

### 3.2 Gzip/Compressed Responses

**Problem**: If the adapter compresses the response body (Content-Encoding: gzip), the same plaintext may compress to different byte sequences (gzip header contains timestamps, compression level differences). Hashing compressed bytes is not deterministic.

**Solution**: The adapter MUST hash decompressed bytes. If the adapter compresses the response for transport (unlikely in the current implementation, which returns JSON), it must decompress before hashing. The coordinator must also decompress before verifying. The spec language is: "response_body_bytes is the raw bytes AFTER any Content-Encoding is stripped."

**Current implementation**: The adapter currently returns JSON without Content-Encoding compression. This case is theoretical for Phase 5 but important to specify explicitly for future-proofing.

### 3.3 Empty Responses (Error Cases)

**Problem**: If the adapter encounters an error and returns an empty body, what is the correct `response_hash`?

**Solution**: SHA-256 of zero bytes = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. This is a valid, deterministic sentinel. The adapter SHOULD still include this hash in the receipt for empty error responses. The coordinator verifies: `sha256(b"") == receipt.response_hash`. If the adapter returns an error via the structured `TaskError` schema (not empty body, but a JSON error object), the body is the JSON of that error object — hash that JSON string as UTF-8.

**Credit award for error responses**: The coordinator SHOULD NOT submit a credit award for a worker that returned an error response, regardless of whether the hash matches. The spec already requires this (§7: credits awarded only for workers whose response was selected in aggregation).

### 3.4 Binary Responses (Non-JSON)

**Problem**: Some intent domains may return binary data (audio, images).

**Solution**: Hash raw bytes. No normalization. The `response_hash` field is agnostic to content type — it is always `sha256(raw_bytes).hex()`.

**Current state**: No existing IICP intent URNs return binary data in Phase 5. All current intents return JSON. This case is future-proofing.

### 3.5 Large Responses

**Problem**: Performance concern for very large responses.

**Analysis**: SHA-256 throughput is approximately 400–800 MB/s on a single modern CPU core. For a 100,000-token response (approximately 400 KB at 4 bytes/token), hashing takes under 1 ms. LLM inference for 100,000 tokens at typical generation speeds (10–50 tokens/second) takes 2,000–10,000 seconds — hashing is negligible by 9+ orders of magnitude. Large responses are not a practical constraint.

### 3.6 Response Body Extraction in the Proxy

**Problem**: The proxy receives IICP RESPONSE JSON. The "response body" for hashing purposes must match what the adapter hashed. For the proxy, the "body" is the full IICP RESPONSE JSON? Or just the `result` field? Or just the `result.content` field?

**Critical decision**: The adapter hashes the bytes it computes and delivers. If the adapter hashes only the `result.content` field, but the proxy hashes the full RESPONSE JSON, the hashes will never match.

**Recommendation**: The adapter hashes the full RESPONSE JSON body as it encodes it for transmission (the raw bytes of the HTTP response body, after JSON serialization). The proxy receives the HTTP response body as raw bytes and hashes those exact bytes. This avoids any ambiguity about which fields are included.

**Implementation**: In the adapter, after constructing the `TaskResponse` object and calling `.model_dump_json()` (or equivalent FastAPI serialization), capture those bytes for hashing before sending. In the proxy, capture the raw response bytes from `httpx` before JSON parsing.

**Spec text**: "response_body_bytes is the UTF-8 encoded JSON string of the complete HTTP response body as transmitted by the worker." This makes the hash unambiguous and removes any risk of field-selection mismatches.

---

## 4. Security Analysis of the Proposal

### 4.1 What This Protects Against (Confirmed)

1. **Response body substitution**: The adapter must sign the hash of the body it actually delivers. If it delivers a different body, the coordinator's hash verification fails, the receipt is rejected, no credits are awarded.

2. **Response truncation post-signing**: If the adapter truncates the delivered body, the coordinator accumulates fewer bytes, the hash differs, receipt rejected.

3. **Receipt forge by coordinator**: The coordinator cannot modify `response_hash` in the receipt it forwards to the directory — the receipt signature covers `response_hash`, and the signature was computed with the adapter's `node_hmac_key` which only the adapter has. A modified receipt will fail HMAC verification at the directory.

4. **Replay with a different body**: A replayed receipt (same nonce) is blocked by nonce uniqueness. A re-signing attempt with a new nonce but substituted `response_hash` requires forging the HMAC — impossible without the `node_hmac_key`.

### 4.2 What This Does NOT Protect Against

1. **Quality of the response**: The adapter can hash a garbage response, sign the receipt, deliver the garbage response, pass hash verification, and earn credits. Hash commitment proves body integrity, not body quality.

2. **Token count inflation with proportional garbage**: The adapter could generate a large volume of low-quality text (e.g., repeated phrases) to match a high `tokens_used` claim. The hash verifies that the garbage was actually delivered; the token count ceiling limits the maximum award; but the user receives garbage.

3. **Collusion within the hash**: Two colluding adapters — one serving as coordinator — agree on what response to return, the coordinator verifies the hash correctly, submits the award. The hash proves the response was consistent, not that it was legitimate.

4. **Directory trust**: The directory trusts that the coordinator actually verified the hash. If the coordinator's `submit_award` code is compromised, it could submit awards without performing hash verification. This is a software correctness concern, not a cryptographic one.

5. **Prompt-response correlation**: The hash does not prove the response was produced in response to THIS specific prompt. A precomputed response that happens to be valid could be used for multiple similar prompts.

---

## 5. Migration Path

### Phase 5.0 (Immediate — this proposal)

1. Add `response_hash: str` to `CIPWorkerReceipt` model (required field, validated as 64-char hex).
2. Update `build_worker_receipt()` to accept `response_body` and compute/include the hash.
3. Update canonical message in both adapter and directory to include `response_hash`.
4. Proxy: add hash verification before `_schedule_award()` call.
5. Directory: `response_hash` is `required` in validation. Existing receipts without the field are rejected with IICP-E027 `"CIPWorkerReceipt missing response_hash"`.

**Breaking change scope**: This breaks the adapter↔directory CIP credit flow for any adapter that does not include `response_hash`. Since CIP is a Phase 5 feature not yet deployed to production adapters, this is acceptable. The breaking change boundary is: adapters running `cip_receipt.py` without the `response_hash` change will have their credit awards rejected by the directory.

**Rollout order**: (1) Update directory first (accept `response_hash` as optional with a warning but still compute the old HMAC for backward compat during a 2-week window). (2) Deploy updated adapter. (3) Enforce `required` in directory after all known adapters have been updated.

### Phase 5.1 (Follow-up — within 30 days)

1. Directory: make `response_hash` strictly required (remove the backward-compat window).
2. Proxy: add `X-IICP-Response-Hash` header request as a hint (verify the header matches receipt hash for an extra check).
3. Spec: close the PENDING marker on §10.3.1 (streaming hash protocol).
4. Add conformance test IDs:
   - `CIP-HASH-01`: Worker receipt MUST include `response_hash` as 64-char hex.
   - `CIP-HASH-02`: Coordinator MUST verify `sha256(received_body) == receipt.response_hash` before award submission.
   - `CIP-HASH-03`: Directory MUST include `response_hash` in HMAC canonical message reconstruction.
   - `CIP-HASH-04`: Coordinator MUST reject and discard response if hash mismatch (not just reject award).

### Phase 5.2 (Streaming hardening — optional, within 90 days)

1. Define the `cip_receipt` SSE event schema formally in the spec.
2. Implement streaming accumulation in the coordinator.
3. Add conformance test `CIP-HASH-05` for streaming hash verification.

---

*Document status: proposed — not normative until accepted by Protocol Steward and merged to spec. Implementation should wait for PS sign-off.*
