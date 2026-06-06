# REP3 — Premium Services Taxonomy

**Track**: REP — Reputation & Tiered Access  
**Issue**: #169  
**Status**: Design-only (no simulation required)  
**Date**: 2026-05-18  
**ADR anchors**: ADR-019 (declarative pricing), ADR-027 (premium services as paid axis)

---

## Design Principle (non-negotiable)

Premium services are a **paid axis**, not a reputation axis. Credits buy access to specific services. Reputation is earned independently by task outcomes. Paying for premium does not change reputation. High reputation does not exempt anyone from paying for premium. The two axes are orthogonal and must remain so.

ADR-027 establishes this as a normative invariant. REP3 operationalises it as a taxonomy.

---

## Taxonomy: five service categories

### Category 1 — Capacity reservation

**Definition**: A node commits to a reserved throughput slot (e.g. 2 concurrent slots, 24h guaranteed) for a specific client.

**Who pays**: Client pays a reservation fee at commitment time (ADR-019 `pricing_credits_per_1000` extended with a `reservation_surcharge` field).

**Gaming surfaces**:
- Reservation squatting: client reserves slots and cancels, preventing real demand from reaching the node.
- Mitigation: reservation forfeiture fee (non-refundable above a cancellation threshold); node can publish max-reservation-fraction.

**Protocol requirement**: none beyond ADR-019. No new wire fields needed — reservation is a billing agreement between client and node, settled via the credit system.

### Category 2 — Priority queue

**Definition**: Tasks submitted with a priority marker are processed ahead of standard-tier tasks. Nodes set a price multiplier per priority level.

**Who pays**: Client pays the priority multiplier at task submission.

**Gaming surfaces**:
- Starvation of standard tasks if priority fraction is uncapped.
- Mitigation: node declares `max_priority_fraction` (default 0.5 = at most half of throughput is priority). Directory surfaces this field.

**Protocol requirement**: `priority` field in task submission body (currently not in spec). Maps to `high` | `standard` | `batch`. Nodes that don't support priority must reject `high` with `IICP-E012` (capacity exceeded).

### Category 3 — Guaranteed latency SLA

**Definition**: Node guarantees p95 latency below a stated threshold. Client pays a premium; if the SLA is missed, the credit charge is reduced or waived.

**Who pays**: Client pays premium upfront; node refunds the SLA portion on miss.

**Gaming surfaces**:
- SLA claim fraud: node advertises a low p95 it cannot deliver, collects premiums, and absorbs small refunds.
- Mitigation: REACH probes independently measure observed p95 for a node; excessive SLA miss rate triggers reputation demotion under ADR-023 compliance rules.

**Protocol requirement**: `sla_p95_ms` declaration in the heartbeat payload (extends ADR-012). REACH adds probe TEL-SLA-01 to verify.

### Category 4 — Attested execution environment

**Definition**: Node runs inference in an attested environment (SGX/TDX enclave, TPM-verified binary) and can provide a hardware attestation receipt with the task response.

**Who pays**: Client pays an attestation surcharge. Nodes declare `attestation: true` in the registry.

**Gaming surfaces**:
- Attestation forgery: node claims attestation without running in an enclave.
- Mitigation: attestation receipt is signed by the TEE manufacturer's chain; REACH (or the client) verifies the chain. ADR-014 OTel spans include attestation event.

**Protocol requirement**: `attestation_receipt` field in task response body (optional, present when client requests it). New intent URN suffix: `urn:iicp:intent:llm:chat:v1+attested`. Spec gap → feed into ARCS.

### Category 5 — Model pinning

**Definition**: Client requests a specific model version be used for the task (rather than the node's declared default). Node charges a pinning surcharge if the requested version is available.

**Who pays**: Client pays the pinning surcharge. Node declares available models in heartbeat `supported_models` array.

**Gaming surfaces**:
- Model bait-and-switch: node accepts a pinned request, silently serves the default model.
- Mitigation: task response must include `model_used` field (spec gap — currently `model` is in the request but not verified in the response). REACH adds probe to submit a known-model request and verify `model_used` in the response.

**Protocol requirement**: `model_used` field in task response body. Spec gap → feed into ARCS.

---

## Cross-category rules

1. **No reputation gating on premium access**: A bronze-tier client can buy any category of premium service if they have credits. High tier does not grant free premium access.
2. **No reputation gain from premium purchase**: Paying for premium does not increment reputation score. Reputation is only updated via task outcome quality/compliance signals (ADR-023).
3. **Directory transparency**: All premium declarations (reservation surcharge, priority multiplier, SLA p95, attestation, supported models) are surfaced via `GET /v1/registry/nodes/{prefix}` so clients can compare.
4. **Credit settlement is bilateral**: Credits settle between client and node. The directory tracks credit balances but does not intermediate individual task payments. This preserves the directory's bootstrap-only role (ADR-003).

---

## Open design decisions (REP2 dependency)

- How does premium access map to tiers? (Recommendation: no mapping — premium is credit-based, independent of tier. The tier just affects task routing preference, not premium eligibility.)
- What happens when a client has credits but is in the bronze tier? (Recommendation: they can still buy premium services; tier is a routing signal, not an access gate.)
- Should there be a "premium node" label in the directory, distinct from "attested node"? (Recommendation: no — premium is a property of the offer, not the node. A node can offer some premium categories and not others.)

---

## Spec gaps identified

| Gap | Required spec change | File | ADR impact |
|-----|---------------------|------|-----------|
| Priority task field | Add `priority` to task submission schema | `spec/iicp-semantics.md` §task | None (additive) |
| SLA declaration | Add `sla_p95_ms` to heartbeat payload | `spec/iicp-core.md` §heartbeat | ADR-012 extends |
| Attestation receipt | Add `attestation_receipt` to task response | `spec/iicp-semantics.md` §task-response | ADR-014 extends |
| Model verification | Add `model_used` to task response | `spec/iicp-semantics.md` §task-response | None (additive) |
| Intent URN suffix | Define `+attested` suffix convention | `spec/iicp-intents.md` | ADR-007 extends |

These gaps feed into ARCS — open a batch issue to cover the 5 spec changes as one ADR update.

---

## Conclusion

Premium services in IICP are a clean orthogonal axis to reputation. The taxonomy identifies five categories (capacity reservation, priority queue, guaranteed latency SLA, attested execution, model pinning) each with distinct gaming surfaces and mitigations. None of the five categories requires changes to the reputation mechanics (ADR-023). Two categories (attestation, model pinning) require minor protocol extensions; three (reservation, priority, SLA) require declaration fields surfaced via the directory. All five categories are fully aligned with ADR-019 (declarative pricing) and ADR-027 (premium as paid axis). The design is ready for ARCS formalisation.

**Next REP step**: REP1 (reputation mechanics and starting credit) — requires simulation (harness now ready).
