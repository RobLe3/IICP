# IICP standalone conformance runner

This preview runs a bounded public-directory black-box profile and emits a
content-free result bundle. It does not publish target URLs, response bodies,
credentials, node identifiers or task data. A project-run result is reproducible
evidence, not independent verification.

```bash
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/iicp-conformance run --target http://127.0.0.1:8010 --output result.json
.venv/bin/iicp-conformance verify result.json
```

Install `.[signing]` and provide a file containing a 32-byte Ed25519 private key
in hexadecimal form to add an RFC 8785/JCS Ed25519 signature. The key is read
locally and is never included in the result. Verification checks the schema,
fixture digest, test inventory, summary, prohibited-field boundary and signature;
use `--require-signature` when unsigned evidence is not acceptable.

The initial `directory-public-v1` profile covers public discovery validation,
SSRF refusal and unauthenticated credit and telemetry boundaries. Registration,
stateful lifecycle, ticket, replay, downgrade, policy-refusal and federation
profiles remain tracked by issue #62 and must be added as isolated profiles.
