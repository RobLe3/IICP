# Official IICP repositories

This index is generated from `ecosystem/repositories.json`. Repositories are
independently versioned; they are logical members of the IICP ecosystem, not
Git submodules. Visibility describes source access, not protocol maturity.

| Component | Authority | Language | Visibility | Lifecycle | Release |
|---|---|---|---|---|---|
| [IICP](https://github.com/RobLe3/IICP) | normative protocol, registries and reviewed research | specification | public | active | 1.10.12 |
| iicp.network (source private) | cross-component issues, integration, conformance and project history | mixed | private | restructuring | — |
| iicp-network-ops (source private) | reviewed deployment, rollback, REACH and community operational source; no live credentials or production data | mixed | private | active | — |
| iicp-network-internal (source private) | FORGE, agent, project-management and reviewed private-history material; never a public build dependency | mixed | private | active | — |
| iicp-website (source private) | private iicp.network website source and static-build contracts; not planned for publication | typescript | private | active | 0.1.0 |
| [iicp-directory-php](https://github.com/RobLe3/iicp-directory-php) | PHP reference directory implementation and current Genesis Seed code line | php | public | active | 1.10.89 |
| [iicp-directory-rust](https://github.com/RobLe3/iicp-directory-rust) | pre-1.0 Rust directory operator preview; not the production Genesis authority | rust | public | operator-preview | 0.1.10 |
| [iicp-client-python](https://github.com/RobLe3/iicp-client-python) | Python consumer and provider SDK | python | public | active | 0.7.101 |
| [iicp-client-typescript](https://github.com/RobLe3/iicp-client-typescript) | TypeScript consumer and provider SDK | typescript | public | active | 0.7.101 |
| [iicp-client-rust](https://github.com/RobLe3/iicp-client-rust) | Rust consumer and provider SDK | rust | public | active | 0.7.101 |
| [iicp-web-node](https://github.com/RobLe3/iicp-web-node) | browser-native IICP consumer and provider implementation | typescript | public | experimental | 0.2.3 |

## Governance boundary

The specification repository defines protocol semantics. Implementations may
propose changes but cannot silently redefine the protocol. Production access,
credentials, backups and operator data are not part of this public repository map.

The planned GitHub organization uses the free plan. No paid GitHub feature is a
conformance, build, publication or governance dependency.
