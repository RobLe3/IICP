# NAT Traversal — Prior-Art Survey

**Date**: 2026-05-26 (iter-1381)
**Issue**: [#328](https://github.com/RobLe3/iicp.network/issues/328) — NAT-aware client + node architecture
**Maintainer directive**: 2026-05-26 *"we need to make the clients/nodes NAT aware and NAT enable with automatic adaption to the circumstance if NAT is detected"*

---

## Why this survey exists

#325 (endpoint validation) + #326 (public/internal split) address the symptom: localhost endpoints landing in the public directory. They do not solve the underlying problem — **most home / SME / mobile / corporate-wifi operators are behind NAT and cannot trivially expose a routable endpoint**.

Without NAT-awareness, the IICP node-operator population is bounded by:
- Owners of VPS-class infrastructure with public IPv4/IPv6
- Operators willing to configure router port-forwarding + dynamic DNS
- Users of external tunnels (Cloudflare Tunnel, ngrok, Tailscale) — adds a non-IICP dependency to the protocol value-prop

This is a tiny fraction of the addressable mesh-joiner population. NAT-awareness is therefore not a feature — it's an adoption precondition.

This document surveys five mature ecosystems that have already solved related variants of this problem. Each section: what it does, what we can borrow, what we should explicitly NOT borrow, and where it fits in the IICP architecture.

---

## 1. WebRTC ICE (Interactive Connectivity Establishment) — RFC 8445

### What it is

A standardized peer-to-peer connection establishment framework used by every browser RTC stack (Chrome / Firefox / Safari). Solves the same problem we have: two endpoints behind unknown NATs need to talk to each other.

### Architecture (high-level)

1. **Candidate gathering**: each endpoint collects multiple potential transport addresses:
   - **Host candidate** — its actual local IP/port (`192.168.1.10:9000`)
   - **Server-reflexive (srflx)** — the public IP/port the STUN server saw it from (`203.0.113.5:43210`)
   - **Relay candidate** — an address on a TURN server willing to forward traffic
2. **Candidate exchange**: endpoints swap their candidate lists via a signaling channel (out-of-band — could be the IICP directory).
3. **Connectivity checks**: each endpoint sends STUN binding requests across every (local-candidate, remote-candidate) pair, in priority order. First one to succeed wins.
4. **Promotion**: the winning pair becomes the data path. Higher-priority pairs continue probing in the background; if one becomes viable later, it can take over.

### What's directly transferable to IICP

- **The candidate model** maps cleanly to our needs: a node registers not a single endpoint but a set of candidate transport addresses with priority weights. Discover returns the candidate set; clients perform connectivity checks.
- **STUN itself** is small, well-specified, easy to host. The IICP directory could double as a STUN server (or recommend a public one like `stun.l.google.com:19302`).
- **The priority calculation** (RFC 8445 §5.1.2.1) is a battle-tested formula for which candidate to try first — re-use it directly, don't reinvent.

### What we should NOT borrow

- **Trickle ICE** (RFC 8838) — candidates streamed incrementally as gathered. Our flow is REST-based discover-then-dispatch, not a long-lived signaling channel. Stick to all-candidates-in-the-response.
- **ICE's full state machine** — designed for symmetric peer-to-peer media flows. Our flow is asymmetric (client→node) with the directory in the middle. Simplify by treating the node as the answerer and the client as the offerer.
- **lite ICE** (the server-side simplification) doesn't quite fit either — the IICP adapter is more capable than a pure relay, so it should gather candidates normally.

### Effort estimate

- Adapter side: ~3-5 days. Use `aioice` or `python-stun` library; integrate into `iicp-adapter` startup.
- Spec side: ~1-2 days. Add `transport_candidates[]` array to register payload + discover response; reference RFC 8445 §5.1.2.1 priority formula by inclusion.

### IICP fit verdict

**High fit.** ICE is the obvious foundation. We don't need media-streaming features but we benefit from the candidate-priority math and the STUN protocol. **Recommend: adopt ICE candidate model + STUN candidate gathering as the core of ADR-041.**

---

## 2. libp2p — multi-transport peer networking

### What it is

The networking layer underlying IPFS, Filecoin, Ethereum 2.0, Polkadot. Designed from the start as a "swiss army knife" for P2P networking — supports many transports (TCP, QUIC, WebSocket, WebRTC, WebTransport, Bluetooth) under a uniform addressing model.

### Architecture (high-level)

1. **Multiaddr** format: every peer is addressed as `/ip4/203.0.113.5/tcp/9000/p2p/QmHash`. The `multiaddr` library composes transports; a peer can advertise multiple multiaddrs at once.
2. **Transport upgraders**: when establishing a connection, libp2p tries each multiaddr in parallel; first connect wins. Security (Noise / TLS) and multiplexing (yamux / mplex) layers stack on top of any transport.
3. **AutoNAT** + **AutoRelay** + **Hole punching v2** (DCUtR — Direct Connection Upgrade through Relay):
   - **AutoNAT**: a peer asks other peers to dial it back from their POV; if dial succeeds, peer is publicly reachable. Otherwise, peer is behind NAT.
   - **AutoRelay**: NAT-bound peer auto-discovers public relay nodes from a known set (DHT-based or operator-configured), reserves a relay slot, advertises its relay address.
   - **DCUtR**: clients connecting to a relay-advertised peer first try direct (hole-punching with STUN-derived addresses); on success they upgrade off the relay; on failure they fall back to relay.

### What's directly transferable to IICP

- **The multi-address advertising model** is a stronger version of ICE candidates. We could use multiaddr literally (`/ip4/203.0.113.5/tcp/8090/iicp/<node_id>`) or we could borrow just the conceptual frame.
- **AutoNAT** is the right pattern: instead of trusting the node to self-report its NAT type, have the IICP directory (or a sibling node) dial back from a different network. If success, mark `nat_type=direct`; otherwise the node MUST advertise via relay.
- **DCUtR's three-phase pattern** (relay-reserve → coordinated hole-punch → upgrade) is sophisticated and well-tested. If we use TURN-style relays, this is the right state machine.

### What we should NOT borrow

- **Full libp2p as a dependency.** It's a massive runtime; pulling it in for one feature is heavy. Re-implementing the patterns is cheaper than depending on the ecosystem.
- **Kademlia DHT for relay discovery.** Our directory is centralized (with TOM federation in flight); use the directory's own registry of relay-capable nodes, not a DHT.
- **Multistream-select / protocol negotiation.** We have a single protocol (IICP) on a single port. Don't import this complexity.

### Effort estimate

- Conceptual adoption: low (mostly spec writing).
- Implementation: ~1 week for AutoNAT-style probe + relay registration + DCUtR-style upgrade path.

### IICP fit verdict

**High fit, but adopt patterns not dependencies.** Re-implement AutoNAT in `iicp-adapter`; specify multiaddr-style transport advertisement in S.13 §register; document DCUtR as the reference state machine for relay→direct upgrade.

---

## 3. Tailscale — wireguard-mesh + DERP relays

### What it is

A commercial mesh-VPN built on WireGuard. Handles NAT traversal so seamlessly that users don't know they're behind NAT. Has the best operational track record of any NAT-traversal system in production.

### Architecture (high-level)

1. **DERP** (Designated Encrypted Relay for Packets): Tailscale-operated relay servers in many regions. Every Tailscale client maintains a persistent outbound connection to its nearest DERP. **All traffic can be relayed through DERP, but the system prefers direct.**
2. **STUN-style direct path setup**: clients exchange candidate addresses via the Tailscale coordination server; attempt direct WireGuard connections; if successful, traffic flows direct.
3. **Pluggable relay**: if direct fails (symmetric NAT both sides — ~7-10% of pairs in field measurements), traffic flows through DERP as fallback. WireGuard tunneling is end-to-end encrypted so DERP sees only ciphertext.
4. **NAT detection at startup**: client probes a known IP twice from different ports; if outbound source port changes, NAT is symmetric. Otherwise, NAT is cone-class.

### What's directly transferable to IICP

- **The fallback-to-relay design** is robust. Aggressively prefer direct; relay only when needed. The relay servers should always exist as a safety net but should rarely carry traffic in steady state.
- **NAT-type probe via source-port observation** is simpler than full STUN binding tests for the common case. Re-use this for adapter startup.
- **"Outbound-only persistent connection" pattern**: every adapter holds an outbound connection to a directory or relay even when not actively serving. Cheap; turns the firewall problem into a non-problem since the adapter punched out first.

### What we should NOT borrow

- **WireGuard itself** — wrong layer. IICP rides on HTTPS, not L3 VPN.
- **The "everyone gets a unique IP" model** — Tailscale gives each device a 100.x.x.x address. IICP is service-discovery, not naming; we don't need addresses, we need endpoints.
- **DERP's cost model**: Tailscale runs and pays for DERP servers. We need a federated relay model where operators or the directory provide relays opt-in (#328 Q4).

### Effort estimate

- Adapter NAT-type probe: ~2 days.
- IICP-relay protocol (reverse-tunnel via outbound WebSocket/QUIC): ~1 week + spec amendment to ADR-001 (or carve a relay-specific exception).

### IICP fit verdict

**Medium-high fit.** The fallback-relay pattern is the right safety net. The "always outbound" optimisation is huge — solves NAT, double-NAT, mobile carrier NAT, and corporate firewall in one shot. **Recommend: spec a relay-mode opt-in for adapters; relay can be the IICP directory itself OR a separate "iicp-relay" operator type.**

---

## 4. Cloudflare Tunnel (cloudflared)

### What it is

A vendor-specific tunneling product. Operator installs `cloudflared` on their machine; it opens an outbound TLS connection to Cloudflare's edge; Cloudflare exposes a public hostname that proxies through the tunnel.

### Architecture (high-level)

1. Operator runs `cloudflared tunnel run`, authenticating to their Cloudflare account.
2. Tunnel maintains persistent outbound TLS connections to multiple CF edges.
3. Cloudflare provisions a `*.trycloudflare.com` (free, ephemeral) or named hostname (registered domain required).
4. Public HTTPS requests to that hostname route through CF edge → tunnel → operator's local service.

### What's directly transferable to IICP

- **The "operator runs nothing public-facing" UX** is the gold standard for adoption. Zero router config; works behind double-NAT and corporate firewalls.
- **The TLS-tunnel-out approach** is conceptually clean — pure outbound, no inbound port exposed, no STUN/TURN gymnastics.
- **The operator-side tooling story**: a single binary, single command, immediate hostname. We should aim for `iicp-adapter --use-tunnel cloudflare` or similar to be a one-flag deployment.

### What we should NOT borrow

- **Single-vendor dependency.** Cloudflare Tunnel works because Cloudflare runs the relay. If IICP depended on CF, the mesh is a CF subsidiary. Wrong governance model. We could RECOMMEND CF Tunnel as one option but the protocol must not require it.
- **Tunnel-as-only-path.** CF Tunnel gives up direct connection always; relays everything. For latency-sensitive workloads, direct is better when available. Adopt as fallback OPTION but keep direct as primary.

### Effort estimate

- Documentation only: ~1 day (operator setup guide showing CF Tunnel as one option).
- Integration: ~0 days — CF Tunnel is transparent to IICP; the adapter just sees a public URL.

### IICP fit verdict

**Recommendation-grade fit, not architectural.** CF Tunnel + similar (ngrok, Tailscale Funnel, bore) are reasonable external-tunnel options to document for operators who can't do anything else. They should be the bottom of the priority list, not the protocol's traversal strategy.

---

## 5. BitTorrent µTP / NAT-PMP / UPnP

### What it is

The deeply pragmatic NAT-traversal approach used by BitTorrent and many P2P apps for ~15 years. UPnP (Universal Plug and Play) and NAT-PMP (NAT Port Mapping Protocol — Apple) let an application request a port forward from the local router via in-LAN broadcast. PCP (Port Control Protocol — RFC 6887) is the modern unified replacement.

### Architecture (high-level)

1. Adapter discovers the local router via SSDP (UPnP) or by querying the default gateway (NAT-PMP / PCP).
2. Adapter requests a port mapping: "forward external port 8090 to my internal 8090 for the next hour."
3. Router (if it supports the protocol AND has it enabled) creates the mapping and responds with the external IP it will use.
4. Adapter advertises that external IP:port as its public endpoint.
5. Mapping auto-renews every ~30 minutes.

### What's directly transferable to IICP

- **It's the lowest-friction option that doesn't require external infrastructure.** Most consumer routers ship with UPnP enabled (Eero, Google Wifi, FRITZ!Box, ASUS, TP-Link, etc.). Many SME routers expose PCP. When it works, it works perfectly.
- **Adapter integration is small.** Python's `aiopynat-pmp` or `upnpclient` libraries; ~50-100 lines.
- **When the mapping fails or the router rejects it, we already know we need to fall back to relay.** It's a useful **detection signal**, not just a connectivity primitive.

### What we should NOT borrow

- **Trust the mapping uncritically.** UPnP has had security CVEs (Universal Plug and Pwn, UPnPProxy). The adapter must verify externally that the mapping works (dial-back from the directory) before advertising it. Don't trust the router's claim.
- **Run a TURN-style relay on top of UPnP.** UPnP gives us a public port; STUN candidate gathering against that is fine. Adding a relay layer on top of a working UPnP mapping is wasteful.

### Effort estimate

- Adapter implementation: ~2-3 days including verify-dial-back.
- Spec: low — just a `nat_traversal_method` enum value in the register payload.

### IICP fit verdict

**Tier-1 fallback below "direct public IP" and above "STUN+relay".** Should be the first thing every adapter tries automatically. **Recommend: ship UPnP support in v1.x of `iicp-adapter`; it's the cheapest reachability win available.**

---

## Synthesis — proposed traversal hierarchy for IICP

Ordered from preferred to last-resort:

| Tier | Method | Detection | Latency | Reliability | When to use |
|------|--------|-----------|---------|-------------|-------------|
| **0** | **Direct public IP** | adapter's external IP == its local IP, or operator-configured | Lowest | Highest | VPS / dedicated server / DMZ host |
| **1** | **UPnP / NAT-PMP / PCP mapping** | router supports + accepts request + verify-dialback passes | Low (~5ms extra) | High when supported | Home routers, most consumer ISPs |
| **2** | **STUN + ICE direct (hole-punched)** | full-cone or restricted-cone NAT both sides | Medium (~10-30ms extra setup) | ~70-85% of NAT pairs | Symmetric-restricted NAT on one side |
| **3** | **TURN-style relay via federated IICP relay nodes** | symmetric NAT both sides OR all-of-above failed | High (added RTT through relay) | ~100% | Last-resort for currently-unreachable peers |
| **4** | **External tunnel (operator-configured)** | adapter starts with `--tunnel cf` or similar | Variable | Vendor-dependent | Recommended option for operators who can't ship public IPs themselves |

### Detection sequence at adapter startup

```
adapter_start():
    if operator_configured_public_endpoint:
        return tier_0(operator_endpoint)
    
    upnp_result = try_upnp_with_dialback_verify(timeout=5s)
    if upnp_result.success:
        return tier_1(upnp_result.public_endpoint)
    
    nat_type = stun_probe(stun_servers)
    if nat_type in {full_cone, restricted_cone}:
        register_with_stun_candidates_for_ice()
        return tier_2
    
    if nat_type == symmetric and configured_relay:
        reserve_relay_slot(configured_relay)
        return tier_3
    
    return tier_4_with_operator_guidance()
```

### Wire-format additions (preview for ADR-041)

- `nodes` table gains:
  - `nat_traversal_method` enum: `direct | upnp | stun_hole_punch | turn_relay | external_tunnel`
  - `transport_candidates` JSON array: each candidate = `{type, address, port, priority, foundation}`
  - `relay_endpoint` (nullable) — if `nat_traversal_method=turn_relay`, the relay node serving as proxy
- `discover` response includes `transport_candidates[]` so clients can do ICE-style priority checks.
- New event type `RELAY_RESERVATION` in S.13 federated log when a node binds to a relay slot.

---

## Open research questions

(These are the Q1-Q6 from #328, now informed by the prior-art survey:)

### Q1. NAT detection
**Answer informed by survey**: combine UPnP probe (cheap, succeeds for ~60% of consumer routers per Tailscale public stats) with STUN-style outbound-port observation (catches the cases UPnP doesn't). Tailscale's approach is the right pattern.

### Q2. Traversal strategy
**Answer informed by survey**: 5-tier hierarchy above. UPnP must be tried first; tier-4 (external tunnel) is operator-elective, not protocol-driven.

### Q3. Wire-format
**Answer informed by survey**: adopt the ICE candidate model (from §1) lightly. `transport_candidates[]` array with `{type, address, port, priority}` is sufficient. No need for full RFC 8445 protocol — just borrow the data shape.

### Q4. Trust + security
**Open questions remain**:
- Who runs TURN-style relays? IICP directory operators? Independent relay operators with their own credit economy? **Recommended next research step**: file ADR-041 with relay-operator-role analysis.
- Does relay-mode break ADR-001 (directory NEVER sees task traffic)?
  - **If the relay is the directory itself**: yes, breaks ADR-001 strictly.
  - **If the relay is a sibling "iicp-relay" service**: doesn't break ADR-001 because the directory remains relay-unaware.
  - **Recommend**: spec relays as a separate service role (BC-13 candidate); directory only stores the relay→relay-capable-node mapping, never the task traffic.

### Q5. Layer choices
**Answer informed by survey**: HTTP/2 + Binary Framing is TCP-based; STUN/ICE work for TCP candidates too (RFC 6544). QUIC would offer better NAT-traversal properties but is a bigger spec change. **Recommend phase split**: ADR-041 covers TCP-based traversal (UPnP + STUN-TCP + relay); a follow-on ADR can spec QUIC migration when timing allows.

### Q6. Adoption framing
**Answer**: the entire 5-tier hierarchy needs to be invisible to the operator. `iicp-adapter` runs through the hierarchy automatically; surfaces a friendly status (`✓ Direct connection available` / `✓ UPnP mapping active` / `✓ Connected via STUN hole punch` / `✓ Connected via relay`). Operator only intervenes if all four tiers fail.

---

## Recommended next steps

1. **ADR-041 draft** (next research deliverable): formal proposal of the 5-tier hierarchy + wire-format additions. ~2 days work.
2. **PoC: UPnP-only `iicp-adapter`** (the cheapest win): adapter auto-detects + auto-maps via UPnP at startup, registers external endpoint. ~3 days. Could ship as Phase 5.x feature.
3. **Spec amendment outline**: which sub-specs (iicp-core / iicp-dir / iicp-adapter) need changes. ~1 day.
4. **Relay-operator role analysis**: BC-13 candidate, credit-economy interaction, trust model. ~1 week research → ADR-042 if it warrants its own ADR.
5. **STUN server choice**: stand up a public IICP STUN service, recommend public alternatives, or rely entirely on operator-configured. ~1 day decision.

---

## References

- RFC 8445 — Interactive Connectivity Establishment (ICE)
- RFC 8838 — Trickle ICE
- RFC 5389 — Session Traversal Utilities for NAT (STUN)
- RFC 5766 — Traversal Using Relays around NAT (TURN)
- RFC 6887 — Port Control Protocol (PCP)
- libp2p AutoNAT spec: github.com/libp2p/specs/blob/master/autonat
- libp2p DCUtR spec: github.com/libp2p/specs/blob/master/relay/DCUtR.md
- Tailscale "How NAT traversal works": tailscale.com/blog/how-nat-traversal-works
- Cloudflare Tunnel docs: developers.cloudflare.com/cloudflare-one/connections/connect-networks
- BitTorrent BEP 32: stigmund.bitcheese.net/bep-0032.html (UPnP usage in BT)
- IICP issues: [#325](https://github.com/RobLe3/iicp.network/issues/325), [#326](https://github.com/RobLe3/iicp.network/issues/326), [#328](https://github.com/RobLe3/iicp.network/issues/328)
- Maintainer directive 2026-05-26
