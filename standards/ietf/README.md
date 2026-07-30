# IETF draft workspace

This directory contains an individual-draft candidate. It is not an IETF
submission and does not imply IETF or IANA endorsement.

Build locally:

```bash
bundle install --gemfile standards/ietf/Gemfile
python3 -m venv .venv-ietf
.venv-ietf/bin/pip install -r standards/ietf/requirements.txt
PATH=".venv-ietf/bin:$PATH" bundle exec --gemfile standards/ietf/Gemfile \
  tools/build_internet_draft.sh
```

Generated files are written to `build/ietf/` and are not release artifacts
unless the specification release procedure explicitly includes them.
