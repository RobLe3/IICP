# Contributing to IICP

Start with a public issue that identifies an interoperability problem rather
than a preferred implementation. Specification changes should include schemas,
compatibility behavior and conformance vectors where applicable.

Run the repository checks before proposing a change:

```bash
python3 tools/generate_implementations.py --check
```

Implementation bugs belong in the owning repository listed in
`IMPLEMENTATIONS.md`. Never include production credentials, private topology or
real task data.
