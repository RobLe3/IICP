# Clean-room directory interoperability guide

This guide supports IICP issue #31. It is for a team outside the IICP
repository family that wants to implement directory-facing behavior from
public contracts and report ambiguities. It does not make an implementation
independent merely by being followed; independence also requires separate
authorship, operation and publication of the result.

## Fixed public inputs

Choose one immutable IICP Protocol Suite release and record its tag and release
archive SHA-256. Use only material shipped in that release:

- `spec/v1.9/iicp-dir.md` and `spec/v1.9/iicp-semantics.md`;
- the checksum-recorded `openapi.yaml` contract projection from the matching
  published PHP directory release, without consulting its runtime source;
- versioned fixtures and schemas listed by the release-integrity manifest;
- the separately released `iicp-conformance` artifact and checksum.

Do not use PHP or Rust directory source, implementation tests, private issue
history, deployment configuration, database schemas, or advice derived from a
reference implementation. Record any point that cannot be resolved from the
fixed public inputs as an ambiguity rather than inspecting an implementation.

## Minimum implementation boundary

Implement a disposable directory surface sufficient for these released
profiles, in order:

1. `directory-public-v1` for discovery validation and public refusal cases;
2. `directory-lifecycle-v1` for registration, authenticated heartbeat, token
   refresh, stale-token refusal and deregistration;
3. `directory-dispatch-v1` for prompt-free route-ticket issuance and negative
   policy/validation behavior.

Run against a loopback endpoint and disposable data store controlled by the
implementer. Do not aim mutating profiles at the public Genesis directory.
Passing the profiles does not prove federation, production availability,
performance, protocol-profile ratification or compatibility outside the pinned
release.

## Evidence record

Publish the following without secrets or operational identifiers:

- implementation repository, commit and license;
- authorship and operator relationship to the IICP project;
- operating system, language/runtime and package versions;
- exact protocol-suite and runner versions plus artifact checksums;
- per-profile signed, content-free result bundles;
- a positive/negative compatibility matrix;
- an ambiguity log with the public source, competing interpretations, chosen
  behavior and suggested specification correction.

Before publication, run `iicp-conformance verify` on every bundle. Never
publish credentials, signing private keys, endpoint URLs, node IDs, route
material, payloads, raw responses, private topology or personal data. Use the
`independent` evidence class only when the external party controls the tested
implementation and publishes its own result. An IICP-project rerun remains
`project-verified`.

Copy `evidence/clean-room-interoperability-record-v1.json` into the external
repository before the run and complete that copy. Validate it with the released
copy of `tools/check_clean_room_interoperability_record.py`. The project copy
must remain a blank template; it is not an IICP-generated external result.

## Completion criteria

The clean-room exercise is complete only when two separately running directory
implementations execute the same pinned positive and negative profiles, every
observed ambiguity has a public disposition, and the published report keeps
protocol interoperability distinct from deployment and federation claims.
Follow [the external run guide](EXTERNAL_RUN.md) for artifact installation,
offline verification and evidence-class rules.
