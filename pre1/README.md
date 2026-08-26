# IICP pre-1.0 feature boundary

[`feature-baseline-v1.json`](feature-baseline-v1.json) is the public,
implementation-neutral crosswalk for the client, Directory and Management
qualification program. It separates the coordinated stable boundary from
existing component version numbers, experimental integrations, standards work
and production authority.

The baseline records capability families rather than individual functions. A
required family names its specification or public contract, executable fixture
and implementing repositories. `CLEAR_WITH_EXPLICIT_BOUNDARY` means the
behavior is mapped without granting a related migration, deployment or
standards claim. `OPEN` would block candidate-bound evidence.

The six component API reviews remain open. The crosswalk therefore validates
but does not yet pass its strict freeze gate:

```bash
python3 tools/check_pre1_feature_baseline.py
python3 tools/check_pre1_feature_baseline.py --strict  # expected OPEN
```

No result in this directory authorizes a coordinated stable label, package
publication, Management service, Directory authority change or deployment.
