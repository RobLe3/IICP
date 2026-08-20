# Restricted trust-domain membership binding v0

**Status:** pre-normative implementation binding; disabled by default.

This binding closes the gap between directory-only bearer authentication and peer-verifiable membership. The existing opaque membership token remains suitable for protected directory HTTP operations. It MUST NOT appear in discovery, bootstrap, gossip or portable configuration.

A peer-verifiable assertion is an authority-signed object containing the restricted Profile identifier, assertion identifier, opaque domain, subject kind and identifier, the subject's existing Ed25519/DID key binding, issuer and key identifier, issuance and expiry, membership generation, operation scopes and audience. The directory signs:

`"IICP-RTD-MEMBERSHIP-V0\\n" || RFC8785-JCS(assertion)`

A gossip sender signs:

`"IICP-RTD-GOSSIP-V0\\n" || RFC8785-JCS(proof)`

The proof binds sender, domain, send time, unique replay identifier, payload SHA-256 and membership assertion identifier. The receiver validates the directory signature, configured issuer, domain/audience, validity, generation and scope before validating the member signature and replay state. Every advertised peer needs its own assertion; a valid sender cannot confer membership on another peer.

## Restricted bootstrap projection

The public `GET /v1/bootstrap` representation is unchanged. When the restricted
trust-domain Profile is active, each returned peer MUST additionally carry a
`membership` value containing that peer's authority-signed membership envelope.
The assertion subject identifier MUST equal the peer's `node_id`, its audience
MUST include the configured trust domain, and its scopes MUST include `peers` or
`bootstrap`. The ordinary assertion signature, issuer, key binding, validity,
generation and revocation-freshness checks apply before the peer becomes
eligible for storage, gossip, relay or execution.

A restricted directory MUST omit a peer whose membership is missing, invalid,
expired or known to be revoked. A restricted client MUST independently reject
such a peer if it is nevertheless returned. Request authentication does not
replace this per-peer verification: it proves the caller's authority, not the
advertised peer's authority.

Bootstrap results are bounded and may be partial. Absence from one response
MUST NOT be interpreted as revocation and MUST NOT, by itself, evict a
previously admitted peer. Revocation is established by an authenticated
generation or revocation mechanism, or by assertion expiry under the configured
freshness policy. The companion bootstrap fixture records these boundaries.

Assertions are usable only until their declared expiry and the configured revocation-freshness bound. When policy requires current revocation status and it cannot be established, restricted mode fails closed. Membership never replaces dispatch or relay authorization.

Public mode is unchanged. This binding adds no base-wire field and does not authorize a deployment, federation relationship or security-default change.
