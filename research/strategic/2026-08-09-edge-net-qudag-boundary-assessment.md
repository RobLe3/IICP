# Edge-Net and QuDAG boundary assessment

**Date:** 2026-08-09  
**Decision status:** research only; no protocol or implementation change is authorized  
**Question:** which Edge-Net or QuDAG concepts expose a general IICP requirement, and which should remain execution-fabric internals?

> **Tracker reconciliation, 2026-08-12:** IICP #4 has since closed after the
> provider-admission baseline and Edge-Net evidence were recorded. Any future
> additive capability/capacity vocabulary belongs under the layered substrate
> and registry gates in IICP #54 and #55. The heterogeneous-model learned-routing
> assessment found no new Edge-Net or QuDAG requirement: observations remain
> portable, while selection algorithms remain client-local. The adapter proof of
> concept is still not justified without a runnable, stable Edge-Net task surface.

## Sources and method

The review used current source at fixed commits rather than README feature lists.

| Repository | Commit inspected | Scope |
|---|---|---|
| `RobLe3/IICP` | [`e0e70e3`](https://github.com/RobLe3/IICP/tree/e0e70e3ce89faced5e0105eae0b83b30abbcade8) | Core, directory, framing, lifecycle, identity, telemetry, federation, receipts and existing NAT research |
| PHP Genesis directory | [`017b75f`](https://github.com/RobLe3/iicp-directory-php/tree/017b75f531f08a933dde67a5a116c4204d48c5f4) | Registration, liveness, reachability, ranking and transport metadata |
| Rust directory | [`9bc2e20`](https://github.com/RobLe3/iicp-directory-rust/tree/9bc2e2097dfd0265cda4b86a7bf920e734757a0d) | Preview parity paths and fixtures |
| Python client | [`2bebeef`](https://github.com/RobLe3/iicp-client-python/tree/2bebeef5ba5baf6b663ab87c58d22993cbc72108) | Provider registration, heartbeat, NAT, tunnel and relay paths |
| TypeScript client | [`c638e2d`](https://github.com/RobLe3/iicp-client-typescript/tree/c638e2d1f86ad4ac6cc66ee9701637ebb5ff3e78) | Provider registration, heartbeat, NAT, tunnel and relay paths |
| Rust client | [`18bdec2`](https://github.com/RobLe3/iicp-client-rust/tree/18bdec23c94e96d1cbbb7cb6acd233c1e35ef3bb) | Provider and native-transport paths |
| Browser node | [`9e8d150`](https://github.com/RobLe3/iicp-web-node/tree/9e8d15016e0c092d5dffe5634eb5f7132eeac1f6) | Browser lifecycle, relay and planned WebRTC reachability |
| `ruvnet/RuVector` | [`9e12078`](https://github.com/ruvnet/RuVector/tree/9e12078ae2af74d0613ae604266cf22fb1113b10/examples/edge-net) | `examples/edge-net` Rust, JavaScript, relay files and tests |
| `ruvnet/QuDAG` | [`6c17c59`](https://github.com/ruvnet/QuDAG/tree/6c17c5974b75e5ab367b6023256d10d2b20e033a) | `core/network`, `core/crypto` and integration boundaries |

Local validation produced two useful controls:

- `cargo check --manifest-path examples/edge-net/Cargo.toml` passed with warnings. This checks the exported Edge-Net Rust library, not the unreferenced `src/network/p2p.rs` design.
- `cargo check -p qudag-network --locked` passed. This establishes that the current QuDAG network crate compiles; it does not turn its explicit mock and `TODO` paths into working STUN, TURN, UPnP or post-quantum transport.

Claims below use four evidence levels: **active** means reachable from the current package or runtime path; **partial** means a real component exists but the complete workflow is absent; **design code** means types or code exist outside the active path; **absent** means a referenced dependency or implementation is missing from the inspected commit.

## Executive finding

Edge-Net can **partially** fit behind an ordinary IICP provider boundary, but a proof of concept should wait. The useful general question is not whether IICP should adopt Edge-Net. It is whether IICP can describe a transient provider's allocatable capacity, capability freshness and reachable transport without learning its scheduler or overlay topology.

IICP already has the stronger control-plane abstraction in several areas:

- stable intent URNs and capability matching;
- directory-owned eligibility and score evidence;
- explicit endpoint, transport candidate, relay and reachability fields;
- a 30-second heartbeat and 90-second stale-node window;
- provider-selection receipts and route tickets;
- a negotiated streaming, cancellation, retry and idempotency lifecycle;
- operator identity slots and federated directory state.

Edge-Net goes deeper in browser resource detection and local contribution controls. QuDAG goes deeper in active libp2p topology primitives. Neither inspected repository demonstrates a production-grade end-to-end reachability system that IICP should port. The current Edge-Net P2P integration imports missing files, and QuDAG's broad NAT module contains explicit mock or placeholder implementations.

The resulting work belongs mainly in existing IICP issues. This review does not justify a new Edge-Net-specific protocol issue.

## Architecture comparison

| Concept | Edge-Net / QuDAG implementation | IICP equivalent | Depth difference | Natural IICP terrain? | Integration relevance | Gap | Recommendation | Boundary risk |
|---|---|---|---|---|---|---|---|---|
| Resource detection | Edge-Net actively detects WebGPU, WebGL2, worker count, texture features, estimated GPU memory and device data; `NodeConfig` limits CPU, memory, bandwidth and battery use. | Capability format identifies models, token/context limits, streaming, quantization, engine and coarse hardware; registration exposes maximum concurrency and live load. | Edge-Net has richer device-local facts; IICP has stronger eligibility semantics. | Yes, for bounded advertisement and selection only. | High | IICP lacks a general distinction between supported resources and currently allocatable resources. | Extend the research under [#4](https://github.com/RobLe3/IICP/issues/4); do not expose scheduler internals or precise fingerprinting data. | High if hardware inventory becomes mandatory or identifying. |
| Capability discovery | Active Edge-Net Rust uses exact string capabilities in an in-memory peer table. Its unexported libp2p file contains DHT provider records. QuDAG has Kademlia/Identify/mDNS and broad capability types, but the separate discovery service simulates DHT/mDNS. | Intent URNs, capability envelopes, directory queries and registry governance. | IICP is more precise and implementation-neutral. | Yes. | Medium | Resource-oriented capability fields are sparse, not discovery itself. | Keep IICP's registry model; do not import a DHT capability index. | Medium. |
| Initial bootstrap | Edge contribution daemon uses a configured central WebSocket relay. Edge P2P design prefers a Firebase bootstrap module that is absent from the commit. QuDAG uses configured bootstrap multiaddresses plus optional mDNS. | Explicit directory URL, Genesis Seed fallback, trusted-replica list, federation redirects; verified local discovery is tracked in #39. | QuDAG has an active local/link bootstrap primitive; IICP has the stronger trust-root and directory model. | Yes, as directory bootstrap. | Medium | No shipped zero-configuration local directory discovery. | Continue #39 after current foundation work. | High if discovery is mistaken for trust. |
| Membership and liveness | Edge signaling membership is connection-scoped; message receipt updates `lastSeen`, and disconnect removes a peer. The contribution daemon heartbeats and reconnects. QuDAG uses libp2p swarm events, ping, mDNS expiry and Kademlia routes. | Provider heartbeats every 30 seconds, inactive after 90 seconds, re-registration and capability refresh, independent reachability evidence. | IICP has clearer provider lifecycle semantics; overlays have more connection-state signals. | Yes. | High for transient providers. | Capability freshness is coupled mainly to registration/health-model refresh; no general per-capability expiry field. | Research under #4 and browser-node #4, without weakening the base heartbeat model. | Medium. |
| Reachability advertisement | Edge signaling forwards WebRTC offer, answer and ICE messages. The referenced WebRTC implementation is absent. QuDAG Identify adds addresses; relay-server and DCUtR behaviours exist, but a complete relay-client/AutoNAT workflow was not found. | `endpoint`, `transport_endpoint`, `transport_method`, ICE-style `transport_candidates`, `transport_metadata`, `relay_endpoint`, `reachability_tier`, route evidence and browser WebRTC draft. | IICP has the stronger descriptive model; external projects provide topology-mechanism examples. | Yes. | High | Candidate expiry and connection-establishment profile support need clearer evidence rules. | Feed evidence into #59, #42 and browser-node #4; do not add a second reachability schema. | High if private addresses/topology leak. |
| Task lifecycle | Edge design code models task request, claim, result, validation and payment release. The active Rust network manager has basic submit/claim/result messages. QuDAG request-response currently returns an empty response on inbound requests. | Negotiated lifecycle defines acceptance, ordered partials, exactly one terminal event, cancellation, timeout, replay, idempotency and accounting cardinality. | IICP is materially deeper and more interoperable. | Yes. | High | Adapter mapping must be proven, but no protocol gap is established. | Wait for streaming implementation work under #89 before an external-fabric PoC. | Low if kept at the provider boundary. |
| Receipts and proofs | Edge design code has input/result hashes, computation-proof variants, execution statistics, payment release and disputes. It is not in the active network export. | Client and node receipts correlate through route tickets; lifecycle receipts distinguish terminal evidence and accounting. | Edge explores computation proof types; IICP has a clearer portable routing/execution evidence boundary. | Partial. | Medium | IICP does not standardize a general proof of correct arbitrary computation, and should not imply one. | Record external proof references only when a concrete intent profile needs them. No new generic receipt type now. | High if self-reported resource use is treated as proof. |
| Operator and node identity | Edge has node keys and a contribution identity, but the daemon creates a new session node ID. QuDAG generates a libp2p Ed25519 identity in `P2PNode::new`. | Identity slot carries operator identity; registration, node IDs, delegation, route tickets and receipts assign distinct roles. | IICP has the stronger abstraction; operational profile work remains. | Yes. | Medium | Device continuity and delegation need evidence, not a new Edge identity scheme. | Keep #63 and managed-operator work authoritative. | High if one identifier is made to serve operator, workload and task authority. |
| Contribution accounting | Edge has contribution reports, credits and settlement-oriented design. | IICP has credit receipts, lifecycle reservation/settlement cardinality and signed event boundaries. | Edge goes deeper into its own economy; IICP is correctly more neutral. | Partial. | Low | No demonstrated need for a new generic economic event. | Keep prices, rewards and settlement policy outside core; reuse terminal receipts where required. | Very high. |
| Adaptive selection | Edge semantic router records capabilities, latency, reputation and success/failure data; capability strings are deterministically hashed into vectors. QuDAG defines several load-balancing types. | Directory scoring uses availability, load, capacity, region, reputation, model match and price; telemetry has independent-observation and smoothing rules. | IICP has stronger evidence governance; Edge has more implementation-specific selection experiments. | Yes, for observations, not algorithms. | Medium | Public measurement vocabulary can be made more portable. | Use #98 for observation provenance; leave EWMA, bandits or ML implementation-specific. | Medium if opaque algorithms become normative. |
| Post-quantum crypto | QuDAG's crypto crate uses ML-KEM, ML-DSA and HQC libraries. Its network transport still contains placeholder certificate loading and a dummy shared-secret path. | Ed25519/JCS and algorithm-dispatched identity/signature slots; signed-envelope work is open. | QuDAG has deeper algorithm implementation; IICP has the safer protocol-agility boundary. | Partial. | Low now. | No immediate interoperability requirement was found. | Add a watch item to #52, not a new mandatory profile. | High if an unintegrated crypto path displaces the reviewed baseline. |

## What the inspected code actually supports

### Edge-Net

The exported Rust package contains an in-memory `WasmNetworkManager`. It records peer keys, capability strings, stake, reputation, last-seen time and latency, considers a peer active for 60 seconds, and selects exact capability matches by reputation. The more ambitious libp2p implementation in `src/network/p2p.rs` is not declared by `src/network/mod.rs`; the package has no `p2p` feature or libp2p dependency. It is design code, not the networking path validated by `cargo check`.

The JavaScript signaling server is more concrete. It registers connection-scoped peers and capabilities, returns capability matches, and separately forwards WebRTC offers, answers and ICE candidates. This is useful evidence for keeping peer discovery separate from connection establishment. It does not establish a complete Edge-Net WebRTC path because `pkg/p2p.js` imports `pkg/webrtc.js` and `pkg/firebase-signaling.js`, neither of which exists at the inspected commit. The relay package also points to an absent `relay/index.js`.

The contribution daemon provides a separate central-relay path. It creates a session node ID, connects to a configured WebSocket relay, registers its public key and two coarse capabilities, heartbeats, reports contribution and reconnects after disconnection. That path is operationally simpler than the P2P architecture described in comments.

Edge-Net's strongest relevant code is device-local resource detection and contribution policy. That logic can inform field semantics, but the code should not be ported into IICP core. SDKs may later implement their own reviewed probes and send a redacted, versioned projection.

### Standalone QuDAG

QuDAG is technically distinct from Edge-Net's QDAG ledger/task terminology. Its active `P2PNode` composes libp2p Kademlia, signed Gossipsub, optional mDNS, ping, Identify, relay-server behaviour, DCUtR and CBOR request-response. Startup listens on configured addresses, adds configured bootstrap peers to Kademlia and calls bootstrap. mDNS discoveries and Identify addresses feed Kademlia.

This is useful topology prior art, but the limits matter:

- `enable_quic` is present in configuration, while the active `build_transport` path constructs TCP, memory and optional WebSocket transports, not QUIC.
- the behaviour hosts relay service requests; a complete relay-client reservation and route workflow was not identified;
- no AutoNAT behaviour is composed even though the Cargo feature is enabled;
- inbound request-response currently returns an empty payload with a `TODO`;
- the separate `discovery.rs` service labels itself production-ready but simulates DHT and mDNS discovery;
- the NAT module describes STUN, TURN, UPnP, NAT-PMP, hole punching and relay fallback, but its STUN path is a custom echo request, TURN allocation is a mock, UPnP is simulated, and other paths contain explicit placeholders;
- the post-quantum transport wrapper has placeholder certificate loading and a dummy shared-secret path.

The appropriate lesson is to reuse protocol patterns only after tracing their active path. QuDAG's working libp2p composition is stronger prior art for local and overlay discovery. Its NAT module is not evidence that IICP should replace its existing ICE-style candidate and reachability work.

## Discovery and reachability matrix

| Concern | IICP | Edge-Net | QuDAG | Gap or observation |
|---|---|---|---|---|
| Initial bootstrap | Configured directory, Genesis fallback, trusted replica registry | Configured WebSocket relay in daemon; Firebase-first P2P design is incomplete | Configured bootstrap multiaddresses; optional mDNS | IICP local zero-config bootstrap remains #39; discovery never establishes trust. |
| Directory/relay discovery | Trusted-replica well-known document and signed federation | Relay URL is configured or hard-coded; no verified relay discovery found | Bootstrap peers configured; no IICP-like directory role | No external mechanism improves IICP's trust-root model. |
| Peer/provider discovery | Directory query by intent; optional bootstrap peers/gossip | Signaling capability query; in-memory exact matching; DHT design code | Kademlia closest-peer lookup and mDNS | IICP provider discovery is clearer and policy-aware. |
| Capability discovery | Versioned intent/capability envelopes | Exact strings; DHT capability records only in inactive code | Broad peer capability types, not an agent intent registry | IICP needs richer resource descriptors, not another discovery system. |
| Local discovery | Proposed verified mDNS/DNS-SD directory profile | Local signaling fallback, no complete zero-config path found | Active optional libp2p mDNS | QuDAG validates #39's optional mechanism, not automatic trust. |
| Wider-network discovery | Genesis/replicas/federation and directory query | Central relay/signaling; incomplete DHT migration design | Kademlia plus configured bootstrap peers | DHT would expand IICP into overlay operation without a demonstrated need. |
| Liveness | 30-second heartbeat; inactive after 90 seconds; active probes and challenges | 60-second in-memory last-seen threshold; connection lifecycle; daemon heartbeat | Ping/swarm/mDNS expiry; broader simulated discovery metrics | IICP has the more explicit provider contract. |
| Capability freshness | Re-registration and live model-health heartbeat | Registration-time strings; semantic router updates peers | Identify/Kademlia addresses; capability freshness not uniformly wired | General per-capability validity/observation time deserves #4 research. |
| Reachability advertisement | Endpoint, native endpoint, method, candidates, metadata, relay, evidence tier | Signaling peer info and forwarded ICE; missing WebRTC manager | Identify addresses and libp2p routes; no complete AutoNAT client path | IICP already has the richer schema; add freshness/provenance, not fields copied from an overlay. |
| NAT traversal | Existing ICE-style research, UPnP/tunnel/relay ladder and SDK paths | Intended WebRTC ICE; implementation missing at inspected commit | Rich API surface, but several mechanisms mocked or incomplete | No new P0 gap. Continue current IICP evidence gates. |
| Rendezvous | Directory route selection and experimental relay/browser paths | WebSocket signaling server | Bootstrap peers and relay-server behaviour | Relay eligibility and browser rendezvous remain #59/browser #4. |
| Direct transport | HTTP/native TCP; QUIC remains evidence-gated | Intended WebRTC data channel; absent manager | Active libp2p TCP/WebSocket; configured QUIC flag not wired | Do not use QuDAG as QUIC evidence for IICP #42. |
| Relay fallback | Experimental IICP relay and route metadata | Contribution relay; WebRTC relay claim not verifiable from current code | Relay server and DCUtR event handling; incomplete client workflow | Useful failure cases for #59, not portable code. |
| Browser support | Experimental browser node and proposed WebRTC advertisement | Strong browser resource detection; incomplete P2P bundle | WASM claims were not an end-to-end focus of this review | Resource projection can help browser providers; lifecycle/reachability evidence remains incomplete. |
| Transient node handling | Heartbeat expiry, dormant/reactivation, re-registration | Disconnect removal, last-seen data and reconnect | Swarm events, ping and mDNS expiry | IICP should keep identity continuity separate from current connection identity. |
| Federation | Signed snapshot/event-tail directory federation | No comparable directory federation; P2P/Firebase migration design | P2P overlay, not directory federation | These solve different problems and should not be merged. |

## Cold-start sequences

### IICP provider

```text
fresh provider
→ load explicit directory URL or Genesis fallback
→ load/create node and optional operator identity
→ detect/configure a routable endpoint and transport evidence
→ REGISTER identity, capabilities, limits and route metadata
→ directory probes policy and endpoint, then issues a node token
→ provider heartbeats load, active jobs, availability and model health
→ consumer queries a directory by intent and constraints
→ consumer receives a route or dispatch ticket
→ consumer connects directly or through an eligible relay
→ first CALL executes outside the directory
```

Implementation-specific points remain: how a provider obtains its first non-default trusted directory, how a browser establishes WebRTC, and how candidate freshness is expressed beyond heartbeat/route evidence.

### Edge-Net contribution daemon

```text
fresh daemon
→ load/create contribution identity and create a session node ID
→ connect to configured WebSocket relay
→ register public key, coarse capabilities and version
→ receive welcome/network count
→ heartbeat and report contribution to the relay
→ relay acknowledges credits
→ reconnect after connection loss
```

The inspected daemon does not expose an independently selected peer execution path.

### Edge-Net P2P design

```text
fresh P2P node
→ create or load node identity
→ initialize QDAG and ledger
→ initialize Firebase bootstrap or local signaling
→ initialize WebRTC and DHT
→ discover peer through bootstrap/signaling
→ exchange offer, answer and ICE through signaling
→ establish data channel
→ announce and exchange tasks
```

This sequence is architectural intent, not a runnable sequence at the inspected commit, because two imported bootstrap/WebRTC modules are absent.

### QuDAG `P2PNode`

```text
fresh node
→ generate libp2p Ed25519 identity
→ build active TCP/memory and optional WebSocket transport
→ listen on configured multiaddresses
→ add configured bootstrap peers to Kademlia and bootstrap
→ add mDNS discoveries and Identify addresses to routing state
→ connect, publish through Gossipsub or send CBOR request-response
→ use ping/swarm events for connection liveness
```

The inspected path does not automatically discover a trusted global bootstrap set, advertise IICP-style service capabilities, or prove a complete relay-to-direct upgrade.

## Edge-Net execution-surface assessment

**Verdict: PARTIALLY.**

An Edge-Net gateway could register as an IICP provider today for a bounded intent that it can execute behind one stable provider endpoint. IICP would discover the gateway through normal registration and determine current route eligibility through the existing heartbeat and reachability fields. The gateway, not IICP, would own Edge-Net peer selection, contribution policy, retries and local scheduling.

The minimum adapter boundary is:

```text
IICP CALL and negotiated profiles
→ validate intent, constraints, timeout and idempotency key
→ map to one Edge-Net task type and capability set
→ submit once to the Edge-Net fabric
→ translate accepted/partial/terminal state
→ map cancellation and timeout without claiming unsupported backend control
→ return an IICP terminal result and redacted node receipt
```

What already works at the IICP boundary:

- intent and model/capability discovery;
- maximum concurrency, active-job load and availability;
- endpoint and relay-aware route selection;
- direct task delivery outside the directory;
- negotiated lifecycle and receipt semantics.

What is missing before a useful PoC:

1. a reviewed general resource/capacity projection under #4;
2. a real, stable Edge-Net task endpoint rather than missing P2P imports or a contribution-only relay;
3. verified streaming, cancellation and error mapping under #89;
4. an explicit privacy decision about hardware/resource fields;
5. replay-safe task/result correlation and evidence that a terminal Edge result is not a self-reported contribution event.

No IICP wire change is yet justified. A PoC becomes useful only after #4 defines the smallest general descriptor and an Edge-Net execution path can be exercised end to end. Until then, a synthetic adapter would test the adapter itself rather than the proposed execution fabric.

## Ranked findings and issue disposition

| Rank | Finding | Disposition |
|---|---|---|
| P1 | A general provider profile should distinguish supported resources, currently allocatable capacity and the evidence/freshness of both. | Existing IICP #4. Add Edge-Net evidence; no new issue. |
| P1 | Transient browser/edge providers need capability and route freshness without binding persistent operator identity to a connection/session identifier. | Existing IICP #4, #59, #63 and browser-node #4. |
| P1 | A generic external execution fabric can fit behind IICP, but only after lifecycle and capacity contracts are implemented and tested. | Sequence #4 and #89 before revisiting IICP #6. No Edge-Net-specific issue yet. |
| P2 | Local mDNS is useful bootstrap prior art, while DHT membership is outside IICP's current directory boundary. | Add QuDAG evidence to #39; reject a general IICP DHT. |
| P2 | Relay/rendezvous design must keep discovery, connection establishment and task routing separate. | Add Edge signaling and QuDAG limitations to #59 and browser-node #4. |
| P2 | Protocol-visible observations should stay portable while adaptive selection algorithms remain local. | Existing #98 and #4. |
| P3 | QuDAG is useful prior art for optional post-quantum algorithm agility, but not for a current transport profile. | Watch under #52; no implementation work. |
| Reject | DAG consensus, token economics, `.dark` naming, onion routing, full overlay management, Edge-Net runtime/scheduler, RuVector storage and learning algorithms. | Outside IICP core. They may exist behind a provider. |

No new GitHub issue is required. The concrete questions map to active, correctly owned issues, and a new Edge-Net umbrella would duplicate them.

## Small roadmap and scheduling

This research should not displace the current quality and parity milestones.

1. **Current foundation work:** finish already-authorized conformance and Rust directory decomposition slices. Do not change releases, production routing or wire semantics for this research.
2. **Capacity decision checkpoint:** when IICP #4 is next selected, use this report to define a privacy-bounded resource/capacity projection. Require the fields to remain useful for browser workers, home GPUs, university clusters and cloud providers if Edge-Net disappears.
3. **Reachability checkpoint:** when #39, #59 or browser-node #4 becomes active, add candidate freshness, identity-continuity and discovery/connection/routing separation cases. Do not add a DHT or port QuDAG NAT code.
4. **Lifecycle implementation checkpoint:** complete #89 across SDK and backend paths. This is a prerequisite for claiming an external execution fabric supports streaming or cancellation.
5. **Interop decision:** revisit IICP #6 only after an Edge-Net endpoint can execute a real bounded task. Then decide whether a small adapter PoC adds evidence beyond the existing generic provider contract.
6. **Long-range watch:** consider post-quantum algorithm identifiers only while #52's envelope algorithm-agility decision is open and only with cross-language vectors.

## Direct answers

1. **What is deeper outside IICP?** Edge-Net has richer browser device/resource detection. QuDAG has an active composition of Kademlia, mDNS, Identify, Gossipsub, relay-server and DCUtR behaviours. Edge-Net design code also explores task claims and computation proofs.
2. **What belongs in IICP terrain?** Bounded resource advertisement, capability freshness, reachability evidence, identity continuity, lifecycle translation and portable observations. Overlay membership, scheduling and consensus do not.
3. **What helps IICP without Edge-Net?** Separating supported capacity from allocatable capacity, attaching freshness/provenance, and keeping discovery, reachability and connection establishment distinct.
4. **What expands the execution surface?** A general resource/capacity profile plus implemented lifecycle adapters would support browser workers, home GPUs, clusters and other execution fabrics.
5. **Does IICP separate the concerns?** Mostly. The specification already distinguishes directory bootstrap, provider discovery, capabilities, route candidates, reachability evidence and task routing. Candidate/capability freshness and browser connection establishment still need firmer profile evidence.
6. **Is IICP sufficient for transient browser/edge nodes?** Partially. Heartbeat expiry and route metadata exist, but WebRTC operation, transient capability freshness and persistent-identity/session separation lack complete cross-implementation evidence.
7. **Is Edge-Net relay/genesis prior art useful?** The signaling message separation and reconnect flow are useful. The inspected P2P/genesis path is incomplete and should not be ported.
8. **Is QuDAG discovery prior art useful?** Yes for understanding mDNS/Kademlia/Identify roles and their separation. It does not justify making IICP a P2P overlay.
9. **What stays outside IICP?** DAG consensus, token settlement, `.dark` naming, onion routing, full overlay management, compute runtimes, scheduler internals and RuVector learning/storage algorithms.
10. **Which issues were opened?** None. Open issues #39, #52, #54, #55, #59, #63 and #98 own the remaining justified questions; closed #4 and #89 retain the delivered admission and streaming evidence.
11. **Is a PoC justified now?** No. Reassess only after a runnable Edge-Net task path exists and the current layered capability work shows that an adapter needs evidence beyond the generic provider contract. The eventual PoC should require no Edge-Net-specific IICP wire field.
