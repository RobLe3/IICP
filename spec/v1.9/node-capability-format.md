# IICP Node Capability Format

**Version**: 0.1.1  
**Date**: 2026-05-14  
**Status**: draft  
**Issue**: #19  
**Authority**: Protocol Steward  
**Relation**: SPEC_ANALYSIS.md GAP-4, ADR-007, IICP-DIR §3.1

---

## 1. Purpose

IICP v1.4.2 uses a generic `capabilities` array in REGISTER but leaves the object
schema unspecified. This document defines the canonical capability object format for
all Phase 1 node types. It is normative for REGISTER payloads and NODELIST responses.

---

## 2. Base Capability Object

All capability objects share this base schema:

```json
{
  "intent": "urn:iicp:intent:llm:chat:v1",
  "version": "1",
  "phase": 1
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `intent` | string | MUST | Full intent URN per ADR-007 |
| `version` | string | SHOULD | Capability version; "1" if absent |
| `phase` | integer | MAY | Minimum IICP phase required; 1 if absent |

All additional fields are capability-type-specific (§3–§7).

---

## 3. LLM Inference Capability

For nodes serving language model inference.

> **Cross-ref (v0.1.1):** two register-time fields are specced normatively in `iicp-dir.md §3.1`, not
> duplicated here: `capabilities[].input_modalities` (`["text"]` default, `["text","image"]` for vision;
> ADR-046) and the top-level `operator_delegation` object (ed25519 operator→node binding; ADR-045 Phase A).

```json
{
  "intent": "urn:iicp:intent:llm:chat:v1",
  "models": ["llama3", "mistral-7b"],
  "max_tokens": 8192,
  "context_length": 32768,
  "supports_streaming": false,
  "quantization": "q4_k_m",
  "inference_engine": "llama.cpp",
  "hardware": "cuda",
  "avg_tokens_per_second": 45.0
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `models` | string[] | MUST | Model identifiers served |
| `max_tokens` | integer | MUST | Max output tokens per request |
| `context_length` | integer | SHOULD | Max context window (input + output) |
| `supports_streaming` | bool | MAY | Default false (Phase 1) |
| `quantization` | string | MAY | e.g., `q4_k_m`, `fp16`, `awq` |
| `inference_engine` | string | MAY | e.g., `llama.cpp`, `ollama`, `vllm`, `exllamav2` |
| `hardware` | string | MAY | `cuda`, `metal`, `cpu`, `rocm` |
| `avg_tokens_per_second` | float | MAY | Self-reported throughput estimate |

**Embeddings**:

```json
{
  "intent": "urn:iicp:intent:llm:embed:v1",
  "models": ["nomic-embed-text"],
  "max_tokens": 8192,
  "dimensions": 768,
  "batch_size": 32
}
```

**Audio transcription (speech-to-text, #414)**:

```json
{
  "intent": "urn:iicp:intent:audio:transcribe:v1",
  "models": ["whisper-large-v3"],
  "inference_engine": "whisper.cpp",
  "hardware": "metal"
}
```

The CALL payload carries the audio as base64 (`audio`) plus optional `language` /
`response_format` / `prompt`; the node posts it as a multipart file upload to the
backend's OpenAI-dialect `/v1/audio/transcriptions` endpoint (Whisper-class backends).
See `registry/intents.json` for the authoritative payload schema.

**Text-to-speech (#414)**:

```json
{
  "intent": "urn:iicp:intent:audio:speech:v1",
  "models": ["tts-1"],
  "inference_engine": "espeak-ng"
}
```

The CALL payload carries the text to synthesize (`input`) plus optional `voice` /
`response_format` / `speed`; the node posts JSON to the backend's OpenAI-dialect
`/v1/audio/speech` endpoint and base64-encodes the returned binary audio into
`result.audio` (with `content_type` + `format`). See `registry/intents.json`.

**Content moderation (#414)**:

```json
{
  "intent": "urn:iicp:intent:safety:moderate:v1",
  "models": ["toxic-bert"]
}
```

The CALL payload carries the text to moderate (`input`, string or array); the node
posts JSON to the backend's OpenAI-dialect `/v1/moderations` endpoint and returns the
`{results: [{flagged, categories, category_scores}]}` verbatim. `model` is OPTIONAL
(the backend supplies a fixed moderation model). See `registry/intents.json`.

---

## 4. MCP Tool Execution Capability

For nodes that execute MCP tool calls (see `iicp-mcp-binding.md`).

```json
{
  "intent": "urn:iicp:intent:mcp:tools/call:v1",
  "mcp_tools": ["bash", "read_file", "web_search"],
  "mcp_version": "2025-03-26",
  "sandboxed": true,
  "allowed_domains": ["*.wikipedia.org"]
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `mcp_tools` | string[] | MUST | Tool names the node can execute |
| `mcp_version` | string | MUST | MCP spec date (ISO 8601) |
| `sandboxed` | bool | SHOULD | Whether execution is sandboxed |
| `allowed_domains` | string[] | MAY | Network domain allow-list for web tools |

---

## 5. Compute / Batch Capability

For nodes offering general compute or batch task processing.

```json
{
  "intent": "urn:iicp:intent:compute:batch:v1",
  "max_batch_size": 100,
  "supported_formats": ["jsonl", "csv"],
  "max_payload_mb": 50
}
```

---

## 6. Data Retrieval Capability

For nodes providing vector search or knowledge retrieval.

```json
{
  "intent": "urn:iicp:intent:data:retrieval:v1",
  "index_type": "faiss",
  "dimensions": 1536,
  "index_size": 1000000,
  "metric": "cosine"
}
```

---

## 7. Capability Array Rules

A single node MAY declare multiple capabilities:

```json
{
  "capabilities": [
    {
      "intent": "urn:iicp:intent:llm:chat:v1",
      "models": ["llama3"],
      "max_tokens": 8192
    },
    {
      "intent": "urn:iicp:intent:mcp:tools/call:v1",
      "mcp_tools": ["bash"],
      "mcp_version": "2025-03-26"
    }
  ]
}
```

A node supporting Phase 5 CIP intents (summarization, reranking, classification) uses the `llm:` URN namespace:

```json
{
  "capabilities": [
    {
      "intent": "urn:iicp:intent:llm:chat:v1",
      "models": ["llama3.2"],
      "max_tokens": 8192
    },
    {
      "intent": "urn:iicp:intent:llm:summarize:v1",
      "models": ["llama3.2"],
      "max_length": 512
    },
    {
      "intent": "urn:iicp:intent:llm:rerank:v1",
      "models": ["llama3.2"],
      "max_candidates": 20
    },
    {
      "intent": "urn:iicp:intent:llm:classify:v1",
      "models": ["llama3.2"]
    }
  ]
}
```

**Rules**:
- Each intent URN MUST appear at most once per capabilities array.
- The directory MUST index each capability by its `intent` for discovery filtering.
- Unknown fields MUST be preserved and returned in NODELIST (forward compatibility).
- A node with zero valid capabilities MUST NOT be registered (directory returns 422).

---

## 8. NODELIST Propagation

The directory MUST return capabilities in NODELIST without modification:

```json
{
  "node_id": "uuid",
  "endpoint": "https://node.example.com",
  "score": 0.91,
  "capabilities": [
    {
      "intent": "urn:iicp:intent:llm:chat:v1",
      "models": ["llama3"],
      "max_tokens": 8192
    }
  ]
}
```

The `capabilities` array is informational. Clients SHOULD validate that the selected
node actually supports their intent before submitting a CALL.

---

## 9. Provider Policy Block (Phase 5 — Cooperative Inference Profile)

Nodes participating in the Cooperative Inference Profile declare a `policy` block
in REGISTER alongside their capabilities. This block is optional in Phase 1–4 and
ignored by nodes that do not implement the CIP.

```json
{
  "node_id": "moltbot-node-123",
  "endpoint": "https://node.example.net",
  "capabilities": [ ... ],
  "policy": {
    "allow_remote_inference": true,
    "allow_tool_execution": false,
    "allow_file_access": false,
    "allow_shell_execution": false,
    "allow_browser_automation": false,
    "allow_private_memory_access": false,
    "minimum_caller_reputation": 0.70,
    "require_credits": true,
    "minimum_reputation": 0.5,
    "max_concurrent_remote": 2
  },
  "pricing": {
    "accepts_credits": true,
    "credits_per_1000_tokens": 1.0,
    "free_tier_tokens": 0
  }
}
```

| Field | Default | Notes |
|-------|---------|-------|
| `allow_remote_inference` | false | Must be `true` to participate in CIP |
| `allow_tool_execution` | false | MUST NOT be `true` unless the node is an explicit MCP exec node |
| `allow_file_access` | false | MUST remain false for cooperative inference |
| `allow_shell_execution` | false | MUST remain false — safety boundary |
| `allow_browser_automation` | false | MUST remain false — safety boundary |
| `allow_private_memory_access` | false | MUST remain false — safety boundary |
| `minimum_caller_reputation` | 0.0 | Caller reputation score threshold (0.0 = accept all) |
| `require_credits` | false | If true, caller must have credits before task is accepted |
| `minimum_reputation` | 0.0 | CIP-specific: minimum reputation score of the requesting coordinator (0.0 = accept any); used in §2.1 Provider Opt-In gate. If the coordinator's `reputation_score` is below this value, the provider MUST reject with `IICP-E020`. |
| `max_concurrent_remote` | 2 | Maximum simultaneous inbound CIP sub-tasks this node will accept. If reached, MUST return `IICP-E021` (capacity exhausted). MUST NOT silently queue. |

The directory MUST return `policy` in NODELIST. Clients MUST pre-screen nodes for
policy compatibility before submitting a CALL (e.g., skip nodes with
`allow_remote_inference: false`).

---

## 10. Versioning

Capability format versions follow semver major only:
- `v1` — Phase 1 (this document)
- `v2` — Phase 3 (adds reputation data, signed capability attestation)
- `v3` — Phase 5 (adds `policy` and `pricing` blocks for Cooperative Inference Profile)

The intent URN suffix (`:v1`) is the capability format version, distinct from the
protocol version.

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.2 | 2026-05-17 | §9 policy block: added `minimum_reputation` and `max_concurrent_remote` fields with IICP-E020/E021 error references; closes #72 |
| 0.1.0 | 2026-05-14 | Initial draft — capability object schema, intent URN format, policy block (Phase 5 reserved); closes issue #19 |
| 0.1.1 | 2026-05-15 | Added Changelog section (A6 spec cleanup) |

---

## Sign-off

**Protocol Steward**: Capability format fills GAP-4 from SPEC_ANALYSIS.md. §9 (policy
block) is reserved for Phase 5 Cooperative Inference Profile — additive, backward
compatible. Closes GitHub issue #19 (draft). ✓
