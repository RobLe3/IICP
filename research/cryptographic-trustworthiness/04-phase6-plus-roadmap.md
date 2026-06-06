# Phase 6+ — Advanced Cryptographic Tracks

**Research track**: W-031 / GitHub issue #301  
**Date**: 2026-05-22  
**Status**: Research — not normative  
**Scope**: Three advanced integrity mechanisms for IICP beyond Phase 5 hash commitment

---

## Preamble: What Phase 5 Hash Commitment Achieves and Leaves Open

Phase 5 (document `03-phase5-spec-proposal.md`) adds `response_hash = sha256(response_body)` to the CIP receipt canonical message. After Phase 5 deployment:

**Closed**:
- Response body substitution (delivering different content than what was signed)
- Response truncation post-signing
- Token count inflation where the inflated count is not supported by the delivered body size

**Still open**:
- **Quality fraud**: The adapter delivers garbage content, hashes it correctly, earns credits. Hash proves consistency, not quality.
- **Model identity**: There is no cryptographic proof that the adapter actually ran the registered model (vs. a cheaper/weaker model, or a cached response).
- **Computation proof**: No proof that inference was actually performed vs. a static cached response database.
- **Sybil collusion**: Multiple colluding adapters can all deliver the same garbage and earn credits for it.

These three advanced tracks address different subsets of the remaining open problems.

---

## Track A: Zero-Knowledge ML (zkML)

### What Phase 5 Hash Commitment Cannot Achieve

Hash commitment proves that "the adapter delivered body B and signed a receipt saying so." It does not prove:
- Body B was produced by model M (registered model)
- Body B was produced by running inference (vs. retrieved from cache)
- Body B was the genuine output of running M on input I

zkML addresses all three. A zkML proof asserts: "Model M with weight commitment W, given input I, produced output O." This is a cryptographic proof over the entire forward pass computation.

**What zkML unlocks beyond hash commitment**:
1. **Model identity verification**: Coordinators can verify the adapter used the declared model, not a cheaper substitute. This eliminates model downgrading attacks (claiming to run Llama-3-70B but running Llama-3-8B).
2. **Computation integrity**: Proves inference was performed, not retrieved from a cache. Caching is detectable because cached responses were not produced by running the model on this specific input.
3. **Trust-minimized credit settlement**: With zkML proofs, the directory could validate credits without trusting the coordinator's claim that it verified the hash. The proof is independently verifiable.

### Concrete Prerequisites

**Hardware**: GPU-accelerated proof generation. Current NVIDIA H100 GPU runs model inference. The same GPU (or a dedicated proving GPU alongside it) generates the zk proof. CUDA support is being added to EZKL, Lagrange, zkPyTorch, and Jolt (2025). A production zkML setup requires at minimum one H100 for inference and significant additional compute for proving.

**Performance thresholds to watch**:
- Target: proof generation under 10 seconds per inference for 7B models (acceptable for batch tasks)
- Target: proof generation under 1 second per inference for 7B models (acceptable for interactive latency)
- 2025 state: approximately 150 seconds per token for Llama-3 (zkPyTorch). This is a 150,000x overshoot for interactive latency.
- GPU acceleration is expected to provide 10–50x speedup (bringing proof generation to 3–15 seconds/token for 7B models in 2026–2027).

**Maturity**: The zkLLM framework (2024, CCS paper) achieves 35.7x speedup over EZKL for transformer models. The NANOZK framework (2025, arxiv) targets layer-wise zero-knowledge proofs. Artemis (2024) addresses commitment verification overhead in zkML pipelines. The field is moving rapidly, but production-grade tooling for 7B+ models does not yet exist.

**Standards**: No IETF or W3C standard for zkML proof formats. Interoperability between zkML frameworks is limited. A production IICP implementation would need to standardize on one proof format (likely PLONK/KZG or Groth16 with a specific curve).

### IICP Integration Design Sketch

**Registration**: A zkML-capable node includes in REGISTER:
```json
{
  "zkml": {
    "framework": "ezkl" | "zkpytorch" | "lagrange",
    "model_commitment": "<hex-KZG-commitment-to-model-weights>",
    "proof_system": "plonk" | "groth16",
    "circuit_hash": "<sha256-of-proving-circuit>"
  }
}
```

**Credit receipt**: The `CIPWorkerReceipt` gains a `zkml_proof` field:
```json
{
  "response_hash": "...",
  "zkml_proof": {
    "proof": "<base64-encoded-SNARK-proof>",
    "public_inputs": {
      "input_hash": "<sha256-of-task-payload>",
      "output_hash": "<response_hash>",
      "model_commitment": "<same-as-registered>"
    },
    "verification_key": "<base64-vk>"  // or reference to registered VK
  }
}
```

**Verification**: The coordinator verifies the proof before submitting the credit award. Verification time: milliseconds (sublinear in model size, typically under 1 second). The directory can independently re-verify if needed (no coordination required).

**Opt-in mechanism**: `zkml_required: true` in discovery filter. Coordinators can request only zkML-verified nodes for high-value or sensitive tasks.

### Estimated Timeline to Viability

| Milestone | Estimated Date | Trigger |
|-----------|---------------|---------|
| zkML proof generation for 7B in < 60 seconds on H100 | 2026–2027 | GPU-accelerated proving frameworks mature |
| zkML proof generation for 7B in < 10 seconds on H100 | 2027–2028 | Hardware specialization + algorithm improvements |
| zkML proof generation for 7B in < 1 second | 2028+ | Custom ASICs for proving, or breakthrough algorithms |
| IICP Phase 7 zkML track opens | When < 10 seconds achieved | Open implementation track per spec |

**Decision trigger**: When a publicly available, open-source zkML framework can prove a 7B parameter model inference in under 10 seconds on commodity cloud GPU hardware, open the IICP Phase 7 zkML implementation track. Until then, track as a research milestone in `FORGE_STATE.json`.

---

## Track B: Trusted Execution Environment (TEE) Attestation

### What Phase 5 Hash Commitment Cannot Achieve

Hash commitment proves the delivered body matches the signed receipt. It does not prove:
- The adapter ran any specific model (vs. a lookup table)
- The computation occurred in an isolated environment free from tampering
- The model weights loaded match the registered model declaration

TEE attestation addresses the execution environment and code integrity dimensions. Combined with Phase 5 hash commitment, it provides: "This specific code ran on this specific hardware, produced this specific output (hash), and signed a receipt over it."

### What TEE Unlocks Beyond Hash Commitment

1. **Code integrity**: The enclave measurement (MRENCLAVE in SGX, PCR values in Nitro) cryptographically identifies the exact code that ran. A compromised or modified adapter code produces a different measurement, detectable at attestation verification time.
2. **Execution isolation**: The model weights and computation occur in hardware-isolated memory. The node operator cannot observe or modify in-flight computation.
3. **Model weight confidentiality**: Combined with KMS-protected model weights (AWS Nitro pattern), the model's identity is cryptographically enforced — the enclave fetches the model from KMS only if the attestation matches the expected measurement, and only KMS-approved measurements can decrypt the weights.
4. **Elevated trust tier**: TEE-attested nodes can be offered to coordinators requiring higher assurance (e.g., regulated industries, sensitive task categories).

### Concrete Prerequisites

**Hardware path 1 — NVIDIA H100 CC mode** (recommended for LLM inference):
- NVIDIA H100 GPU with Confidential Computing mode enabled
- CVM (Confidential VM) host OS support (AMD SEV-SNP or Intel TDX for the host)
- NVIDIA attestation service integration for remote attestation verification
- Performance overhead: 4–8% throughput penalty at batch sizes used for LLM inference
- Attestation provisioning: 1–3 second one-time cost per instance startup
- Proof of concept: Phala deployed DeepSeek R1 (70B) in GPU TEE with full remote attestation (2025)

**Hardware path 2 — AWS Nitro Enclaves** (recommended for cloud-only nodes):
- EC2 instance family that supports Nitro (most modern EC2 instance types)
- AWS KMS for model weight encryption and access control
- AWS Nitro Attestation Service for remote attestation document verification
- Demonstrated with Llama-3.1-8B-Instruct and medical LLMs (AWS blog, 2024–2025)
- Limitation: hobbyist nodes and bare-metal nodes are excluded

**Hardware path 3 — Intel SGX + TDX** (legacy path, less recommended for LLM):
- SGX classic: EPC limited to 256 MB–8 GB; insufficient for 7B parameter models without paging
- SGXv2/TDX: removes strict EPC limits; supports larger models, but hardware is less widely deployed
- SGX is practical for smaller models (embedding models < 1B parameters)

### IICP Integration Design

**Phase 6 approach**: TEE attestation as an optional NODELIST field, not a requirement. Nodes that have TEE attestation declare it at registration; coordinators can filter for TEE-attested workers.

**Registration addition**:
```json
{
  "tee_attestation": {
    "type": "nvidia_cc" | "aws_nitro" | "sgx" | "tdx",
    "verified": true,
    "last_verified_at": "2026-05-22T10:00:00Z",
    "attestation_report_url": "https://attest.iicp.network/v1/verify/<node_id>",
    "enclave_measurement": "<hex-PCR0-or-MRENCLAVE>"
  }
}
```

**Directory verification flow**:
1. At REGISTER: directory calls the attestation service (AWS Nitro Attestation, NVIDIA attestation, Intel IAS) to verify the quote.
2. On verification success: sets `tee_verified = true` in the node record.
3. In NODELIST: surfaces `tee_verified` (boolean) and `tee_type` per node.
4. Periodic re-attestation: nodes MUST re-attest at least once per 24 hours. Directory clears `tee_verified` for nodes that do not re-attest.

**Receipt addition**: In Phase 6, TEE-attested workers include a `tee_attestation_nonce` in the CIP receipt — a per-task attestation document proving the computation occurred in the enclave. The coordinator verifies this document before submitting the award.

**Discovery filter**:
```
GET /v1/discover?intent=...&tee_required=true
```
Returns only nodes with `tee_verified = true`.

### Operational Complexity Assessment

**For hobbyist operators**: TEE attestation is not feasible for hobbyist bare-metal or consumer hardware nodes. NVIDIA H100 CC mode requires H100 hardware (approximately $30,000 USD). AWS Nitro requires running on AWS. This creates a two-tier node ecosystem.

**Recommendation**: Make TEE a routing preference, not a requirement. Coordinators handling sensitive tasks (e.g., tasks with `sensitivity = high`, regulated data) MAY require `tee_required = true`. Standard tasks use non-TEE nodes. This preserves hobbyist participation while enabling enterprise-grade assurance for use cases that need it.

**Migration for existing node operators**: Existing Phase 5 nodes continue operating without TEE. New nodes that want to advertise TEE capabilities configure and register with attestation. No forced migration.

### Estimated Timeline to Integration

| Milestone | Estimated Date | Notes |
|-----------|---------------|-------|
| NVIDIA CC mode production stability confirmed | 2025 (done) | H100 CC mode deployed by Phala, AWS |
| AWS Nitro LLM inference attestation open-source reference | 2025 (done) | aws-samples/aws-nitro-enclaves-llm |
| IICP Phase 6 TEE attestation spec draft | Q3 2026 | After Phase 5 hash commitment deployed |
| Directory attestation verification integration | Q4 2026 | Requires attestation service API integration |
| First TEE-attested IICP node registered | Q1 2027 | Dependent on cloud node operator adoption |

---

## Track C: Probabilistic Challenge-Response Verification (REACH Extension)

### What Phase 5 Hash Commitment Cannot Achieve

Hash commitment is a per-receipt mechanism: it verifies each individual response delivery. It does not provide:
- Cross-session quality consistency evidence
- Detection of systematic quality degradation (model has drifted, quantization has worsened)
- A quality floor signal that feeds into reputation scoring
- Evidence that the adapter is running the declared model at all (not just delivering consistent garbage)

Challenge-response can provide a probabilistic quality floor signal: if the adapter consistently passes known-answer challenges, it is more likely to be running the declared model correctly.

### What REACH Extension Unlocks Beyond Hash Commitment

1. **Quality floor enforcement**: Adapters that consistently fail challenge-response probes have their reputation penalized, regardless of whether their per-receipt hashes are valid.
2. **Model identity signal**: If the adapter is running a different model, its responses to known prompts will deviate from expected outputs (semantic distance check).
3. **Reputation input**: REACH probe results feed directly into GRIT dimension DG6 (live-state accuracy) and reputation scoring, providing a continuous quality signal beyond per-task outcomes.
4. **Conformance proof**: Challenge-response provides evidence that can be surfaced as a conformance signal in NODELIST (e.g., `last_challenge_passed_at`).

### Design: Extended REACH Challenge-Response

**Challenge set design** (addressing the precomputation attack):

Challenge prompts must be:
1. **Numerous**: A challenge library of at least 10,000 prompts per intent category. At each probe run, REACH selects a random subset of 3–5 prompts.
2. **Freshness-nonce embedded**: Each challenge prompt includes a freshness element that varies per probe: `"[session_nonce: {nonce_hex}] Given the following context, answer correctly: {base_prompt}"`. The nonce prevents exact precomputation (the node must process the nonce as part of the input).
3. **Semantic verification**: Expected outputs are stored as embedding vectors. Actual outputs are compared via cosine similarity (threshold ≥ 0.90 for passing). This resists exact-hash precomputation while being robust to minor phrasing variation.

**Determinism caveat**: LLM outputs are not deterministic across platforms (see survey document §6). Semantic verification (cosine similarity) is more robust than hash comparison for generative models.

**Embedding model exception**: For embedding models (e.g., `nomic-embed-text`), outputs are more deterministic within the same platform. Hash comparison is feasible if the challenge and expected-hash are platform-specific.

**Protocol**:
1. REACH sends `POST /iicp/v1/call` with a challenge payload (marked internally as a probe, not a production task).
2. The adapter responds normally (no special probe handling — the adapter should not know it is being probed).
3. REACH computes the cosine similarity of the response embedding to the expected embedding.
4. If similarity ≥ 0.90: probe passes. If similarity < 0.90: probe fails.
5. Consecutive failures → reputation penalty signal sent to directory.

**Anti-gaming**: The adapter SHOULD NOT be able to identify probe traffic from production traffic. This requires probes to be indistinguishable from normal IICP CALL messages. The probe task_id SHOULD be a normal UUID v4 (not a recognizable pattern). Probe prompts SHOULD use realistic, varied phrasing.

**Limitation**: An adapter that runs inference correctly for ALL inputs will pass. An adapter that runs inference only when it detects it is being probed would also pass if it can distinguish probes. Perfect probe indistinguishability is difficult but achievable with sufficient prompt diversity and nonce randomization.

### Integration with Reputation Scoring

**New GRIT dimension signal** (DG6 extension): Each probe pass/fail result feeds into the node's reputation score via a new delta:
- `probe_pass`: +0.002 (minor positive signal)
- `probe_fail`: −0.02 (significant negative signal — 10x asymmetric penalty, because false negatives on quality are costly)
- Consecutive probe failures (3+ in a 24-hour window): trigger reputation audit flag

**NODELIST field**: Add `challenge_score` (float [0.0, 1.0]) to NODELIST — the rolling 7-day challenge pass rate for the node. Coordinators can use `min_challenge_score=0.8` in discovery to filter out nodes with poor probe performance.

**Directory endpoint for REACH reporting**: `POST /api/v1/reputation/probe-result` (authenticated by REACH's operator token). Accepts `{node_id, task_id, passed: bool, probe_type: "semantic" | "hash", similarity_score: float}`.

### Estimated Timeline to Integration

| Milestone | Estimated Date | Notes |
|-----------|---------------|-------|
| REACH challenge library design (10K prompts per intent) | Q3 2026 | Requires editorial effort to curate challenge set |
| Semantic verification pipeline (embedding model + cosine similarity) | Q3 2026 | REACH already runs Python; add embedding step |
| Directory probe-result endpoint | Q4 2026 | New API endpoint + reputation update logic |
| NODELIST `challenge_score` field | Q4 2026 | Directory schema change |
| Conformance test: `REACH-PROBE-01` | Q4 2026 | Adapter correctly handles probe traffic (no special-casing) |
| Production REACH challenge-response active | Q1 2027 | Dependent on challenge library completeness |

---

## Phase Roadmap Summary

| Track | Phase | What It Adds Over Phase 5 | Prerequisite | Estimated Open |
|-------|-------|--------------------------|--------------|---------------|
| B: TEE Attestation | Phase 6 | Code + hardware integrity proof; model weight protection | H100 CC mode or AWS Nitro infrastructure | Q3 2026 spec draft |
| C: Challenge-Response | Phase 6 | Probabilistic quality floor; reputation input; anti-model-substitution signal | REACH challenge library (10K prompts); embedding similarity pipeline | Q3 2026 |
| A: zkML | Phase 7+ | Full computation proof; model identity; anti-cache | Proof generation < 10 seconds for 7B models on commodity GPU | 2027–2028+ |

### Combined Protection Level by Phase

| Phase | Guarantees |
|-------|-----------|
| Phase 5 (hash commitment) | Response body unchanged between signing and delivery; truncation detected; token inflation bounded by body size |
| Phase 6 (+ TEE + challenge-response) | Above + code/hardware integrity for TEE nodes; probabilistic quality floor; model identity signal via probe performance |
| Phase 7+ (+ zkML) | Above + cryptographic proof of full computation; model weight identity; no trust-in-coordinator needed for hash verification |

### Research Trigger Conditions (Recommendations for FORGE State)

Add to `project/FORGE_STATE.json` under a new `research_triggers` section:

1. **zkML trigger**: When any open-source framework proves 7B parameter LLM inference in under 10 seconds on an H100 GPU, open Phase 7 zkML implementation issue and ADR.
2. **TEE trigger**: When at least 3 node operators have expressed interest in running TEE-attested nodes (GitHub issue survey), draft Phase 6 TEE spec additions.
3. **Challenge-response trigger**: When REACH has been operating conformance probes for 90+ days with stable infrastructure, begin challenge library design (this trigger is already reachable in Phase 5).

---

## Open Research Questions (Not Resolved by This Document)

1. **Merkle-tree streaming integrity**: Is there a practical scheme for per-chunk hash verification in SSE that does not require full body accumulation? The IETF `mi-sha256` content-encoding draft (draft-thomson-http-mice) defines Merkle Integrity Content Encoding for HTTP, enabling progressive integrity verification. This is worth evaluating for IICP streaming in Phase 6.

2. **zkML for embeddings**: Embedding models (< 200M parameters) are already provable in under 60 seconds (2025). For IICP intent routing and majority-vote semantic equivalence checks (cosine similarity ≥ 0.95 per §3.2), zkML proofs of embedding computation may be practical in Phase 6. This is a narrower, more achievable target than full LLM inference proofs.

3. **Model commitment registry**: Any trust model that requires model identity verification (TEE, zkML) needs a registry of model weight hashes to model names and versions. Hugging Face's model card hashes are a starting point, but IICP would need its own canonicalization (which quantization format? which runtime version?). This is a social/governance problem as much as a technical one.

4. **Federated directory trust**: Phase 6 introduces federated directory replicas (ADR-013, spec/iicp-federated-directory.md). In a federated model, which directory is authoritative for credit settlement? Response hash verification in a federated model requires consensus among directory replicas on the canonical receipt. This is an open design question.

---

*Document status: research-grade. Not normative. Content is forward-looking and depends on external technology developments that are uncertain in timeline.*
