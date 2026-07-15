# IICP Endpoint Security Profile v1

Status: pre-normative implementation profile  
Tracking: iicp.network #667

## Purpose

Prevent a directory-supplied provider hostname from reaching loopback, private,
link-local, metadata, reserved, or otherwise non-public addresses through DNS
resolution, rebinding, or redirects. This profile applies to consumer-to-provider
HTTP(S) dispatch. It does not alter directory discovery or expose resolver data.

## Required behavior

1. Parse the provider URL and allow only HTTP or HTTPS without user information.
2. Resolve the hostname before dispatch. Every returned address MUST satisfy the
   active network policy; a mixed public/prohibited answer set is refused.
3. Connect to one address from that validated set without a second uncontrolled
   lookup. HTTP Host, TLS SNI, and certificate verification use the original host.
4. Automatic redirects are disabled. A client MAY follow at most three same-origin
   307/308 redirects only after repeating steps 1-3 for each target. Cross-origin
   and other redirects fail so provider credentials and payloads cannot be forwarded
   to a different authority.
5. Resolver failure, an empty answer set, invalid mapped addresses, and unsupported
   pinning behavior fail closed for that provider candidate.
6. Private-network providers require explicit local operator opt-in. This setting
   MUST NOT be inferred from directory data or widened by fallback behavior.
7. Public receipts and directory output MUST NOT include raw endpoints, resolved
   addresses, resolver errors, or connection details.

## Compatibility

This profile strengthens the local connection path and adds no wire fields. A
client that cannot bind the connection to a validated address MUST NOT claim this
profile. Existing lexical endpoint checks remain an early rejection optimization,
not the security boundary.

## Fixture

`fixtures/endpoint-security-v1.json` defines the portable address and hostname
policy vectors. The fixture is pre-normative until all maintained SDKs pass policy,
redirect, pinning, and Docker rebinding tests.
