# Native AI Infrastructure Assessment — Source Manifest

**Status:** reproducible research baseline  
**IICP suite:** v1.9.0, local baseline commit `3fe6560`
**MeshLLM:** v0.73.0, commit `002f2d8abb0bce3dbed59dc4e0944a51621ab47f`

## Normative IICP corpus

- `spec/v1.9/iicp-core.md`
- `spec/v1.9/iicp-framing.md` (draft, not yet ratified)
- `spec/v1.9/iicp-cbor-wire.md`
- `spec/v1.9/iicp-semantics.md`
- `spec/v1.9/node-capability-format.md`
- `spec/v1.9/iicp-cooperative-inference.md`
- `spec/v1.9/iicp-confidentiality.md`
- `spec/v1.9/iicp-identity-slot.md`
- `spec/v1.9/iicp-telemetry.md`
- `spec/v1.9/iicp-extensions.md`
- `spec/v1.9/iicp-service-lifecycle-profile.md` (proposed)
- `spec/v1.9/iicp-provider-admission-profile.md` (proposed)
- `spec/v1.9/iicp-dir.md`
- `spec/v1.9/iicp-federated-directory.md`
- `spec/v1.9/conformance-test-suite.md`
- `spec/v1.9/validation-methodology.md`

## Implementation evidence

- Rust `48eef3e`: `src/iicp_tcp.rs`
- Python `0bf91b7`: `src/iicp_client/iicp_tcp.py`
- TypeScript `5b72d37`: `src/iicp_tcp.ts`
- IICP network reference: `iicp-node/src/cbor.rs`, adapter framing, and REACH
  framing probes
- `../iicp.network/scripts/docker_client_release_gate.sh`
- `../iicp.network/scripts/docker_meshllm_real_smoke.sh`

## Framing evidence

- Canonical implementation-backed vectors:
  `fixtures/native-framing-v1.json`
- Digest and copy-integrity gate:
  `tools/check_native_framing_fixtures.py`
- Root-cause record:
  `FRAMING_ROOT_CAUSE_2026-07-14.md`
- Published-artifact audit:
  `FRAMING_RELEASE_ARTIFACT_AUDIT_2026-07-14.md`
- Draft lifecycle/admission conformance vectors:
  `fixtures/service-profiles-v1.json`
- Cross-SDK binary interoperability evidence: the local `iicp.network`
  constellation harness passed the full Rust/Python/TypeScript 3 x 3 matrix
  (9/9) on 2026-07-14.

## MeshLLM validation corpus

- `README.md`
- `crates/openai-frontend/README.md` and `src/router.rs`
- `SKIPPY_PROTOCOL_TODO.md`
- `docs/skippy/DATA_FLOW.md`, `CONFIGURATION.md`, `EXPERIMENTS.md`
- `crates/skippy-protocol/`, `crates/skippy-runtime/`, `crates/skippy-server/`

## Evidence policy

Repository prose is not performance evidence. Measurements must record command,
source revision, environment, raw output, and limitations. MeshLLM topology,
peer identities, routes, tokens, prompts, and raw payloads are excluded from
IICP public artifacts unless an explicit privacy-reviewed test requires them.
