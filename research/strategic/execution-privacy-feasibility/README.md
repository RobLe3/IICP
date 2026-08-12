# Execution-privacy feasibility evidence

This research fixture tests the consumer-side boundary proposed in
[IICP #136](https://github.com/RobLe3/IICP/issues/136): a fresh challenge,
an ephemeral IICP-CX recipient key, and an accepted runtime measurement must
be bound into one signed attestation result before the consumer releases a
protected task.

The [research profile](profile-v0.md) now fixes the next experiment's EAT/CWT,
COSE_Sign1, verifier-trust, route-binding and key-lifecycle choices. The fixture
uses synthetic, verifier-signed JSON results. It is not AMD SEV-SNP,
Intel TDX, EAT, or production evidence. It cannot prove that a private key
remained inside confidential hardware. Its purpose is narrower: make the
relying-party checks and failure order executable before hardware-specific
evidence is introduced.

## Covered checks

The 17 vectors cover a valid result and fail-closed rejection for:

- an invalid verifier signature;
- an untrusted verifier key;
- the wrong consumer nonce;
- expired evidence;
- future-dated evidence;
- replayed evidence;
- execution-key substitution;
- an unsupported execution key;
- an unaccepted runtime measurement;
- debug mode;
- an unaccepted TCB state;
- an incomplete protected boundary; and
- attempted downgrade to ordinary IICP-CX;
- the wrong consumer-session audience;
- a different selected candidate; and
- a different dispatch ticket.

The signed result is intentionally content-free. It carries no prompt,
response, node endpoint, route ticket, hardware serial number, or raw vendor
quote.

## Software composition proof

[`software_prototype.py`](software_prototype.py) generates a short-lived X25519
key, binds its public half into a synthetic result, verifies the result,
performs a preflight proof of possession, sends one encrypted task using the
existing IICP-CX envelope, validates an encrypted response, and retires the
key. The negative tests reject an unrelated private key and response-context
substitution.

The prototype is intentionally one process. A Python attribute is not a
confidential-computing boundary, so the result does not prove private-key or
plaintext containment against an operator. It only shows that a hardware-bound
key can fit the existing request and response cryptographic construction.

## Selected hardware feasibility target

The first hardware-backed proof should use an AMD SEV-SNP Linux confidential
VM. The worker would obtain a report through `/dev/sev-guest`, bind the digest
of the caller nonce and ephemeral X25519 execution key into the 64-byte
`REPORT_DATA` field, and use the VCEK certificate chain and current AMD KDS
material for appraisal. The reviewed verifier reference is VirTEE `snpguest`
`v0.9.2` (`dc7c8003d823856ab2156f30813bf7e565486564`).

This selection defines the next proof target; it does not claim that the
current development host or any public IICP node has SEV-SNP support. The
hardware gate still requires a representative confidential VM, current
firmware/TCB policy, reference measurements, and evidence that the private
execution key is generated and retained inside the measured worker.

## Run

The script requires Python `cryptography` and uses only a deterministic test
key. No production key is stored in the fixture.

```bash
python3 research/strategic/execution-privacy-feasibility/verify_vectors.py
python3 research/strategic/execution-privacy-feasibility/verify_vectors.py --check-generated
python3 research/strategic/execution-privacy-feasibility/software_prototype.py
python3 tools/test_execution_privacy_feasibility.py
```

The JSON canonicalization and Ed25519 wrapper in this fixture are deterministic
research encodings. The selected future representation is an EAT Claims-Set as
a CWT protected by COSE_Sign1 and carried as `application/eat+cwt`; actual CBOR
and COSE interoperability vectors remain a later pre-normative deliverable.

Primary implementation references:

- [Linux SEV guest API](https://docs.kernel.org/virt/coco/sev-guest.html)
- [AMD SEV-SNP platform attestation using VirTEE](https://www.amd.com/content/dam/amd/en/documents/epyc-technical-docs/tuning-guides/58217_amd-epyc-9004-ug-platform-attestation-using-virtee-snp.pdf)
- [VirTEE `snpguest` v0.9.2](https://github.com/virtee/snpguest/tree/v0.9.2)
- [RATS architecture, RFC 9334](https://www.rfc-editor.org/rfc/rfc9334.html)
- [Entity Attestation Token, RFC 9711](https://www.rfc-editor.org/rfc/rfc9711.html)
- [EAT media types, RFC 9782](https://www.rfc-editor.org/rfc/rfc9782.html)
- [CWT proof-of-possession keys, RFC 8747](https://www.rfc-editor.org/rfc/rfc8747.html)
- [COSE structures, RFC 9052](https://www.rfc-editor.org/rfc/rfc9052.html)
