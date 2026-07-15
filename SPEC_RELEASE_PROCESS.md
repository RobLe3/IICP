# Spec-Only Release Process

This repository is the canonical public source for reviewed IICP protocol text,
intent registry state, and conformance fixtures. It is not a blind mirror of an
implementation worktree.

## Promotion procedure

1. Gather current implementation evidence and the corresponding approved
   working specification changes. A proposed change must distinguish deployed
   behavior, draft behavior, and research.
2. Update the candidate protocol text, registry, fixtures, and conformance rows
   together in this repository. Semantic profiles and experiments stay marked
   draft until independently implemented and reviewed.
3. Update `spec/v1.9/release-integrity-manifest.json` only after review, using
   the exact digests of the canonical candidate artifacts.
4. Run `tools/check_spec_release_integrity.py`, the fixture gates, and the
   relevant cross-implementation tests. A changed digest without a reviewed
   manifest update is a release blocker.
5. Commit one coherent canonical spec change. Consumer repositories may link to
   this source or carry a clearly labeled synchronized reference; they MUST NOT
   silently overwrite canonical text through a generic copy script.
6. Bump the Protocol Suite version only through its explicit versioning process.
   A draft profile or fixture update does not by itself ratify a suite release.

## Promotion checklist

- Classify every changed artifact as research, pre-normative, or ratified.
- Link implementation and conformance evidence for registry or normative changes.
- Update schema and fixture digests in the same reviewed change.
- Run both release-integrity and profile-fixture gates in the pull request.
- Record compatibility, deprecation and successor behavior where applicable.
- Ratify only after the required independent implementations pass the pinned
  fixture; otherwise retain the artifact's draft status.

## Boundaries

- Current executable behavior takes precedence over contradictory historical
  prose; record the discrepancy and correction rather than retroactively
  reinterpreting wire behavior.
- Registry entries require implementation evidence and payload/schema review.
- Base-frame changes require an independent compatibility, malformed-input,
  and cross-implementation evidence package. Semantic profiles are preferred.
- Website and implementation-repository documentation are public references,
  not substitutes for this canonical source.
