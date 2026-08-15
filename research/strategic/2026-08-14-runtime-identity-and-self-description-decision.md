# Runtime identity and self-description decision

**Date:** 2026-08-14  
**Status:** Implemented pre-normative parity contract; default-auto on compatible chat helpers
**Trackers:** [IICP #158](https://github.com/RobLe3/IICP/issues/158), [IICP #178](https://github.com/RobLe3/IICP/issues/178)

## Decision

IICP has a real runtime self-description gap. The official chat clients can
route a request correctly while the selected model receives no authoritative
information about IICP, the active intent, the client, or the reason it was
selected. A model that has not learned about IICP therefore guesses.

The smallest suitable response is a versioned, structured runtime identity
context with a compact conversational rendering. It is not a new intent, an
assistant persona, a directory response, a replacement for routing receipts,
or a general prompt-management framework.

The profile remains pre-normative, but the implementation evidence now supports
a default-auto composition rule on compatible `urn:iicp:intent:llm:chat:v1`
helpers. Raw `submit()` calls and all non-chat intents remain byte-for-byte
unchanged. Applications can disable the context, opt into the legacy explicit
mode, or require it before dispatch. This changes local chat prompt semantics;
it does not change the IICP base wire or make the profile normative.

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

The stable text remains pre-normative, but the composition contract is now reviewed for an opt-in implementation. Rendered messages carry the exact marker `IICP-RUNTIME-CONTEXT/1` for duplicate suppression.

## Fact authority and disclosure

| Fact | Source required | Default disclosure |
| --- | --- | --- |
| IICP name and relationship | versioned profile | safe |
| active intent | validated task request | safe |
| protocol/profile version | negotiated runtime fact | safe when present |
| coarse selection summary | client decision enum | safe: matched intent and constraints |
| client implementation/version | local client | safe by default on compatible chat helpers; applications may disable the capsule |
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
| `llm:chat:v1` with compatible system/instruction support | compose in `auto` by default; `disabled`, `explicit` and `required` remain available |
| raw `submit()` | always unchanged by the chat helper contract |
| embeddings | never inject text; it would change the vector |
| transcription, speech, image, moderation, reranking | never inject text |
| MCP or tool execution | do not inject a chat persona into structured calls |
| raw completion | defer; prepending text changes completion semantics |
| unsupported/rejecting chat template | omit in optional mode; fail before dispatch only if explicitly required |

This does not justify a generic self-description intent. A separate
machine-readable status or documentation query can exist independently; it
would not make an executing model aware of the current request.

## Composition and precedence

The profile must not become a universal prompt owner. The reviewed composition rules are deliberately mechanical:

1. preserve every application, developer, provider-safety, and user message
   without rewriting its role or content;
2. render one canonical `system` message marked `IICP-RUNTIME-CONTEXT/1`;
3. insert it after all leading `system` or `developer` messages and before the
   first other message;
4. if any existing `system` or `developer` message contains the exact marker,
   do not insert another capsule;
5. keep the capsule factual and non-personal so it does not redefine the
   application's assistant role;
6. cap the UTF-8 rendering at 2,048 bytes and reject prohibited facts before
   composition;
7. do not claim that a system message prevents prompt injection;
8. in `auto` or `explicit` mode, leave the request unchanged when the
   instruction channel is unsupported; in `required` mode, refuse before
   dispatch;
9. resolve client identity for every compatible chat call and rebuild model,
   capability and selection facts from the original application messages for
   each fallback candidate.

These rules define portable observable behavior, not provider-internal prompt
precedence. A provider may still apply its own safety prompt outside the caller's
message array.

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
The profile keeps a 2,048-byte serialized-size limit. The default decision is
bounded to compatible chat helpers and remains reversible with `disabled`;
additional tokenizer measurements remain useful evidence rather than a timed
gate.

## Representative semantic smoke test

A content-free local smoke test on 2026-08-15 exercised six self-description
questions through Ollama. `phi3:mini` followed all six supplied facts and
boundaries. `qwen2.5:0.5b` and `llama3.2:1b` understood the IICP relationship
but did not reproduce every model or capability fact reliably. This is useful
evidence for the mechanism and a limit on its claim: the capsule supplies
authoritative context, but model instruction-following remains model-dependent.
It is not semantic conformance or a security boundary. The report retains only
classifications, not prompts, answers, endpoints or routing data:
[`runtime-identity-semantic-smoke-2026-08-15.json`](runtime-identity-semantic-smoke-2026-08-15.json).

## Security boundary

Runtime identity improves factual grounding; it does not authenticate the
model, prevent instruction override, or hide data from the selected executor.
Every injected field must already be approved for disclosure to that executor
and potentially to the user. Requests to print hidden routing data do not widen
the allowed field set. The capsule contains no secrets, and exact system-prompt
secrecy is not a security assumption.

## Issue audit and implementation evidence

| Issue | Disposition | Evidence |
| --- | --- | --- |
| IICP #158 | **CLOSED / semantic foundation** | Decision record, capsule marker and original opt-in fixture were reviewed and implemented. |
| IICP #178 | **IMPLEMENTATION OWNER** | Defines auto default, candidate recomposition, client identity, proxy/browser behavior and coordinated release evidence. |
| Python #101 | **IMPLEMENTED CANDIDATE** | Chat and proxy paths default to auto; raw submit remains unchanged; serial and parallel candidates recompose from original messages. |
| TypeScript #89 | **IMPLEMENTED CANDIDATE** | Chat defaults to auto and recomposes for the selected fallback candidate. |
| Rust #101 | **IMPLEMENTED CANDIDATE** | `chat()` defaults to auto; `chat_with_runtime_identity` retains explicit control; raw `submit()` is unchanged. |
| Browser #19 | **IMPLEMENTED CANDIDATE** | Browser chat adds client, selected advertised model and complete advertised capability facts when available. |
| Website #41 | **IMPLEMENTED, NOT DEPLOYED** | Mesh chat and local WebLLM use the shared contract; local mode explicitly says that no remote provider was selected. Deployment requires separate authorization. |
| IICP #156 | **REUSED** | Effective capability facts use its vocabulary only when the complete selected variant is available. |

The canonical fixture is `0.3.0-draft`, remains pre-normative, and is copied
byte-for-byte into the official SDK/browser parity directories. The release
changes a chat-helper default, not a directory contract or base-wire field.

## Implemented dependency order

```text
IICP #158 semantic decision and fixture
        ↓
IICP #178 default-auto migration contract
        ↓
Python / TypeScript / Rust / browser parity
        ↓
compatibility proxy and website browser/local composition
        ↓
coordinated package evidence and separately authorized website deployment
```

Directories do not generate prompts. Candidate facts are composed at the
client boundary after eligibility and selection, and are re-evaluated for each
fallback attempt.

## Long-term alignment

This mechanism supports IICP's goals because it makes routed execution easier
to understand without moving discovery, routing, policy, or model behavior into
the directory. It reuses existing intent, identity, capability, receipt, policy,
and migration work. It would still be useful with any model vendor or runtime.

The proposal should be rejected if it becomes an IICP persona, a hidden
marketing prompt, a directory-side answer bot, a new capability registry, or a
way to expose private routing state.
