# IICP MCP gateway × CCS external interoperability experiment

- **Experiment date:** 2026-09-28
- **Source review date:** 2026-09-29
- **Classification:** `EXTERNAL_INTEROPERABILITY_EVIDENCE`
- **Disposition:** successful bounded externally reported experiment
- **Pre-1.0 qualification credit:** zero

Correctover reports that an external execution-assurance layer composed with an
unmodified, released IICP MCP gateway. This is useful third-party composition
evidence, not IICP certification, independent Directory implementation evidence,
or a complete intent-to-execution interoperability result. No IICP source change,
Core change or CCS dependency is required by this finding.

## Source and verification boundary

The source is Correctover's findings report, dated 2026-09-28 and supplied to the
IICP maintainer. This note preserves a sanitized account, not the original
correspondence, raw requests, responses or operational records. The report says
that Correctover performed the experiment independently under a boundary of
released IICP surfaces and no IICP-specific changes.

All execution results below are **Correctover-reported**. IICP's September 29
review inspected the report, the released Python gateway source and public
background sources. It did not rerun the experiment or independently verify its
receipts. The harness, raw receipts, signing-key identity, exact checker commit,
artifact digests and complete checker output were not available in the supplied
material. They remain unavailable; current repository HEADs must not be
substituted for the experiment's missing identities. There is no complete public
reproduction bundle or executable reproduction procedure established here.

An independently implemented checker can recompute cryptographic results without
being an unaffiliated operator or an independent IICP implementation. This note
does not close a clean-room, external-participant or qualification gate.

## Tested surface and environment

The selected command was:

```text
iicp-node mcp-gateway --tools format_json,summarize_text
```

The actual installation was the **Python SDK from PyPI**, not Rust. The report
states that a Rust toolchain was unavailable and the released Python entry point
was used instead. These results do not qualify the Rust or TypeScript gateways.

| Component | Reported tested version or boundary |
| --- | --- |
| Python `iicp-client` / `iicp-node` | `0.7.109`; gateway source unmodified |
| `ccs-verifier` | **`1.3.0`**, not the proposal's `1.4.2` |
| Python | `3.13.12`, CPython |
| Environment | Linux x86_64 container; Linux `5.15.0-100-generic`, glibc `2.35` |
| `cryptography` | `46.0.5` |
| `jcs` | `0.2.1` |
| Independent checker | `ccs-conformance-vectors` checker; exact revision unavailable |
| Directory and backend | Local Directory stub and local MCP server |
| Admission path | External pre-admission, gateway tool call, external post-admission, CCS receipt |

The two tools were selected as safe, deterministic operations. The experiment
did not exercise the dangerous-tool authorization/sandbox control bundle.
Correctover's seven dimensions were Structure, Schema, Latency, Cost, Identity,
Integrity and Security; they are the external verifier's checks, not newly
adopted IICP requirements.

The report attributes version drift to `1.4.2` being unavailable from PyPI at
execution time. The actual tested version is retained without treating the
package index's historical availability claim as separately reproduced by IICP.

## Reported results

| Case | Bounded observation | Expected / reported result |
| --- | --- | --- |
| P1 | Valid `format_json` invocation | Allow / allow |
| P2 | Valid `summarize_text` invocation | Allow / allow |
| P3 | Valid Unicode/CJK `summarize_text` invocation | Allow / allow |
| N1 | Malformed response structure | Deny / deny |
| N2 | Missing required argument | Deny / deny |
| N3 | Incorrect argument type | Deny / deny |
| N4 | Argument schema constraint violation | Deny / deny |
| N5 | Identity mismatch | Deny / deny |
| N6 | Argument-byte budget exceeded | Deny / deny |
| N7 | Credential-pattern detection | Deny / deny |
| N8 | End-to-end latency budget exceeded | Deny / deny |
| N9 | Malformed response content | Deny / deny |
| N10 | Mutation of an already signed receipt | Original verifies; modified receipt fails verification |
| N11 | Backend transport failure | Escalate / escalate |

Correctover reports **14/14 expected case outcomes**: three positive and eleven
negative/escalation cases, with no negative case admitted as `allow`.
The argument-byte budget test does not establish actual billing or monetary cost
accuracy. Security checks are bounded test observations, not universal protection.

Separate native gateway probes reportedly returned **HTTP 404** for an
unadvertised tool and **HTTP 401** without authorization. These observations are
distinct from CCS verdict logic and apply to the paths probed, not every possible
gateway refusal or execution binding.

### Checker vocabulary and cryptographic scope

The reported independent-checker result is **415/426 individual checks**. The
eleven remaining checks are attributed to a verdict vocabulary mismatch:

- tested verifier: `allow` / `deny` / `escalate`;
- checker: `allow` / `block`.

The report attributes these eleven checks to vocabulary rather than receipt
signature/hash failures. Do not describe the result as `426/426 conformance`.
An escalation requiring operator action is not automatically equivalent to a
binary refusal. No IICP vocabulary or normalization rule is changed here.

Correctover reports detached Ed25519 signatures over RFC 8785 JCS bytes, SHA-256
content bindings, independently recomputed canonical bytes/hashes/signatures,
and rejection of a post-signing mutation. This supports the **reported**
tamper-evidence result for the tested CCS receipt/key model. It does not establish
who legitimately controlled that key, the truth of every issuer assertion, or
execution of the full IICP chain.

## Existing IICP mechanisms and separate trust responsibilities

The tested Python release resolves locally to commit
`7718dd35904568f3a10777a11ee3a3ffeeeaffab`:

- [`McpToolPolicy.receipt`](https://github.com/RobLe3/iicp-client-python/blob/7718dd35904568f3a10777a11ee3a3ffeeeaffab/src/iicp_client/mcp_policy.py)
  emits unsigned metadata including tool risk, decision, policy/sandbox labels,
  redaction status, argument count and `argument_content: "excluded"`.
- The [gateway response](https://github.com/RobLe3/iicp-client-python/blob/7718dd35904568f3a10777a11ee3a3ffeeeaffab/src/iicp_client/cli.py)
  places `task_id` beside the successful result and policy receipt. This is
  existing correlation, not detached-signed authorization or execution evidence.
- The [MCP binding](../spec/v1.9/iicp-mcp-binding.md) distinguishes IICP task
  correlation from MCP credentials and excludes downstream credentials, session
  identifiers and raw tool arguments from receipts/audit records.
- The [route-ticket and receipt proposal](../research/pre-normative-profiles/route-ticket-and-receipt-profile.md)
  already separates Directory, client and node evidence. A v1 ticket authorizes
  **route disclosure only**, not node admission or proof of execution. The
  [optional v2 trust proposal](../research/pre-normative-profiles/dispatch-ticket-trust-profile-v2.md)
  remains separately scoped; this experiment does not promote either profile.
- Existing [session/principal/receipt crosswalks](../standards/EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-09-25.md)
  and [IICP #63](https://github.com/RobLe3/IICP/issues/63) distinguish identity,
  authority and evidence assertions. [IICP #54](https://github.com/RobLe3/IICP/issues/54)
  records the layered protocol approach. Their completed work is reused, not
  reopened or treated as approval of CCS.

The report's broad statement that both receipt models were detached-signed
conflicts with its own unsigned-policy-receipt finding and the released source.
This note does not carry that statement forward. The present MCP policy receipt
must not be called cryptographically non-repudiable evidence.

At the architectural level, IICP routing/policy evidence and external invocation
evidence answer adjacent questions. Neither substitutes for the other's verifier
or authority. In this experiment, the policy receipt alone did not prove a real
Directory selection or route-ticket authorization.

An external receipt could later reference an earlier immutable task, ticket or
binding artifact. A possible later completion/provenance artifact could reference
the external receipt digest. Those are review questions, not new wire fields:
avoid cyclic signing and requiring an original ticket to reference a future
receipt. Existing `task_id` correlation does not settle immutable binding or
attempt identity for every future assurance use case.

### Privacy, licensing and measurement boundaries

IICP excludes tool arguments and execution content from the policy receipt; the
reported CCS receipts use digests rather than embedding complete payloads. This
is content-minimization alignment, not identical privacy models or evidence that
the verifier never sees arguments/results. Digests can retain correlation or
guessability risks; evidence purpose, issuer and disclosure limits remain explicit.

The [public vectors repository's license scope](https://github.com/DSHCorrectover/ccs-conformance-vectors#license-scope)
identifies CC0 vectors and an MIT checker. The separately distributed
[`ccs-verifier` 1.3.0 package](https://pypi.org/project/ccs-verifier/1.3.0/)
declares Elastic License 2.0; IICP is Apache-2.0. No verifier source, checker or
vectors are imported, installed as an IICP dependency or vendored by this task.
ELv2 implementation code must not be copied into IICP under this task. Any later
third-party source/vector reuse needs explicit, component-specific licensing review.

The report distinguishes Python canonicalization/sign/verify, security-rule work
and the full local gateway/tool round trip. These boundaries and languages are
not interchangeable. Its numerical measurements are not adopted as IICP
performance claims, routing budgets or qualification thresholds.

CCS background is an [individual Internet-Draft](https://datatracker.ietf.org/doc/draft-correctover-ccs/09/),
not an RFC, adopted IICP contract or IETF endorsement. Revision `09` is a
September 29 background reference; the experiment did not provide an exact
draft-revision pin, and this note does not invent one.

## Durable disposition map

| Insight | Disposition | Owner / record | Revisit trigger |
| --- | --- | --- | --- |
| External execution-assurance composition | DOCUMENTED; TRACKED_AS_ISSUE; DEFERRED | [IICP #256](https://github.com/RobLe3/IICP/issues/256) and this note | Concrete relying-party need after pre-1.0 qualification |
| Route/policy versus invocation evidence | COVERED_BY_EXISTING_ARCHITECTURE; DOCUMENTED | MCP binding; ticket/receipt proposals; [IICP #190](https://github.com/RobLe3/IICP/issues/190) | Demonstrated gap, not shared cryptographic vocabulary |
| Authorization-artifact correlation | TRACKED_AS_ISSUE; DEFERRED | IICP #256 | Review immutable identity, verifier and causal scope |
| Possible later completion/provenance artifact | TRACKED_AS_ISSUE; DEFERRED | IICP #256 | Justified reverse-link need; no cyclic signing |
| Policy-receipt trust scope and unsigned status | TRACKED_AS_ISSUE; DEFERRED | [Python SDK #142](https://github.com/RobLe3/iicp-client-python/issues/142) | Accepted trust-model review after qualification |
| Signing policy receipts merely by analogy | REJECTED_AS_UNNECESSARY | Python SDK #142 | Only a separately justified trust requirement could reopen signing design |
| Verifier/checker verdict mismatch | DOCUMENTED; no IICP terminology change | This note, checker-boundary section | External version-pinned checker evidence; generic semantics only if later needed |
| Proposed `1.4.2` versus tested `1.3.0` | DOCUMENTED; no IICP defect | This note, environment section | A future external experiment must pin actual artifacts |
| Independent receipt recomputation and tamper rejection | DOCUMENTED as externally reported | This note, cryptographic-scope section | Public raw bundle and pinned verifier/checker/key identities for reproduction |
| Content-minimization alignment and limits | DOCUMENTED; COVERED_BY_EXISTING_ARCHITECTURE | MCP binding; IICP #256 | Future composition review must preserve disclosure boundaries |
| Latency calibers and language differences | DOCUMENTED; no imported performance claim | This note, measurement-boundary section | Any later evidence must declare exact measurement scope |
| CC0/MIT/ELv2/Apache-2.0 boundaries | DOCUMENTED; dependency/import rejected for this task | This note, licensing section | Explicit licensing review before any later reuse |
| Generic assurance Profile or evidence reference | TRACKED_AS_ISSUE; DEFERRED | IICP #256 | Compare entirely external, binding-local, optional Profile and no-change designs |
| Full intent-to-execution/evidence-chain experiment | TRACKED_AS_ISSUE; DEFERRED | IICP #256 | After qualification plus a separately reviewed test proposal; not scheduled |
| Future Software Defined Intelligence relevance | TRACKED_AS_ISSUE; DEFERRED | IICP #256; [architecture map](../docs/architecture/decision-documentation-map.md) | Independently justified post-qualification research, not a released Core capability |
| CCS dependency, Core redesign or qualification expansion | REJECTED_AS_UNNECESSARY | This note and both new issues | Not authorized by this evidence record |

The specification owns generic cross-binding questions; the Python SDK owns the
gateway implementation tested here. Related Rust/TypeScript receipt behavior is
a future parity concern only if a shared semantic requirement is independently
accepted. No duplicate SDK, Management or SDI implementation issue is created.

## What remains untested and unchanged

The complete consumer intent -> real Directory discovery -> capability,
eligibility/policy and selection -> real dispatch ticket -> execution binding ->
invocation -> external attestation chain was **not tested**. A future experiment
must distinguish route-disclosure verification from any separately authorized
node-admission mechanism and keep assurance providers independently selectable.

The active pre-1.0 candidate, support matrix, source bindings, sentinels,
qualification scope and credit remain unchanged. This note neither delays nor
adds requirements to Directory closure, Linux/Windows staging, successor
freeze/rebind or the existing campaign. No full-chain experiment is scheduled,
no assurance schema or SDI feature is implemented, and no release, production,
deployment, standards submission or live Directory authority changes occur.
