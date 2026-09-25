# IICP — Intent-based Inter-agent Communication Protocol

![IICP — Open AI Mesh: Discover, Route, Connect](IICP_Title.png)

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![OIA pending classification](https://agenticsorg.github.io/community-projects/badges/RobLe3/IICP.svg)](https://agenticsorg.github.io/community-projects/oia-matrix.html#oia-roble3-iicp)

Provider-neutral discovery, eligibility and execution handoff for intelligence workloads.

**Published Protocol Suite**: see the generated [current-version projection](ecosystem/CURRENT_VERSIONS.md)<br>
**Wire compatibility baseline**: v1.9.0<br>
**Project status**: project-normative beta; each optional Profile has its own status<br>
**Working `main`**: may contain unreleased changes; cite an immutable tag for a released contract

---

## Repository family

IICP components are independently versioned repositories rather than Git
submodules. This repository remains authoritative for protocol semantics and
publishes the machine-readable ecosystem registry. See
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) for the official implementations,
their current visibility, maturity and ownership boundaries.
[`ecosystem/CURRENT_VERSIONS.md`](ecosystem/CURRENT_VERSIONS.md) presents every
current release axis from the same machine-readable catalog.

No paid GitHub feature is required to build, test, implement or participate in
the protocol.

The terms **project-normative**, **stable**, **active draft**, **experimental**
and **externally ratified** have distinct meanings. See
[`SPEC_STATUS.md`](SPEC_STATUS.md). IICP has not been ratified by the IETF or
assigned a service port by IANA.

The Open Intelligence Architecture Application Matrix currently lists this
repository in its **pending review** band. The badge above reports an automated
structural classification, not approval, certification or endorsement. See the
[IICP-to-OIA evidence map](docs/oia-application-matrix.md) for the intended
layer boundaries and links to the implementation evidence a reviewer can
inspect.

---

## What Is IICP?

IICP specifies how a consumer expresses an intent, discovers currently eligible
execution resources, applies non-overridable policy constraints and receives a
route for direct execution. The directory is a control plane, not a task-payload
broker. A selected execution binding may be HTTP, MCP, A2A or another supported
path when that binding is implemented by the parties; native IICP execution is
not a prerequisite for provider selection.

```
Agent A  ──CALL──▶  IICP Node B  ──▶  LLM Backend
              ▲
              │  discovery
         iicp.network
         (directory only —
          no payload passes through)
```

The directory handles registration, health, discovery and route authorization;
it does not receive task payloads. Tasks route to the selected execution node,
whose operator can read the work it executes.
IICP-CX can encrypt a request across the network and relays when the chosen
client and provider support the Profile and the provider advertises a usable
`cx_public_key`. This is route confidentiality, not executor-blind inference
or anonymity; key advertisement alone is not a verified encrypted round trip.

### The core idea (conceptual, not a wire-format example)

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440001",
  "intent":  "urn:iicp:intent:llm:chat:v1",
  "payload": { "messages": [{ "role": "user", "content": "Summarise this doc." }] },
  "constraints": { "timeout_ms": 5000, "qos": "interactive" }
}
```

An intent identifier describes the requested operation, not a particular model
or endpoint. Discovery returns candidates under the applicable capability,
policy and availability rules. A client still needs the appropriate dispatch
authority and an eligible route before execution. For executable examples,
start with the [role-based agent guide](docs/agent-bootstrap.md) and the
applicable released Profile or binding.

### Factual runtime self-description

Official `chat()` helpers give compatible models a small, versioned IICP
runtime context by default. It explains that the model or service was selected
through IICP and is not IICP itself. The client includes the active intent and
its implementation version, then adds a model, effective-capability or bounded
selection fact only when the current route supplies it authoritatively.
Applications can disable the capsule or require a supported instruction
channel. Raw task submission, embeddings, transcription, MCP calls and other
non-chat operations are unchanged. The context is not an assistant persona, a
secret prompt or a prompt-injection defense. See the
[runtime identity decision](research/strategic/2026-08-14-runtime-identity-and-self-description-decision.md).

### Protocol role and adjacent work

IICP's narrow role is intent resolution and provider eligibility/selection.
It can select a policy-compliant provider before MCP, A2A, HTTP or another
negotiated binding performs the task. It does not replace those execution
protocols or the transports and security standards beneath them.

| Question | IICP | Adjacent protocol examples |
|---|---|---|
| How is the requested operation named? | Versioned Intent identifier plus constraints | A2A skills/messages and MCP tool, resource or prompt names describe different execution-layer concepts |
| How are usable service properties advertised? | Effective capabilities exposed by the complete service path | A2A Agent Cards and MCP server discovery describe their own execution or integration surfaces |
| Who applies eligibility and selects a provider? | Directory filtering plus client policy and final validation | A2A and MCP normally leave provider choice to the application; IAIP and AIDIP directly overlap this area |
| How is the task executed? | A negotiated binding | MCP, A2A, HTTP APIs and IICP peer framing can carry the selected task |
| What does the directory see? | Intent and bounded routing metadata, not the task payload | Depends on the adjacent protocol and deployment |

The comparison rates public evidence separately for specification precision,
versioning, security, implementations, conformance, independent implementation,
deployment and governance. It does not calculate a winner score. The chronology
also separates the age of a protocol from the first public appearance of an
overlapping mechanism.
The [September feature crosswalk](standards/PROTOCOL_COMPARISON_2026-09-25.md#direct-protocol-feature-crosswalk)
compares IICP's intent naming, live eligibility, selection, route authority,
execution handoff and evidence boundaries directly with IAIP, AIDIP and CIRP.
Its [separate maturity table](standards/PROTOCOL_COMPARISON_2026-09-25.md#specification-and-implementation-maturity)
compares published code, fixtures, negative tests, conformance tooling,
release integrity and deployment evidence. IICP has more public
implementation-backed evidence in the reviewed sources; its mostly
same-project parity is not independent interoperability.

This boundary has real overlap with individual Internet-Drafts such as IAIP and
AIDIP; mandatory filtering before ranking is not unique to IICP.
Review the [selection and eligibility problem statement](standards/SELECTION_ELIGIBILITY_PROBLEM_STATEMENT.md),
the [current positioning entry point](standards/IICP_PROTOCOL_POSITIONING.md)
and its dated, source-backed assessment before
making differentiation or standards claims. Internet-Drafts are work in
progress and are not IETF endorsement.

---

## Specification Documents

### Core (read these first)

| Document | What it covers | Normative level |
|----------|---------------|-----------------|
| [iicp-core.md](spec/v1.9/iicp-core.md) | Core task and directory contracts, errors and security boundaries | Apply requirements within the named release and binding |
| [iicp-semantics.md](spec/v1.9/iicp-semantics.md) | Intent routing, eligibility, selection and retry semantics | Apply requirements within the named release and Profile |
| [iicp-extensions.md](spec/v1.9/iicp-extensions.md) | Extension and optional Profile overview | Check each Profile's own status |

### Sub-protocols

| Document | What it covers |
|----------|---------------|
| [iicp-dir.md](spec/v1.9/iicp-dir.md) | IICP-DIR: directory registration, heartbeat, discovery, peer exchange |
| [iicp-mcp-binding.md](spec/v1.9/iicp-mcp-binding.md) | MCP ↔ IICP translation rules |
| [node-capability-format.md](spec/v1.9/node-capability-format.md) | Capability object schema: intents, models, limits, availability |
| [iicp-billing-extension.md](spec/v1.9/iicp-billing-extension.md) | Credits, billing fields, receipt protocol |
| [iicp-cbor-wire.md](spec/v1.9/iicp-cbor-wire.md) | Optional CBOR wire encoding (Phase 3, `application/iicp+cbor`) |

### Conformance and governance

| Document | What it covers |
|----------|---------------|
| [IICP-core-phase1-profile.md](spec/v1.9/IICP-core-phase1-profile.md) | Historical Phase 1 compatibility subset; not the general current quickstart |
| [conformance-test-suite.md](spec/v1.9/conformance-test-suite.md) | Canonical test identifiers and their applicable contracts; identifiers are not passing results |
| [validation-methodology.md](spec/v1.9/validation-methodology.md) | How to validate implementations; performance claim disclosure |
| [iicp-v1.5-overview.md](spec/v1.9/iicp-v1.5-overview.md) | What changed in v1.5; migration guide from v1.4.2 |
| [Pre-1.0 feature boundary](pre1/README.md) | Bounded client, Directory and Management capability crosswalk; not a stable-release authorization |

### Supporting assets

| Path | Contents |
|------|---------|
| [schemas/task.json](schemas/task.json) | Historical Phase 1 JSON task schema, not a universal current task contract |
| [schemas/nodelist.json](schemas/nodelist.json) | JSON Schema 2020-12 for `NodeListResponse` |
| [registry/intents.json](registry/intents.json) | Official intent URN registry |
| [spec/intent-risk-taxonomy.json](spec/intent-risk-taxonomy.json) | Shared prohibited/high-risk/transparency/minimal intent classification fixture |
| [spec/mcp-tool-risk-taxonomy.json](spec/mcp-tool-risk-taxonomy.json) | Shared MCP tool-risk and default-gating fixture |

### Archived

| Path | Contents |
|------|---------|
| [spec/archived/IICP_draft_1.4.2.txt](spec/archived/IICP_draft_1.4.2.txt) | Original monolithic Internet-Draft (archived) |

---

## Start with the applicable contract

- **Application or agent developer:** use the [role-based agent guide](docs/agent-bootstrap.md) for consumer discovery and direct execution; use the chosen SDK repository for its current API.
- **Provider operator:** use the same guide for registration and the [operator onboarding path](docs/operator-onboarding-recovery.md) for persistent service behavior.
- **Directory implementer:** read the [specification index](spec/v1.9/README.md), directory contract and applicable HTTP/OpenAPI projection. PHP and Rust implementation details belong in their own repositories.
- **Independent implementer or reviewer:** pin a Protocol Suite release, declare supported Profiles and bindings, then use the [conformance suite](spec/v1.9/conformance-test-suite.md) and [runner](conformance-runner/README.md). The [Phase 1 profile](spec/v1.9/IICP-core-phase1-profile.md) remains a historical compatibility path, not a claim of current full support.

A Profile is optional to select unless the named release requires it. Once an
implementation declares support for a Profile, that Profile's requirements
are mandatory within its scope. Publication, test execution, qualification
and live deployment remain separate evidence states.

---

## Client SDKs

Three official client SDKs (see the generated
[current-version projection](ecosystem/CURRENT_VERSIONS.md)) implement
both sides of the protocol — the consumer (discovery, routing, retry, fallback, CIP
consumer) and the provider (`iicp-node` runtime with backend auto-detection, NAT
escalation, relay worker/server modes, and a built-in MCP gateway). All are open-source
and published:

| Language | Install | Package registry | Source repository |
|----------|---------|------------------|-------------------|
| Python | `pip install iicp-client` | [PyPI: iicp-client](https://pypi.org/project/iicp-client/) | [github.com/RobLe3/iicp-client-python](https://github.com/RobLe3/iicp-client-python) |
| TypeScript | `npm install @iicp/client` | [npm: @iicp/client](https://www.npmjs.com/package/@iicp/client) | [github.com/RobLe3/iicp-client-typescript](https://github.com/RobLe3/iicp-client-typescript) |
| Rust | `cargo add iicp-client` | [crates.io: iicp-client](https://crates.io/crates/iicp-client) | [github.com/RobLe3/iicp-client-rust](https://github.com/RobLe3/iicp-client-rust) |

**Experimental browser path:** [iicp.network/browser-node](https://iicp.network/browser-node)
can run a supported model with WebGPU and query the public mesh as a consumer
on compatible browsers. It is not a general installation or availability guarantee.

These maintained reference SDKs are useful implementation examples. A package
release or same-project parity test does not by itself establish independent
interoperability or certification; consult the named fixtures and retained
results for a bounded conformance claim.

### Community integrations — independently maintained

| Project | Language | Integration surface | Status |
|---------|----------|---------------------|--------|
| [`michaeloboyle/iicp-node-monitor`](https://github.com/michaeloboyle/iicp-node-monitor) | Python | Local node events and health plus the public Directory Registry API | Independent community application; compatibility patch [under upstream review](https://github.com/michaeloboyle/iicp-node-monitor/pull/1) |

Community integrations are maintained by their respective authors. They are not
official SDK releases, protocol-conformance results, or evidence of support for
every optional Profile. The node monitor was last reviewed against current public
IICP interfaces on 21 August 2026; its upstream repository remains authoritative.

If you are connecting an autonomous agent rather than calling the API by hand,
start with [Connect an AI agent to IICP](docs/agent-bootstrap.md). It separates
consumer discovery from provider registration and shows where MCP or A2A can
carry the task after IICP selects a route.

### Reachability: the automatic NAT ladder

Maintained providers can attempt direct, UPnP, IPv6, relay and tunnel routes
according to their runtime and configuration. Reachability depends on the
environment and must be observed, not inferred from a running process or an
advertised URL. Relay remains experimental. See the owning SDK's current
operator guide and the [directory state semantics](docs/architecture/directory-state-semantics.md).

---

## Research

The protocol's normative choices are backed by simulation and analysis. The full research
record — credit economy & rate calibration, reputation/tier modelling, adversarial robustness
(FRAME8, REP, MESH), routing/multi-path selection, cryptographic trustworthiness, portable
operator identity, gamification anti-gaming, NAT traversal, and more — lives under
[`research/`](research/), indexed in [`research/RESEARCH.md`](research/RESEARCH.md).

These notes are published so the spec's decisions are **externally verifiable**: each major
parameter (tier weights, credit schedule, decay floors, EMA α, etc.) traces back to a documented
simulation or analysis. Found a flaw or have a better method? The research is meant to be
challenged — open an issue.

The live reference implementation also keeps a public research summary at
[iicp.network/research](https://iicp.network/research). Treat live-network
evidence, controlled validation, simulation and future research as different
confidence levels; do not cite simulations as production measurements.

---

## Intent identifier registry

IICP intent identifiers name *what* is being requested, independent of model or
backend. The deployed `urn:iicp:` form is preserved as a stable project-defined
identifier while formal namespace registration is pending:

```
urn:iicp:intent:<domain>:<action>:v<version>
```

Examples from [`registry/intents.json`](registry/intents.json):

| Identifier | Purpose |
|-----|---------|
| `urn:iicp:intent:llm:chat:v1` | Conversational LLM completion |
| `urn:iicp:intent:llm:embedding:v1` | Text embedding / vector |
| `urn:iicp:intent:llm:summarise:v1` | Document summarisation |
| `urn:iicp:intent:vision:describe:v1` | Image-to-text description |
| `urn:iicp:intent:audio:transcribe:v1` | Speech-to-text |

To propose a new intent, open an issue with the URN, domain justification, and example payload.

---

## Node Discovery and Scoring

The directory returns an ordered, eligibility-filtered list. Hard policy,
security, availability and required capability constraints cannot be bypassed
by a ranker or fallback. Default clients preserve directory recommendation
order. A declared supported selection Profile may reorder only the eligible
set and must keep any local ranking value distinct from the canonical
directory score. A ticket for one directory-selected route does not authorize
provider substitution. See [selection semantics](spec/v1.9/iicp-semantics.md)
for the scoped rules.

**Historical Phase 3 scoring example** (not a current deployment claim):

```
score = 0.35 × availability_factor
      + 0.28 × (1 − normalized_load)
      + 0.18 × capacity_ratio
      + 0.09 × region_match
      + 0.10 × reputation_score
```

See [iicp-semantics.md](spec/v1.9/iicp-semantics.md) for full term definitions.

---

## Security Baseline

Apply the security, identifier, size and error requirements of the named
release, Profile and binding rather than treating this overview as a
validation grammar. Directory control endpoints require production HTTPS;
HTTP task endpoints require HTTPS in the coordinated stable/production scope,
with only explicit development exceptions. Plaintext native TCP is
development-only and outside that stable scope; QUIC remains future work.
See [Core transport and security](spec/v1.9/iicp-core.md), the
[directory scheme rules](spec/v1.9/iicp-dir.md) and the
[conformance identifiers](spec/v1.9/conformance-test-suite.md).

Registration credentials identify a provider to its directory. Discovery
does not give an arbitrary consumer permission to execute: provider task
authorization uses the applicable consumer credential or dispatch mechanism.
The historical Phase 1 body `auth.node_token` and later header-based consumer
authorization have different scopes. HTTP error envelopes, native errors and
optional binding errors must be interpreted under their respective contracts;
there is no universal README-only `IICP-Exxx` JSON rule.

---

## Development Status

Published, deployed and observed versions are separate facts. The release map
in [`ecosystem/current-versions.json`](ecosystem/current-versions.json) remains
the authority for published component versions. The additive
[`ecosystem version truth`](docs/ECOSYSTEM_VERSION_TRUTH.md) contract explains
how public evidence can report deployment and adoption without treating either
as a synonym for publication.

**Implementation and qualification evidence**

The [iicp.network](https://iicp.network) directory is live and the client SDK
release line is recorded in the generated
[current-version projection](ecosystem/CURRENT_VERSIONS.md). Each SDK includes
the `iicp-node` provider runtime, so a participant can use the mesh first and
provide capacity later. Live node availability, installed-version adoption and
encryption evidence change over time; consult the
[live stats page](https://iicp.network/stats) before treating any network
condition as current.

The [implementation index](IMPLEMENTATIONS.md) distinguishes published SDKs,
the deployed PHP Genesis line, the Rust directory operator preview, the
experimental browser node and the optional Management developer preview.
The [pre-1.0 feature boundary](pre1/README.md) describes the proposed stable
qualification scope; it does not grant a stable designation. The
[SDK evidence contract](SDK_QUALITY_EVIDENCE.md) and
[release-candidate rules](RELEASE_CANDIDATES.md) define how results must be
attributed. Same-project parity is not independent interoperability.

The public mesh can be used within its observed capabilities, but relay
hardening, privacy evidence and federation operation remain separate gates.
The selected remote executor can read the task it performs. Check dated
[live evidence](https://iicp.network/stats) rather than assuming a published
feature is deployed or currently reachable.

Follow this repo or [iicp.network](https://iicp.network) for announcements.

---

## Version History

The immutable [`CHANGELOG.md`](CHANGELOG.md) is the release history. The
generated [current-version projection](ecosystem/CURRENT_VERSIONS.md) records
the current protocol, implementation, package and browser axes without copying
those values into this overview. Compatibility claims are release-specific;
the current base-wire baseline is labeled at the top of this page.

---

## Implementations

IICP components are published as dedicated repositories. The
[implementation registry](IMPLEMENTATIONS.md) records their authority,
visibility, lifecycle and independently versioned releases.

The PHP directory is the current Genesis Seed implementation. The Rust
directory is a pre-1.0 operator preview and the intended long-term successor,
but publishing it does not move production traffic or deprecate PHP. The three
SDK repositories provide consumer and provider runtimes; the browser-node
repository provides the experimental browser implementation.

This repository is authoritative for released interoperability semantics.
Conformance must name a release, supported Profiles and bindings, environment,
fixtures and retained results. It does not by itself prove compatibility with
every current live-directory feature or deployment policy.

Directory implementations also share an implementation-neutral
[context and signed service-event ownership](docs/architecture/context-and-service-event-ownership.md)
contract. Internal module or service placement cannot redefine public routes,
event ownership, replication behavior or authorization.

The accepted
[environmental-independence and extension architecture](docs/architecture/environmental-independence-and-extension-architecture.md)
separates Core semantics from Profiles, Bindings, Registry entries and local
implementation extensions. It preserves current connected operation while
keeping transport, locator, timing, encoding and execution-backend choices out
of Core.

The companion [task time semantics](docs/architecture/task-time-semantics.md)
keeps the current provider attempt budget separate from delivery lifetime,
logical-task deadline, result validity and caller-local wait behavior.

The [directory state semantics](docs/architecture/directory-state-semantics.md)
separate identity and advertisement validity from current reachability,
execution availability and dispatch eligibility. Default discovery still
returns only candidates that are eligible now.

The [effective service capability semantics](docs/architecture/effective-service-capability-semantics.md)
define capabilities as behavior exposed by the complete serving path. They
separate modalities, features, runtime actions, limits, policy, Profiles,
evidence, observations and evaluator-specific quality.

The [architecture decision and documentation map](docs/architecture/decision-documentation-map.md)
shows how accepted decisions move from public rationale into normative
contracts, implementation guides, and user-facing explanations without turning
the website into a second specification.

The [public evidence access profile](docs/public-evidence-access.md) lists the
version, implementation, registry, conformance, release and live-runtime
artifacts intended for non-browser retrieval. Static source evidence has a
repository fallback; unavailable live state is reported as unavailable rather
than inferred from source metadata.

---

## Contributing

- **Bug reports / clarifications**: Open an issue
- **New intent URNs**: Open an issue with URN, domain, and example payload
- **Protocol proposals**: Open an issue tagged `protocol-change`
- **Conformance tests**: PRs to `spec/v1.9/conformance-test-suite.md` welcome

All normative language follows RFC 2119 / BCP 14.

For an independent protocol or standards review, start with
[`standards/REVIEWING.md`](standards/REVIEWING.md). The public
[`ecosystem/public-repositories.json`](ecosystem/public-repositories.json)
identifies the repositories and roles needed to continue implementation work.
The specification release and review-bundle procedures are reproducible from
public inputs and do not depend on the project's private development methods.
[`CONTINUATION.md`](CONTINUATION.md) explains how an independent implementation
or successor effort can preserve compatibility and release history.

---

## Verification tools

Start with the current [contribution checks](CONTRIBUTING.md), the
[profile fixture contract](tools/run_profile_fixture_contract.sh) and the
[public artifact closure check](tools/check_public_artifact_closure.py).
The conformance runner and its supported Profiles are documented in their
own [runner guide](conformance-runner/README.md).

| File | Purpose |
|------|---------|
| [tools/protocol_integrity_analysis.py](tools/protocol_integrity_analysis.py) | Analyses a spec file for internal consistency |
| [tools/quick_validation.py](tools/quick_validation.py) | Quick syntax + field validation against v1.4.2 |

The tools in the table above are historical analysis aids, not the current
validation entry point. Their optional scientific dependencies can be installed
them in an isolated environment with
`python3 -m pip install -r tools/research-requirements.txt`. They are historical
research aids, not normative conformance or release gates.
