# Shared SDK quality evidence

Python, TypeScript and Rust SDK releases use the same content-free result shape:
`schemas/sdk-quality-evidence-v1.json`. Each result binds the intended version to
an exact commit and records supported-runtime, static-analysis, measured coverage,
dependency-audit, locked-build and clean-install outcomes.

The contract does not impose one copied coverage number on three different code
bases. Each SDK establishes a measured starting ratchet and may raise it. A result
fails when observed coverage is below that SDK's declared minimum, a supported
runtime is absent or failing, or any required gate fails.

The required runtime sets for the current compatibility line are:

| SDK | Required release evidence |
| --- | --- |
| Python | CPython 3.11, 3.12 and 3.13 |
| TypeScript | Node.js 18, 20, 22 and 24 |
| Rust | Rust 1.86 MSRV and current stable |

Expensive matrices remain local or scheduled/manual evidence because the project
uses a permanent free GitHub account. Each repository keeps one small pull-request
gate. A missing evidence file or failed gate stops coordinated publication; it
does not justify adding redundant hosted workflows.
