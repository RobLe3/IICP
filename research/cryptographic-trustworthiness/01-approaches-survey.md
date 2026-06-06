# Cryptographic Approaches to Response Integrity — Survey

**Research track**: W-031 / GitHub issue #301  
**Date**: 2026-05-22  
**Status**: Research — not normative  
**Scope**: Six cryptographic approaches evaluated for IICP CIP response integrity

---

## Problem Statement

The current CIP receipt signing (adapter `cip_receipt.py`, spec §10.3) signs:

```
canonical = f"{task_id}:{tokens_used}:{parent_task_id or ''}:{session_key or ''}:{nonce}"
```

The response body content — the actual inference output — is absent from the signed canonical message. A malicious adapter can therefore:

1. Claim `tokens_used = 2000` while returning a 10-token garbage response (token inflation)
2. Return a cached or wrong response while collecting full credits
3. Truncate the response after the 200 OK is sent (the receipt is already signed)
4. Return adversarially injected content while the coordinator has no basis to detect the substitution

This survey evaluates six cryptographic approaches to closing this gap, ordered from simplest to most complex.

---

## Approach 1: Hash Commitment (Response Body Hash)

### Description

The simplest extension: the adapter computes `SHA-256(response_body)` and includes this hash in the CIP receipt canonical message. The coordinator, having received the response body, verifies the hash matches before submitting the credit award.

**New canonical message:**
```
{task_id}:{tokens_used}:{parent_task_id}:{session_key}:{nonce}:{response_hash}
```

Where `response_hash = sha256(response_body_bytes).hex()`.

### Mapping to IICP Threat Model

| Threat | Mitigated? | Mechanism |
|--------|-----------|-----------|
| Token inflation (claim 2000, send 10) | Partial | Hash can be verified, but only if coordinator also verifies token count against body length |
| Cached/wrong response | Yes | Coordinator hashes received body; mismatch → reject |
| Truncated response | Yes | Truncated body produces different hash |
| Injected content | Yes | Hash ties the signed receipt to the exact bytes delivered |

### Technical Feasibility

- **CPU cost**: SHA-256 throughput is approximately 400–800 MB/s on a single modern CPU core. A 10,000-token response at ~4 bytes/token is roughly 40 KB — hashing takes under 0.1 ms. Negligible relative to LLM inference time (hundreds of milliseconds to seconds).
- **Wire cost**: A SHA-256 hex digest is 64 characters. No material overhead.
- **Implementation complexity**: Low. One additional field in `CIPWorkerReceipt`, one `hashlib.sha256` call in `cip_receipt.py`, one verification step in the proxy's `submit_award` path.

### What It Protects Against

- Coordinators can detect any modification to the response body post-signing.
- Prevents the adapter from signing a receipt for a different body than the one it sent.
- Binds credit claims to specific, verifiable output.

### What It CANNOT Protect Against

1. **Pre-computation of a valid garbage response**: the adapter can run inference, compute hash, sign the receipt over the hash of garbage, then send garbage. The coordinator verifies hash match successfully — but never knows if the output was *correct* or *useful*. The hash proves consistency, not quality.
2. **Coordinated collusion between adapter and proxy**: if both sides are compromised, the coordinator can generate a fake receipt for a fake response.
3. **Token count inflation that the hash does not contradict**: a 2000-token claim for a genuinely 2000-token garbage response will pass hash verification. Token count accuracy still depends on the adapter's self-report.
4. **Streaming responses where the body is never accumulated**: in SSE mode, the body is delivered in chunks. Hash computation requires accumulating the full body or a Merkle-tree approach (see §3.1 below).
5. **Quality**: the hash cannot attest that the response is a correct, helpful answer to the prompt.

### Streaming Edge Cases

**Problem**: LLM responses are often streamed as SSE (`text/event-stream`). The adapter cannot sign a hash of the complete body at `200 OK` time because the body has not been fully generated.

**Three approaches:**

1. **Accumulate-then-hash (simplest)**: The adapter buffers all SSE chunks internally, finishes inference, computes the hash over the accumulated body, then releases the buffered response to the coordinator. The coordinator accumulates on its side and verifies. This adds per-response latency equal to zero (since inference must complete before the last chunk anyway) but requires buffering. For typical 4–40 KB responses, buffering is trivial.

2. **Per-chunk Merkle tree (more complex)**: Each SSE chunk gets a sequential index `i` and hash `h_i = sha256(chunk_i)`. A Merkle tree is built from `[h_0, h_1, ..., h_n]`. The root `R` is placed in the final SSE event (`event: receipt`, `data: {root: R, signature: ...}`). The coordinator verifies each chunk hash and the root. This enables progressive verification but requires the coordinator to buffer all chunks for Merkle verification anyway. No practical latency advantage over approach 1.

3. **Token count as integrity proxy (weakest)**: Sign only `token_count` and rely on the coordinator to verify that the number of tokens in the received body approximately matches `tokens_used`. This is imprecise (tokenizer boundaries vary) and does not prevent body substitution. Not recommended.

**Recommendation**: Approach 1 (accumulate-then-hash) in the adapter. The adapter already must wait for inference to complete before signing the receipt; buffering the output adds no delay to the round-trip. The `response_hash` field goes in the receipt, and the coordinator verifies before submitting the credit award.

### Binary / Encoding Edge Cases

- **JSON responses**: hash the raw UTF-8 bytes of the JSON string as returned by the inference backend. Do NOT normalize (no key sorting, no whitespace normalization) — normalization introduces implementation divergence risk.
- **Gzip/compressed responses**: hash the decompressed bytes. The adapter must strip `Content-Encoding` before hashing. Hashing compressed bytes is wrong because the same plaintext can compress differently (different gzip headers, timestamps in the stream).
- **Empty responses (error case)**: SHA-256 of empty bytes is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. This is a valid sentinel — a legitimate empty response produces this hash deterministically. The coordinator MUST accept it.
- **Non-JSON responses (binary/audio)**: hash raw bytes. No normalization.
- **Large responses**: SHA-256 is O(n) in body size. For a 100,000-token response (~400 KB), hashing takes under 1 ms on current hardware. Not a practical constraint.

### Phase Recommendation

**Phase 5 — implement now.** This is the minimum viable fix for the response integrity gap. Low complexity, high impact, backward-compatible (field optional in Phase 5, required in Phase 5.1+).

---

## Approach 2: HTLC-Style Conditional Payment

### Description

In Bitcoin's Lightning Network, a Hash Time-Locked Contract (HTLC) works as follows:
- Alice creates secret `x`, computes `H = sha256(x)`, gives `H` to Bob
- Bob's payment is conditional on Alice revealing `x` such that `sha256(x) == H`
- Time-lock: if Alice does not reveal `x` within timeout `T`, payment refunds to Alice

The IICP analogue would be: the worker (adapter) generates a commitment `H` to its planned response before delivering it. The coordinator withholds credit payment until the actual response hash matches `H`.

### Mapping to IICP Threat Model

The critical question is whether HTLC-style commitment adds anything beyond Approach 1. The answer depends on what "commitment before delivery" means in practice.

**Key distinction**: In Bitcoin, Alice commits to `x` before receiving the routing payment from Bob. The timelock prevents Bob from simply not paying once Alice reveals `x`. In IICP, the delivery is synchronous HTTP — the coordinator receives the response before submitting the credit award. The temporal ordering is therefore:

```
[Adapter sends response] → [Coordinator receives response] → [Coordinator submits award]
```

There is no analogous race. The coordinator already withholds the credit award until after it receives the response. HTLC structure buys nothing additional in a synchronous RPC protocol.

**The one scenario where pre-commitment matters**: If an adaptive attack were possible where the proxy resubmits the same task with a different prompt until it gets a desired response, then forcing the adapter to commit to the hash before knowing the prompt would break this attack. However, in IICP the prompt is included in the task payload sent to the adapter — the adapter cannot commit to a hash before knowing the prompt.

**Two-phase protocol sketch**: Could the adapter run inference, compute the hash, send a "commitment message" with the hash to the coordinator, wait for acknowledgment, then deliver the body? This reduces to: the coordinator receives the hash, then the body, then verifies. This is functionally equivalent to Approach 1 (hash in receipt + body verification), with one extra round trip and higher latency. No security gain.

### Technical Feasibility

Impractical in its pure HTLC form because:
1. LLM output is non-deterministic at temperature > 0. The adapter cannot commit to a hash before running inference (it does not know what it will generate).
2. At temperature = 0 and fixed seed, determinism exists within the same process/platform (see Approach 6), but not across restarts or platforms.
3. Two-phase adds 1+ round trips (~50–200 ms network latency each way), increasing end-to-end task latency materially.

### What It Protects Against

In the pure HTLC model: nothing that Approach 1 does not already protect against, in the IICP synchronous context.

In a theoretical two-phase model with temperature=0: prevents adaptive prompt-injection attacks by binding the adapter's response before the coordinator can influence it. But this threat model does not apply to standard IICP task dispatch (the prompt is sent in the task payload, not derived from the response).

### What It CANNOT Protect Against

Everything Approach 1 cannot protect against, plus: HTLC-style time-locks require on-chain or directory-mediated enforcement, which IICP does not have. Without a smart contract or equivalent enforcer, a time-lock is advisory only.

### Phase Recommendation

**Not applicable** for IICP in its current synchronous architecture. The HTLC pattern solves a different problem (multi-hop payment routing without trusting intermediaries) that does not arise in IICP's coordinator-direct model. File as a research note, not an implementation track.

---

## Approach 3: Zero-Knowledge Proofs / zkML

### Description

zkML (zero-knowledge machine learning) uses cryptographic proof systems (typically zk-SNARKs or zk-STARKs) to prove that a model's output was correctly computed from specific weights and an input, without revealing the weights. The verifier checks the proof rather than re-running the inference.

**Claim being proven**: "I ran model M (with committed weight hash W) on input I and obtained output O. I did not fabricate O."

### Current State (2025–2026)

Research findings from web searches:

**Proof generation overhead**: zkVMs historically showed 100,000x to 1,000,000x overhead versus native inference. As of 2025–2026, specialized zkML systems have dramatically reduced this:
- EZKL (general-purpose): practical up to roughly 18M parameter models; 50-second proof on a powerful AWS instance (Modulus Labs "Cost of Intelligence" benchmark).
- zkLLM (specialized for transformers): proof generation for GPT-2 (117M parameters) in 287 seconds, with a 35.7x speedup over prior EZKL approach. Still far from real-time.
- zkPyTorch: can prove VGG-16 inference in 2.2 seconds. For Llama-3, approximately 150 seconds per token.
- 2025 state: "past the toy phase" for small models; transformer attention mechanisms "barely feasible in 2024, multiple frameworks support them by late 2025."

**Verification time**: Consistently sublinear in model size, typically seconds or less on consumer hardware. The asymmetry is: proof generation is expensive (minutes to hours for LLMs), verification is cheap (milliseconds to seconds).

**Practical model size limits**:
- Under 18M parameters: provable in under 60 seconds on dedicated hardware (2024 baseline).
- 117M parameters (GPT-2): 287 seconds proof generation (zkLLM, 2024).
- 7B parameters (Llama-3): roughly 150 seconds per token (zkPyTorch, 2025). Not practical for interactive latency.
- GPU support for proof generation (CUDA) is being added to EZKL, Lagrange, zkPyTorch, and Jolt (2025), which will reduce proof generation time by 10–50x within 12–18 months.

**Practical verification cost**: The Ethereum on-chain verification of the smallest model sub-circuit costs approximately 300K gas (~$20/transaction at 2024 prices). IICP operates off-chain, so on-chain verification costs are not directly applicable. Off-chain verification (proxy verifies the proof locally) is milliseconds.

**Weight commitment approach (partial forward pass proof)**: Rather than proving the full forward pass, a commit-and-prove approach can attest "output O was produced by a model with weight commitment C." The recent Artemis and Apollo frameworks (2024) address commitment verification overhead, which was previously a hidden cost in zkML pipelines. This is an active research area; off-the-shelf implementations for production use are not yet available.

### Mapping to IICP Threat Model

zkML would prove that:
1. The adapter ran a specific model (weight commitment matches the registered model)
2. The output was the genuine result of running that model on the task input
3. The token count matches the actual computation

This eliminates all forms of response fabrication, not just hash-consistency attacks. It is the strongest possible integrity guarantee short of re-running inference.

### Technical Feasibility (Current)

For IICP's typical workload (7B parameter models like Llama 3):
- Proof generation: ~150 seconds per output token. Completely impractical for interactive latency.
- Proof size: tens of kilobytes (manageable for transmission).
- Verification: milliseconds at the coordinator side.
- Hardware: proof generation requires significant GPU or specialized prover hardware (not a hobbyist Raspberry Pi node).

**Timeline to practical zkML for 7B models**: GPU-accelerated proving is emerging (2025). Optimistic estimate: 10–50x speedup from CUDA, meaning 3–15 seconds per token by 2026–2027. Still not real-time interactive, but potentially acceptable for batch tasks. For real-time interactive latency (under 1 second total), zkML for 7B models is unlikely to be practical before 2028 at the earliest, given the current trajectory.

**For small embedding models** (under 100M parameters, e.g., `nomic-embed-text` at 137M parameters): proof generation times of under 60 seconds are already achievable. For IICP conformance probes and embedding-based intent matching, zkML is already borderline practical.

### What It Protects Against

Everything: garbage responses, token inflation, model substitution (wrong model), response fabrication. The strongest guarantee available.

### What It CANNOT Protect Against

1. **Quality**: zkML proves correctness of computation, not usefulness of output. A model can be correctly run on a junk prompt and produce a correct-but-useless response.
2. **Model identity without a public weight registry**: the weight commitment proves "same model as committed," but the registry of weight→name mappings must be maintained externally.
3. **Prompt privacy**: the input must be disclosed to the verifier in most schemes. Zero-knowledge over the input requires additional complexity (input commitment hiding, not standard in current zkML stacks).

### Phase Recommendation

**Phase 7+ stretch** (post-2027): not practically deployable for interactive 7B+ model inference within the Phase 5 or Phase 6 timeframe. Track as a research milestone with a defined trigger: "when zkML proof generation for a 7B model reaches under 1 second per inference on commodity hardware, open the Phase 7 CIP-zkML implementation track."

**Exception**: For small embedding models (< 100M params), zkML becomes relevant in Phase 6 as an optional attestation mode for specific intent categories.

---

## Approach 4: Trusted Execution Environments (TEE)

### Description

TEEs provide hardware-enforced isolation for code execution. The key property for IICP: code running inside a TEE can generate a signed **attestation report** that proves to a remote verifier that:
1. Specific code (measured as a cryptographic hash) ran inside the enclave
2. The hardware root of trust is genuine (manufacturer-signed)
3. The enclave has not been tampered with

Relevant TEE technologies:
- **Intel SGX**: enclave-based isolation; EPC (Enclave Page Cache) limited to 256 MB historically, extended in SGXv2.
- **Intel TDX**: VM-level isolation, larger memory footprint allowed.
- **AMD SEV**: memory encryption at the VM level; less mature remote attestation.
- **NVIDIA H100 Confidential Computing**: GPU-level TEE; first GPU to natively support confidential computing.
- **AWS Nitro Enclaves**: used by Signal, AWS KMS. VM-level isolation with cryptographic attestation, suitable for LLM workloads.

### Hardware Reality for LLM Inference

**Intel SGX classic**: EPC limited to 256 MB–8 GB depending on hardware generation. A 7B parameter model in float16 is approximately 14 GB — impossible in classic SGX EPC without extensive paging, which would impose extreme overhead. SGXv2 removes strict EPC size constraints, allowing gigabytes of protected memory, but SGXv2 hardware is recent and not widely deployed in commodity node scenarios.

**NVIDIA H100 Confidential Computing**: This is the practical path for LLM inference in TEEs. Key facts from 2025 research:
- Performance overhead: 4–8% throughput penalty in CC mode for LLM inference, diminishing at larger batch sizes. NVIDIA publishes 2–5% overhead for most workloads.
- Attestation: Hardware-signed attestation reports generated by the NVIDIA driver, verifiable in one step for the entire VM + GPU configuration. Attestation provisioning is a one-time startup cost of 1–3 seconds per instance.
- LLM deployment: AWS and Phala demonstrated running Llama-3.1-8B-Instruct and DeepSeek R1 (70B) inside GPU TEEs with full remote attestation, as of 2025.
- The attestation document proves "this exact code ran on this exact hardware"; consumers can validate that the inference environment was not backdoored.

**AWS Nitro Enclaves**: Demonstrated LLM inference with attestation using AWS KMS-protected model weights. The enclave image is measured; only the measured code can request decryption of model weights from KMS. This creates a strong chain: (a) model identity is known, (b) inference ran in the measured enclave, (c) attestation report proves this to the coordinator. Practical for cloud-hosted nodes.

### IICP Integration Design

**Registration**: A TEE-capable node would include an attestation field in its REGISTER payload:

```json
{
  "tee_attestation": {
    "type": "nitro" | "sgx" | "nvidia_cc",
    "quote": "<base64-attestation-report>",
    "measurement": "<hex-enclave-measurement>",
    "verified_at": "<ISO-8601>"
  }
}
```

The directory would verify the attestation chain (against AWS Nitro attestation service, Intel IAS, or NVIDIA attestation service) at registration. A `tee_verified: true` flag would appear in NODELIST for discovery filtering.

**Runtime**: Each CIP receipt would include the TEE's signed measurement, allowing the coordinator to cryptographically bind the response to the specific attested enclave that produced it.

### Operational Complexity

The critical question: **would a hobbyist node operator realistically set this up?**

- **AWS Nitro Enclaves**: requires running on AWS EC2 Nitro-based instances. Not available for home or bare-metal nodes. Eliminates hobbyist participation.
- **NVIDIA H100 CC mode**: requires H100 GPU hardware (approximately $30,000 USD retail, or cloud pricing). Not accessible to hobbyist operators.
- **Intel SGX**: requires SGX-capable hardware (available in some consumer Intel CPUs, but EPC limits make LLM inference impractical without SGXv2 + sufficient EPC).

TEE attestation therefore creates a **two-tier node ecosystem**: TEE-attested nodes (cloud/enterprise) and non-attested nodes (hobbyist). IICP must decide if this is acceptable or if it fragments the mesh.

### What It Protects Against

A properly attested TEE provides the second-strongest guarantee available (after zkML): the response was produced by the stated code running on the stated hardware. Token inflation is prevented by running the inference backend inside the enclave and measuring it. Content substitution is impossible (the enclave is the only code with access to the model weights and response buffer).

### What It CANNOT Protect Against

1. **Model quality within the enclave**: the attested code ran, but nothing proves the model weights loaded are the claimed model (unless the weight hash is included in the enclave measurement, which requires custom enclave code).
2. **Side-channel attacks on TEEs**: TEEs are not immune to microarchitectural attacks (Spectre variants, power analysis). Advanced adversaries could potentially extract information, though not forge responses at the application layer.
3. **Software bugs in the enclave**: if the enclave code has a vulnerability, it can still be exploited (the attestation proves the code ran, not that the code was correct).
4. **Hobbyist nodes**: TEE requirements exclude the grassroots node operator demographic that IICP is designed to serve.

### Phase Recommendation

**Phase 6 medium-term (cloud/enterprise path)**: TEE attestation is viable today for cloud-deployed nodes. It should be an optional NODELIST field in Phase 6, surfaced as `tee_verified: true` in discovery, allowing coordinators to preference TEE-attested workers for sensitive tasks. Hobbyist nodes remain valid without TEE attestation.

**NOT a Phase 5 requirement**: requiring TEE would exclude the majority of current node operators.

---

## Approach 5: Reputation Staking and Slashing

### Description

Ethereum validators stake 32 ETH and are slashed (stake destroyed) for provable misbehavior (double-signing, equivocation). The economic incentive: the stake value exceeds the gain from cheating. IICP analogue: nodes stake credits; a trust auditor can slash the stake for provable misbehavior (e.g., verified response hash mismatch).

### Ethereum Slashing Model Details

- Validators stake 32 ETH (currently ~$50,000–100,000 USD range); slashed for equivocation (proposing two blocks for the same slot, attesting conflicting views).
- The slash magnitude scales with the number of simultaneously slashed validators — coordinated attacks are penalized more than individual misbehavior (correlation penalty).
- Slashing requires a **slashable condition**: a cryptographic proof of double-behavior. In Ethereum, this is two conflicting signed attestations from the same validator key.

### IICP Analogue Analysis

**What constitutes provable misbehavior in IICP?**

1. **Response hash mismatch**: If the adapter signs a receipt with `response_hash = H` but the coordinator received body `B` where `sha256(B) != H`, this is provable misbehavior — the adapter's signature is the evidence.
2. **Duplicate receipt submission**: Two receipts with the same `task_id` but different `tokens_used` — the adapter signed both, proving inconsistency.
3. **Token count inflation**: Provable only if the coordinator retains the raw response body and can demonstrate it contains fewer tokens than claimed. Requires the coordinator to act as an auditor, which it currently does not.
4. **Garbage quality**: NOT provable. Quality is subjective and cannot be cryptographically evidenced.

**Minimum stake for economic deterrence**: Credits in IICP are small — approximately 0.001–0.01 credits per task (1,000 tokens / 1,000 = 1 credit; at average task sizes of 1–10 tokens, approximately 0.001–0.01 credits). For slashing to deter, the stake must exceed the gain from cheating over the node's expected lifetime.

If a node earns approximately 1 credit/hour of serving tasks, and its expected lifetime is 1,000 hours, its total earn capacity is approximately 1,000 credits. A stake of 100 credits (10% of lifetime earnings) would provide modest deterrence. However:

- New nodes have no credits to stake (chicken-and-egg problem).
- Small credit amounts mean slashing is not economically meaningful unless the credit-to-fiat conversion rate is established.
- In a mesh of volunteer nodes, staking may reduce willingness to participate.

**The chicken-and-egg problem**: New nodes cannot stake until they have earned credits. You cannot earn credits without being trusted. You cannot be trusted without staking. Solution options: (a) directory issues initial bootstrapping credits to new nodes (requires trust in the directory issuer), (b) new nodes are in a probation pool with no staking requirement but also no CIP eligibility (current approach, but this means staking is irrelevant for new nodes), (c) external staking (real money) which introduces regulatory complexity IICP should avoid.

**What slashing can enforce with evidence**:
Only hash-level misbehavior is cryptographically provable. Everything else requires off-chain dispute resolution, which requires a trusted arbitrator. In a decentralized system, this arbitrator does not exist without significant additional infrastructure.

### What It Protects Against

- Economically deters provable misbehavior when stake value is material relative to gain from cheating.
- Creates a persistent reputation cost for misbehaving nodes beyond reputation score decay.

### What It CANNOT Protect Against

- Quality (subjective — not provable).
- Misbehavior below the detection threshold.
- New nodes (no stake to lose).
- Sophisticated attackers who cheat and exit before slashing.

### Phase Recommendation

**Phase 6 medium-term (supplementary mechanism)**: Reputation staking is a useful supplemental deterrent once the credit economy has sufficient volume to make stakes meaningful. Not a substitute for cryptographic integrity (Approach 1). The slashable condition must be defined precisely: only response hash mismatches and duplicate receipts with conflicting fields are appropriate slashing triggers in Phase 6. Slash magnitude: 50% of staked credits, with the remainder returned to the staking pool for bootstrapping new nodes.

---

## Approach 6: Challenge-Response Deterministic Proofs

### Description

REACH (the conformance probe system) already sends known HTTP calls to nodes. The challenge-response extension: REACH sends known prompts with known expected outputs (or known expected output hashes) and verifies that registered nodes return the expected response.

This works only if LLM inference is deterministic for the given prompt, model, and parameters.

### LLM Determinism Research Findings

From web search (Ollama GitHub issues, keyword-ai.co research 2025):

**Temperature = 0 + fixed seed**: GPU floating-point operations are inherently non-deterministic in the general case (different instruction orderings, different thread schedules). However, in practice:
- Within the same process, same model, same CUDA version: outputs are consistent across calls.
- Across restarts: the first call after a restart often differs; subsequent calls converge to a consistent output.
- Across platforms (Windows vs. Ubuntu): outputs differ even with identical seed and temperature.
- Cross-version: model loader changes, quantization changes, or runtime changes can alter outputs.

**Embedding models**: More deterministic than generative models because the forward pass has no sampling. Embedding vectors are consistent within the same model/runtime combination. Cross-platform floating-point differences do exist but are below cosine similarity thresholds for practical use.

**Practical determinism verdict**: Temperature = 0 + fixed seed = 42 achieves **process-local determinism** but not **cross-platform determinism**. A challenge-response system would need to specify the exact model binary (hash), exact runtime version, and exact hardware class to expect identical outputs. This level of specificity is operationally impractical for a distributed network.

### Challenge-Set Inference Attack

A node that knows the full challenge set can precompute correct answers, cache them, and return cached answers without running actual inference. This defeats the purpose of challenge-response as a liveness/quality probe.

Mitigations:
- **Large challenge set with random sampling**: REACH sends a random subset of challenges per probe run; the node cannot precompute all possible answers without effectively running inference.
- **Freshness challenge**: include a timestamp or session nonce in the prompt to prevent precomputation. But this breaks determinism (the response will differ for different nonces, making hash comparison impossible).
- **Semantic verification instead of hash comparison**: verify that the response is semantically correct (e.g., cosine similarity ≥ 0.95 to the expected embedding), not bit-identical. Semantic verification resists precomputation less well than hash comparison.

There is a fundamental tension: determinism requires the same input → same output, but anti-precomputation requires varying inputs. These goals are partially contradictory.

### What It Protects Against

- Conformance probing: detecting nodes that are offline, broken, or running the wrong model.
- Basic quality floor: nodes returning random garbage will fail challenge-response tests.

### What It CANNOT Protect Against

- Precomputation attacks if the challenge set is finite and known.
- Cross-platform non-determinism breaking expected-hash comparison.
- A node that runs inference correctly on challenge prompts but returns garbage on production tasks.
- Quality on novel prompts not in the challenge set.

### Phase Recommendation

**Phase 5/6 (supplementary, not primary)**: Challenge-response is already partially implemented via REACH probes. Extend REACH with a probabilistic response-hash verification mode: for embedding models, hash the embedding vector; for generative models, use cosine similarity against a known-good output. This provides a quality floor signal that feeds into reputation scoring (GRIT dimension DG6). Do not rely on it as a cryptographic integrity mechanism — it is a conformance/liveness probe, not a tamper-evidence system.

---

## Summary Comparison Table

| Approach | Phase | Complexity | Overhead | What It Proves | Covers Streaming | Hobbyist-Friendly |
|----------|-------|-----------|----------|----------------|-----------------|-------------------|
| 1. Hash Commitment | 5 | Low | < 1 ms | Response body unchanged | Yes (accumulate-then-hash) | Yes |
| 2. HTLC | N/A | High | High (extra round trips) | Nothing new vs. Approach 1 in sync context | No | N/A |
| 3. zkML | 7+ | Very High | 150s/token for 7B (2025) | Full computation correctness | No | No |
| 4. TEE | 6 | High | 4–8% throughput loss | Code + hardware attestation | Yes | No (requires H100/Nitro) |
| 5. Staking | 6 | Medium | None (off-chain) | Economic deterrence only | Yes | Partial (bootstrapping problem) |
| 6. Challenge-Response | 5/6 | Medium | None (async probes) | Conformance floor | Yes | Yes |

**Recommended implementation sequence**: Approach 1 (Phase 5) → Approach 6 extension (Phase 5/6) → Approach 4 optional TEE path (Phase 6) → Approach 5 staking (Phase 6) → Approach 3 zkML research milestone (Phase 7+).

---

*Document status: research-grade. Not normative until promoted to a spec change or ADR.*
