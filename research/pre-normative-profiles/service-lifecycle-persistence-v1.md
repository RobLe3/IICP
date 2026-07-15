# Service Lifecycle Persistence — Reference Contract

**Status:** pre-normative implementation evidence  
**Profile:** `urn:iicp:profile:service-lifecycle:v1`  
**Fixture:** `fixtures/service-lifecycle-persistence-v1.json`

## Purpose

This contract defines the storage-port guarantees exercised by opt-in Python
and Rust reference adapters. It does not alter the lifecycle profile, fixed
frame, HTTP binding, intent registry or ordinary node behavior.

## Reference guarantees

A conforming local adapter preserves task and idempotency bindings, request
digest equality, atomic state/event transitions, contiguous event sequences,
bounded replay, terminal TTL and one authoritative terminal transition across
multiple processes on one host. Restarting the adapter does not create a new
execution claim.

Durable event detail is limited to bounded progress, event identifiers, safe
reason/outcome codes and integrity digests. Prompts, payloads, responses,
credentials, URLs, filesystem paths, checkpoints, shards and private topology
are rejected before persistence.

## Explicit non-guarantees

The reference adapters do not provide cross-host consensus, whole-store
rollback resistance, production identity authorization, backend cancellation,
live slow-consumer flow control or settlement behavior. Persistence formats are
implementation-specific and are not interoperable protocol artifacts.
