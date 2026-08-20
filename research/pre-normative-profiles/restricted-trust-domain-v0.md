# Restricted Trust-Domain Profile

**Version:** 0.1.0-draft<br>
**Status:** pre-normative; not implemented or required for base IICP conformance<br>
**Profile identifier:** `urn:iicp:profile:restricted-trust-domain:v1`<br>
**Related issues:** IICP #53 and #180

## 1. Purpose and terminology

This Profile defines the minimum interoperable boundary for an independently
operated IICP control plane whose membership, discovery and execution are
restricted to approved participants. “Closed User Group” and “private control
plane” remain useful operator descriptions. **Restricted trust domain** is the
protocol term because the same semantics apply to a household, laboratory,
company, public body, sovereign deployment or research consortium.

A **trust domain** is an administrative security boundary identified by a
stable opaque `domain_id` and one or more explicitly trusted directory
authorities. A **member** is a node or client with a current, verifiable and
domain-scoped membership assertion. Membership permits only the operations
allowed by policy; it is not a dispatch ticket, relay ticket, capability claim,
reputation statement or authority in another domain.

This is Profile work. It does not change IICP Core, create a new intent or make
a transport binding responsible for membership decisions.

## 2. Current-state assessment

| Area | Existing foundation | Gap addressed by this Profile |
| --- | --- | --- |
| Directory choice | Clients and nodes can select a directory. | Selection alone does not prohibit public fallback or prove domain membership. |
| Node and client authentication | Node credentials and short-lived consumer credentials exist. | Current credentials are not a complete, named-domain membership lifecycle. |
| Discovery and bootstrap | Maintained directories expose public discovery/bootstrap behavior. | Restricted routes need authenticated membership and policy checks. |
| Peer gossip | Signed/authenticated mechanisms exist in parts of the ecosystem. | Every learned peer needs the same domain-aware admission pipeline; transitive trust is forbidden. |
| Dispatch and relay | Purpose-specific tickets already bound short-lived authority. | Membership must precede, and must not replace, route authorization. |
| CIP | Coordinator and worker policy gates exist. | All participants, retries and fallbacks must inherit the originating domain boundary. |
| Federation | Signed replication groundwork exists. | Cross-domain access needs an explicit peer-domain and capability policy. |
| Configuration | Individual directory, authentication and mesh settings exist. | No single versioned preset currently validates the complete fail-closed boundary. |

The Profile therefore records semantics and conformance inputs. It does not
claim that current public releases enforce restricted-domain operation.

## 3. Security boundary and decision order

For registration, discovery, bootstrap, gossip, relay, direct execution, CIP
and federation, an implementation claiming this Profile MUST apply the
following checks before storing a peer, returning protected discovery data or
dispatching work:

1. parse and validate the request and required Profile;
2. authenticate the presenting principal and bind it to the asserted subject;
3. validate signature, issuer authority, audience/domain, validity interval and
   replay state of the membership assertion;
4. apply current revocation state and membership epoch;
5. evaluate operation, intent, capability, direction and federation policy;
6. validate any purpose-specific dispatch or relay authority;
7. revalidate material decisions immediately before execution.

Failure at an earlier step is not reclassified by a later one. Implementations
MUST use the stable reason order defined by the fixture so malformed or
unauthenticated input cannot become an oracle for protected membership or
policy state.

Learning a peer from a trusted member does not make the learned peer trusted.
Every gossip, relay and bootstrap candidate enters the same admission pipeline.
Cached membership MUST NOT outlive its assertion, revocation freshness bound or
configured membership epoch. Restart does not restore revoked authority.

## 4. Membership assertion requirements

The exact credential encoding remains implementation- and binding-neutral. A
conforming assertion MUST make these facts verifiable:

- Profile identifier and assertion version;
- opaque trust-domain identifier;
- subject identifier and subject kind (`node` or `client`);
- issuer identifier and a chain to a configured domain authority;
- issuance and expiry times;
- membership epoch or equivalent rollback-resistant revision;
- intended audience or operation scope where the credential is not general to
  the domain;
- signature algorithm and key identifier through an existing IICP trust
  mechanism or an explicitly negotiated adapter.

Private keys and bearer secrets never appear in portable configuration,
discovery results, gossip or conformance evidence. Implementations SHOULD use
short validity periods and offline-verifiable trust material. Revocation MAY use
short expiry, signed revocation state, an epoch, or a combination, but it MUST
have a bounded freshness rule and MUST fail closed when current status is
required but unavailable.

Existing DID/Ed25519 directory identity, node/client credentials and
purpose-specific tickets should be extended before another credential family is
introduced. SPIFFE/SVID can be an optional managed-deployment adapter; it is not
a mandatory IICP wire identity.

## 5. Operating-mode presets

Modes are reproducible presets over explicit settings, not separate protocols.

| Mode | Required observable behavior |
| --- | --- |
| `public` | Existing public behavior remains unchanged unless another accepted Profile is required. |
| `private` | Authenticated node/client membership, authenticated gossip, restricted discovery and no public fallback are required. Federation is disabled unless explicitly configured. |
| `federated_private` | Private behavior applies locally. Cross-domain operations require a configured peer authority plus direction, intent/capability and execution policy. |
| `local_only` | No external directory, bootstrap, relay, gossip, federation or execution network activity is permitted. |
| `custom` | Every security-sensitive field is explicit. An omitted required control is a configuration error, not a permissive default. |

Private and local-only modes MUST NOT silently fall back to a public directory,
relay, peer cache or provider. A compatibility or downgrade setting cannot
weaken a required Profile.

The future canonical configuration must expose, directly or through preset
expansion, `mode`, `domain_id`, trusted directory authorities, membership and
revocation sources, client/node/gossip requirements, public-fallback policy,
relay policy, CIP policy and federation policy. A GUI or wizard may generate
that configuration but cannot introduce different semantics.

## 6. Discovery, gossip, relay and execution

- Protected registration, discovery and bootstrap require an authenticated
  member whose operation scope permits the request.
- Discovery responses MUST reveal no protected node, capability or membership
  information to an unauthorized caller. An implementation may use a common
  refusal to reduce enumeration.
- Gossip senders and every advertised peer require independent authentication,
  membership, freshness and policy checks. Replay is rejected.
- A relay candidate requires valid membership and a purpose-specific relay
  authorization. Membership alone never authorizes relay use.
- Direct execution requires membership, eligibility, policy and the existing
  dispatch authorization. Membership never bypasses provider validation.
- CIP coordinators, workers, retries, replacements and fallbacks MUST satisfy
  the originating task's trust-domain and execution policy. A public fallback
  is forbidden unless the caller explicitly selected a policy that permits it
  and the request does not require this Profile.

## 7. Federation

Federation is an explicit relationship between independently governed domains,
not “private mode off.” A cross-domain decision requires:

- the remote directory authority is configured and currently trusted;
- ingress or egress direction is allowed;
- the requested intent and effective capability are within scope;
- security, privacy, region and execution requirements remain satisfied;
- hop/delegation limits and CIP permission are enforced when configured;
- the final execution path is revalidated under the originating policy.

A domain MUST reject records from an unknown domain, an untrusted authority or
an allowed domain operating outside the configured scope. Federation does not
merge membership namespaces or make one domain's member a local member.

## 8. Stable refusal reasons

The portable fixture defines this first-match order:

1. `invalid_input`
2. `unsupported_required_profile`
3. `local_only_external_forbidden`
4. `public_fallback_forbidden`
5. `authentication_required`
6. `replay_detected`
7. `membership_missing`
8. `membership_expired`
9. `membership_revoked`
10. `wrong_trust_domain`
11. `federation_untrusted`
12. `federation_scope_denied`
13. `policy_denied`
14. `route_authorization_required`
15. `allowed`

The public response MAY map several reasons to a less specific authenticated
error, but content-free conformance evidence and protected operator logs MUST
retain the stable classification. Reasons do not disclose credentials, node
identifiers, topology or task content.

## 9. Compatibility and protocol surfaces

No base-wire change is authorized by this draft. Profile negotiation uses the
existing required/optional Profile mechanism. Membership presentation belongs
on the protected directory, peer and execution operations that consume it; the
chosen HTTP header, token claim or native-binding field must be specified by
the implementing binding and pass the common fixture.

An unknown required restricted-domain Profile rejects before discovery or
execution. An unknown optional Profile may be ignored only in public mode and
only when no request or local policy requires restricted-domain behavior.
Older public clients and directories retain their current behavior. They cannot
claim this Profile until they implement its complete boundary.

## 10. Threat model and privacy limits

The Profile addresses unknown participants, malicious gossip, stolen or replayed
credentials, stale membership, poisoned bootstrap, relay or CIP injection,
accidental public fallback, downgrade and misconfigured federation. A
compromised valid member can still act within its granted scope until revocation
becomes effective. A compromised authority can issue credentials within its
domain; short validity, independent trust anchors, audit evidence and bounded
federation scope reduce but do not eliminate that consequence.

Membership does not provide payload confidentiality, execution privacy,
anonymity, traffic-analysis resistance, endpoint availability or protection
from denial of service. Directory and peer metadata remain observable according
to the selected binding and privacy policy.

## 11. Conformance and release boundary

The canonical draft vectors and schema are:

- `fixtures/restricted-trust-domain-v0.json`
- `schemas/restricted-trust-domain-v0.schema.json`

They cover CUG-01 through CUG-10 plus malformed, expiry, replay, wrong-domain,
downgrade, poisoned-bootstrap, relay and restart cases. Passing the semantic
fixture is necessary but not sufficient for a support claim. Such a claim also
requires implementation-specific tests and black-box evidence across directory,
runtime, CIP and restart/revocation boundaries.

## 12. Non-goals

This Profile does not define a general IAM product, mandate PKI or SPIFFE,
activate federation, change public defaults, choose a GUI framework, place
secrets in configuration, require `iicp.network`, authorize deployment or make
CIP membership a substitute for task authorization.
