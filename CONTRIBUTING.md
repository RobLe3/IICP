# Contributing to IICP

Start with a public issue that identifies an interoperability problem rather
than a preferred implementation. Specification changes should include schemas,
compatibility behavior and conformance vectors where applicable.

From the repository root, use an isolated Python environment with the
requirements in `tools/requirements.txt` and the local conformance runner
(`python3 -m pip install './conformance-runner[signing]'`). Run the checks
relevant to the files changed before proposing a pull request:

```bash
python3 tools/generate_implementations.py --check
tools/run_profile_fixture_contract.sh
python3 tools/check_public_prose.py --strict README.md GOVERNANCE.md CONTRIBUTING.md
python3 tools/check_public_artifact_closure.py --all-public
```

`ecosystem.yml` contains the required pull-request `validate` job.
`profile-fixtures.yml` is a manual diagnostic workflow, not an additional
qualification pass. Do not interpret a skipped, unrun or dependency-failed
check as passing evidence. Run locally first to conserve hosted CI minutes.

The prose check blocks objective citation artifacts and reports stylistic or
substance heuristics for human review. It checks writing quality, not whether a
person or a model wrote the text. Do not replace flagged words mechanically;
remove unsupported claims, add the concrete evidence, or keep clear wording
when the warning does not apply in context.

Coordinated releases must update `ecosystem/releases.json` with their wire,
conformance, compatibility, upgrade, migration and rollback semantics. Public
release evidence must be reproducible from component manifests, immutable tags
and public package registries. Private project tooling may run additional
checks, but it is not part of the public acceptance contract.

Implementation bugs belong in the owning repository listed in
`IMPLEMENTATIONS.md`. Never include production credentials, private topology or
real task data.

An implementation result may expose a discrepancy in the specification, but
it cannot silently change released semantics. Record the applicable release,
Profile and binding; propose any interoperable correction with compatibility
behavior and fixtures. Preserve immutable tags and release assets.

## Where to open an issue

- Use this repository for normative protocol semantics, registries,
  conformance, reviewed protocol research and standards work.
- Use the PHP or Rust directory repository for behavior specific to that
  implementation. PHP remains the current Genesis code line; Rust remains an
  operator preview until its separate cutover gates pass.
- Use the owning SDK or browser-node repository for language- or
  runtime-specific defects.
- Use this repository for cross-component interoperability questions that
  cannot be assigned to one implementation. Send private deployment or account
  matters to `community@iicp.network`, without credentials or task content.

When responsibility moves between repositories, create one sanitized canonical
successor, link both issues and close the old issue as moved. Do not transfer a
private issue directly into a public repository: its comments may contain
private operational context. Closing preserves the historical record and does
not mean that the successor work is complete.

## Standards contributions and intellectual property

Specification contributions remain subject to the repository license. Text
prepared for an Internet-Draft may also be submitted under the current IETF
Trust Legal Provisions and IETF Note Well. A contribution does not authorize a
standards submission. Contributors must disclose known intellectual-property
claims that would affect implementation or standardization and must not submit
text they are not entitled to license.

The public record preserves technical evidence, alternatives and decisions.
Private development prompts, orchestration, work-selection systems and
meta-tools are not contribution requirements and must not be copied into this
repository. See
[`docs/governance/public-artifact-boundary.md`](docs/governance/public-artifact-boundary.md).
Independent implementers and successor maintainers should also read
[`CONTINUATION.md`](CONTINUATION.md).
