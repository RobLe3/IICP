# Separating reliability, latency, health and integrity in provider selection

**Date:** 21 August 2026  
**Status:** IICP implementation-experience note  
**Scope:** A bounded account of one defect, its correction and the evidence available at publication. This is not an Internet-Draft or a claim of external review.

## Summary

An earlier IICP reputation rule treated a successful task as a failure-equivalent reputation event when its average latency exceeded twice an assumed interactive budget. The heartbeat report did not carry the task's QoS, so the directory substituted a 2,000 ms interactive budget. A successful request above 4,000 ms therefore received the same `-0.05` delta as an adapter or backend failure.

Operation on 20 August 2026 showed why that interpretation was unsafe. Genesis reported eight heartbeating nodes, 100% reachability and 100% aggregate task success, while a reachable Rust node with 205 completed tasks and about 7.27 seconds of self-reported task latency had a reputation of 0.10. Under the old rule, ten successful 7-second tasks could move a score from 0.50 to 0.00. These figures are dated observations preserved in [IICP issue #182](https://github.com/RobLe3/IICP/issues/182); they are not independent measurements of answer quality.

The defect was semantic rather than an implementation mismatch. The PHP and Rust directories implemented the same rule. The correction, identified as `outcome-v2`, makes task completion the subject of the outcome score and keeps latency, health, semantic quality and integrity as separately labelled evidence.

## Why the old rule failed

The old rule tried to make reputation reflect both completion and responsiveness:

```text
unknown QoS -> interactive budget = 2,000 ms
successful batch with average latency > 2 × budget -> -0.05
backend failure -> -0.05
```

This looked conservative, but the directory lacked the per-task information needed to interpret the latency. It could not distinguish an interactive deadline from a large generation, batch request, best-effort task or slower specialist model. Substituting an interactive default converted missing context into a negative reliability claim.

The shared implementation tests confirmed that both directories calculated the specified result. They did not initially challenge whether the specified result still meant what operators and routing policy expected it to mean. Increasing real task volume exposed that mismatch.

## Outcome-v2 decision

The current rule is:

| Outcome | Reputation delta |
| --- | ---: |
| Successful task | `+0.01` |
| Adapter or backend failure | `-0.05` |
| Protocol timeout | `-0.10` |

A heartbeat applies the sum atomically. Its positive component is capped at `+0.10`, negative deltas remain uncapped, and the result is clamped to `[0.0, 1.0]`. A separate hourly positive-gain ceiling remains in force.

Latency can still inform selection. If a request carried an explicit QoS class or deadline, an implementation may report whether the performance constraint was met. Missing that constraint does not turn success into failure. A protocol timeout remains a timeout outcome.

The evidence dimensions now have separate meanings:

| Dimension | What it can support | What it does not establish |
| --- | --- | --- |
| Execution outcome | Whether an execution reported success, failure or timeout | Answer quality or integrity |
| Latency | Performance relative to an explicit requirement, or advisory timing | Failure when the task succeeded |
| Health and reachability | Whether a service appears operational and reachable | Semantic correctness |
| Semantic quality | Externally defined evaluation of the returned work | Transport health or authorization |
| Integrity evidence | A separately identified finding and its provenance | Automatic proof of fraud |
| Evidence class | Whether information is self-reported, directory-observed or independently verified | A reason to merge the dimensions |

## Retry-safe metric delivery

The incident also exposed an evidence-delivery problem. The Python, TypeScript and Rust SDKs had drained pending task counters before sending a heartbeat. If transport failed, that evidence could be lost.

Current SDKs retain one pending batch with an opaque `metrics_batch_id` until the directory acknowledges it. A directory applies each `(node_id, metrics_batch_id)` at most once. A duplicate delivery is acknowledged without reapplying counters or reputation. A mismatched acknowledgement does not clear the pending batch.

Older clients may omit the identifier and older directories may not acknowledge it. This remains wire-compatible, but retry idempotency cannot be proven for that legacy exchange. The three SDKs and both directory flavors test the shared duplicate-batch contract; the maintained implementations remain separate from independent interoperability evidence.

## Migration and mixed versions

A score produced by the old latency-coupled rule is not relabelled. A directory adopting `outcome-v2` starts a new opaque epoch at the neutral score `0.5`, retains the previous score only as labelled audit history and exposes both `reputation_model` and `reputation_epoch`. A missing model identifier is treated as legacy evidence.

This also keeps three release facts separate:

- **Published:** the source release contains the new semantics.
- **Deployed:** a directory is running that release and epoch.
- **Adopted:** nodes are using SDK behavior that supports retry-safe batches.

One fact does not imply the other two.

## Evidence

The normative rules are in [`spec/v1.9/iicp-semantics.md`](../../spec/v1.9/iicp-semantics.md#112-per-task-delta-rules) and the retry contract is in [`spec/v1.9/iicp-dir.md`](../../spec/v1.9/iicp-dir.md). The shared cases are in [`reputation-outcome-v2.json`](../pre-normative-profiles/fixtures/reputation-outcome-v2.json), with conformance identifiers `REP-01`, `REP-08` and `REP-09`.

After the guarded Genesis upgrade to PHP directory `v1.10.93`, a finite live check observed four ordinary successful tasks move one score from 0.50 to 0.54. A separate successful request completed in about 9.1 seconds while its provider's reported lifetime task latency remained above 7.3 seconds; its score moved from 0.50 to 0.51. Four later heartbeat observations did not apply that batch again. The bounded acceptance record and its limitations are summarized in [IICP issue #182](https://github.com/RobLe3/IICP/issues/182).

That live check did not inject failures into production. Task outcomes and latency were provider-reported, not independent semantic evaluations. Negative, duplicate, legacy and cutover cases are demonstrated by project fixtures and maintained implementation tests.

## Reusable finding

A routing system should not infer one evidence dimension from another merely because a single score is convenient. In this case, slowness was not failure, a low outcome score was not a fraud verdict, reachability was not semantic quality and self-reported telemetry was not independently verified evidence. Selection policy may consider all of these dimensions, but it should preserve their labels and provenance long enough to explain the decision.
