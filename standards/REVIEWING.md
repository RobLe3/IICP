# Reviewing IICP standards material

## Review target

The current IETF workspace contains an individual Internet-Draft candidate. It
has not been submitted and has no IETF or IANA status. The candidate covers the
peer transport only; directory ranking, credits, federation, cooperative
execution, MCP and deployment-specific NAT traversal are outside its normative
scope.

Start with:

1. [`standards/IICP_PROTOCOL_POSITIONING.md`](IICP_PROTOCOL_POSITIONING.md)
   for the narrow problem and protocol boundary;
2. [`standards/PROTOCOL_COMPARISON_2026-08-15.md`](PROTOCOL_COMPARISON_2026-08-15.md)
   for current overlap with IAIP, AIDIP, MCP, A2A and related work;
3. `standards/ietf/draft-roble-iicp-peer.md`;
4. `standards/SECURITY_PRIVACY_OPERATIONAL_CONSIDERATIONS_2026-08-13.md`;
5. [`standards/ietf/evidence-matrix.md`](ietf/evidence-matrix.md);
6. `spec/v1.9/iicp-framing.md` and the pinned native-framing fixtures when a
   requirement needs implementation context.

Implementations are evidence, not normative authority. A disagreement between
the candidate and a maintained implementation is a review finding, not an
automatic change to the specification.

## Reproducible build

Use the pinned Ruby and Python dependencies:

```bash
bundle install --gemfile standards/ietf/Gemfile
python3 -m venv .venv-ietf
.venv-ietf/bin/pip install -r standards/ietf/requirements.txt
PATH=".venv-ietf/bin:$PATH" bundle exec --gemfile standards/ietf/Gemfile \
  tools/build_internet_draft.sh
```

The build writes XML, plain text and HTML to `build/ietf/`. It also verifies
that the candidate makes no IANA request and does not call port 9484 assigned.

Create a deterministic review bundle after a successful build:

```bash
python3 tools/build_standards_review_bundle.py
```

The bundle contains the source, rendered formats, evidence matrix, public
security and governance context, and a digest manifest. Building it does not
submit the draft.

## Reporting a finding

Open a public issue in `RobLe3/IICP` using the protocol-proposal or
documentation template. Include:

- the draft section and exact text;
- the competing interpretation;
- the interoperability, security or operational consequence;
- relevant public specification, implementation or test evidence;
- whether the proposed correction is normative or editorial.

Do not use private implementation history to resolve an ambiguity. Record the
ambiguity so that the public source can be corrected.

Security vulnerabilities should follow `SECURITY.md` rather than a public
issue. Do not include credentials, task content, private topology or personal
data in review evidence.

## Status and authority

Building or reviewing the candidate does not authorize an Internet-Draft
upload, mailing-list post, IANA request, protocol release or deployment. Those
actions require their separately recorded governance decisions.
