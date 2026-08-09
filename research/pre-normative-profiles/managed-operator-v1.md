# Managed operator profile v1

**Status:** pre-normative implementation profile; disabled by default  
**Tracking:** IICP #91

## Purpose

`urn:iicp:profile:managed-operator:v1` defines a fail-closed operating mode for
nodes whose identity, exposure and update lifecycle are administrator-managed.
It preserves the current convenience-oriented beta mode and changes no default.

The profile governs local node operation. It is not a directory trust claim,
remote-management protocol, update service, or permission to expose a node.

## Mode selection

Implementations expose `IICP_OPERATOR_PROFILE=convenience|managed` or an
equivalent explicit configuration field. Missing configuration selects
`convenience`. Unknown values fail before registration or listener startup.
Profile selection is local and MUST NOT be inferred from directory data.

## Managed-mode requirements

A managed node MUST fail before registration or listener startup unless:

1. provider registration and re-registration use fail-closed authentication;
2. persistent operator identity storage exists and rejects access by unrelated
   local users;
3. automatic update is disabled, unless the candidate is authenticated and
   digest-pinned and a verified rollback target exists;
4. automatic UPnP and tunnel exposure are disabled, unless the administrator
   explicitly approves each enabled exposure mechanism.

An implementation that cannot verify any required condition MUST reject
managed startup. It MUST NOT silently downgrade to convenience mode. Failure
output identifies only the portable reason code and remediation category; it
does not print credentials, identity material, paths, endpoints or update URLs.

## Portable decision input

The shared fixture uses these implementation-neutral booleans:

| Field | Meaning |
|---|---|
| `authentication_configured` | Registration ownership is configured to fail closed. |
| `identity_storage_protected` | The implementation verified its platform-specific storage policy. |
| `auto_update_requested` | Unattended update is enabled. |
| `update_authenticated` | The update source and artifact are authenticated and digest-pinned. |
| `rollback_verified` | A locally usable rollback target was verified. |
| `upnp_requested` | Automatic UPnP mapping is enabled. |
| `tunnel_requested` | Automatic tunnel creation is enabled. |
| `upnp_approved` | The administrator explicitly approved UPnP exposure. |
| `tunnel_approved` | The administrator explicitly approved tunnel exposure. |

Convenience mode preserves existing local choices. Managed mode applies the
requirements above in fixed order and returns the first applicable reason:
`authentication_required`, `protected_identity_storage_required`,
`authenticated_update_required`, `rollback_required`,
`upnp_approval_required`, or `tunnel_approval_required`.

## Compatibility and promotion

This profile adds no wire field, endpoint or production default. SDKs may
implement it as an opt-in startup policy while it remains pre-normative.
Promotion requires equivalent behavior in all maintained SDKs, platform-
appropriate protected-storage evidence, update rollback tests, exposure tests,
security and privacy review, and an explicit release decision.
