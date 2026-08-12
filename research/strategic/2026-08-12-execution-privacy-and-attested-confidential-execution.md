# Execution privacy and attested confidential execution

**Assessment date:** 2026-08-12  
**Decision status:** research recommendation; no production security claim, wire change, hardware endorsement or deployment is authorized

## Sources and current revisions

The IICP source baseline is the same fixed ecosystem used in the companion heterogeneous-routing assessment: specification `fbc30489dff7`, Rust SDK `f7a67b16b702`, Python SDK `72d82096fdfc`, TypeScript SDK `8527d3f04f4a`, and Rust directory `57483563c68c`. The three SDKs are `0.7.102`; the Rust directory is the published `0.1.11` operator preview.

Primary external references include:

- [IETF RATS architecture, RFC 9334](https://www.rfc-editor.org/rfc/rfc9334.html);
- [Entity Attestation Token, RFC 9711](https://www.rfc-editor.org/rfc/rfc9711.html) and [EAT media types, RFC 9782](https://www.rfc-editor.org/rfc/rfc9782.html);
- [AMD SEV-SNP overview and specifications](https://www.amd.com/en/developer/sev.html);
- [Intel TDX documentation](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/documentation.html);
- [NVIDIA attestation documentation](https://docs.nvidia.com/attestation/attestation-client-tools-sdk/latest/gpu_and_switch_attestation.html), [confidential-container platforms](https://docs.nvidia.com/datacenter/cloud-native/confidential-containers/latest/supported-platforms.html) and [confidential inference reference architecture](https://docs.nvidia.com/enterprise-reference-architectures/deploying-proprietary-models-confidential-compute-self-hosted-vms/latest/architecture-summary.html);
- [BLB hybrid HE/MPC Transformer inference](https://www.usenix.org/conference/usenixsecurity25/presentation/xu-tianshi) and [Cachemir FHE generative inference](https://arxiv.org/abs/2602.11470).

Vendor capabilities and TCB status change. Any implementation decision must re-check current platform, firmware, verifier and driver documentation.

## Executive decision

Ordinary IICP-CX protects task content from the directory, relay and network path. It does not hide plaintext from the selected executor. The current provider process loads a persistent CX private key, decrypts the request and passes plaintext to its backend. A machine administrator or compromised host can therefore inspect the key, prompt, output and inference state.

The smallest credible backward-compatible direction is an optional **attested confidential execution profile**:

1. retain the existing IICP-CX envelope where possible;
2. generate the recipient execution key inside a confidential execution environment;
3. bind that public key, a fresh caller nonce, the runtime measurement and security state into verifiable attestation evidence;
4. require the consumer or its explicitly trusted verifier to appraise that evidence before encrypting;
5. keep every plaintext-touching component, including the model runtime and KV cache, inside the attested boundary;
6. preserve IICP eligibility, policy, route tickets and fail-closed dispatch;
7. leave ordinary CX and ordinary nodes unchanged for workloads that do not require execution privacy.

This is a research profile, not a current product claim. CPU confidential VMs are the most plausible first prototype. CPU-plus-GPU confidential inference is viable only on supported composite stacks. FHE and MPC remain separate research paths for now.

## Current IICP trust boundary

### Current request path

```text
consumer
  -> IICP-CX encryption to advertised provider key
  -> transport / optional relay (ciphertext)
  -> provider node process loads persistent CX private key
  -> provider node process decrypts request
  -> provider handler / Ollama / LM Studio / vLLM / llama.cpp sees plaintext
  -> provider node process encrypts response when response_encryption_v1 is negotiated
  -> consumer decrypts response
```

The directory and relay do not need plaintext. The selected node does.

### Source findings

- The confidentiality specification explicitly states that the selected executor decrypts the payload and can see it. Its Tier-1 static provider key also lacks forward secrecy against later compromise of that key.
- Rust `confidentiality.rs`, Python `_confidentiality.py` and TypeScript `confidentiality.ts` generate or load a node CX key from local persistent storage.
- Rust `node.rs`, Python `node.py` and TypeScript `node.ts` decrypt in the ordinary node process before invoking the handler/backend.
- All three SDKs advertise and enforce `response_encryption_v1`, but response encryption does not change the executor trust boundary.
- The existing compliance attestation is a signed project/conformance statement. It is not hardware remote attestation and must not be presented as such.

The June 2026 privacy reports reached the correct high-level conclusion: local execution is the strongest current option; TEE-attested execution is the realistic remote research direction; FHE is longer-term. This report updates and narrows that proposal against the current implementation and standards. It does not create a second privacy architecture.

## Precise property and non-properties

When an execution-privacy requirement is satisfied, the intended property is:

> The accepted threat model prevents the node operator, host administrator and ordinary host software from extracting the protected request, response, KV cache and relevant inference state from outside the attested confidential boundary.

It does not by itself provide:

- anonymity;
- traffic-analysis resistance;
- hidden task timing or ciphertext sizes;
- availability against a malicious host;
- protection from every microarchitectural side channel;
- proof that the measured application is logically correct or free of logging;
- safety when firmware, verifier roots, reference values or the accepted TCB are vulnerable;
- privacy if plaintext is forwarded to an ordinary host-level inference process.

Hardware attestation proves claims about a measured environment under a platform-specific trust model. The relying party must still decide whether those measurements and security versions are acceptable.

## Technology assessment

| Approach | Operator sees plaintext? | Current fit | Main constraints | IICP disposition |
|---|---|---|---|---|
| Ordinary IICP-CX | Yes, at selected executor | Shipped | Static provider key; executor is trusted | Keep as baseline payload confidentiality. |
| Local-only execution | No remote operator | Shipped policy option | Requires adequate local model/hardware | Strongest current option. |
| AMD SEV-SNP confidential VM | Intended no, outside accepted CVM boundary | Plausible CPU prototype | EPYC/platform/firmware support, image measurement, attestation verification and current TCB policy | Research first CPU adapter. |
| Intel TDX trust domain | Intended no, outside accepted TD | Plausible CPU prototype | Supported Xeon/platform/module, quote verification, measurement and TCB policy | Research alternative CPU adapter. |
| NVIDIA Hopper/Blackwell confidential GPU plus CVM | Intended no, across accepted CPU/GPU trust boundary | Plausible accelerated prototype | Supported H100/H200/B100/B200 configurations, confidential VM, protected PCIe, driver/firmware and composite attestation | Later prototype after CPU flow. |
| AMD/Intel accelerator alternatives | Not established as a comparable general IICP stack by this review | Monitor | Current primary evidence did not establish a broadly deployable equivalent to the NVIDIA confidential-GPU path | Do not advertise support without a concrete verified platform. |
| FHE generative inference | Server need not see plaintext | Research | Specialized models/operators and very high latency; Cachemir reports under 100 seconds per token for Llama-3-8B on GPU | Separate long-term backend research. |
| MPC / hybrid HE-MPC | Parties need not learn protected inputs under stated assumptions | Research | Multiple parties, communication, interaction and specialized runtimes; current work remains expensive even on smaller Transformers | Separate private-inference/CIP research. |
| Privacy-preserving CIP | Not by ordinary model splitting | Not implemented | Requires a purpose-built HE/MPC/secret-sharing protocol | Do not equate distributed inference with private inference. |

AMD SEV-SNP and Intel TDX protect confidential virtual machines from a malicious or curious host under their documented threat models and provide attestation. Both require current firmware and TCB appraisal. AMD's `REPORT_DATA` and Intel TDX report data can carry caller-defined hashes, which makes binding an ephemeral public key and nonce technically plausible.

NVIDIA's supported confidential-computing path couples a confidential VM with a confidential-capable Hopper or later GPU. NVIDIA provides local and remote GPU attestation; current Intel Trust Authority material also documents composite Intel TDX plus NVIDIA GPU appraisal. GPU-only attestation is not enough for an application whose CPU-side runtime handles plaintext. The inference runtime, tokenizer, model code, logs and response encryption must stay in the measured confidential environment.

## Standards boundary

IICP should use the RATS role model rather than inventing a second attestation vocabulary:

| RATS concept | IICP mapping |
|---|---|
| Attester | confidential worker and its platform adapters |
| Evidence | vendor/platform evidence, potentially represented by a profiled EAT or opaque vendor object |
| Verifier | local consumer verifier or an explicitly trusted verification service |
| Attestation Results | normalized, time-bounded result consumed by client policy |
| Relying Party | IICP consumer deciding whether to release the CX-encrypted task |
| Endorsements/reference values | vendor roots, firmware/runtime reference values and project/operator policy inputs |

RFC 9711 provides a standardized EAT claims framework and nonce-based freshness, but it is not a universal vendor-evidence decoder or protocol flow. Composite CPU/GPU attestation may use EAT submodules or platform-specific nested results. The profile must state exactly how verification keys, endorsements, reference values and appraisal policies are obtained.

Key binding is essential. A valid quote about one environment plus an unrelated CX public key is insufficient. AMD SEV-SNP can include guest-supplied data in an attestation report, and Intel TDX report data can bind runtime/user data. An IETF key-binding draft also illustrates EAT `cnf` plus proof-of-possession, but it remains an Internet-Draft and cannot be treated as a stable standard. The IICP research profile should define the required property while adapters implement the platform-specific binding.

## Recommended trust split

```text
untrusted host shell
  directory registration, heartbeat, discovery transport,
  relay/NAT, lifecycle, ciphertext forwarding, coarse resource advertisement
                         |
                         v
attested confidential worker
  execution CX private key, request parsing, tokenization,
  model runtime, model weights when protected, prompt/context,
  KV cache, tools covered by the profile, output and response encryption
```

A normal host-level Ollama, LM Studio, vLLM or llama.cpp process cannot be reused outside the boundary for a protected task. A compatible runtime may run **inside** the measured CVM or confidential container, but the entire plaintext path must remain there.

Tools need explicit treatment. If a model emits protected tool arguments to an ordinary host tool, the profile no longer protects those arguments. The first prototype should either prohibit tools or define a narrow protected-tool boundary.

## Candidate protocol flow

The endpoint name and encoding remain open until the profile audit is complete. The required semantics are:

1. Consumer discovers an eligible node advertising stable support for an execution-privacy profile and supported evidence formats.
2. Consumer generates a cryptographically random nonce and requests fresh evidence.
3. The confidential worker generates or exposes an ephemeral CX execution key whose private half never leaves the protected boundary.
4. Platform evidence binds the nonce, execution public key, runtime measurement, configuration/security state and expiry.
5. A verifier appraises the evidence against current endorsements, reference values and policy.
6. The consumer appraises the result, including freshness, key binding, TCB status, debug state, CPU/GPU coverage and accepted measurement.
7. IICP applies ordinary policy eligibility and obtains the route ticket for the same candidate.
8. The consumer encrypts the existing IICP-CX payload to the attested execution key.
9. The untrusted shell forwards ciphertext. Only the confidential worker decrypts, executes and encrypts the response.
10. The consumer verifies that response context and routing evidence correspond to the selected attested execution.

If execution privacy is required, any missing, invalid, stale, replayed, downgraded or key-mismatched evidence rejects the candidate. Fallback to ordinary CX is allowed only when the caller explicitly authorized that weaker mode.

## Can the current CX envelope survive?

Probably, but this must be proven. The current envelope already accepts a recipient X25519 public key. If the provider advertises or returns a fresh attestation-bound X25519 execution key, the payload encryption construction may remain unchanged.

Potential changes are more likely in:

- capability/profile negotiation;
- the fresh attestation request and response;
- verifier policy and evidence adapters;
- route context that binds the selected node/profile/key;
- key lifetime and replay rules;
- conformance fixtures.

The profile must test whether the existing associated data binds enough request context and whether a route-ticket or task-ID binding is needed. It must not claim “no CX change” until cross-task substitution and replay tests pass.

## Capability, policy and evidence placement

| Information | Placement |
|---|---|
| supports attested confidential execution | additive, stable capability/profile advertisement |
| supported evidence profiles and protected workload classes | capability/profile advertisement |
| attestation request location or negotiated method | profile metadata, subject to endpoint-safety review |
| current nonce, quote, measurement and execution key | fresh point-to-point evidence; not a directory record |
| accepted TCB, debug, runtime and CPU/GPU policy | consumer/verifier policy |
| execution privacy required/optional/forbidden fallback | client routing/data-handling policy |
| verification result reference | local evidence record and possibly a redacted receipt reference |

Directory assertions remain claims used to find candidates. They are not proof that the current execution is confidential.

## Key lifecycle

The safest first prototype uses an ephemeral execution key generated inside the protected worker and bound to a fresh consumer nonce. Per-task keys minimize replay and continuity risk but make attestation expensive; per-boot or short-lived session keys reduce cost but require strict expiry, nonce binding and revocation behavior. The prototype should compare these choices rather than persisting today's static CX private key into the CVM.

Private execution keys must never be exported to the host. Sealing may support restart continuity, but it expands rollback and TCB policy. The first prototype should prefer ephemeral generation and no host-readable persistence. Restart invalidates prior evidence and requires fresh verification.

## Runtime measurements and supply chain

An acceptable platform quote is necessary but not sufficient. The consumer must know which software and configuration the measurement represents. The measurement policy should cover at least:

- confidential worker and base image;
- kernel/initrd or equivalent measured launch components;
- model runtime and relevant dynamic libraries;
- model identity and serving configuration where required;
- debug and crash-dump state;
- logging and plugin/tool configuration;
- CPU-only versus CPU-plus-GPU protection;
- network egress policy if it affects the promise.

Exact binary measurements may be brittle. A signed execution-profile manifest tied to reproducible images and reference values may be more manageable, but it adds supply-chain governance. Hardware attestation must not be described as proving source-code correctness.

## Metadata and limitations

Even a successful profile may expose node and provider identifiers, network addresses, intent, task and ticket identifiers, timing, ciphertext length, duration, model choice, resource usage and directory queries. Traffic analysis, denial of service, rollback, compromised firmware, verifier compromise, side channels and malicious allowed runtime code remain threats. The final specification must publish a precise threat model and accepted residual risks.

Attestation evidence itself may contain device-identifying information. The profile should prefer normalized attestation results and short-lived pseudonymous references where possible, limit directory publication, and assess correlation risk before exposing hardware identifiers.

## Component gap analysis

| Component | Current state | Required if prototype succeeds |
|---|---|---|
| IICP-CX | request and response confidentiality to selected executor | prove ephemeral attestation-bound recipient-key reuse; add no new envelope field unless required |
| Rust consumer | policy filtering, CX, ticketed dispatch | challenge, verifier adapters, fail-closed policy and correlation |
| Rust provider | same-process persistent key and decryption | confidential-worker boundary and host ciphertext forwarder |
| Python/TypeScript | CX parity | later verifier/provider parity after Rust proof |
| Browser consumer | can encrypt CX | may verify supported evidence, subject to bundle size and trust-root constraints |
| Browser provider | local/browser execution | should advertise unsupported unless a credible browser attestation mechanism exists |
| Directories | additive profiles/capabilities | store stable support descriptors only; preserve unknown-field compatibility |
| Route tickets/receipts | selected-route evidence | determine minimal profile/key/result correlation without hardware identifiers or payload data |
| Conformance runner | CX and dispatch vectors | add vendor-neutral negative vectors plus adapter-specific evidence tests |

## Required security tests

Before any implementation claim, test:

- valid evidence and accepted reference values;
- bad signature, wrong trust root and revoked/expired endorsement;
- stale evidence, wrong nonce and replay;
- execution key substitution and proof-of-possession failure;
- changed runtime measurement, insecure debug state and unacceptable TCB;
- CPU attested while the GPU or plaintext backend remains unprotected;
- host-forwarded plaintext or logging outside the boundary;
- capability advertised while fresh attestation is unavailable;
- directory tampering and malicious relay;
- downgrade to ordinary CX;
- provider restart and key rotation;
- concurrent clients and cross-task replay;
- response-context substitution;
- verifier outage without silent acceptance.

Platform fault and side-channel testing remains vendor- and deployment-specific; it cannot be replaced by shared JSON vectors.

## Existing work and issue disposition

| Area | Action | Reason |
|---|---|---|
| June 2026 confidentiality research | **REUSE and supersede where more precise** | It correctly identified local-first, TEE-next and FHE-later. |
| Attested execution privacy | **OPEN one focused IICP research umbrella** | No open issue owns the threat model, RATS/EAT mapping, CX key binding and prototype gate. |
| Layered substrate (#54) | **UPDATE** | Execution privacy should reuse capabilities, policy, evidence and dispatch rather than form a parallel protocol. |
| Registry profile (#55) | **UPDATE** | Only stable support descriptors belong in discovery; fresh evidence does not. |
| Policy/data handling (#56) | **UPDATE** | Required execution privacy must filter and fail closed with no implicit downgrade. |
| Route ticket/receipt (#58) | **MONITOR** | Add correlation only if the prototype proves it necessary; do not copy quotes into receipts. |
| DID/VC crosswalk (#63) | **UPDATE** | Operator identity and RATS workload evidence are distinct; VC is not a substitute for platform attestation. |
| IETF security/privacy (#45) | **UPDATE LATER** | Document the distinction and limitations if a profile is adopted; do not imply current support. |
| SDK/directory implementation children | **DEFER** | Create only after threat model, profile and a hardware-backed feasibility prototype pass. |
| FHE/MPC/private CIP | **RESEARCH LATER** | Keep separate from the first confidential-execution profile. |

## Phased roadmap

### Phase 0: threat model and feasibility

- establish the research umbrella;
- define protected data, attackers, metadata and residual risks;
- select one CPU confidential-VM target and verifier path;
- prove fresh nonce plus ephemeral CX key binding with a minimal measured worker;
- decide whether the current CX envelope and route context are sufficient.

### Phase 1: pre-normative vendor-neutral profile

- define RATS roles, evidence/result profiles, capability descriptor and fail-closed policy;
- define key lifetime, measurement, TCB and verifier trust rules;
- publish negative vectors that do not depend on proprietary quotes;
- keep the profile experimental and optional.

### Phase 2: Rust CPU prototype

- split untrusted shell from confidential worker;
- keep decryption, parsing, inference and response encryption inside a measured CVM;
- support one reviewed AMD SEV-SNP or Intel TDX adapter;
- run replay, downgrade, restart and host-plaintext tests.

### Phase 3: CPU-plus-GPU prototype

- use a supported confidential GPU and protected CPU/GPU link;
- appraise composite evidence;
- prove that tokenizer, runtime, model, KV cache and outputs remain inside the boundary;
- benchmark latency and operational cost.

### Phase 4: interoperability decision

- decide whether Python/TypeScript consumers need verifier parity;
- add directory capability parity and standalone conformance evidence;
- require external security review before any production claim.

### Separate research track

- FHE generative inference;
- HE/MPC private Transformer inference;
- purpose-built private CIP.

These paths should become IICP providers only when they expose a stable execution boundary. IICP should not absorb their cryptographic runtimes.

## Smallest backward-compatible extension

The smallest extension is an optional, negotiated capability and evidence profile that lets a candidate declare support for attested confidential execution, lets the consumer request fresh platform evidence bound to a nonce and ephemeral CX recipient key, and requires the consumer to appraise that evidence before ordinary IICP-CX encryption and ticketed dispatch. Stable descriptors may pass through existing additive capability mechanisms; fresh evidence stays point-to-point. Ordinary CX and non-confidential providers remain unchanged. Required execution privacy fails closed and never silently downgrades.

That answer is technically plausible, but it is not implementable as a trustworthy public claim until the threat model, verifier trust, runtime measurement, key binding, hardware TCB and full plaintext boundary are explicit and tested.

