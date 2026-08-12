# Execution-privacy binding fixture

This research fixture tests the consumer-side boundary proposed in
[IICP #136](https://github.com/RobLe3/IICP/issues/136): a fresh challenge,
an ephemeral IICP-CX recipient key, and an accepted runtime measurement must
be bound into one signed attestation result before the consumer releases a
protected task.

The fixture uses synthetic, verifier-signed results. It is not AMD SEV-SNP,
Intel TDX, EAT, or production evidence. It cannot prove that a private key
remained inside confidential hardware. Its purpose is narrower: make the
relying-party checks and failure order executable before hardware-specific
evidence is introduced.

## Covered checks

The vectors cover a valid result and fail-closed rejection for:

- an invalid verifier signature;
- the wrong consumer nonce;
- expired evidence;
- execution-key substitution;
- an unaccepted runtime measurement;
- debug mode;
- an unaccepted TCB state;
- an incomplete protected boundary; and
- attempted downgrade to ordinary IICP-CX.

The signed result is intentionally content-free. It carries no prompt,
response, node endpoint, route ticket, hardware serial number, or raw vendor
quote.

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
python3 tools/test_execution_privacy_feasibility.py
```

The JSON canonicalization in this fixture is a deterministic research
encoding. A future profile must select and version its actual EAT/COSE or
attestation-result encoding before interoperability claims are made.

Primary implementation references:

- [Linux SEV guest API](https://docs.kernel.org/virt/coco/sev-guest.html)
- [AMD SEV-SNP platform attestation using VirTEE](https://www.amd.com/content/dam/amd/en/documents/epyc-technical-docs/tuning-guides/58217_amd-epyc-9004-ug-platform-attestation-using-virtee-snp.pdf)
- [VirTEE `snpguest` v0.9.2](https://github.com/virtee/snpguest/tree/v0.9.2)
