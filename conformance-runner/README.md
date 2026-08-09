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
.venv/bin/iicp-conformance verify-dispatch-ticket-trust-v2-semantics-fixture \
  --evidence-class project-verified --output ticket-trust-semantics-result.json
.venv/bin/iicp-conformance verify-policy-refusal-fixture \
  --evidence-class project-verified --output policy-refusal-result.json
.venv/bin/iicp-conformance verify-federation-chain-fixture \
  --evidence-class project-verified --output federation-chain-result.json
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
only against a disposable directory database. The offline profile commands are isolated evidence profiles. The offline v1
ticket command covers only the published v1 vector set; it does not claim v2
trust-store or stateful replay behavior.

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

`verify-dispatch-ticket-trust-v2-semantics-fixture` is a separate
**pre-normative** decision-table profile. It verifies strict-mode rejection of
a v1 fallback, explicit open-compat labeling, bundle rollback, key state,
claim, signature, and local-replay outcomes. It emits only case identifiers and
aggregate outcomes. It does not parse live tickets, alter v1 behavior, enable
v2, or make any runtime trust-store, federation, or independent-conformance
claim.

`verify-policy-refusal-fixture` is a separate **pre-normative** offline subset
of the canonical profile-compatibility fixture. It evaluates only cases that
declare `policy_refusal`, and emits only their case identifiers and aggregate
outcomes. It is not a general eligibility engine, live dispatch test, policy
attestation, or evidence that a provider enforces its declared policy.

The loopback-only `directory-lifecycle-v1` profile registers a disposable node,
authenticates a heartbeat, refreshes the registration and rotates its token,
rejects the stale token, accepts the replacement token, and deregisters the
node. The runner substitutes only values captured from earlier successful
responses in the same run. It rejects unresolved variables before sending a
request and never writes captured node IDs or credentials to the result bundle.
The target must provide the fixture node's HTTPS health response in its
disposable test environment; the profile does not weaken endpoint validation.

## Release-candidate and external-run boundary

Run `python3 conformance-runner/scripts/release_preflight.py` before proposing
a runner artifact. It builds the candidate locally, checks wheel and source
distribution metadata, then clean-installs the source, wheel and source
distribution from a temporary working directory. Each installation must run
and verify every bundled offline profile with `self-attested` content-free
output. The command does not publish an artifact or create independent
evidence.

An operator outside the IICP repository family may use a published artifact and
this README to submit a result. Select `independent` only when the operator
controls the implementation and result publication; a project-run or
project-hosted test remains `project-verified` or `self-attested`. Do not put
credentials, target URLs, node IDs, route data, payloads or personal data in a
published result bundle.

For a clean-environment installation, offline-first evidence, loopback safety
boundary and evidence-class decision, follow [the external run guide](EXTERNAL_RUN.md).
It is intentionally release-artifact based: it does not ask an external operator
to install a moving repository checkout.
