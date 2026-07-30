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

## Where to open an issue

- Use this repository for normative protocol semantics, registries,
  conformance, reviewed protocol research and standards work.
- Use the PHP or Rust directory repository for behavior specific to that
  implementation. PHP remains the current Genesis code line; Rust remains an
  operator preview until its separate cutover gates pass.
- Use the owning SDK or browser-node repository for language- or
  runtime-specific defects.
- Use `iicp.network` for cross-component integration, adoption, governance,
  production evidence and private website or operations work.

When responsibility moves between repositories, create one sanitized canonical
successor, link both issues and close the old issue as moved. Do not transfer a
private issue directly into a public repository: its comments may contain
private operational context. Closing preserves the historical record and does
not mean that the successor work is complete.
