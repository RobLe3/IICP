# External conformance run guide

This guide is for an operator working outside the IICP repository family. It
produces reproducible **self-attested** evidence from a released runner artifact.
It does not grant access to a directory, elevate a result to independent
verification, or authorize a protocol-profile promotion.

## 1. Install a released artifact

Use an isolated Python 3.11+ environment and the runner wheel published for the
release you intend to report. Verify the artifact checksum from its release
record before installation.

```bash
python3 -m venv iicp-conformance-venv
. iicp-conformance-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'iicp-conformance[signing]==<released-version>'
iicp-conformance --help
```

If your environment requires an offline installation, replace the package name
with the verified local wheel path. Do not install from a moving branch or
unverified archive.

## 2. Produce and verify offline evidence

The offline profiles need no target directory and are the safe starting point.
They emit case identifiers and aggregate outcomes only.

```bash
for command in \
  verify-dispatch-ticket-fixture \
  verify-dispatch-ticket-trust-v2-fixture \
  verify-dispatch-ticket-trust-v2-semantics-fixture \
  verify-policy-refusal-fixture \
  verify-federation-chain-fixture
do
  iicp-conformance "$command" \
    --evidence-class self-attested \
    --output "$command.json"
  iicp-conformance verify "$command.json"
done
```

The v2 ticket and federation-chain profiles are pre-normative offline checks.
A passing result does not enable those profiles, create a trust store, prove
federation, or demonstrate a production deployment.

## 3. Optional loopback directory profiles

Run `directory-public-v1`, `directory-dispatch-v1`, or
`directory-lifecycle-v1` only against a disposable loopback directory and
database you control. The dispatch and lifecycle profiles can create temporary
registration state or route material. Never aim them at a shared production
directory unless its operator has separately authorized that test.

```bash
iicp-conformance run --profile directory-public-v1 \
  --target http://127.0.0.1:<port> --output directory-public.json
iicp-conformance verify directory-public.json
```

## 4. Publish responsibly

Before sharing a bundle, run `iicp-conformance verify` again and inspect it.
Do not publish credentials, signing keys, target URLs, node IDs, route data,
payloads, raw responses, private topology, or personal data.

Use evidence classes precisely:

- `self-attested`: you ran the tool and publish the result yourself.
- `project-verified`: the IICP project independently reran or reviewed the
  same result under documented conditions.
- `independent`: an operator outside the IICP repository family controls both
  the tested implementation and the result publication.

A signature proves the result bundle was signed by its declared result key; it
does not by itself make a result independent.
