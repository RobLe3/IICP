# Native Framing Header-Count Root-Cause Record

**Status:** implementation-backed pre-ratification correction
**Scope:** native IICP frame header only; no wire behavior change
**Decision:** the established frame layout is **12 bytes**.

## Question

Why did the public draft describe an 11-byte frame while all maintained native
implementations use 12 bytes, and did either layout reach an executable
implementation?

## Evidence timeline

| Date | Commit / source | Observed fact |
|---|---|---|
| 2026-05-20 | `e071bfc` — initial `iicp-framing.md` | The prose says 11 bytes, but its own listed fields are `4 + 1 + 1 + 1 + 1 + 4 = 12`; its length offset is also consistent with a 12-byte layout. |
| 2026-05-22 | `744e84e` — `iicp-node/src/cbor.rs` | Initial executable native framing explicitly documents and implements 12 bytes, with a four-byte length at offsets 8–11. |
| 2026-05-23 | `bd9266c` — REACH framing probes | Operational conformance probes use `!4sBBBBI`, a 12-byte layout. |
| 2026-05-23 / 2026-05-26 | `744e84e` / `444aced` — adapter framing | Adapter reference encoder/decoder uses 12 bytes; its server fix reads the announced payload after the full 12-byte header. |
| 2026-05-27 | Rust `86d3d95`, Python `1a9e8ca`, TypeScript `8a85e18` | All three SDK native transports were introduced as 12-byte ports of the reference behavior. |
| 2026-05-31 onward | v1.5 → v1.9 spec migration | The 11-byte prose was copied forward without correction. |

## Root cause

This is a **documentation/design-transition defect**, not evidence of an
early implementation defect:

1. The initial framing draft retained an 11-byte count despite describing a
   12-byte field layout.
2. A related historical research simulation describes a different, never
   implemented 11-byte proposal: two reserved/flag bytes plus a three-byte
   length. That proposal conflicts with the initial draft's four-byte-length
   layout and with every executable source examined.
3. The executable reference implementation consistently selected the
   four-byte big-endian length plus one reserved byte, making the header 12
   bytes from its first native implementation onward.
4. Later spec synchronization preserved the stale count rather than checking
   the arithmetic, field offsets, and conformance implementations together.

## Why 11 bytes is not valid for the current contract

The current field set is fixed at:

```text
magic(4) + version(1) + type(1) + flags(1) + reserved(1) + length:u32be(4) = 12
```

An 11-byte header would require a different contract, such as removing the
reserved byte or replacing the `u32` length with a three-byte integer. Neither
appears in the maintained encoder/decoder, relay framing, REACH probes, or
cross-SDK native transport code. It would therefore be a breaking protocol
redesign, not a correction.

## Current disposition

- The canonical pre-ratification framing contract is a 12-byte header.
- `fixtures/native-framing-v1.json` pins implementation-backed decoding
  vectors and field offsets.
- The canonical vectors passed in the Rust, Python, and TypeScript SDKs, and
  the existing executable 3 x 3 TCP constellation matrix passed all nine
  client/server pairings on 2026-07-14. This is independent interoperability
  evidence, not merely three same-language round trips.
- The framing draft remains unratified; this correction does not claim full
  lifecycle, QUIC, fragmentation, or unknown-type interoperability.
- No client, directory, relay, or deployed node changes as a result of this
  documentation correction.

## Remaining verification before final closure

1. Preserve the canonical fixture gate in every maintained SDK release path.
2. Treat any future framing proposal as a new versioned contract with fixtures,
   malformed-input vectors, and cross-SDK evidence before implementation.

## Closure evidence

The release-artifact audit is recorded in
`FRAMING_RELEASE_ARTIFACT_AUDIT_2026-07-14.md`. It inspected the earliest
published native-transport archives and current `0.7.88` archives for all
three SDKs, their tag histories, canonical fixture tests, and the 3 x 3 binary
TCP constellation. No executable 11-byte implementation was found.
