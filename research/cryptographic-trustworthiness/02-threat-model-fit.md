# IICP Trust Model and Attack Surface Analysis

**Research track**: W-031 / GitHub issue #301  
**Date**: 2026-05-22  
**Status**: Research — not normative  
**Scope**: Threat actor taxonomy, attack scenarios, current vs. proposed defenses, trust model recommendation

---

## 1. Threat Actor Taxonomy

### 1.1 Malicious Adapter (Worker Node)

**Who**: A node operator who has registered a legitimate IICP node, passed the liveness check, and holds a valid `node_token` and `node_hmac_key`, but intentionally behaves dishonestly after registration.

**Motivation**: Maximize credit earnings with minimal compute expenditure. Specific goals:
- Earn credits for tokens never computed
- Return cached or pre-generated responses without running inference
- Return garbage responses while claiming full credit
- Exploit token count self-reporting to inflate billing

**Capability**: Full control over the adapter software stack. Can modify `cip_receipt.py` behavior, forge any non-cryptographically-anchored field, and control the response body. Cannot forge `node_hmac_key`-signed fields if the key remains exclusively held by the directory.

**IICP-specific constraint**: The adapter signs receipts with its `node_hmac_key`. The directory verifies this signature. Therefore, the adapter cannot generate a valid receipt for a task it did not participate in (session key mismatch). But it CAN generate a valid receipt for a task it participated in while returning wrong/cheap content — because the receipt currently does not commit to the response body.

### 1.2 Colluding Adapter Pair

**Who**: Two or more adapter operators acting in coordination to extract credits from the system without performing legitimate inference.

**Mechanism**: Node A dispatches CIP sub-tasks to Node B (its colluder). Node B returns garbage responses. Node A submits credit awards for Node B. Credits accumulate in Node B's balance and can be reused as Node A spends them.

**Current defense**: Per-node hourly credit award rate limit (1,000 credits/hour, spec §10.6). This bounds the rate of credit laundering but does not prevent it — it only limits throughput.

**Gap**: Without response body integrity, the collusion is indistinguishable from legitimate cooperation at the credit-accounting layer. The directory cannot tell if Node B actually produced useful output.

### 1.3 Malicious Proxy (Consumer)

**Who**: A proxy that fabricates task results, manipulates the aggregation result, or selectively submits credit awards for non-responding workers.

**Motivation**: Deny credits to legitimate workers, or fraudulently collect coordination fees.

**Current defense**: Workers sign receipts; the directory validates the signature. A malicious proxy cannot generate a valid worker receipt without the worker's `node_hmac_key`. However:
- The proxy CAN selectively NOT submit a valid receipt it received (denying credits to a legitimate worker while benefiting from the response).
- The proxy CAN submit receipts for workers whose responses were NOT selected in the aggregation result (spec §7 prohibits this, but there is no cryptographic enforcement — it relies on policy enforcement in `submit_award`, which is proxy-side code under the proxy operator's control).

### 1.4 Sybil Attack

**Who**: An operator who registers many pseudonymous nodes (using different IP addresses, registration metadata) to gain disproportionate influence in the mesh or accumulate credits at scale.

**IICP-specific mechanism**: Multiple Sybil nodes can:
1. All collude (Scenario 1.2 at scale) to launder credits faster
2. Vote as a bloc in majority-vote CIP mode, controlling the "majority" result
3. Inflate reputation scores by reporting completed tasks to each other
4. Exhaust the CIP worker pool for a specific intent, forcing legitimate coordinators to use only Sybil-controlled workers

**Current defense**: Registration requires passing a liveness check (the directory pings the registered endpoint). This provides weak Sybil resistance — registering N nodes requires N publicly reachable endpoints. Rate limiting (10 REGISTERs per minute per IP, spec DIR-RL-01) provides partial protection. Identity age gating on the Platinum reputation tier (§5.1.1) provides some long-term Sybil resistance.

**Gap**: Nothing prevents an operator with multiple public IP addresses (e.g., cloud instances) from registering many nodes cheaply.

---

## 2. Attack Taxonomy: Seven Scenarios

### Attack S1: Token Count Inflation

**Description**: The adapter claims `tokens_used = N` in the receipt while the actual response contains substantially fewer tokens than N would imply.

**Example**: A 10-token response ("Sure, I can help!") with `tokens_used = 2000` (claiming the maximum credit ceiling).

**Current defense**:
- Credit ceiling check: `ceil(tokens_used / 1000) × multiplier × 1.1` (spec §10.3). This limits the absolute credit award per receipt, but if `tokens_used = 2000` and the multiplier allows it, the node still earns the ceiling for 2000 tokens even if it returned 10.
- The ceiling check does NOT verify that `tokens_used` matches the actual response body length.

**Proposed defense (Phase 5)**: `response_hash` in the canonical message commits the receipt to the exact response bytes. The coordinator, having received the response body, can compute `len(body)` and apply a rough token count sanity check (body bytes / ~4 ≈ tokens for typical English text). This is a heuristic, not a proof, but makes inflation harder to disguise.

**Residual risk**: The adapter returns a long, low-value response (e.g., a repeated character string) to match a high token count. Hash verification passes; token count matches body size; but the response is garbage. This is the "quality" problem — not addressable by hashing alone.

### Attack S2: Response Body Substitution

**Description**: The adapter runs actual inference on the task, then before signing the receipt, substitutes the response body with a cached or cheaper response. Signs the receipt over the hash of the cheaper response, delivers the cheaper response.

**Current defense**: None. The receipt has no response body commitment.

**Proposed defense (Phase 5)**: `response_hash = sha256(response_body)` in receipt. The coordinator hashes the received body and compares against `receipt.response_hash`. Mismatch → reject award, flag misbehavior.

**Residual risk**: The adapter must now deliver the body matching the hash it signed. It cannot sign a hash of a good response and deliver garbage (the coordinator rejects the award). It CAN deliver a bad response and sign a receipt over the hash of that bad response — hash verification passes, but the quality was bad. The quality problem remains.

**Attack surface still present**: If the coordinator does not verify the hash before delivering the response to the end user, the user gets garbage and the coordinator does not detect it until award submission. Fix: coordinator MUST verify hash BEFORE returning the response to the client.

### Attack S3: Response Truncation

**Description**: The adapter completes inference and signs a receipt for the full response body hash. The adapter then truncates the response during delivery — e.g., closes the connection mid-stream.

**Current defense**: None.

**Proposed defense (Phase 5)**: Hash of the full accumulated body. If the adapter truncates delivery, the coordinator accumulates a partial body. `sha256(partial_body) != receipt.response_hash` → reject award.

**Edge case**: The adapter could deliberately design a truncation point where the partial body happens to be a valid response, but its hash is different from the receipt hash. The coordinator rejects the award. The user received a partial-but-plausible response and may not detect the truncation. This is a denial-of-service against credit awards, not a credit fraud.

### Attack S4: Receipt Replay

**Description**: The adapter submits the same valid receipt to the directory multiple times to earn duplicate credits.

**Current defense**: Nonce uniqueness (spec §10.3): the directory uses atomic `Cache::add()` to reject any receipt whose nonce has been seen. The nonce is `secrets.token_hex(16)` (128-bit random). Collision probability: negligible.

**Status**: Adequately defended. No change proposed.

### Attack S5: Collusion (Credit Laundering)

**Description**: Two colluding adapters (A and B) where A dispatches CIP sub-tasks to B, B returns garbage, A submits credit awards for B. Credits accumulate in B's balance. B spends credits by dispatching tasks back to A, completing a laundering cycle.

**Current defense**:
- Hourly rate limit: 1,000 credits/hour per node (spec §10.6). This bounds the throughput of the laundering cycle.
- Session binding: session key must match (TC-9d). This prevents non-session receipts but does not prevent session-internal collusion.
- Response hash (proposed, Phase 5): If A verifies `sha256(received_body) == receipt.response_hash` before submitting, and B must sign a receipt over the hash of whatever it actually delivers, then the colluding pair is constrained to: A receives B's garbage body, verifies hash, submits award. The IICP directory never sees the response body — it only sees the receipt. The directory cannot detect that B's response was garbage.

**Proposed defense (Phase 6)**: Stake slashing for provable misbehavior. If an external auditor (REACH or a third party) re-sends the same task to B and detects a qualitatively different response, slashing can be triggered. However, quality variation is not provable without consensus from multiple independent parties.

**Residual risk**: Collusion is the hardest attack to eliminate without a decentralized oracle for response quality. The rate limit is the primary control; response hash commitment (Phase 5) provides marginal improvement by requiring the colluding pair to actually execute the response path (they cannot short-circuit to an empty response).

### Attack S6: Sybil Node Cluster

**Description**: An operator controls N nodes, all registered with different identities. In majority-vote CIP mode, they vote as a bloc. In best-of-N mode, they all return the same (bad) response, which wins by "best quality" if they collude to report high quality scores.

**Current defense**:
- Registration rate limiting (10/min/IP). Partial mitigation.
- Identity age Platinum gate (720 hours). Prevents new Sybil nodes from immediately reaching highest routing priority.
- Reputation decay for idle nodes: idle nodes lose routing priority over time.

**No response-hash-level defense**: Response hash does not help against Sybil attacks. All Sybil nodes can return the same valid (but garbage) body and a valid receipt for it.

**Proposed defense (Phase 6)**: Cross-node response diversity requirement in majority-vote mode: if the coordinator detects that `k > 2` workers returned bit-identical responses (same hash) without being in a `best_of_n` context where that would be expected, flag the session for auditing. Identical responses from multiple "independent" nodes are a Sybil indicator.

**Residual risk**: Sophisticated Sybil operators return slightly different (but equally garbage) responses to avoid identical hash detection. This attack is not eliminable without identity verification infrastructure beyond the current IICP scope.

### Attack S7: Challenge-Set Inference (REACH Gaming)

**Description**: A node operator learns the REACH challenge set (by observing repeated probes) and precomputes correct answers. The node serves probe traffic perfectly but serves garbage on production tasks.

**Current defense**: REACH probes are not secret (they test conformance, not quality), so gaming is expected. The probes test protocol conformance (correct HTTP response codes, correct JSON schema), not output quality.

**If REACH is extended to quality challenge-response** (see Approach 6 in survey): the operator who knows the challenge set can precompute. Mitigation: large randomized challenge set; nonce-freshness in prompts (breaks determinism comparison); semantic verification (cosine similarity threshold rather than hash match).

**Residual risk**: Any finite challenge set is gameable given sufficient observation time. Not eliminable without randomized, non-reusable challenges — which requires the verifier to have ground-truth answers for each unique prompt, which requires running inference itself.

---

## 3. Attack Scenario Defense Summary

| Attack | Current Defense | Proposed Phase 5 Defense | Residual Risk |
|--------|----------------|--------------------------|---------------|
| S1: Token inflation | Credit ceiling (10% tolerance) | Hash + sanity check on body/token ratio | Quality garbage still earns credits |
| S2: Body substitution | None | `response_hash` in receipt; coordinator verifies before award | Quality not provable |
| S3: Truncation | None | Hash of full accumulated body; mismatch rejects award | Partial-response DoS on awards |
| S4: Replay | Atomic nonce lock | No change (adequate) | Collision: negligible |
| S5: Collusion | Hourly rate limit | Response hash constrains short-circuit (body must be delivered) | Quality collusion undetectable |
| S6: Sybil cluster | Rate limit + identity age | Phase 6: identical-hash detection in majority-vote | Slightly varied garbage evades detection |
| S7: REACH gaming | N/A (probes test conformance) | Nonce-freshness + semantic verification | Finite challenge set always gameable |

---

## 4. Trust Model Decision: Centralized-Directory-Anchored vs. Decentralized-Cryptographic

### 4.1 Current Architecture: Centralized-Directory-Anchored

IICP's current trust model is anchored in the directory as a central authority:

- The directory issues `node_token` and `node_hmac_key` at registration
- The directory validates all credit award signatures
- The directory maintains the canonical ledger
- The directory enforces rate limits, ceiling checks, and nonce uniqueness
- Reputation scores are computed and stored at the directory

**Trust assumptions in this model**:
1. The directory is honest and not compromised
2. The directory is available (single point of failure for credit settlement)
3. The directory's implementation is correct (no bugs in HMAC verification, nonce logic, etc.)

**Strengths**: Simple to implement, easy to evolve, allows central policy enforcement, no need for consensus protocols, compatible with Phase 1–4 infrastructure.

**Weaknesses**: Single point of failure, single point of trust, directory operator can in principle inflate/deflate balances, not trustworthy in a fully adversarial environment.

### 4.2 Alternative: Decentralized-Cryptographic (Bitcoin-Style)

A fully decentralized trust model would replace the directory ledger with a blockchain or distributed ledger:
- Credit awards recorded as on-chain transactions signed by both coordinator and worker
- Smart contracts enforce slashing conditions
- No single authority can inflate balances or retroactively modify the ledger
- Consensus protocol (e.g., Tendermint, PoS Ethereum) provides finality

**Technical prerequisites**:
- A blockchain deployment (substantial infrastructure, gas costs, latency)
- Smart contract development and auditing
- Cross-chain bridging if using an existing chain
- Wallet management for node operators
- Non-trivial transaction costs per credit award

**Latency impact**: On-chain finality on Ethereum Mainnet takes 12–64 seconds (proof of stake, checkpoint finality). This is incompatible with interactive LLM task latency requirements (< 30 seconds total task budget per spec §6). Layer 2 solutions (Optimism, Arbitrum) provide 1–2 second finality but add complexity and trust assumptions about the L2 operator.

**The Ethereum validator staking context**: Ethereum requires validators to stake 32 ETH (~$80,000 USD at 2025 prices) because the stake must be economically significant relative to the value at risk (control of $1B+ in staked ETH). IICP credits are worth fractions of a cent in the current economy. The stake-to-reward ratio that makes Ethereum slashing effective does not translate to IICP's credit economy without first establishing a fiat-equivalent value for credits.

### 4.3 Recommendation: Centralized-Directory-Anchored (Maintain and Extend)

**Recommendation**: Maintain the centralized-directory-anchored model through Phase 5 and Phase 6. Extend it with response hash commitment (Phase 5) and optional TEE attestation + reputation staking (Phase 6). Reserve decentralized-cryptographic as a Phase 7+ research milestone.

**Justification**:

1. **Pragmatism**: The directory is already deployed and operational. A blockchain would require rebuilding the credit settlement layer from scratch, with 6–18 months of additional development.

2. **Attack surface**: The attacks most relevant to IICP's current scale (token inflation, body substitution) are addressable by the centralized model with hash commitment. A decentralized model does not close the quality gap any more than a centralized model does.

3. **Latency**: On-chain finality is incompatible with IICP's task latency budgets. Off-chain credit settlement with periodic on-chain settlement is possible but adds complexity without proportional benefit at current network scale.

4. **Economic reality**: IICP credits are not yet worth enough for sophisticated economic attacks to be ROI-positive. The threat model for Phase 5 is hobbyist-level misbehavior (lazy/opportunistic token inflation), not sophisticated adversarial attacks. Centralized enforcement is proportionate.

5. **Upgrade path**: The directory already stores `node_hmac_key` per node. Adding `response_hash` to the credit award request is a minimal change. Migrating to decentralized requires replacing the entire settlement layer.

6. **Phase 6 partial decentralization**: Reputation staking can be implemented within the centralized directory model (the directory holds the stake as a ledger entry), providing economic deterrence without requiring a blockchain. This is a pragmatic middle ground.

**What "centralized-directory-anchored" requires for trustworthiness**:
- Directory source code must be auditable (currently open source under Apache-2.0: checked)
- Directory operator must be accountable (IICP.network maintainer: checked)
- Directory must implement all the spec-mandated checks correctly (HMAC verification, nonce atomicity, ceiling check, rate limit: checked in `CreditsController.php`)
- Directory should publish an audit log of all credit awards (currently: `NodeEventLogger` logs to event log: checked)

The directory's trustworthiness is sufficient for the current network scale and adversary sophistication. Revisit the decentralization question at Phase 7 when (a) credit volume is high enough to attract sophisticated adversaries, or (b) the network has multiple independent directory operators (Phase 6 federated control plane per ADR-013 / spec/iicp-federated-directory.md).

---

*Document status: research-grade. Not normative until promoted to a spec change or ADR.*
