# Architecture decision: environmental independence and extension architecture

**Status:** Accepted architectural boundary  
**Recorded:** 2026-08-14  
**Machine-readable contract:**
[`environmental-independence-v1.json`](environmental-independence-v1.json)  
**Related work:** IICP #40, #42, #43, #47, #55, #156 and #160–#163

## Decision

IICP standardizes the logical meaning of intent-based communication without
requiring a particular transport, medium, locator, latency, topology, encoding,
execution backend or continuously connected deployment. Current connected HTTP
and native-framing operation remains valid, but it is a binding choice rather
than a Core assumption.

New work belongs to one of five extension classes:

- **Core** defines logical operations and invariants required by every
  conforming implementation.
- A **Profile** defines optional interoperable semantics composed with Core.
- A **Binding** maps Core and negotiated profiles onto a transport or peer
  protocol.
- A **Registry** assigns stable identifiers and their lifecycle and
  compatibility metadata.
- An **implementation extension** is local behavior with no interoperability
  claim. It cannot weaken Core or a negotiated requirement.

A new domain capability is Registry work. New optional interoperable behavior
is Profile work. A new transport or peer-protocol mapping is Binding work. A
Core revision is justified only when the existing logical operations cannot
express a generally required semantic operation.

## Core invariants

1. An intent identifies a semantic operation. Changing a transport, medium,
   locator or delivery topology does not create a new intent.
2. A capability describes effective service behavior. It does not require a
   model, vendor, runtime or hardware class unless a separately negotiated
   profile makes that property part of the request.
3. Stable identity and current locators are separate. Locator rotation does not
   change identity, although the new locator still requires normal ownership
   and reachability validation.
4. Advertisement validity, reachability evidence, execution availability and
   dispatch eligibility remain distinguishable.
5. A logical `task_id` remains stable across delivery or execution attempts.
   Each attempt uses its own `call_id`; retransmission does not create a new
   logical task.
6. Execution timeout, delivery lifetime, task deadline, result validity and
   caller wait timeout are different time axes.
7. QoS, priority, delivery policy, execution constraints and security
   requirements remain orthogonal.
8. Core names security properties. A binding or profile identifies and proves
   the mechanisms that satisfy those properties. Current TLS requirements
   remain mandatory for the bindings that require TLS.
9. Logical messages are independent from JSON, CBOR, native frames or another
   encoding.
10. Fragmentation, segmentation, retransmission and stream partitioning do not
    change logical task identity or lifecycle.
11. Contemporaneous end-to-end connectivity is not a Core invariant when an
    operation can use the asynchronous lifecycle.
12. Unknown required behavior fails closed. Unknown optional behavior may be
    ignored only when doing so preserves every required constraint.

## Current classification

| Existing area | Class | Boundary |
| --- | --- | --- |
| Intent, task, constraints, policy, discovery, selection, invocation, result and receipt semantics | Core | Logical meaning remains independent from transport and implementation. |
| Service lifecycle, provider admission, confidentiality, policy/data handling and other negotiated optional behavior | Profile | A profile is effective only after its requirements and dependencies are satisfied. |
| HTTP projection and native framing | Binding | They encode and carry Core/profile semantics. Native framing does not make TCP, QUIC or a future convergence layer part of Core. |
| MCP and A2A mappings | Binding to a peer protocol | MCP and A2A retain ownership of their tool, resource, task and artifact semantics. |
| Intents, capabilities, profiles, policies, evidence classes, bindings and public extension identifiers | Registry | Registry entries name behavior; they do not implement it. |
| Billing and reputation behavior that crosses implementations | Profile plus Registry entries | Local accounting or ranking details remain implementation policy unless an interoperable contract is negotiated. |
| Custom frame-type range | Binding extension point | A custom frame cannot create new semantic requirements without an identified, negotiated Profile or Binding contract. |
| Local rankers, caches, metrics and provider adapters | Implementation extension | Local behavior cannot bypass eligibility, policy, security or negotiated profiles. |

QUIC, DTN, BPv7, BPSec, contact-plan routing and space operation are not current
IICP capabilities. A future implementation must use an accepted Profile,
Binding and Registry entries rather than reinterpret this decision as support.

## Profile composition and compatibility

A request may declare required and optional profiles. All required profiles and
their transitive dependencies must be supported before dispatch. An unknown,
expired, incompatible or unsatisfied required profile rejects before execution.
Optional profiles may be omitted only when baseline behavior still satisfies
all required constraints.

Profiles use stable opaque identifiers and explicit versions. A registry entry
records dependencies, incompatibilities, lifecycle status, replacement and
conformance material. Deprecation does not silently change semantics. A profile
cannot weaken Core, another required profile, authorization, confidentiality or
policy. Bindings must report whether negotiated profiles can be represented;
they may not silently downgrade them.

## Intent modifier compatibility

The legacy `+modifier` syntax is deprecated as a requirements channel. Current
official implementations already reject `+` in intent identifiers, so this
decision documents deployed fail-closed behavior rather than adding a new wire
requirement.

A sender must use the registered base intent and a required Profile identifier
for additional behavior. A receiver that encounters a modifier must not strip
it and route the request as the base intent. A separately standardized mapping
may translate a known legacy modifier to an equivalent required profile, but an
unknown modifier rejects. `+attested` remains reserved and unusable until an
accepted profile defines its evidence, identity and security requirements.

## Consequences

- Existing unprofiled requests retain their current behavior.
- Current HTTP and native bindings remain supported.
- SDKs and directories must treat identifiers as opaque and must not infer
  environment or implementation semantics from their spelling.
- Future high-delay or disconnected operation can reuse the existing logical
  task and lifecycle model.
- Phase 8 can add a delay-tolerant delivery Profile and BPv7 Binding without
  redefining Core, if later evidence justifies them.

## Non-goals

This decision does not register a URN namespace, add request fields, implement
DTN/BPv7/BPSec, change timeout values, return offline providers from ordinary
discovery, enable QUIC, change a security default or authorize deployment.
