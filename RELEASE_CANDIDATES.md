# Release-candidate evidence

IICP coordinated releases use a local-first candidate stage before any tag or
registry publication. A candidate is evidence about exact commits. It is not a
release, deployment or adoption claim.

The machine-readable result uses
`schemas/release-candidate-evidence-v1.json`. It records only repository names,
commit hashes, intended versions, named gate outcomes and artifact digests. It
must not contain credentials, command output, local paths or runtime payloads.

For an ordinary coordinated release, the candidate lane must:

1. reject dirty worktrees and commits that do not match the reviewed plan;
2. run version-truth, fixture-integrity, manifest and clean-install gates;
3. build deterministic artifacts twice from separate detached checkouts where
   that component promises reproducibility;
4. leave the review checkpoint pending until a human approves the evidence;
5. publish only from the exact approved commits; and
6. refuse to replace an existing tag or registry version.

Urgent security or interoperability corrections may omit a time-based soak.
They may not omit integrity checks, clean-install checks or the exact-commit
binding. Rollback selects an earlier immutable release; it never rewrites a tag.

Candidate, published, deployed and adopted states remain separate. Passing this
profile authorizes only the next release decision.
