# IICP peer-transport evidence matrix

**Status:** informative review aid  
**Draft:** `draft-roble-iicp-peer`  
**Protocol baseline:** IICP 1.9 wire compatibility; suite release 1.10.13

This matrix connects each requirement class in the peer-transport candidate to
public specifications, fixtures and implementation tests. The Internet-Draft
remains the text under review. An implementation or test can show that a rule
is implementable, but it cannot redefine the rule.

## Evidence classes

| Draft section | Requirement class | Public protocol evidence | Executable or implementation evidence |
| --- | --- | --- | --- |
| Protocol Scope | Separation of route selection from task execution | [`iicp-core.md`](../../spec/v1.9/iicp-core.md), [`iicp-framing.md` §13.5](../../spec/v1.9/iicp-framing.md#135-directory-control-plane-constraint) | The maintained SDK repositories expose peer invocation independently of the PHP and Rust directory repositories; the public repository roles are listed in [`public-repositories.json`](../../ecosystem/public-repositories.json). |
| Connection Establishment | TLS, peer authentication and route distrust | [`iicp-framing.md` §9](../../spec/v1.9/iicp-framing.md#9-security-considerations), [`iicp-core.md`](../../spec/v1.9/iicp-core.md) | Consumer/provider security and negative-path tests in the [Rust](https://github.com/RobLe3/iicp-client-rust), [Python](https://github.com/RobLe3/iicp-client-python) and [TypeScript](https://github.com/RobLe3/iicp-client-typescript) SDKs. |
| Frame Format | Twelve-octet header, network-order length and allocation limits | [`iicp-framing.md` §§1-2](../../spec/v1.9/iicp-framing.md#1-binary-frame-format) | Canonical [`native-framing-v1.json`](../../research/native-ai-infrastructure/fixtures/native-framing-v1.json), its [digest manifest](../../research/native-ai-infrastructure/fixtures/native-framing-fixture-manifest-v1.json), and [`check_native_framing_fixtures.py`](../../tools/check_native_framing_fixtures.py). |
| Messages | INIT/ACK, CALL/RESPONSE, PING/PONG and CLOSE behavior | [`iicp-framing.md` §§3-4 and 8](../../spec/v1.9/iicp-framing.md#3-message-type-table) | The shared native-framing fixture is consumed by all three maintained SDKs through their `native_framing_fixture` tests. |
| CBOR Encoding | Deterministic CBOR, bounded schemas and prohibited indefinite lengths | [`iicp-cbor-wire.md`](../../spec/v1.9/iicp-cbor-wire.md), [`iicp-framing.md` §4](../../spec/v1.9/iicp-framing.md#4-cbor-payload-encoding) | Canonical framing fixture plus SDK-local decoding/validation tests. `run_native_framing_conformance.sh` verifies byte-identical fixture copies before running those tests. |
| Timeouts, Cancellation, and Replay | Timeout is not cancellation; task identity is scoped; conflicting reuse fails | [`iicp-service-lifecycle-profile.md`](../../spec/v1.9/iicp-service-lifecycle-profile.md), [`iicp-framing.md` §4.4](../../spec/v1.9/iicp-framing.md#44-response-message-schema-0x06) | `native_call_identity` and `native_response_sequence` tests in each maintained SDK. Confirmed cancellation remains outside the candidate unless a lifecycle profile is negotiated. |
| Error Handling | Distinct malformed-input classes, pre-dispatch rejection and bounded diagnostics | [`iicp-core.md` §7](../../spec/v1.9/iicp-core.md), [`iicp-framing.md` §§9.6-9.7](../../spec/v1.9/iicp-framing.md#96-malformed-frame-handling--disposition-table) | Parser and framing negative tests in maintained SDKs; release-integrity and fixture checks in this repository. |
| Security Considerations | Downgrade, replay, endpoint, relay and resource-exhaustion boundaries | [`iicp-core.md`](../../spec/v1.9/iicp-core.md), [`iicp-framing.md` §9](../../spec/v1.9/iicp-framing.md#9-security-considerations), [`privacy-adversary-and-trust-model.md`](../../docs/security/privacy-adversary-and-trust-model.md) | [`SECURITY_PRIVACY_OPERATIONAL_CONSIDERATIONS_2026-08-13.md`](../SECURITY_PRIVACY_OPERATIONAL_CONSIDERATIONS_2026-08-13.md) records implemented, experimental and future evidence separately. |
| Privacy Considerations | Directory bypass, executor visibility and metadata leakage | [`iicp-confidentiality.md`](../../spec/v1.9/iicp-confidentiality.md), [`privacy-adversary-and-trust-model.md`](../../docs/security/privacy-adversary-and-trust-model.md) | IICP-CX and relay tests are supporting project evidence only. They do not change the candidate's statement that an ordinary selected executor sees plaintext. |
| IANA Considerations | No current assignment or registration claim | [`iicp-framing.md` §11](../../spec/v1.9/iicp-framing.md#11-iana-considerations), [`STANDARDS_READINESS.md`](../STANDARDS_READINESS.md) | [`build_internet_draft.sh`](../../tools/build_internet_draft.sh) fails if the source omits the no-request statement or describes TCP port 9484 as assigned. |

## Path and platform coverage

### Direct and relay-carried paths

The peer payload normally travels directly between consumer and provider. An
explicitly selected relay may carry the same payload, but it is then on the
transport path. Relay use does not move the directory onto the payload path and
does not authenticate the provider. End-to-end payload confidentiality through
a relay requires a separately negotiated confidentiality mechanism whose keys
remain outside relay control.

Relay operation is experimental and is not used as evidence that the minimal
peer transport is independently deployed or operationally stable.

### Browser limitation

The browser implementation is public and useful interoperability evidence for
HTTP/Web platform mappings. A normal browser does not expose a raw TCP socket
API, so the browser node is **not** evidence for the native TLS-over-TCP framing
path described by this candidate. Browser support does not change the native
transport requirements.

### Maintained implementation set

The Rust, Python and TypeScript SDKs are maintained by the same project. Their
agreement is cross-language parity evidence, not an independent implementation.
The PHP and Rust directory projects implement the control plane and are not
additional peer-transport implementations. The current public component list
and roles are machine-readable in [`public-repositories.json`](../../ecosystem/public-repositories.json).

## Reproduction

From a clean checkout with the documented toolchains:

```bash
python3 tools/check_native_framing_fixtures.py \
  --copy ../iicp-client-rust/tests/fixtures/native-framing-v1.json \
  --copy ../iicp-client-python/tests/fixtures/native-framing-v1.json \
  --copy ../iicp-client-typescript/tests/fixtures/native-framing-v1.json
./tools/run_native_framing_conformance.sh

bundle install --gemfile standards/ietf/Gemfile
python3 -m venv .venv-ietf
.venv-ietf/bin/pip install -r standards/ietf/requirements.txt
PATH=".venv-ietf/bin:$PATH" bundle exec --gemfile standards/ietf/Gemfile \
  tools/build_internet_draft.sh
```

The review-bundle builder packages the source, rendered XML/text/HTML, this
matrix and the public review dependencies with a digest manifest. It does not
submit the draft or make an IANA request.
