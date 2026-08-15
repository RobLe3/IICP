# Security policy

## Reporting a vulnerability

Do not disclose an unpatched vulnerability through a public issue. Use
[GitHub private vulnerability reporting](https://github.com/RobLe3/IICP/security/advisories/new)
or contact `community@iicp.network`. Include the affected protocol or component
version, minimal synthetic reproduction, expected security boundary and
observed impact.

Do not submit credentials, task payloads, production database contents,
operator records, private endpoints or personal data. Protocol reports should
use minimal synthetic reproductions and identify the affected version/profile.

## Scope and support

Security corrections target the latest published protocol suite and maintained
implementation release lines. Older releases may not receive backports. The
machine-readable repository and lifecycle list is
[`ecosystem/public-repositories.json`](ecosystem/public-repositories.json).

Protocol requirements, implementation behavior and deployment state have
separate version axes. A specification fix does not prove that every deployed
node has adopted it, and an implementation fix does not silently redefine the
normative protocol.

## Shared boundaries

The public [`privacy adversary and trust model`](docs/security/privacy-adversary-and-trust-model.md)
states the common directory, relay, provider, identity and metadata boundaries.
In particular, transport security does not hide plaintext from the selected
execution provider, and a directory response alone is not provider
authentication. Unsupported required security or confidentiality profiles must
fail closed.

After a correction can be disclosed safely, publish a sanitized issue,
advisory, test or release note sufficient for independent implementers to
understand the affected boundary and verify the fix. Do not publish private
incident records, credentials or personal development-method material.
