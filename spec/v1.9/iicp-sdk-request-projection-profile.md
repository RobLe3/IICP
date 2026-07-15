# SDK Request Projection Profile

**Status:** pre-normative, fixture-gated  
**Fixture:** `sdk-request-projection-v0.json`

This profile defines how a client projects one public task request into the
prompt-free directory control plane and the provider data plane. It does not
change IICP framing, intent URNs, directory payload ownership, or provider wire
messages.

## Projection boundary

`route_constraints` contains only provider-discovery criteria: region, QoS,
model availability, minimum reputation, browser usability, profile negotiation,
candidate limit, and retry exclusions. It is never serialized to a provider.

`execution_constraints` contains provider-facing controls: timeout, maximum
tokens, requested model, QoS, and generation parameters.

Model and QoS may intentionally appear in both projections: the directory uses
them for eligibility and selection, while the chosen provider uses them for
execution. Region, reputation, browser status, profile negotiation, and retry
exclusions remain control-plane-only.

## Precedence

Clients resolve each route field in this order:

1. explicit `route_constraints`;
2. compatible historical task/helper fields;
3. client configuration;
4. protocol defaults.

Ticketed discovery and legacy discovery MUST receive equivalent normalized
criteria. Automatic fallback MUST NOT silently discard a criterion. Language
SDKs may expose idiomatic APIs, but the normalized fixture transcript must
remain equivalent.

## Compatibility

The initial profile preserves historical task fields as compatibility inputs.
Implementations should normalize them once, before choosing ticketed or legacy
discovery. New applications should prefer explicit route constraints.

Consumer-authentication policy is independent of request projection:
`optional` preserves open-mesh behaviour, `required` refuses unauthenticated
dispatch, and `disabled` never requests a consumer token.

