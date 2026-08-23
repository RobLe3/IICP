# Verified Local Directory Discovery Profile

**Version:** 0.1.0-draft<br>
**Status:** pre-normative; no implementation or default enablement<br>
**Profile identifier:** `urn:iicp:profile:local-directory-discovery:v1`<br>
**Related issue:** IICP #39

## 1. Purpose

This Profile lets a native IICP client or operator directory discover candidate
IICP directories on its local link through mDNS and DNS-Based Service Discovery
(DNS-SD). Discovery answers only:

> Which local endpoints claim to offer an IICP directory service?

It does not answer whether an endpoint is trusted, authorized for the current
operating mode, synchronized, healthy or eligible to serve a request. A
candidate enters the normal identity, trust, policy and selection pipeline
before any credential or protected request is sent.

The mechanism follows RFC 6762 and RFC 6763. It is an optional bootstrap
Profile, not IICP Core, a federation transport, provider discovery, endpoint
authentication or a replacement for explicit configuration.

## 2. Service and records

The first Profile uses the service type:

```text
_iicp-dir._tcp.local.
```

An advertiser publishes the normal DNS-SD PTR, SRV and TXT record set. The
instance label is display text and MUST NOT be treated as identity. SRV supplies
only a candidate host and port. Address records remain link-local observations
and MUST NOT be exported through directory federation.

TXT contains small bootstrap hints only:

| Key | Requirement | Meaning |
|---|---|---|
| `pv` | required, value `0` | local-discovery Profile revision |
| `path` | required | relative HTTPS descriptor path; v0 requires `/.well-known/iicp-directory.json` |
| `transport` | required, value `https` | descriptor and directory transport |
| `did` | optional | claimed directory DID, used only as a pre-verification hint |
| `role` | optional | `seed`, `replica` or `standalone`, used only as a hint |

Unknown keys are ignored and retained only in bounded diagnostic state. A TXT
record is invalid if its aggregate encoded data exceeds 512 bytes, repeats a
required key, contains an absolute descriptor URL, or contains credential,
token, node, model, Intent, Capability, topology or federation-state data.

The descriptor is fetched from the SRV candidate using HTTPS and the fixed
relative path. No credential, membership assertion or bearer token is sent
during this fetch. Redirects are rejected. Implementations apply ordinary SSRF
and interface-scope controls and MUST NOT broaden an observed link-local
candidate into a globally trusted locator.

## 3. Directory descriptor

`/.well-known/iicp-directory.json` is a time-bounded signed statement containing:

- schema identifier `iicp.local-directory-descriptor.v0`;
- this Profile identifier and version;
- stable directory identifier and DID;
- advertised role;
- one or more HTTPS API endpoints;
- issuance and expiry times;
- RFC 8785 JCS canonicalization;
- Ed25519 key identifier and signature.

The signature covers the descriptor with the `signature` member omitted and the
domain-separation prefix `IICP-LOCAL-DIRECTORY-DESCRIPTOR-V0\n`. The signing key
must resolve through the asserted directory DID or an already configured trust
relationship. TLS certificate validation and descriptor signature validation
are separate requirements. A valid signature proves who issued the statement;
it does not establish that the issuer is trusted for the current mode.

An API endpoint that differs from the SRV origin is accepted only when it is
covered by the verified descriptor and passes local SSRF, address-scope and
operator policy. The selected API endpoint is never copied from unsigned TXT
data.

## 4. Resolution and trust order

Directory resolution uses this order:

1. explicit application or operator configuration;
2. verified local DNS-SD candidates, only when this Profile is enabled;
3. configured and authenticated replica/operator bootstrap sources;
4. a later accepted DNS or well-known operator-pool Profile;
5. public Genesis fallback, only in `public` mode or an explicit `custom` mode.

Finding a candidate never changes that order. Explicit configuration suppresses
multicast discovery for the request unless the operator separately asks for a
diagnostic scan.

Trust is mode-specific:

| Mode | Candidate acceptance |
|---|---|
| `public` | The descriptor must validate to a configured directory trust anchor. A `standalone` directory may use an explicit, interactive first-use approval that persists the exact DID/key; silent TOFU is forbidden. |
| `private` | The DID and authority relationship must match the configured trust domain. Public fallback is forbidden. |
| `federated_private` | The candidate must be a configured local authority or carry a currently valid, signed federation relationship allowed by policy. |
| `local_only` | No multicast query, descriptor fetch or external fallback is permitted. |
| `custom` | Discovery, trust anchors and fallback are explicit. Omitted security-sensitive settings are configuration errors. |

A claimed TXT `did` that differs from the signed descriptor is rejected. An
unknown DID, valid but untrusted signature, expired descriptor or stale
federation relationship is not an accepted candidate.

## 5. Timing, cache and selection

The default DNS-SD collection window is 1,000 milliseconds and the configurable
hard maximum is 3,000 milliseconds. Timeout, multicast-disabled and no-candidate
outcomes continue to the next permitted resolution source without delaying
startup further. Failure is final when the active mode forbids every later
source.

Cached candidate state records its source interface, DNS name, descriptor
digest, verified DID, trust basis, observation time and expiry. It expires at
the earliest of DNS TTL, descriptor expiry and five minutes. Cache presence
never extends certificate, DID key, membership, federation or policy validity.
Revocation and trust-policy changes invalidate affected entries immediately.

After trust and policy filtering, an application-defined preference may choose
among candidates. Without one, implementations use the deterministic tuple
`(directory_did, normalized_api_endpoint)`. Latency, instance label and arrival
order are not implicit trust or ranking signals.

## 6. Applicability and compatibility

The first implementation scope is native clients and operator directories.
Browser clients retain explicit configuration or use an already trusted local
bridge because ordinary browser APIs do not expose general mDNS/DNS-SD browsing
safely. This Profile does not require browser-specific network privileges.

An unknown required Profile fails closed through existing Profile negotiation.
An unknown optional Profile preserves ordinary behavior only when the operating
mode and local policy allow it. Public behavior is unchanged when the Profile is
absent or disabled.

No released Intent, Capability, Core frame, directory API or provider record is
changed. Directory advertisement and native-client consumption require separate
component issues after this draft and its fixtures are accepted.

## 7. SSDP disposition

SSDP remains part of UPnP/IGD reachability discovery in implementations that use
it. It is not an IICP directory-discovery mechanism in this Profile. No target
environment has been evidenced where SSDP is necessary and DNS-SD is
unavailable, while adding it would create another unauthenticated multicast
input and service vocabulary.

The v0 decision is therefore **defer/reject for directory discovery**. A later
proposal needs concrete interoperability evidence, an independently verified
identity path and the same mode/fallback protections. An SSDP response never
establishes IICP directory identity or authorization.

## 8. Security and privacy considerations

Threats include spoofed advertisements, descriptor substitution, replay,
malicious redirects, downgrade to public Genesis, local-network tracking,
interface confusion, oversized TXT data, DNS rebinding, and leakage of private
topology. The Profile limits those risks by keeping TXT data non-sensitive,
fetching without credentials, rejecting redirects, signing descriptors,
requiring independent trust, bounding time and cache state, and prohibiting
link-local propagation.

mDNS reveals that a device is seeking or advertising a local IICP directory to
observers on the link. Operators in sensitive environments can disable the
Profile. Private domain identifiers, membership, provider inventory, supported
models and capability details MUST NOT appear in multicast data.

This Profile does not provide anonymity, payload confidentiality, directory
availability, authorization to discover protected providers, dispatch authority
or proof that an advertised directory is synchronized.

## 9. Conformance boundary

The canonical draft artifacts are:

- `fixtures/local-directory-discovery-v0.json`;
- `schemas/local-directory-discovery-v0.schema.json`;
- `tools/test_local_directory_discovery.py`.

They cover explicit precedence, valid pinned candidates, spoofing, stale state,
deterministic selection, private/local-only isolation, timeout fallback, unknown
TXT keys, secret-bearing and oversized records, browser exclusion and the SSDP
disposition. Passing them does not claim an implementation or production
advertisement.

## 10. References

- RFC 6762, *Multicast DNS*: <https://www.rfc-editor.org/rfc/rfc6762>
- RFC 6763, *DNS-Based Service Discovery*: <https://www.rfc-editor.org/rfc/rfc6763>
- RFC 8785, *JSON Canonicalization Scheme*: <https://www.rfc-editor.org/rfc/rfc8785>
