# Reviewing IICP standards material

## Review target

The current IETF workspace contains an individual Internet-Draft candidate. It
has not been submitted and has no IETF or IANA status. The candidate covers the
peer transport only; directory ranking, credits, federation, cooperative
execution, MCP and deployment-specific NAT traversal are outside its normative
scope.

Start with:

1. [`standards/SELECTION_ELIGIBILITY_PROBLEM_STATEMENT.md`](SELECTION_ELIGIBILITY_PROBLEM_STATEMENT.md)
   for the narrow interoperable function and its explicit exclusions;
2. [`standards/SELECTION_TRUST_AND_REVALIDATION.md`](SELECTION_TRUST_AND_REVALIDATION.md)
   for verifier, freshness, replay and consumer revalidation boundaries;
3. [`standards/IICP_PROTOCOL_POSITIONING.md`](IICP_PROTOCOL_POSITIONING.md)
   for the narrow problem and protocol boundary;
4. [`standards/PROTOCOL_COMPARISON_2026-08-15.md`](PROTOCOL_COMPARISON_2026-08-15.md)
   and [`standards/EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-08-21.md`](EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-08-21.md)
   for current overlap, per-dimension evidence maturity and chronology across
   IAIP, AIDIP, MCP, A2A and related work;
5. `standards/ietf/draft-roble-iicp-peer.md`;
6. `standards/SECURITY_PRIVACY_OPERATIONAL_CONSIDERATIONS_2026-08-13.md`;
7. [`standards/ietf/evidence-matrix.md`](ietf/evidence-matrix.md);
8. [`standards/TRANSPORT_BINDING_AND_PORT_DECISION_2026-08-21.md`](TRANSPORT_BINDING_AND_PORT_DECISION_2026-08-21.md) for supported and unsupported binding evidence;
9. `spec/v1.9/iicp-framing.md` and the pinned native-framing fixtures when a
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

Create the narrow selection-and-eligibility reviewer bundle without building or including the peer-transport draft:

```bash
python3 tools/build_selection_review_bundle.py
```

Read the [adversarial review](SELECTION_CANDIDATE_ADVERSARIAL_REVIEW_2026-08-21.md)
before treating the bundle as ready for review. It records direct overlap,
residual evidence gates and the limits of that disposition.

Create the separate peer-transport review bundle only after a successful Internet-Draft build:

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
