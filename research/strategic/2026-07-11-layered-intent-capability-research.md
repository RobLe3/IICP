# Strategic research — layered intent, capability and policy profiles

**Date:** 2026-07-11
**Status:** non-normative research guidance; no Protocol Suite or wire-contract change.

## Decision

IICP should remain the intent-routing and capability-discovery layer for AI
systems. It should interoperate with MCP tool servers and A2A agents through
compatibility profiles, not replace their host, tool or task-lifecycle models.

The proposed long-term substrate is:

| Layer | Responsibility |
|---|---|
| Core intent | Stable, outcome-level URN. |
| Capability profile | Schema identifier/digest, modalities, limits and execution binding. |
| Policy profile | Data class, jurisdiction, retention/training claim, approval and tool risk. |
| Evidence profile | Key state, conformance, observed health, receipt support and claims. |
| Extension declaration | Versioned URI with explicit required/optional compatibility. |

Existing stable URNs remain valid. Broad domains are not standardized merely
because they are useful; each needs schemas, policy/approval semantics,
fixtures and a migration path.

## Reproducible evidence

The reference working set evaluated three deterministic research artifacts:

1. **Taxonomy compatibility:** 9/9 scenarios passed, covering stable intents,
   a deprecated alias, schema mismatch, required/optional extensions, policy
   refusal, A2A skill mapping and MCP tool mapping.
2. **Receipt boundary:** 4/4 expected results passed. Directory-only evidence
   was rejected because it leaked canary prompt/token data; the recommended
   model combines redacted directory metadata with correlatable client and node
   receipts.
3. **Selection screening:** 30 seeds across pools of 10, 50 and 500 nodes and
   five scenarios. Composite inverse-load weighting was non-regressive in all
   screened size/scenario cells. Adaptive candidates were not consistently safe
   under adversarial conditions and remain research-only.

These simulations guide the next specification work. They do not prove live
performance, security, or production suitability.

## Ratification gates

Before any profile becomes normative, the project requires:

- reviewed public spec-source release synchronization;
- lifecycle, schema and migration rules;
- deterministic fixtures shared by the directory and maintained SDKs;
- backwards-compatible implementation review;
- controlled evidence for replay, key rotation, policy refusal and receipt
  privacy.

Tracking: [`RobLe3/IICP#2`](https://github.com/RobLe3/IICP/issues/2) for
spec-source governance and
[`iicp.network#619`](https://github.com/RobLe3/iicp.network/issues/619) for
the strategic substrate.

## Interoperability boundary

- **MCP:** tool schemas and annotations may inform an IICP capability/policy
  profile; MCP session semantics remain MCP's responsibility.
- **A2A:** Agent Card/skill metadata may map to a discoverable capability;
  A2A task lifecycle remains A2A's responsibility.
- **IICP:** chooses eligible execution capabilities under declared policy,
  trust, quality, cost, locality and availability constraints.

Primary external references: [MCP architecture](https://modelcontextprotocol.io/specification/2025-06-18/architecture),
[MCP tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools),
[A2A specification](https://a2a-protocol.org/latest/specification/), and
[JSON Schema 2020-12](https://json-schema.org/draft/2020-12/json-schema-core).
