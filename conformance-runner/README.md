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
.venv/bin/iicp-conformance verify-dispatch-ticket-fixture \
  --evidence-class project-verified --output ticket-result.json
.venv/bin/iicp-conformance verify-dispatch-ticket-trust-v2-fixture \
  --evidence-class project-verified --output ticket-trust-result.json
.venv/bin/iicp-conformance verify ticket-result.json
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
only against a disposable directory database. Policy-refusal and
federation-chain profiles remain tracked by issue #62 and must be added as
isolated profiles. The offline v1 ticket command covers only the published v1
vector set; it does not claim v2 trust-store, stateful-replay, or federation
behavior.

`verify-dispatch-ticket-fixture` is an offline profile over the canonical
`dispatch-route-ticket:v1` Ed25519 vectors. It verifies the signature, issuer,
audience, node, intent, expiry and malformed/tampered cases, then emits only
case names and aggregate outcomes. It does not output ticket material, claims,
routes or endpoint data. Install `.[signing]` before running it. It verifies
v1 route-disclosure semantics only: v1 does not claim stateful redemption or
signer-key revocation.

`verify-dispatch-ticket-trust-v2-fixture` is a separate **pre-normative**
offline profile over the canonical v2 Ed25519, key-status and local-replay
vectors. It emits only case identifiers and aggregate outcomes. It does not
enable v2 at runtime, persist a replay cache or trust bundle, distribute or
rotate keys, provide global single-use redemption, or prove federation
behavior. Install `.[signing]` before running it.

The loopback-only `directory-lifecycle-v1` profile registers a disposable node,
authenticates a heartbeat, refreshes the registration and rotates its token,
rejects the stale token, accepts the replacement token, and deregisters the
node. The runner substitutes only values captured from earlier successful
responses in the same run. It rejects unresolved variables before sending a
request and never writes captured node IDs or credentials to the result bundle.
The target must provide the fixture node's HTTPS health response in its
disposable test environment; the profile does not weaken endpoint validation.
