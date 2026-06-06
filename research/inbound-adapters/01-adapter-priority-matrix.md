# Inbound Adapter Priority Matrix

**Track**: #273 — Inbound LLM adapter parity  
**Status**: Research complete — implementation issues to be filed  
**Date**: 2026-05-21  
**FORGE iter**: 370 (ADOPTION)

---

## Summary

IICP proxy exposes one inbound surface: OpenAI-compat (`POST /v1/chat/completions` on
`:11434`). This document evaluates five additional adapter candidates and recommends
a sequenced implementation plan.

**Recommendation: Ollama-compat first, Anthropic-compat second.**

---

## Scoring Methodology

Each adapter is scored on four axes (1–5):

| Axis | What it measures |
|------|-----------------|
| **Reach** | Estimated count of apps/tools that would work zero-config |
| **Philosophy fit** | How closely the user base overlaps IICP's self-hosted-AI thesis |
| **Implementation cost** | Inverse of complexity (5 = trivial, 1 = high effort) |
| **Overlap with OpenAI** | Proximity to existing compat layer (higher = more code reuse) |

Composite = Reach × 0.35 + Fit × 0.30 + Cost × 0.20 + Overlap × 0.15

---

## Adapter Candidates

### 1. Ollama-compat — `POST /api/generate`, `POST /api/chat`

**Composite score: 4.4** ← Top pick

| Axis | Score | Evidence |
|------|-------|---------|
| Reach | 5 | Open WebUI, Continue.dev, LobeChat, Cursor, Msty, Chatbox, Jan, GPT4All-UI, aider, Obsidian-ollama, Logseq AI, dozens more — all speak `/api/chat` or `/api/generate` |
| Philosophy fit | 5 | Every Ollama user runs their own local LLM. IICP extends that to a mesh. This is the same user who would run a node. |
| Implementation cost | 4 | `/api/chat` message shape closely mirrors OpenAI; streaming uses NDJSON not SSE but that's a thin wrapper |
| Overlap | 4 | 70-80% of translator.py reusable; main delta is response envelope + `/api/tags` model list endpoint |

**Routes needed:**
- `POST /api/chat` — streamed NDJSON, role-based messages (same semantics as `/v1/chat/completions`)
- `POST /api/generate` — raw completion, single `prompt` string (maps to single user message)
- `GET /api/tags` — returns `{"models": [{"name": "iicp", ...}]}` (static, no discovery query)
- `GET /api/version` — returns `{"version": "0.1.0"}` (static)

**Translator delta from OpenAI:**
```
Request:  {"model": "iicp", "messages": [...], "stream": true}
          → identical semantics, just different path
Response: {"model": "...", "created_at": "...", "message": {...}, "done": true}
          → envelope rename, not a format change
```

**Effort estimate**: ~100 lines translator + ~150 lines server, ~1 day.

---

### 2. Anthropic-compat — `POST /v1/messages`

**Composite score: 3.8** ← Second pick

| Axis | Score | Evidence |
|------|-------|---------|
| Reach | 4 | Claude API clients, Anthropic SDK (Python/TypeScript), anything built on `anthropic` SDK — growing fast post-Claude-4 |
| Philosophy fit | 4 | Claude API users are developers who may want to swap from Anthropic cloud to self-hosted IICP nodes |
| Implementation cost | 3 | `content` is a list of typed blocks `[{type: "text", text: "..."}]`; system prompt is a top-level field not inside messages; streaming uses SSE with `event:` type lines |
| Overlap | 2 | Message shape is different enough that translator needs its own logic; most reuse comes from routing layer |

**Routes needed:**
- `POST /v1/messages` — Anthropic Messages API shape
- `GET /v1/models` — static list or forward to directory /v1/discover

**Key differences from OpenAI:**
- `system` is a top-level string, not a message with `role: system`
- `content` is `[{type: "text", text: "..."}]` not a string
- Streaming events: `message_start`, `content_block_delta`, `message_delta`, `message_stop`
- `max_tokens` is required (not optional)
- Response: `{"id": "...", "type": "message", "role": "assistant", "content": [...]}`

**Translator delta**: Non-trivial. Content block unwrapping + SSE event sequence.

**Effort estimate**: ~180 lines translator + ~150 lines server, ~1.5–2 days.

---

### 3. HuggingFace TGI-compat — `POST /generate`

**Composite score: 2.9**

| Axis | Score | Evidence |
|------|-------|---------|
| Reach | 3 | HF Inference SDK, text-generation-inference clients, some academic tooling |
| Philosophy fit | 3 | Self-hosted HF TGI users are technically aligned but fewer in number |
| Implementation cost | 5 | `/generate` takes `inputs` (string) + `parameters`; maps almost 1:1 to `POST /api/generate` Ollama |
| Overlap | 3 | Similar to raw completion path |

**Routes needed:**
- `POST /generate` — `{"inputs": "...", "parameters": {...}}`
- `POST /generate_stream`

**Verdict**: Low effort but low reach. Defer until Ollama-compat ships (shares most of the same code path).

---

### 4. Cohere-compat — `POST /v1/chat`

**Composite score: 2.1**

| Axis | Score | Evidence |
|------|-------|---------|
| Reach | 2 | Cohere SDK has a niche; Command-R users, RAG pipelines using Cohere re-rank |
| Philosophy fit | 2 | Cohere is a hosted API service; self-hosted overlap is low |
| Implementation cost | 3 | Cohere v2 chat shape has `message` (single string) + `chat_history` list; distinctive but not complex |
| Overlap | 2 | Low reuse; distinct role labeling and response envelope |

**Verdict**: Defer. Niche adoption, low philosophy alignment.

---

### 5. Mistral-compat — `POST /v1/chat/completions`

**Composite score: 2.7**

| Axis | Score | Evidence |
|------|-------|---------|
| Reach | 3 | Mistral SDK, some EU-market developer shops |
| Philosophy fit | 3 | Open-source Mistral models align, but the SDK is for Mistral's hosted API |
| Implementation cost | 5 | Mistral mirrors OpenAI exactly — it IS OpenAI-compat |
| Overlap | 5 | Zero additional code needed; OpenAI-compat already handles it |

**Verdict**: Already done. The OpenAI-compat layer handles Mistral SDK clients at
`/v1/chat/completions`. Close this as WONTDO in issue triaging — the Mistral Python SDK
works against IICP proxy today with `base_url="http://localhost:11434/v1"`.

---

## Ranked Summary

| # | Adapter | Score | Effort | Recommended |
|---|---------|-------|--------|-------------|
| 1 | Ollama-compat | 4.4 | ~1 day | **Yes — Phase A** |
| 2 | Anthropic-compat | 3.8 | ~1.5d | **Yes — Phase B** |
| 3 | Mistral-compat | 2.7 | 0 | Done (OpenAI-compat covers it) |
| 4 | HF TGI-compat | 2.9 | 0.5d | After Phase A (shares code path) |
| 5 | Cohere-compat | 2.1 | ~1 day | Defer — low alignment |

---

## Implementation Design

### Shared pattern (`openai_compat/` reference)

```
proxy/src/proxy/
  openai_compat/
    server.py       ← FastAPI router, mounts at /v1
    translator.py   ← to_iicp_task() + to_openai_response()
  ollama_compat/    ← NEW Phase A
    server.py       ← FastAPI router, mounts at /api
    translator.py   ← to_iicp_task() + to_ollama_response()
  anthropic_compat/ ← NEW Phase B
    server.py       ← FastAPI router, mounts at /v1 (distinct routes)
    translator.py   ← to_iicp_task() + to_anthropic_response()
```

Both new adapters mount alongside `openai_compat`. Route collision risk:
- Ollama uses `/api/*` — no collision with `/v1/*`
- Anthropic uses `/v1/messages` + `/v1/models` — no collision with `/v1/chat/completions`

### ollama_compat/translator.py sketch (Phase A)

```python
def to_iicp_task(body: dict) -> tuple[UUID, str, dict]:
    task_id = uuid4()
    # /api/chat: messages list (same as OpenAI)
    # /api/generate: single prompt → wrap as user message
    messages = body.get("messages") or [{"role": "user", "content": body.get("prompt", "")}]
    return task_id, "urn:iicp:intent:llm:chat:v1", {
        "messages": messages,
        "model": body.get("model"),
        "temperature": body.get("options", {}).get("temperature"),
        "max_tokens": body.get("options", {}).get("num_predict"),
        "stream": body.get("stream", False),
    }

def to_ollama_response(iicp_response: dict, model: str = "iicp") -> dict:
    result = iicp_response.get("result") or {}
    choices = result.get("choices", [{}])
    content = (choices[0].get("message") or {}).get("content", "")
    return {
        "model": model,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "message": {"role": "assistant", "content": content},
        "done": True,
        "done_reason": "stop",
        "total_duration": 0,
    }
```

### Streaming note (Phase A)

Ollama streaming sends NDJSON lines (`Content-Type: application/x-ndjson`), not SSE.
Each line is a partial message object with `done: false`, final line has `done: true`.
The proxy's existing SSE streaming from `openai_compat/server.py` needs adaptation —
wrap each SSE chunk as a `\n`-delimited JSON line instead.

---

## Next Steps

1. **File implementation issue**: `[ADOPTION/CORC] Ollama-compat inbound adapter — /api/chat + /api/generate` — reference this doc, tag phase-5 + adoption + proxy + medium
2. **File implementation issue**: `[ADOPTION/CORC] Anthropic Messages API inbound adapter — /v1/messages` — reference this doc, phase-5 + adoption + proxy + medium  
3. **Update #273**: mark research deliverable done, close if implementation issues filed
4. **Update /docs/quickstart**: add Ollama-compat note alongside existing Open WebUI entry (they share the endpoint)

---

## Adoption Impact Estimate

| Adapter | Tools immediately unlocked |
|---------|--------------------------|
| Ollama-compat | Open WebUI (already works via :11434), Continue.dev (ollama provider), LobeChat, Chatbox, Jan, aider `--model ollama/iicp`, Obsidian AI, `ollama` CLI |
| Anthropic-compat | Any app using `from anthropic import Anthropic; client.messages.create(...)` with `base_url` override |

Combined: estimated 30–50 additional tools working zero-config or single-line-config
against IICP proxy post-Phase-A.
