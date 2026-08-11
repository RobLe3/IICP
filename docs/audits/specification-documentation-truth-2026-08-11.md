# Specification documentation truth audit, 11 August 2026

## Scope and authority

This audit covers the current specification index, root overview, versioning
guide, intent registry documentation, conformance metadata and their local
validation tools. It does not rewrite research reports, changelogs or other
dated evidence as though they described the current deployment.

The following sources were treated as current authority:

- `spec/v1.9/VERSION` and `ecosystem/current-versions.json` for the protocol and
  component release axes;
- `SPEC_STATUS.md` for status terminology;
- `registry/intents.json` and its JSON Schema for registry content;
- the conformance-suite header and changelog for suite-version identifiers;
- `spec/v1.9/release-integrity-manifest.json` for the immutable v1.10.12
  release set.

Runtime deployment and adoption claims are outside this repository's normative
authority. They require dated live evidence and must not be inferred from a
published specification or package version.

## Results

### Confirmed current state

- The protocol-suite release is 1.10.12 and the stable wire baseline remains
  1.9.0.
- The generated component projection records PHP directory 1.10.90, Rust
  directory preview 0.1.10, all three SDKs at 0.7.101 and the experimental
  browser node at 0.2.3.
- The intent registry is version 1.4.0 and contains 17 entries. Structural
  validation, the pre-normative profile manifest, source classification and
  SDK-currency checks pass locally.
- Registry documentation correctly distinguishes the canonical vocabulary
  from live provider availability and does not treat implementation evidence
  as proof that a provider is currently online.

### Confirmed corrections required

1. `spec/v1.9/README.md` labels the current suite as v1.9.0 even though its
   linked `VERSION` file contains 1.10.12. Its status legend also defines a
   draft as project-normative, contrary to `SPEC_STATUS.md`, where an active
   draft is not required for suite conformance unless a released profile
   incorporates it. The reading-order table repeats sequence numbers 5 and 6.
2. The root `README.md` reports the official SDK line as 0.7.100. The generated
   catalog records 0.7.101. Its manually maintained release-history table ends
   at v1.10.2 while the same page identifies v1.10.12 as current. This is a
   duplicated-current-fact failure, not a package or protocol defect.
3. `spec/v1.9/iicp-framing.md` has a 0.1.8-draft header and a latest changelog
   entry of 0.1.9-draft. The lifecycle-envelope content described by the later
   entry is present, so the header is stale.
4. `VERSIONING.md` calls the S.12 0.6.8 value current, while the S.12 document
   header is 0.6.13. This editorial version should be derived or described as
   an example rather than copied as current state.
5. `tools/check_conformance_version_truth.py` applies the released-suite
   `suite_version` requirement to every bundled runner fixture. Five fixtures
   explicitly marked pre-normative have no suite version, causing the
   repository-state unit test to fail. The gate needs to distinguish released
   conformance profiles from pre-normative research fixtures without relaxing
   checks on released profiles.

These files are members of the v1.10.12 integrity set. Editing them and
regenerating its manifest without a new corrective release would change an
already identified immutable release. The corrections therefore belong in the
next ordinary patch release; this audit does not bump or rewrite a release.

## Checks executed

| Check | Result |
|---|---|
| `python3 tools/generate_implementations.py --check` | Pass |
| `python3 tools/check_intent_registry.py` | Pass |
| `python3 tools/check_profile_fixture_manifest.py` | Pass, 22 fixtures |
| `python3 tools/audit_intent_sources.py --check` | Pass |
| `python3 tools/check_discovery_sdk_currency.py` | Pass, 0.7.101 |
| `python3 tools/check_spec_release_integrity.py` | Pass, v1.10.12 and 109 pinned artifacts |
| `python3 -m unittest tools.test_conformance_version_truth -v` | Fail: five pre-normative fixtures lack `suite_version` |
| `python3 tools/check_intent_registry_schema.py` | Not run: local `jsonschema` dependency is absent |
| `python3 tools/quick_validation.py` | Not run: local `numpy` dependency is absent |

No result above is evidence of publication, deployment, live adoption or
independent interoperability.

## Disposition

The confirmed corrections are tracked in
[`IICP#128`](https://github.com/RobLe3/IICP/issues/128) because the pinned
documents, integrity manifest and version-truth gate must move in one
corrective release.
No intent-registry issue was opened: the current registry checks passed and the
documentation states its authority and limitations accurately.
