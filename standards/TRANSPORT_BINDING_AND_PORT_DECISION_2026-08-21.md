# IICP transport binding and service-port decision

**Decision date:** 2026-08-21  
**Amended:** 2026-08-28
**Status:** reviewed project decision; no IANA request; native TCP excluded from the current stable baseline

## Decision

IICP Core remains independent of transport, port and locator. HTTP projections
and native framing are bindings. The native framed TCP binding remains optional
and project-draft. It is not required for selection and eligibility
interoperability and is not promoted to a general conformance requirement.

For the coordinated stable baseline, the supported HTTP application binding is
the qualification target. Native framed TCP is explicitly excluded from stable
and production claims. Maintained SDKs compile its framing and connection code
for compatibility and research, but provider listeners require the explicit
development opt-in `IICP_ENABLE_EXPERIMENTAL_NATIVE_TCP=1`. Compilation, fixture
parity or a configured `transport_endpoint` is not production-security evidence.

The project will not request a service-name or port registration now. Port 9484
is an unassigned local convention for the implemented native TCP lane. It is
not reserved or assigned to IICP. No UDP request is justified because IICP has
no maintained interoperable QUIC implementation.

Port 443 fallback means using an existing application transport correctly, such
as HTTPS, HTTP/2, WebSocket where specified by a binding, MCP or A2A. IICP does
not claim an ALPN identifier and must not tunnel an unregistered native protocol
through port 443 while presenting it as ordinary HTTPS.

## Reproducible supported-lane evidence

The bounded native evidence is a framing-compatibility test, not a network
performance benchmark:

```bash
git clone https://github.com/RobLe3/IICP.git
# Place clean iicp-client-rust, iicp-client-python and
# iicp-client-typescript checkouts beside it.
cd IICP
bash tools/run_native_framing_conformance.sh
```

On 21 August 2026 this command verified fixture digest
`e73a871c069f194c42716f462d2bde04fb79d769e1e98249c2d17c9af50bcfc1`
and passed two canonical framing tests in each maintained SDK. The fixture
covers encoding, decoding, invalid magic, truncation, reserved-byte behavior and
unknown flags. It does not open a TCP connection or test TLS, authentication,
stream multiplexing, NAT traversal, QUIC, HTTP/3 or WAN behavior.

On 28 August 2026 the fixture was extended with the finite task-type boundary
and explicit stable exclusion disposition. Its current digest is
`02cc7bfbd3c238191ca3961aa03d09f143a51a43397e056d496977e5a9bf0471`.
The additional metadata changes no framing bytes and adds no production claim.

The current maintained HTTP lane has implementation and integration coverage in
the SDK, node and directory repositories. Its evidence is repository-specific
rather than one artificial cross-transport benchmark. HTTP and native framing
do not yet share a harness that controls connection setup, TLS, payload shape,
streaming, cancellation, concurrency and network shaping. Therefore this record
makes no latency, throughput or efficiency comparison between them.

Reference environment for the reproduced framing run:

| Component | Value |
|---|---|
| Host | Apple M3 Max, arm64 |
| OS | macOS 26.6.2, Darwin |
| Rust | 1.97.1 |
| Python | 3.14.7 |
| Node.js | 26.7.0 |
| Fixture | `native-framing-v1.json`, digest above |

Different supported toolchain versions should produce the same fixture bytes.
The environment is reported for reproduction, not as a portability claim.

## Binding evidence matrix

| Lane | Current evidence | Supported conclusion | Unsupported conclusion |
|---|---|---|---|
| HTTPS/HTTP application projection | Maintained client, node and directory paths plus repository integration tests | A current interoperable application binding | Comparative superiority, HTTP/3 support or universal streaming behavior |
| Native framed TCP | Canonical bytes across three SDKs; explicitly enabled development listeners | Experimental project binding with cross-SDK framing compatibility; excluded from the current stable/production baseline | Native TLS, production support, two independent network implementations, fixed-port need or standards readiness |
| Native QUIC/UDP | Descriptive draft text and local socket experiments only | Research input | Interoperability, production support, UDP registration or congestion-behavior evidence |
| MCP and A2A | Published adjacent protocols plus IICP binding/crosswalk work | Execution can follow IICP selection when an application supports the binding | That MCP/A2A are transports below IICP or require IICP |
| Dynamic signed endpoint | Current directory route metadata and short-lived ticket work | Ports and locators can be carried without changing Intent | That a permanent fixed port is unnecessary in every deployment |
| DNS SRV/SVCB/HTTPS | Standards-based architectural option; no maintained IICP discovery binding | Candidate future bootstrap/binding research | Current IICP interoperability or reason to alter Core |
| ALPN over 443 | No registered IICP ALPN and no maintained mapping | Existing registered application protocols may use 443 under their own rules | Native IICP-over-443 or ALPN interoperability |
| BPv7/DTN | Phase 8 reservation only | Future binding remains architecturally possible | Present support or a Core requirement |

## Dedicated port compared with alternatives

A dedicated service port can simplify a known native listener and make packet
classification explicit. It also adds firewall, service-registration and
operational obligations. Current IICP deployments already carry signed or
policy-checked endpoint metadata, use dynamic tunnel endpoints and support HTTP
bindings. NAT mechanisms and port auto-increment prove deployment flexibility;
they do not prove that a permanent service port is required.

DNS SRV/SVCB/HTTPS records could publish service locators, while signed dynamic
endpoints can bind a selected route to a short lifetime. These mechanisms solve
different discovery and trust problems. Neither is implemented as a complete
IICP binding today, so this decision does not select one as a replacement.

The fixed-port question can be reopened only with evidence that independent
native implementations need stable rendezvous that cannot be met by advertised
endpoints or existing application transports. The comparison must include
firewall behavior, service discovery, key and endpoint rotation, virtual
hosting, load balancing and operational recovery.

## QUIC and HTTP/3 disposition

The framing specification contains a draft QUIC mapping, but maintained SDK
fixture parity proves only the frame representation. A UDP socket bind or QUIC
library experiment does not prove an IICP application mapping. Until two
interoperable implementations demonstrate stream mapping, connection lifecycle,
error handling, cancellation, migration, amplification controls and congestion
behavior, QUIC remains unsupported research.

HTTP/3 support in an HTTP stack would not automatically validate the native
QUIC mapping. They are separate application bindings and must be reported
separately.

## Reopening and IANA gates

A later TCP service-port proposal requires:

- a concrete fixed-port operational need;
- at least two interoperable native network implementations;
- public comparison with dynamic signed endpoints, DNS service discovery and
  existing application transports;
- security and operational review;
- the governance and submission authority required by IICP #43 and #47.

A UDP request additionally requires a maintained QUIC mapping and corresponding
interoperability and congestion evidence. No port block is planned. Any IANA
packet remains a separate, explicitly authorized action.

## Compatibility and deployment

This decision changes no endpoint schema, wire bytes, release or live deployment.
Existing explicitly enabled development uses of 9484/TCP remain valid as a
provisional project convention. Maintained providers must not mount or advertise
the native listener by default, must advertise the actual endpoint when enabled,
and must not describe 9484 as assigned. An HTTPS proxy or tunnel does not prove a
native TLS path and must not be rewritten or advertised as `iicpsec://`.
