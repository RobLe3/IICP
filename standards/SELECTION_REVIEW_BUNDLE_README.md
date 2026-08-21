# Selection and eligibility review bundle

This archive is a bounded project review candidate. It has not been submitted
to a standards body and is not externally ratified.

Read in this order:

1. `standards/SELECTION_ELIGIBILITY_PROBLEM_STATEMENT.md`
2. `standards/SELECTION_TRUST_AND_REVALIDATION.md`
3. `standards/IICP_PROTOCOL_POSITIONING.md`
4. `standards/PROTOCOL_COMPARISON_2026-08-15.md`
5. `IMPLEMENTATIONS.md` and `SPEC_STATUS.md`
6. the capability, directory-state and observability decisions under `docs/`
7. the core, semantics, directory and conformance sources under `spec/v1.9/`

The bundle uses these evidence labels literally:

| Label | Meaning |
|---|---|
| Project-normative | Controlled by the IICP project release process |
| Implemented | Present in a named implementation and version |
| Published | Available as an immutable source/package release |
| Deployed | Observed in an identified running deployment |
| Project conformance | Tested by project-maintained fixtures or tooling |
| Independent evidence | Produced and maintained outside the IICP project |
| Externally standardized | Approved through the named external standards process |

One label never implies another. In particular, same-project PHP/Rust parity is
not independent implementation evidence, and publication does not imply
production deployment.

`michaeloboyle/iicp-node-monitor` is an independently maintained application
that consumes IICP observability interfaces. It is adoption and integration
evidence, not a clean-room directory implementation and not evidence that the
normative protocol independently conforms to itself.

The peer-transport Internet-Draft candidate, generated renderings, native
framing, federation, CUG completion, learned routing, CIP and enterprise
management are not bundled as parts of the narrow selection candidate. Some
source documents mention them to state boundaries or implementation context.
Their presence in a source does not promote them into the candidate.

Verify `SHA256SUMS.json` before review. Rebuild with:

```bash
python3 tools/build_selection_review_bundle.py
```
