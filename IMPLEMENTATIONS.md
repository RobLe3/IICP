# Official IICP repositories

This index is generated from `ecosystem/repositories.json`. Repositories are
independently versioned; they are logical members of the IICP ecosystem, not
Git submodules. Visibility describes source access, not protocol maturity.

| Component | Authority | Language | Visibility | Lifecycle | Release |
|---|---|---|---|---|---|
| [IICP](https://github.com/RobLe3/IICP) | normative protocol, registries and reviewed research | specification | public | active | 1.9.0 |
| iicp.network (source private) | cross-component issues, integration, conformance and project history | mixed | private | restructuring | — |
| iicp-website (source private) | iicp.network website source and static-build contracts | typescript | private | active | 0.1.0 |
| iicp-directory-php (source private) | PHP reference directory implementation and current Genesis Seed code line | php | private | publication-review | 1.10.76 |
| iicp-directory-rust (source private) | Rust directory implementation and parity candidate | rust | private | publication-review | 0.1.0 |
| [iicp-client-python](https://github.com/RobLe3/iicp-client-python) | Python consumer and provider SDK | python | public | active | 0.7.94 |
| [iicp-client-typescript](https://github.com/RobLe3/iicp-client-typescript) | TypeScript consumer and provider SDK | typescript | public | active | 0.7.94 |
| [iicp-client-rust](https://github.com/RobLe3/iicp-client-rust) | Rust consumer and provider SDK | rust | public | active | 0.7.94 |
| [iicp-web-node](https://github.com/RobLe3/iicp-web-node) | browser-native IICP consumer and provider implementation | typescript | public | experimental | 0.2.2 |

## Governance boundary

The specification repository defines protocol semantics. Implementations may
propose changes but cannot silently redefine the protocol. Production access,
credentials, backups and operator data are not part of this public repository map.

The planned GitHub organization uses the free plan. No paid GitHub feature is a
conformance, build, publication or governance dependency.
