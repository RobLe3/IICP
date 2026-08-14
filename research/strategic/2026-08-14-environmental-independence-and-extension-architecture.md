# Environmental independence and extension architecture

**Date:** 2026-08-14  
**Status:** implementation-neutral research and issue plan; no wire, runtime,
release, deployment, DTN, BPv7, or space-operations change.

## Decision

IICP's foundation is suitable for long-lived, environmentally independent use,
but four boundaries need to become explicit before external standardization or
new delivery environments make them expensive to change:

1. define the relationship among Core, Profile, Binding, Registry, and local
   implementation extensions;
2. resolve the standards status and governance of the unregistered `iicp` URN
   namespace identifier;
3. separate execution timeout from delivery lifetime, task deadline, and result
   validity; and
4. separate persistent identity and capability-advertisement validity from
   current reachability and default discovery eligibility.

These are standards-readiness changes, not a request to build a space protocol.
Actual DTN, BPv7, BPSec, contact-plan, and space-network support remains Phase 8.
The correct future shape is an optional delivery profile and binding over an
unchanged logical task model.

## Evidence inspected

The audit used current default branches and live primary standards sources.

| Component | Commit | Relevant evidence |
|---|---:|---|
| IICP specification | `fea540b263cc` | Core, semantics, framing, directory, federation, identity, lifecycle, profile negotiation, registries, IETF draft |
| Python SDK | `2990a529cbd3` | intent validation/construction, request timeouts, native call identity |
| TypeScript SDK | `e9297b0f6e3e` | equivalent intent and timeout behavior |
| Rust SDK | `60433388d0e5` | equivalent intent validation, native transport and lifecycle behavior |
| PHP directory | `19c5a96339fc` | registration, heartbeat, discovery, liveness and federation behavior |
| Rust directory | `a9ae62dc77d9` | intent parser, discovery, liveness and federation behavior |
| Browser node | `025867e9a348` | browser intent validation and request timeout behavior |
| WASM compatibility surface | `3655e561c0c5` | browser-equivalent intent and timeout behavior |

The issue audit covered IICP #3, #40-#43, #46-#47, #52-#55, #60, #63, #99,
#104-#105, #121, #135-#136, #156, and iicp.network #231, #234, #236,
#244, #332, #619, #625, #668-#669, #709 and #726. No existing issue owns the
full environmental-independence decision, identifier/namespace architecture,
or the delivery-time versus execution-time distinction.

Primary sources checked on 2026-08-14:

- [RFC 8141](https://www.rfc-editor.org/rfc/rfc8141.html) defines URNs as
  managed, persistent, location-independent identifiers and says a syntactically
  plausible `urn:` string is not a valid URN unless its namespace identifier is
  registered. The [IANA URN namespace registry](https://www.iana.org/assignments/urn-namespaces/urn-namespaces.xhtml)
  contains no `iicp` entry.
- [RFC 8126](https://www.rfc-editor.org/rfc/rfc8126.html) defines registration
  policies such as Private Use, Experimental Use, Expert Review and
  Specification Required. It recommends the least restrictive policy that
  still protects interoperability.
- [RFC 4838](https://www.rfc-editor.org/rfc/rfc4838.html) describes DTN as a
  store-and-forward architecture for intermittent connectivity. [BPv7,
  RFC 9171](https://www.rfc-editor.org/rfc/rfc9171.html) keeps endpoint identity,
  transmission attempts, bundle lifetime, fragmentation and convergence layers
  distinct. [BPSec, RFC 9172](https://www.rfc-editor.org/rfc/rfc9172.html)
  supplies integrity and confidentiality mechanisms for BP bundles.
- The [CCSDS active-publications catalogue](https://ccsds.org/publications/allpubs/)
  lists its Bundle Protocol standard for space DTN. It is a possible future
  operating environment, not an IICP Core dependency.
- [IEEE 802.1DP-2025 / SAE AS6675](https://1.ieee802.org/tsn/802-1dp/) is a
  published profile of Ethernet TSN and security standards for deterministic
  aerospace onboard networks. It remains a lower-layer substrate relative to
  IICP.
- The [MCP architecture](https://modelcontextprotocol.io/specification/2025-06-18/architecture)
  separates its data and transport responsibilities. The [A2A
  specification](https://a2a-protocol.org/latest/specification/) defines an
  agent interaction/task protocol with multiple bindings. Both are peers or
  interoperability targets where appropriate, not physical transports beneath
  IICP.

## What IICP already gets right

### Logical task and attempt identity

The service-lifecycle profile and native framing already distinguish a stable
logical `task_id` from an attempt-scoped `call_id`. A retry retains `task_id` and
`idempotency_key` and uses a new `call_id`. This is the correct basis for
exactly-once logical execution over at-least-once delivery. The older Core phrase
that `task_id` is “unique per execution” should be reconciled with this more
precise rule; it does not justify a new identity mechanism.

### Streaming and fragmentation

The framing specification explicitly says streaming is not fragmentation.
Transport or BPv7 fragmentation can therefore remain below the logical task and
result lifecycle. No task semantics need to be added for packet, frame, stream,
or bundle fragmentation.

### Async lifecycle

The negotiated service-lifecycle profile already models submitted, accepted,
streaming, completed, failed, cancelled and timed-out states. Synchronous
`CALL`/`RESPONSE` can remain the optimized baseline. A future disconnected
binding can carry the same lifecycle without adding a new Core operation.

### Identity and route separation

The directory stores `node_id` separately from `endpoint` and
`transport_endpoint`, permits endpoint rotation with ownership controls, and
retains dormant node records. The identity slot is URI-based and verifier
pluggable. Federation snapshots and event tails are signed and bounded for
cached verification. These are strong foundations for changing locators and
offline verification.

### Profile negotiation and layered registries

The current pre-normative profile negotiation rejects unknown required profiles
and permits unsupported optional profiles without weakening required behavior.
The intent/capability/extension registry proposal already has entry kinds for
intents, capability profiles, policy profiles, evidence profiles, bindings and
subprotocols. The A2A execution binding correctly leaves A2A task lifecycle to
A2A after IICP selection. This should be consolidated, not replaced.

### Capability and implementation independence

IICP intents name operations rather than vendors or model families. The
capability work in #156 defines an effective end-to-end service property rather
than a theoretical model property. A deterministic program, sensor, instrument,
human service or future runtime can therefore satisfy an intent without changing
Core.

## Confirmed risks

### R1 — Core/Profile/Binding/Registry taxonomy is implicit

**Classification:** P1 standards readiness.

`iicp-extensions.md` mixes billing, reputation, subprotocol bindings,
cooperative execution and planned transport work. `iicp-framing.md` also has a
custom frame-type range that can look like the default extension path even when
a negotiated semantic profile or external binding would be safer. MCP and A2A
are treated more carefully in newer artifacts, but the rule is not authoritative
in one place.

The missing decision is small:

- **Core:** fundamental logical operations and invariants required by every
  conforming implementation;
- **Profile:** optional interoperable semantics composed with Core;
- **Binding:** mapping of Core/profile semantics onto a transport or peer
  protocol;
- **Registry:** stable identifiers and compatibility metadata;
- **Implementation extension:** local behavior that makes no interoperability
  claim and cannot weaken negotiated requirements.

A new domain capability belongs in a registry; a new optional behavior belongs
in a profile; HTTP, native TCP, A2A or future BPv7 mappings belong in bindings.
Core changes should be rare.

The legacy `+modifier` path is part of this risk. `iicp-semantics.md` currently
says unknown modifiers should route fail-open, while the newer profile contract
correctly fails closed for unknown required behavior. The two channels must be
reconciled before ratification. An unknown requirement must never silently
become an ordinary base-intent request.

### R2 — `urn:iicp:` is not a registered URN namespace

**Classification:** P1 standards readiness and migration risk.

All implementations validate, compare and sometimes construct strings beginning
with `urn:iicp:`. The IANA registry has no `iicp` NID. Under RFC 8141, syntax
alone does not make these strings valid URNs. Current documents should therefore
call them stable project-defined identifiers pending namespace registration,
not imply an already registered namespace.

This does not justify breaking deployed values. Implementations should continue
treating identifiers as opaque stable strings. The preferred standards path is
to prepare a formal `iicp` NID registration after #47 establishes durable change
control and succession. If that path fails, an alternative identifier and
alias/migration plan must preserve existing values. A bulk rewrite is rejected.

The `x.` custom-intent convention is an internal namespace rule, not “IETF
practice.” RFC 8141 removed experimental `X-` URN namespaces, and RFC 6648
retired the general `X-` convention. Private and experimental allocation should
be governed inside the eventual IICP namespace or another valid identifier
space.

The source audit also found hard-coded parsing and construction across every
SDK and both directories. Typed wrappers such as `IntentId`, `ProfileId` and
`BindingId` may reduce future migration risk, but they should wrap opaque values
and must not trigger a wire change by themselves.

### R3 — execution and delivery time are conflated

**Classification:** P1 architectural blocker for disconnected bindings; bounded
current impact.

`constraints.timeout_ms` is variously described as an execution timeout, an
end-to-end deadline, a provider-receipt-relative deadline and a client request
wait. The lifecycle profile begins the deadline at provider receipt. This is
adequate for current connected calls but cannot express, for example, 30 seconds
of execution within a 48-hour delivery lifetime and a 72-hour result deadline.

The protocol needs definitions before fields:

- execution timeout: maximum local execution time after accepted execution
  begins;
- delivery lifetime: how long a delivery system may retain/forward an attempt;
- task deadline: latest acceptable completion time for the logical task;
- result validity: how long a completed result remains useful or retrievable;
- request wait timeout: local caller patience, not a provider guarantee.

Existing `timeout_ms` behavior must remain compatible until a reviewed additive
profile defines any additional fields. BPv7 lifetime is evidence for separation,
not a field to copy into Core.

### R4 — capability validity and current reachability are not explicit axes

**Classification:** P2 extensibility improvement.

The directory retains dormant records, signed events and availability windows,
but default discovery returns only nodes that are available and seen within the
90-second liveness window. Registration also requires a live endpoint probe.
That behavior is correct for today's public connected-mesh profile. The
specification does not, however, clearly distinguish:

- identity validity;
- advertisement validity and version;
- current reachability evidence;
- current execution availability;
- scheduled or predicted availability; and
- default dispatch eligibility.

A future profile must be able to say “this signed capability advertisement is
valid, but this provider is not reachable now” without returning an offline node
as an immediately dispatchable candidate. This is a semantic and projection
change, not a request to weaken current liveness gates.

## Recommended architectural invariants

The following wording is suitable as the target for a reviewed architecture
decision. It is not normative until the specification process accepts it.

1. An Intent identifies a semantic operation and MUST NOT change solely because
   a transport, medium, locator or delivery topology changes.
2. A Capability describes effective service behavior and MUST NOT require a
   particular model, vendor, runtime, hardware class or implementation technique
   unless that property is itself an explicit profile requirement.
3. Stable identities MUST be represented independently from current locators.
4. Advertisement validity, reachability evidence, availability and dispatch
   eligibility MUST remain distinguishable.
5. A logical task MUST be distinguishable from each delivery or execution
   attempt. Retransmission MUST NOT create a new logical task by itself.
6. Execution timeout, delivery lifetime, task deadline, result validity and
   caller wait timeout MUST NOT be treated as synonyms.
7. QoS, priority, delivery policy, execution constraints and security
   requirements MUST remain orthogonal.
8. Core expresses required security properties; each binding/profile identifies
   the mechanisms that satisfy them. Existing TLS requirements remain mandatory
   for current HTTP/native bindings unless those bindings are revised.
9. Logical message semantics MUST be distinguishable from JSON, CBOR, native
   frames or another encoding.
10. Transport fragmentation, stream partitioning and retransmission MUST NOT
    alter logical task identity or lifecycle.
11. Contemporaneous end-to-end connectivity MUST NOT become a Core invariant
    when the semantic operation can be represented asynchronously.
12. Unknown required behavior MUST fail closed; unknown optional behavior may be
    ignored without weakening required behavior.

## Standards mosaic

| Standard or family | Relationship to IICP | Boundary |
|---|---|---|
| MCP | Peer protocol / binding target | MCP tools, resources, prompts and session rules remain MCP-owned; IICP may discover/select an eligible service and map an invocation. |
| A2A | Peer task protocol / binding target | A2A agent cards, tasks and artifacts remain A2A-owned after an IICP binding selects the service. |
| HTTP, WebSocket, QUIC, TCP/IP, UDP/IP | Current or potential transport substrate/binding | They carry IICP data; they do not define intent or logical task identity. |
| IEEE 802, 802.1, 802.1Q | Lower-layer network substrate | Link/bridge/VLAN behavior is outside IICP. |
| IEEE 802.1DP / SAE AS6675 | Deterministic aerospace onboard Ethernet profile | Useful lower-layer substrate; not a deep-space or IICP profile. |
| DTN architecture / BPv7 | Phase 8 future binding target | BP owns store-and-forward delivery, EIDs, bundle lifetime, fragmentation and convergence layers. |
| BPSec | Phase 8 security mechanism mapping | May satisfy binding-level integrity/confidentiality properties; does not replace IICP authorization or execution privacy. |
| CCSDS DTN/space networking | Phase 8 operating environment and standards family | IICP should use, not duplicate, space-network delivery standards. |
| DID/VC and signed credentials | Optional identity/evidence mechanisms | Reuse the verifier/evidence layers; do not make one identity method Core. |
| Hardware attestation | Optional execution-privacy evidence mechanism | Remains under #136 and must not become general transport identity. |

## Identifier and registry recommendation

Use one governance model now that can map to RFC 8126 later:

| Registry class | Near-term project policy | Possible later IANA policy |
|---|---|---|
| Stable public intents/capabilities/profiles/bindings | public specification, compatibility fixture, review and change controller | Specification Required or delegated hierarchical policy |
| Frame/message types and error codes | bounded ranges, collision check, review and conformance evidence | Expert Review or Specification Required |
| Security mechanisms | explicit threat model and interoperable specification | stricter review where warranted |
| Private use | explicitly reserved non-public range/namespace | Private Use |
| Experimental use | owner, expiry/review date, no stable-interoperability claim | Experimental Use or project-governed space |

Do not create IANA bureaucracy before submission authority and stable public
specifications exist. Do ensure every registry entry already carries an owner,
lifecycle, reference, compatibility rule, and change history so later migration
is administrative rather than architectural.

## Phase 8 reservation

No Phase 8 implementation issue is justified now. Reserve the following names
as planning concepts only, not registry entries or promises:

- IICP Delay-Tolerant Delivery Profile;
- IICP-over-BPv7 Binding;
- DTN-aware Directory Profile;
- BPSec Security Mapping;
- Contact/Reachability Advertisement Extension; and
- Delay-Tolerant Conformance Suite.

They become eligible for issues only when a concrete mission/operator,
prototype, standards liaison, or interoperability experiment supplies evidence.
No `mars_delay`, orbital window, contact-plan, BP fragment, LTP segment, or
similar environment-specific field belongs in Core.

## Conformance recommendations

The accompanying research fixture records the semantic result expected from
transport and timing stress cases. Later conformance work should cover:

- same logical task across a new call attempt;
- duplicate and reordered attempt delivery;
- provider locator rotation without identity rotation;
- a valid advertisement whose provider is currently offline;
- unknown required versus optional profile behavior;
- delayed result retrieval on a later connection;
- transport change and fragmentation without task-identity change;
- security-property satisfaction by a binding-specific mechanism;
- an unknown future capability carried as an opaque identifier; and
- current behavior remaining unchanged when no new profile is negotiated.

These cases improve ordinary terrestrial reliability. They do not simulate Mars
or claim BPv7 support.

## Issue disposition

| Work | Action | Priority | Reason |
|---|---|---:|---|
| IICP #160 — environmental-independence and extension taxonomy | Opened as architecture owner | P1 | Owns the cross-cutting invariants and Core/Profile/Binding/Registry decision. |
| IICP #161 — identifier and registry architecture | Opened as standards owner | P1 | `iicp` is absent from IANA's URN NID registry; governance and migration require focused review. |
| IICP #162 — timing semantics | Opened as lifecycle owner | P1 | Current `timeout_ms` descriptions conflate distinct clocks. |
| IICP #163 — identity/capability validity versus reachability | Opened as directory-semantics owner | P2 | Current connected-mesh filtering is correct but the semantic axes are implicit. |
| IICP #40 and #47 | Updated | P1 | Added architecture, identifier and durable change-control prerequisites to external readiness. |
| IICP #42 / iicp.network #669 | Updated without expanding benchmark | P1 | Classified native TCP/QUIC as bindings and Phase 8 BPv7 as deferred; retained current evidence gates. |
| IICP #43 | Updated dependency wording | P1 | The port/media packet is now explicitly separate from identifier-namespace registration. |
| IICP #55 | Updated | P1 | Added #160/#161 and the legacy fail-open modifier reconciliation gate. |
| IICP #156 | Updated | P1 | Added implementation independence and the #163 reachability boundary without merging quality or telemetry. |
| IICP #3 / #60 / #63 / #105 | Keep closed | — | Their delivered lifecycle, A2A, identity/evidence and IEEE crosswalk work remains reusable. |
| DTN/BPv7/space implementation | No issue now | Phase 8 | No concrete implementation evidence or operator requirement exists. |

## Dependency order

```text
IICP #160 environmental-independence architecture decision
        |
        +--> #161 identifier and registry architecture
        |         |
        |         +--> #40 standards readiness / #43 registration packets
        |
        +--> #162 timing-semantics clarification
        |         |
        |         +--> future delay-tolerant delivery profile
        |
        +--> #163 reachability/advertisement semantic split
        |         |
        |         +--> future disconnected-directory profile
        |
        +--> #55 extension/profile ratification
                  |
                  +--> future bindings, including Phase 8 BPv7 if justified
```

## Compatibility assessment

The current change is research-only. It adds no field, frame, endpoint, package,
runtime default or deployment behavior. Existing identifiers, current TLS
requirements, heartbeat gates, default discovery, buffered calls, lifecycle
profile and SDK behavior remain unchanged.

The eventual architecture work can remain additive if it preserves existing
`urn:iicp:` values as opaque identifiers, treats current HTTP/native behavior as
bindings, and adds any new timing or delivery semantics only through negotiated
profiles. Phase 8 should therefore be possible without redesigning Core:

```text
Earth application -> IICP logical task -> future BPv7 binding -> DTN -> IICP logical task -> remote application
```

That is the architectural target, not a current support claim.
