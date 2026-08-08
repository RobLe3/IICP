# IICP agent-protocol landscape — 2026-08-08

**Status:** research for IICP #46. This is not standards outreach, an IETF
submission, or a compatibility claim. Individual Internet-Drafts are work in
progress, not IETF endorsement.

## Narrow problem statement

IICP should address **protocol-neutral intent resolution and execution
selection**: find currently eligible providers across execution protocols, apply
policy and operational evidence, issue short-lived route authorization, then
let the chosen endpoint execute directly. It should not compete to define every
agent task format, runtime, planning system, identity framework, or transport.

| Area | Current primary source and status | IICP relationship | Disposition |
|---|---|---|---|
| Intent gateway resolution | [IAIP -02](https://datatracker.ietf.org/doc/html/draft-sz-dmsc-iaip-02), active individual I-D | Direct overlap in registration, capability matching, filtering, ranking and direct execution. IAIP puts an Agent Gateway in the forwarding path; IICP keeps task payloads off its directory. | Compare terminology; retain payload boundary. |
| Federation and delegation | [AIPF -01](https://datatracker.ietf.org/doc/html/draft-zahed-agent-comm-framework-01), individual I-D | Relevant to cross-domain trust, federation, delegation and sessions. No interoperability claim is justified without concrete profile text and tests. | Track; defer mapping. |
| DNS candidate discovery | [DNS-AID -00](https://www.ietf.org/archive/id/draft-mozleywilliams-dnsop-dnsaid-00.html), individual I-D | DNS may publish candidates and provenance; it cannot by itself establish live eligibility or dispatch authority. | Optional bootstrap/profile input. |
| Agent discovery/invocation | [AIDIP -01](https://datatracker.ietf.org/doc/html/draft-cui-ai-agent-discovery-invocation-01/), individual I-D | Overlaps registry, semantic discovery and invocation. IICP federation and short-lived route authorization remain separate candidate value. | Crosswalk before terminology claims. |
| Agent URI/addressing | [agent URI -03](https://datatracker.ietf.org/doc/html/draft-narvaneni-agent-uri-03), individual I-D | May provide portable endpoint addressing; it does not replace operational provider selection. | Reuse if stable and suitable. |
| Tool and agent boundary | [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) and its Agents WG | MCP is expanding beyond a simple tools-only characterization. IICP must not rely on “MCP equals tools” as differentiation. | Keep IICP protocol-neutral; complete #35 authorization mapping. |
| Task execution | [A2A](https://github.com/a2aproject/A2A) v1.x | A2A can carry selected execution; IICP #60 defines a pre-execution selection layer. | Implement a binding, not a competing task lifecycle. |
| Identity and claims | [DID v1.1](https://www.w3.org/TR/did-1.1/) and [VC Data Model v2.1](https://www.w3.org/TR/vc-data-model-2.1/) | Portable operator/provenance claims differ from workload identity and task authority. | Keep #63 crosswalk; no mandatory replacement. |
| API contracts and transport | [OpenAPI 3.2](https://spec.openapis.org/oas/v3.2.0.html), HTTP, QUIC, OAuth and OTel standards | Reuse established contracts and transport/security primitives instead of duplicating them. A service-port request needs concrete operational evidence. | Reuse; keep #42 evidence-gated. |
| Registry interoperability | [IEEE P3931 Active PAR](https://standards.ieee.org/ieee/3931/12499/) | P3931 public scope overlaps registry description/lifecycle/discovery but excludes trust scoring and governance. | See dated #105 crosswalk; no IEEE compatibility claim. |

## IETF engagement decision

Do not submit a broad “agent communication protocol” now. First complete #35,
#60 and #62; publish independent conformance results under #31; then take a
narrow problem statement and implementation evidence to the appropriate public
coordination venue for review and venue guidance. Any future contact must state
that IICP is an implemented beta with limits, not imply endorsement or standards
status.
