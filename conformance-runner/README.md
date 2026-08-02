# IICP standalone conformance runner

This preview runs bounded directory black-box profiles and emits a
content-free result bundle. It does not publish target URLs, response bodies,
credentials, node identifiers or task data. A project-run result is reproducible
evidence, not independent verification.

```bash
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/iicp-conformance run --target http://127.0.0.1:8010 --output result.json
.venv/bin/iicp-conformance run --profile directory-dispatch-v1 \
  --target http://127.0.0.1:8010 --output dispatch-result.json
.venv/bin/iicp-conformance run --profile directory-lifecycle-v1 \
  --target http://127.0.0.1:8010 --output lifecycle-result.json
.venv/bin/iicp-conformance verify result.json
```

Install `.[signing]` and provide a file containing a 32-byte Ed25519 private key
in hexadecimal form to add an RFC 8785/JCS Ed25519 signature. The key is read
locally and is never included in the result. Verification checks the schema,
fixture digest, test inventory, summary, prohibited-field boundary and signature;
use `--require-signature` when unsigned evidence is not acceptable.

The `directory-public-v1` profile covers public discovery validation, SSRF
refusal and unauthenticated credit and telemetry boundaries. The
`directory-dispatch-v1` profile covers prompt-free ticket issuance and negative
policy/validation cases. It is restricted to loopback targets because a passing
case issues route material and may update aggregate adoption counters. Run it
only against a disposable directory database. Registration lifecycle, replay,
downgrade, canonical ticket verification and federation profiles remain tracked
by issue #62 and must be added as isolated profiles.

The loopback-only `directory-lifecycle-v1` profile registers a disposable node,
authenticates a heartbeat, refreshes the registration and rotates its token,
rejects the stale token, accepts the replacement token, and deregisters the
node. The runner substitutes only values captured from earlier successful
responses in the same run. It rejects unresolved variables before sending a
request and never writes captured node IDs or credentials to the result bundle.
The target must provide the fixture node's HTTPS health response in its
disposable test environment; the profile does not weaken endpoint validation.
