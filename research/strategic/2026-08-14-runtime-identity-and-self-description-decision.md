# Runtime identity and self-description decision

**Date:** 2026-08-14  
**Status:** Research foundation; not a wire contract or SDK default  
**Tracker:** [IICP #158](https://github.com/RobLe3/IICP/issues/158)

## Decision

IICP has a real runtime self-description gap. The official chat clients can
route a request correctly while the selected model receives no authoritative
information about IICP, the active intent, the client, or the reason it was
selected. A model that has not learned about IICP therefore guesses.

The smallest suitable response is a versioned, structured runtime identity
context with a compact conversational rendering. It is not a new intent, an
assistant persona, a directory response, a replacement for routing receipts,
or a general prompt-management framework.

The initial profile should remain research-only and explicitly enabled. It
applies only to `urn:iicp:intent:llm:chat:v1`. Raw `submit()` calls and all
non-chat intents remain byte-for-byte unchanged. A default for user-facing
CLI, Web, or compatibility-proxy surfaces requires shared semantics,
cross-SDK parity, provider compatibility evidence, and an explicit migration
decision.

## Sources inspected

| Component | Commit | Relevant behavior |
| --- | --- | --- |
| IICP specification | `75279d72f0dd` | chat payload, task response, routing receipts, privacy, capability taxonomy |
| Python SDK | `2990a529cbd3` | `IicpClient.chat_async`, OpenAI and Anthropic adapters |
| TypeScript SDK | `e9297b0f6e3e` | `IicpClient.chat`, compatibility proxy and provider adapters |
| Rust SDK and CLI | `60433388d0e5` | `IicpClient::chat`, `iicp-node query`, provider adapters |
| Browser node | `025867e9a348` | browser consumer, WebLLM provider and chat-role handling |
| Website | `926ea1890dc9` | browser consumer copy and public Web surfaces |
| PHP directory | `19c5a96339fc` | discovery and route metadata boundary |
| Rust directory | `a9ae62dc77d9` | discovery and route metadata boundary |

The audit also checked the current and historical issue set. No existing issue
owned model-visible IICP runtime context.

## Reproduction

The production-compatible Rust CLI `iicp-node 0.7.103` was used on 2026-08-14
through the normal public discovery and encrypted dispatch path.

For `What is IICP?`, the selected model returned an unrelated expansion of the
acronym and unrelated institutional claims. A second request asked about the
interface, IICP identity, model, intent, capabilities, selection, and client.
The model incorrectly associated the interface with Alibaba Cloud, did not know
the active intent or client, and guessed about the surrounding system.

The behavior is explained by the source:

- Python `IicpClient.chat_async`, TypeScript `IicpClient.chat`, Rust
  `IicpClient::chat`, and the browser consumer serialize the caller's messages
  without adding IICP context.
- OpenAI-compatible provider adapters forward that payload and add only a
  configured model when needed.
- the three Anthropic adapters translate system-role messages into Anthropic's
  top-level `system` field, but they do not create an IICP message;
- the browser provider passes the supplied messages to WebLLM unchanged.

The result is not uniform in wording because model training differs, but the
absence of authoritative context is uniform across the maintained chat paths.
An answer may happen to be accurate when a model has learned about IICP; that
is not runtime evidence.

## Existing mechanisms that must be reused

- Registry 1.4 already defines `llm:chat:v1` and its message-array payload.
- `generated_by_ai` and `X-IICP-Generated-By-AI` identify model-produced output.
  They do not tell the model about its runtime context.
- IICP #70 separates implementation identity, implementation version, and SDK
  compatibility. That distinction should be reused rather than replaced.
- IICP #156 owns effective service-capability meaning and provenance. Runtime
  identity may render accepted capability facts later, but must not invent a
  second vocabulary.
- Routing receipts already contain a content-free selection record for the
  caller. Model-visible context should expose only a bounded explanation, not
  the receipt, candidate set, scores, or endpoint details.
- Existing routing policy and CX confidentiality remain authoritative. The
  selected executor can read any context used by the model under the current
  execution trust boundary.

## Proposed representation

The semantic source should be a small object, not a client-specific string:

```text
runtime_identity_context
├── context_version
├── stable_identity
│   ├── protocol
│   └── relationship
└── supplied_facts
    ├── intent
    ├── client (optional)
    ├── selected_model (only when resolved)
    ├── effective_capabilities (blocked on #156)
    └── selection_summary (bounded)
```

Each dynamic fact needs a source and disclosure classification. Absence means
unknown to this context. It never means unsupported, false, or permission to
infer a value.

A deterministic formatter can turn the object into one compact instruction for
providers that support system or instruction context. The draft base text in
the fixture says, in substance:

> This request reached you through IICP, the Intent-based Inter-agent
> Communication Protocol. IICP discovers eligible services and routes
> requests. You are the selected model or service, not IICP. Use only supplied
> runtime facts when describing this connection; do not guess missing facts.

The exact text is research material until #158 reviews composition and
provider behavior.

## Fact authority and disclosure

| Fact | Source required | Default disclosure |
| --- | --- | --- |
| IICP name and relationship | versioned profile | safe |
| active intent | validated task request | safe |
| protocol/profile version | negotiated runtime fact | safe when present |
| coarse selection summary | client decision enum | safe: matched intent and constraints |
| client implementation/version | local client | optional; can fingerprint callers |
| selected model | explicit pin or provider-resolved model | optional; omit if unresolved |
| effective capabilities | reviewed #156 projection | optional and intent-scoped |
| coarse region | policy-approved route fact | policy-controlled |
| provider/operator identity | verified identity evidence | policy-controlled; normally omit |
| node ID, endpoint, IP, exact location | none | never inject |
| candidate set, scores, costs, reputation internals | none | never inject |
| credentials, tickets, keys, policy internals | none | never inject |

Provider-reported model identity is an assertion unless stronger evidence binds
it. The text must not turn an assertion into a verified fact.

## Applicability

Initial applicability is deliberately narrow:

| Intent or surface | Action |
| --- | --- |
| `llm:chat:v1` with compatible system/instruction support | eligible for explicit experimental composition |
| raw `submit()` | unchanged unless the caller explicitly supplies the profile |
| embeddings | never inject text; it would change the vector |
| transcription, speech, image, moderation, reranking | never inject text |
| MCP or tool execution | do not inject a chat persona into structured calls |
| raw completion | defer; prepending text changes completion semantics |
| unsupported/rejecting chat template | omit in optional mode; fail before dispatch only if explicitly required |

This does not justify a generic self-description intent. A separate
machine-readable status or documentation query can exist independently; it
would not make an executing model aware of the current request.

## Composition and precedence

The profile must not become a universal prompt owner. The following principles
need implementation evidence before exact ordering is normative:

1. preserve application, developer, provider-safety, and user messages without
   rewriting their content;
2. compose one canonical IICP context rather than one prompt per SDK;
3. keep the capsule factual and non-personal so it does not redefine the
   application's assistant role;
4. suppress an identical versioned capsule rather than duplicate it;
5. do not promise that a system message prevents prompt injection;
6. degrade without altering the request when a provider lacks a compatible
   instruction channel, unless the caller explicitly required the profile.

The existing adapters demonstrate why a structured source is necessary.
OpenAI-compatible and WebLLM paths accept message arrays, Anthropic uses a
top-level system field, and Apple Foundation Models uses session instructions.
llama.cpp and vLLM depend on the loaded model's chat template. One literal
message-placement rule cannot be assumed to work everywhere.

## Token measurement

The 42-word, 289-character draft base capsule was measured locally against
Ollama with `qwen2.5:0.5b`, `max_tokens=1`, and the same user question:

- baseline prompt: 35 tokens;
- base capsule plus prompt: 77 tokens;
- measured overhead: 42 prompt tokens.

This is one runtime measurement, not a cross-tokenizer guarantee. Dynamic facts
add further cost and should be limited to facts relevant to the active request.
The profile should set a small serialized-size limit and test more than one
backend before any default is enabled.

## Security boundary

Runtime identity improves factual grounding; it does not authenticate the
model, prevent instruction override, or hide data from the selected executor.
Every injected field must already be approved for disclosure to that executor
and potentially to the user. Requests to print hidden routing data do not widen
the allowed field set. The capsule contains no secrets, and exact system-prompt
secrecy is not a security assumption.

## Issue audit

| Issue | Disposition | Reason |
| --- | --- | --- |
| IICP #158 | **OPEN / owner** | New semantic gap; owns representation, composition, privacy and fixtures. |
| IICP #156 | **BLOCKS capability facts only** | Runtime identity reuses its effective-capability vocabulary; base identity can proceed independently. |
| IICP #55 | **KEEP** | Registry ratification is not blocked by runtime identity. Do not merge the scopes. |
| IICP #70 | **KEEP CLOSED / reuse** | Already separates implementation identity from SDK compatibility. |
| iicp.network #614 | **KEEP CLOSED / reuse** | Output notice is complementary and complete; no reopening. |
| iicp.network #585 | **KEEP CLOSED / reuse** | Existing pre-dispatch privacy policy remains authoritative. |
| IICP #56 | **KEEP** | Policy/data-handling ratification is related but not an identity-capsule implementation issue. |

No Web-only issue is justified. The Web path reproduced a shared architectural
gap. No SDK or directory implementation child is justified before #158 reviews
the shared semantics.

## Dependency order

```text
IICP #158 semantic decision and fixture
        |
        +---- #156 effective capability projection (optional fact only)
        |
        v
shared formatter and composition contract
        |
        v
coordinated Python / TypeScript / Rust / browser provider parity
        |
        v
provider compatibility and semantic self-description tests
        |
        v
opt-in user-facing CLI / Web / proxy experiment
        |
        v
measured migration and explicit default decision
```

Directories do not need to generate prompts. They may later provide already
public, policy-approved facts, but prompt composition belongs at the
client/provider execution boundary.

## Long-term alignment

This mechanism supports IICP's goals because it makes routed execution easier
to understand without moving discovery, routing, policy, or model behavior into
the directory. It reuses existing intent, identity, capability, receipt, policy,
and migration work. It would still be useful with any model vendor or runtime.

The proposal should be rejected if it becomes an IICP persona, a hidden
marketing prompt, a directory-side answer bot, a new capability registry, or a
way to expose private routing state.

