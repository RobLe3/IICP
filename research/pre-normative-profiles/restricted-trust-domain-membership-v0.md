# Restricted trust-domain membership binding v0

**Status:** pre-normative implementation binding; disabled by default.

This binding closes the gap between directory-only bearer authentication and peer-verifiable membership. The existing opaque membership token remains suitable for protected directory HTTP operations. It MUST NOT appear in discovery, bootstrap, gossip or portable configuration.

A peer-verifiable assertion is an authority-signed object containing the restricted Profile identifier, assertion identifier, opaque domain, subject kind and identifier, the subject's existing Ed25519/DID key binding, issuer and key identifier, issuance and expiry, membership generation, operation scopes and audience. The directory signs:

`"IICP-RTD-MEMBERSHIP-V0\\n" || RFC8785-JCS(assertion)`

A gossip sender signs:

`"IICP-RTD-GOSSIP-V0\\n" || RFC8785-JCS(proof)`

The proof binds sender, domain, send time, unique replay identifier, payload SHA-256 and membership assertion identifier. The receiver validates the directory signature, configured issuer, domain/audience, validity, generation and scope before validating the member signature and replay state. Every advertised peer needs its own assertion; a valid sender cannot confer membership on another peer.

Assertions are usable only until their declared expiry and the configured revocation-freshness bound. When policy requires current revocation status and it cannot be established, restricted mode fails closed. Membership never replaces dispatch or relay authorization.

Public mode is unchanged. This binding adds no base-wire field and does not authorize a deployment, federation relationship or security-default change.
