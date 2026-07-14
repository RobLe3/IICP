# IICP Intent and Semantic Profile Proposal

## Existing intent coverage

| Workload | Current basis | Action |
|---|---|---|
| Chat/completion/embedding | `llm:*` intents | Retain; clarify payload and streaming profile binding. |
| Classification/reranking | vendor/application capabilities | Add standard intent only after two independent implementations and stable schemas. |
| Tool use | MCP binding/capabilities | Keep binding-led; do not add generic execution privilege intent. |
| Agent delegation/verification | CIP and application semantics | Define profile/receipt semantics before a broad new intent. |
| Best-of-N/consensus/map-reduce | CIP constraints | Keep as cooperative execution modes, not independent provider capabilities. |
| Model availability/capacity/health | capability envelope + directory | Add fields/profile, not routable task intents. |
| Distributed stage execution | none | Do not standardize as ordinary intent. |

## Candidate profiles

| Profile | Purpose | Status |
|---|---|---|
| `urn:iicp:profile:streaming:v1` | ordered events, finality, cancellation and bounded buffering | Priority proposal. |
| `urn:iicp:profile:structured-output:v1` | schema declaration and validation outcome | Research. |
| `urn:iicp:profile:tool-call:v1` | references MCP binding and explicit authorization | Research. |
| `urn:iicp:profile:confidential:v1` | CX/key readiness and safe fallback behavior | Align existing CX semantics. |
| `urn:iicp:profile:latency-sensitive:v1` | deadline/admission behavior without provider internals | Priority proposal. |
| `urn:iicp:profile:batch:v1` | batch semantics and partial-result policy | Research. |
| `urn:iicp:profile:cooperative:v1` | CIP lifecycle/receipt requirements | Priority clarification. |

## Non-proposals

- Do not make `runtime:health`, `runtime:capacity`, or `runtime:model-availability`
  ordinary execution intents; they are capability/telemetry data.
- Do not expose MeshLLM `mesh` ensemble behavior as a normal model capability.
- Do not standardize tensor transfer, GPU placement, KV cache, or stage topology
  as base intent payloads.

## Versioning rules

Profiles and sub-protocols use independent major versions, are negotiated in
INIT/SUB_PROTOCOL, fail closed when required but unsupported, and must declare
conformance vectors before being promoted. Unknown optional profiles are ignored;
unknown required profiles reject before task acceptance.
