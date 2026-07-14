# Native Framing Release-Artifact Audit

**Date:** 2026-07-14
**Scope:** published SDK archives that contain the native IICP TCP transport
**Result:** no executable 11-byte framing implementation found.

## Method

The audit downloaded published archives directly from PyPI, npm, and crates.io,
then inspected their packaged native-transport source or compiled JavaScript.
It also searched the complete local tag histories for an 11-byte framing
constant or an 11-byte framing-header declaration.

## Published-artifact evidence

| SDK | Earliest published archive with native framing | Current published archive | Evidence | Result |
|---|---|---|---|---|
| Python | `iicp-client 0.5.2` | `0.7.88` | `FRAME_HEADER_LEN = 12`; `struct.Struct("!4sBBBBI")` | 12 bytes |
| TypeScript | `@iicp/client 0.5.3` | `0.7.88` | packaged `dist/iicp_tcp.js` exports `FRAME_HEADER_LEN = 12` | 12 bytes |
| Rust | `iicp-client 0.5.2` | `0.7.88` | `FRAME_HEADER_LEN: usize = 12`; u32 length at bytes 8–11 | 12 bytes |

The first native Rust commit (`86d3d95`, 2026-05-27), Python commit
(`1a9e8ca`), and TypeScript commit (`8a85e18`) are also 12-byte
implementations. Local tag-history searches found no executable 11-byte
constant or header declaration.

## Cross-implementation confirmation

The canonical `native-framing-v1.json` fixture passed focused encoder/decoder
tests in all three SDKs. The independent binary TCP constellation harness then
passed all nine Rust/Python/TypeScript client-to-server pairings.

## Disposition

The historical 11-byte proposal did not ship in a reviewed native SDK archive.
IICP #5 may close as a framing-count correction, while future framing work
remains subject to the normal fixture, malformed-input, and transport-profile
conformance process.
