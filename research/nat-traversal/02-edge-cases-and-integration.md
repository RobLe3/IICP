# NAT-Traversal — Edge Cases + Integration Strategy

**Date**: 2026-05-26 (iter-1394)
**Trigger**: Live UPnP test against maintainer FRITZ!Box 6591 + VPN exposed a class of bugs the original PoC didn't anticipate. Maintainer directive: *"make sure you test more edge cases regarding the VPN, NAT and UPNP detection and it also would probably make sense to think about including this either in the dependencies or maybe add this as part fo the code within the different clients"*.

**Companion to**: `01-prior-art-survey.md` (the high-level design) + `project/decisions/ADR-041.md` (the architectural decision).

---

## Why this matters

The PoC shipped iter-1384 passed 7 unit tests AND the maintainer's environment surfaced 2 bugs the tests didn't catch:

1. **VPN tunnel IP confusion** — `socket.connect(("8.8.8.8", 80))` returns the VPN tunnel IP (10.234.x), not the LAN IP. Passing this to FRITZ!Box's `AddPortMapping` made the FRITZ!Box reject the mapping.
2. **Misdiagnosis of CGNAT** — `GetExternalIPAddress` returning `None` was due to UPnP auth, not CGNAT. The PoC's `operator_guidance` for tier-4 was misleading.

Both bugs come from the same root cause: **the original PoC assumed a single-interface, no-VPN, no-auth network environment**. Real adopters don't live in that environment. This document catalogs the realistic environments that will fail today's code, and proposes the test + code structure that handles them.

---

## 1. Edge case taxonomy

### 1.1 VPN edge cases (the maintainer's case + variants)

| # | Scenario | What breaks today | Fix difficulty |
|---|----------|-------------------|----------------|
| V1 | Full-tunnel VPN with LAN access (default for WireGuard, Tailscale, most corporate VPNs) | `_detect_local_ip_for_default_gateway` returns VPN IP; UPnP `AddPortMapping` rejected for wrong InternalClient | ✅ Fixed iter-1393 (IGD-LAN-subnet matching) |
| V2 | Full-tunnel VPN WITHOUT LAN access | SSDP discovery fails entirely (multicast doesn't cross tunnel); tier-1 unreachable | Hard — needs VPN config change, not code |
| V3 | Split-tunnel VPN (LAN local, internet via VPN) | Same as V1 for routing; SSDP works | ✅ Fixed iter-1393 |
| V4 | Multiple concurrent VPNs (Tailscale + corp VPN + WireGuard) | Multiple non-LAN interfaces; current code picks first match | Medium — need priority sort (LAN before tunnel before VPN) |
| V5 | VPN with conflicting RFC1918 ranges (corp VPN uses 192.168.178/24, FRITZ!Box also 192.168.178/24) | LAN-IP heuristic matches both; might pick wrong interface | Medium — need interface-level (not just IP-range) matching |
| V6 | VPN connects/disconnects mid-session | Cached LAN IP becomes stale; new mappings fail | Hard — needs runtime re-detection or netlink watch |
| V7 | IPv6-only LAN, IPv4-VPN | UPnP discovery should still work over IPv6; current code is IPv4-only | Hard — full IPv6 UPnP path needed |

### 1.2 NAT edge cases

| # | Scenario | What breaks today | Fix difficulty |
|---|----------|-------------------|----------------|
| N1 | True CGNAT (100.64.0.0/10 WAN, no public IPv4) | UPnP succeeds locally but external reachability fails silently | Medium — verify-dial-back (ADR-041 invariant 3) needed; would catch in seconds |
| N2 | Double NAT (router behind router) | First NAT's IGD knows nothing about second NAT; mapping leaks to wrong scope | Hard — needs multi-hop traceroute + cascading IGD discovery |
| N3 | IPv6 with no IPv4 (rare in EU, common APAC mobile) | All current code paths are IPv4-only | Hard — full IPv6 UPnP-IGD-v2 path |
| N4 | Multi-WAN router (load-balanced internet links) | First WANIPConn service might not be the one inbound traffic comes through | Medium — query all WAN services, prefer the one with non-null external IP |
| N5 | Router with VLAN segmentation (separate LAN per VLAN, separate IGD per VLAN) | Multiple IGDs respond; current code picks first | Medium — filter by "matches my subnet" |
| N6 | Container/WSL2/Hyper-V networking (separate virtual switch) | Current LAN IP heuristic might match a virtual interface that's not actually on the IGD's LAN | Easy — already largely handled by /24 matching, but virt-net interfaces sometimes alias real ones |
| N7 | Captive portal (hotel wifi, conference network) | UPnP discovery may succeed but external traffic is blocked at L7 by portal | Hard — needs HTTP-level reachability check, not just TCP probe |

### 1.3 UPnP-specific edge cases

| # | Scenario | What breaks today | Fix difficulty |
|---|----------|-------------------|----------------|
| U1 | IGD requires auth for AddPortMapping (FRITZ!Box default in some configs, Asus AiProtection) | Returns UPnP error 606 / 718; we log but can't recover | Medium — UPnP IGD AAA spec exists; supply credentials |
| U2 | IGD rate-limits AddPortMapping (Eero, some Google Wifi configs) | Returns UPnP error 502; would need retry-with-backoff | Easy — add retry on 502 |
| U3 | Multiple IGDs on the network (mesh wifi: primary + satellite both expose IGD) | First-match might be the wrong device (satellite, not main router) | Medium — prefer IGD whose subnet matches the default gateway |
| U4 | IGD reports success but mapping silently fails (router bug or NAT-PMP/UPnP race) | Silent failure; we trust the success and advertise an unreachable URL | Medium — verify-dial-back (ADR-041 invariant 3) |
| U5 | IGD has stale state from previous run (mapping persists, but on wrong InternalClient) | New mapping attempt rejected with 718 "ConflictInMappingEntry" | Easy — DeletePortMapping first, then AddPortMapping |
| U6 | Router supports NAT-PMP / PCP but NOT UPnP-IGD (Apple AirPort, some MikroTik) | upnpclient's SSDP discovery returns nothing | Medium — add natpmp library as alternative |
| U7 | SSDP timeout because switch has IGMP snooping (enterprise networks) | Discovery times out | Easy — increase timeout; document SSDP requirement |
| U8 | UPnP discovery returns devices but no WANIPConn service (some printers, smart TVs) | Current code correctly skips these | ✅ Already handled |
| U9 | IGD reports `WANIPConnection:2` but our code only matches `WANIPConnection:1` (legacy) | Current code uses substring match `"WANIPConn"` which catches both | ✅ Already handled |

### 1.4 Cross-component edge cases (where the logic should live)

| # | Scenario | Implications |
|---|----------|--------------|
| X1 | iicp-proxy needs to know if outbound is via VPN (latency budget changes) | Currently doesn't matter for proxy; adapter is the relevant side |
| X2 | iicp-adapter on a server (no VPN, public IP) — tier-0 trivial | Detection should short-circuit to tier-0 ASAP without wasting time on UPnP |
| X3 | iicp-node (Rust) — needs equivalent in Rust | Cross-language code duplication concern |
| X4 | iicp-adapter inside Docker (NAT'd to host network OR bridged) | Container detection should disable UPnP attempts (router can't reach container) |
| X5 | iicp-adapter on Kubernetes (pod network, service mesh) | UPnP completely inappropriate; tier-3 relay is the only path |
| X6 | iicp-client (the SDK) doesn't care about NAT detection — it just connects to whatever discover returns | Confirms: NAT detection is adapter-side only |

---

## 2. Where should the code live?

### 2.1 Adapter-only (current state)
**Pros**: minimal scope, no cross-component coupling, only the side that needs reachability does the work.
**Cons**: if iicp-node (Rust) ships its own adapter mode, we need a Rust port; future iicp-relay would also need it.

### 2.2 Shared library
**Option A**: Python package `iicp-nat` distributed via PyPI; adapter + proxy + future-relay depend on it.
**Option B**: Cross-language spec (`spec/iicp-nat.md`) with reference implementations in Python + Rust + JS.

**Recommendation**: **Option A for Phase 5.x** (Python-only shipping today; adapter is the only consumer). **Option B for Phase 6+** once iicp-node and iicp-relay need it too. Keep the Python module `adapter.network.nat_detector` for now — extract to `iicp-nat` only when there's a second consumer.

### 2.3 In-proxy NAT awareness (do clients need this?)
Probing the maintainer's case: clients (`iicp-proxy`) sit BEHIND a NAT making OUTBOUND connections. They don't need port forwarding. Their concern is:
- "Can I reach the adapter at the URL discover returned?" — this is a connectivity-check, not NAT-detection.
- "How long should I wait?" — latency budget concerns.

**Conclusion**: clients DON'T need NAT detection. They need *connectivity selection* over a candidate set (ICE-style priority checks per ADR-041 §3 wire-format), which is a different module. Filing that as a follow-on if/when transport_candidates[] becomes a real surface area.

---

## 3. Dependency strategy

### 3.1 Current state
- `upnpclient` is **lazy-imported** in `nat_detector.py` (graceful degradation when missing)
- `nat_detector.py` is **always imported** by adapter even when `auto_nat_detect=false`
- Tests pass without `upnpclient` installed (mocked)

### 3.2 Options

**A. Hard dependency** — add `upnpclient` to `pyproject.toml [project.dependencies]`.
- ✅ One install, no surprise tier-4-due-to-missing-dep
- ❌ Pulls in `lxml` (C extension, fails on some musl-based Alpine containers) + `requests` + `six` (~10 MB of deps, 4 transitive)
- ❌ Hard-blocks adapter install on platforms where `lxml` doesn't have a wheel

**B. Optional extra** — `pip install iicp-adapter[nat]` pulls upnpclient; default install skips it.
- ✅ Existing operators unaffected
- ✅ Opt-in by operators who want the feature
- ✅ Modern Python packaging idiom
- ❌ Two-step install for the operator (`[nat]` extra not obvious from `pip install iicp-adapter`)

**C. Vendored minimal implementation** — write our own ~150-line SSDP + UPnP-IGD client; ship in-tree.
- ✅ Zero external deps for the common case
- ✅ Full control over edge cases (auth, retries, IPv6)
- ❌ Re-implements a battle-tested library; risk of subtle bugs
- ❌ Maintenance overhead

**Recommendation**: **Option B (optional extra)** for Phase 5.x. Add `iicp-adapter[nat]` to pyproject.toml. Document prominently in the operator-facing docs. Migrate to Option C (vendored) only if Option B is shown to be a real install-friction problem in operator field-testing.

### 3.3 Cross-component: pyproject extras structure

```toml
# adapter/pyproject.toml
[project.optional-dependencies]
nat = ["upnpclient>=2.0.0"]
nat-full = ["upnpclient>=2.0.0", "ifaddr>=0.2.0", "natpmp>=1.1.0"]  # Phase 6 — adds NAT-PMP/PCP
```

Operators choose:
- `pip install iicp-adapter` — minimal, no NAT detection (tier-0 only via operator_public_endpoint)
- `pip install iicp-adapter[nat]` — UPnP for Phase 5.x
- `pip install iicp-adapter[nat-full]` — UPnP + NAT-PMP/PCP for Phase 6

---

## 4. Test coverage additions

To catch the iter-1393 class of bug at unit-test time (not field-test), add tests for:

### 4.1 LAN IP detection (VPN scenarios)
- `test_lan_ip_picks_lan_over_vpn` — mock `_detect_local_ip_for_default_gateway` to return VPN IP, mock IGD to return LAN gateway; assert helper picks LAN IP
- `test_lan_ip_falls_back_when_no_match` — IGD on subnet with no local interface; helper returns None; caller uses fallback
- `test_lan_ip_handles_multiple_matching_interfaces` — two local interfaces on the same subnet (e.g. en0 + bridge0); prefer the first non-loopback
- `test_lan_ip_ipv6_igd` — IGD reported via IPv6 location URL; current code doesn't try IPv6, document this gap

### 4.2 UPnP error classification
- `test_error_606_classified_as_auth_required` — surface in detection_log + tier-4 guidance
- `test_error_718_classified_as_conflict` — suggest "delete existing mapping first" hint
- `test_null_external_ip_classified_as_cgnat_or_auth` — current ambiguity — document both possibilities in log

### 4.3 IGD selection (multi-device LAN)
- `test_multiple_igds_prefer_default_gateway_match` — two IGDs respond; pick the one whose host matches `route -n get default`
- `test_skip_non_wan_devices` — currently handled; lock down with a positive test

These tests are achievable with mocks; no live router needed.

---

## 5. Recommendations summary

For Phase 5.x (next sprint):

1. **Keep `upnpclient` as optional extra**, not hard dependency. Add `iicp-adapter[nat]` to pyproject.toml.
2. **Add the iter-1394 test set** covering V1-V5, U1-U2, U5 (the achievable subset).
3. **Defer cross-language extraction**: iicp-nat as separate package waits until iicp-node or iicp-relay need it.
4. **Document the gap**: V2 (full-tunnel VPN without LAN access), V6 (mid-session VPN flip), V7 (IPv6-only), N1 verify-dial-back, N7 captive portal — all flag as "future work" with clear "what doesn't work today" wording.

For Phase 6+:

5. **Verify-dial-back is the highest-priority Phase 6 NAT work** — catches U4 (silent mapping failure), N1 (CGNAT trust gap), and the V6 VPN-flip case in a single probe.
6. **NAT-PMP / PCP fallback** as `iicp-adapter[nat-full]` extra — covers U6 (Apple/MikroTik routers without UPnP).
7. **IPv6-IGD support** when IPv6-only LANs become more common.
8. **Cross-language Rust port** when iicp-node grows an adapter mode OR when iicp-relay needs to register itself with NAT-awareness.

---

## 6. Open research questions (deferred)

- **Q-A** — How common is the "FRITZ!Box auth-required UPnP" config in EU consumer broadband? Estimate from field data once we have 10+ operators with auto_nat_detect=true.
- **Q-B** — Does Tailscale's WireGuard tunnel preserve enough source-port info for STUN candidates to work over it? (Affects Phase 6 tier-2 design.)
- **Q-C** — Is there an open spec for "I'm behind X kind of NAT/VPN, here's my preferred relay" that operators can configure in one line, vs the 5-tier detection ladder? Maybe libp2p's multiaddrs are the right model — TBD.
- **Q-D** — Operator-experience: when tier-4 fires, the operator gets the multi-option guidance message. Should we also surface an HTTP endpoint on the adapter (`GET /v1/nat-status`) so operators can curl their adapter and get a structured JSON of what happened? Phase 5.x scope decision.

---

## References

- `01-prior-art-survey.md` — survey of WebRTC/libp2p/Tailscale/CF Tunnel/UPnP
- `project/decisions/ADR-041.md` — the architectural decision this work derives from
- `adapter/src/adapter/network/nat_detector.py` — implementation (current state)
- Issue [#328](https://github.com/RobLe3/iicp.network/issues/328) — NAT-aware research arc
- Issue [#330](https://github.com/RobLe3/iicp.network/issues/330) — live FRITZ!Box test findings (CGNAT misdiagnosis corrected)
- `docs/nat-aware-adapter-setup.md` — operator-facing recipe
- Live verification 2026-05-26 against FRITZ!Box 6591 Cable + WireGuard VPN
