# Ecosystem version truth

IICP reports three different facts separately:

1. **Published release** — the immutable versions released by each component owner.
2. **Deployed release** — versions verified at a named deployment, backed by deployment evidence.
3. **Observed adoption** — versions seen in a stated sample at a stated time.

These values answer different questions. Publishing a release does not deploy it, and a deployment does not prove that nodes have adopted the same version.

`ecosystem/current-versions.json` remains the release authority and existing consumers can continue to use it. The additive `iicp.ecosystem-version-truth.v1` schema defines a projection that combines that authority with deployment and adoption observations without changing the existing file.

## Evidence and missing data

Every axis has its own status, observation time, evidence URI and limitations. `observed` means the evidence was obtained for the stated time. `stale` preserves historical evidence while clearly warning that it may no longer describe current state. `unavailable` requires `data: null`; a publisher must not copy the published version into an unobserved deployment or adoption axis.

A deployed observation can reference an `iicp.deployment-record.v1` document and its verified SHA-256 digest. This projection does not replace signature verification of that record.

Adoption observations state their population, sample size and aggregated implementation/version counts. They do not identify nodes or operators. Node count must not be presented as operator diversity.

## Privacy boundary

The projection is content-free. It contains no task data, credentials, node identifiers, endpoints, operator identities or network topology. Evidence publishers should use public, bounded evidence resources.

## Validation

```bash
python3 tools/check_ecosystem_version_truth.py
python3 -m unittest tools/test_ecosystem_version_truth.py
```

The fixtures cover a release ahead of deployment with mixed adoption, unavailable live evidence and explicitly stale evidence. They are examples, not assertions about the current public network.
