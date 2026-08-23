# IICP software update trust model

Status: project architecture guidance. This document does not change the IICP wire protocol.

## Why update handling is a trust boundary

An unattended updater can replace code that holds node identity, reads operator configuration and executes provider workloads. A registry response proves that a package version is available. It does not, by itself, authorize that version to run.

IICP update implementations therefore keep these decisions separate:

1. **Discovery** finds one candidate version from an explicitly selected source.
2. **Validation** checks the package name, stable version syntax and forward-only version relationship.
3. **Authorization** applies the configured release channel and source policy.
4. **Installation** installs that exact candidate without resolving a different top-level version.
5. **Verification** confirms the installed program reports the expected version.
6. **Activation** restarts or re-executes only after installation succeeds.
7. **Recovery** retains or restores the previous installation when activation or health verification fails.

Manual rollback is a separate operator action. An automatic updater must not interpret an older registry version as permission to downgrade.

## Independent controls

| Layer | Current control | What it does not prove |
| --- | --- | --- |
| Dependency determinism | Rust executable releases publish `Cargo.lock`; automatic Cargo installation uses `--locked`. | Locked dependencies can still contain malicious code. |
| Registry integrity | Automatic paths name the official crates.io, PyPI or npm source and use registry transport/integrity mechanisms. | Registry availability does not authorize a release. |
| Release authorization | Stable candidates must have an exact version greater than the running version. | A compromised maintainer account could publish an apparently valid release. |
| Artifact authenticity | Package-registry integrity and current release evidence bind the fetched object to the published object. | A checksum alone does not establish who intended the release. |
| Activation | Managed directory and fleet paths stage, verify and health-check before completing an upgrade. | Unsupervised SDK re-exec paths do not yet provide uniform cross-platform rollback. |

`Cargo.lock` plus `cargo install --locked` prevents install-time dependency re-resolution. It is not a complete software supply-chain guarantee and must not be described as one.

## Implementation boundaries

The three SDKs use ecosystem-specific mechanisms:

- Rust installs the exact discovered crate version with the published lockfile and preserves the node's supported runtime feature set.
- Python installs the exact discovered top-level package from the official PyPI index. This does not freeze every transitive wheel dependency.
- TypeScript installs the exact discovered top-level package from the official npm registry. This does not make npm's transitive graph immutable.
- The Rust directory uses an externally supervised, staged updater with checksum and release-manifest binding, schema checks, stable-symlink activation, health verification and rollback.

No updater may fall back to an unlocked or floating installation after a verification failure.

## Threats and remaining work

The current controls reduce exposure to dependency re-resolution, malformed registry metadata, accidental downgrade, prerelease drift, feature drift and interrupted installation. Release-time advisory and deny policies add early detection for known malicious packages and unapproved sources.

They do not fully solve compromised publisher credentials, a malicious but correctly published IICP release, compromised build infrastructure, or universal cross-platform activation rollback. The next architecture stage should evaluate authenticated prebuilt artifacts and standard provenance mechanisms such as Sigstore, SLSA provenance or GitHub artifact attestations. That work must define signing authority and key rotation before it changes the updater. IICP will not invent a signing scheme or package manager.
