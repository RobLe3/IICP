# IETF draft workspace

This directory contains an individual-draft candidate. It is not an IETF
submission and does not imply IETF or IANA endorsement.

Review scope, evidence boundaries and ambiguity reporting are documented in
[`../REVIEWING.md`](../REVIEWING.md). The informative
[`evidence-matrix.md`](evidence-matrix.md) maps the candidate's requirement
classes to public specification, fixture and implementation evidence.

Build locally:

```bash
bundle install --gemfile standards/ietf/Gemfile
python3 -m venv .venv-ietf
.venv-ietf/bin/pip install -r standards/ietf/requirements.txt
PATH=".venv-ietf/bin:$PATH" bundle exec --gemfile standards/ietf/Gemfile \
  tools/build_internet_draft.sh
```

Generated files are written to `build/ietf/` and are not release artifacts
unless the specification release procedure explicitly includes them. After a
successful build, `python3 tools/build_standards_review_bundle.py` creates a
deterministic, self-contained reviewer archive without submitting the draft.
