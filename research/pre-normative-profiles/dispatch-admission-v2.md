# Provider-local dispatch admission v2

**Status:** pre-normative, disabled prototype

This optional semantic profile gives the selected provider local, durable and
atomic single-use admission for an already verified provider-bound ticket. The
Directory remains control-plane only, relays remain opaque forwarders, and
failover requires a new ticket for the replacement provider.

Python and Rust reference implementations persist only JTI, provider/intent
digests, state, expiry and timestamps behind opt-in store ports. They are not
mounted by ordinary node paths. SQLite is an implementation choice, not wire or
protocol state, and does not claim distributed consensus or whole-store
rollback resistance.

The companion `fixtures/dispatch-admission-v2.json` covers deterministic
semantic outcomes. Ratification still requires adversarial review, independent
implementation evidence, migration and governance approval. This proposal adds
no endpoint, base-frame field, task transit, SDK default or production
authority.
