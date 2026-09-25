# Specification documentation truth ledger, 25 September 2026

**Scope:** documentation and comparison, not a new Protocol Suite release or
qualification decision. The clean local checkout and GitHub `main` were
`2d240649cf8d11a235132658a599e22ebcba6620` at baseline. Published
Protocol Suite `v1.10.17` points to tag commit
`156e0260660f382e236ecb12477d785e131ec2d5`; its wire compatibility
baseline is `v1.9.0`. Working `main` has later changes and must not be
retroactively described as the published tag.

The August [documentation audit](specification-documentation-truth-2026-08-11.md)
and its closed [issue #128](https://github.com/RobLe3/IICP/issues/128) are
historical evidence, not an open authorization to rewrite a release. The
generated implementation and version projections derive from
`ecosystem/repositories.json`; their numbers are not copied into this ledger.

| File / section | Existing claim or gap | Class and authority | Correction and acceptance |
|---|---|---|---|
| `README.md` / opening | Fixed suite number beside working-main prose, without clear release boundary. | Confirmed editorial defect; `VERSIONING.md`, generated projection and immutable tag. | Link generated current projection; distinguish tag from main. Projection and integrity checks pass. |
| `VERSIONING.md` / history | Published v1.10.17 called a current candidate; obsolete monorepo source paths presented as current component metadata. | Confirmed editorial defect; release and owning component repositories. | Label published release and use generated/owning sources. No version bump or tag rewrite. |
| `README.md` / quickstart | Historical Phase 1 endpoints and error shape presented as general implementation instructions. | Confirmed scope defect; current Core, DIR, agent bootstrap and binding rules. | Replace with role paths, preserve Phase 1 compatibility link. No current quickstart relies on historical Phase 1 alone. |
| `README.md` / JSON example | Incomplete task sample could be mistaken for a valid wire submission. | Confirmed example-applicability defect; named contracts. | Label conceptual and link executable examples; schema validation applies only to examples named as executable. |
| `README.md` / selection | “Clients may only filter” conflicts with scoped optional selection Profile. | Confirmed contradiction; `iicp-semantics.md` §3.2. | State hard eligibility, default directory order, optional eligible-set ranking and single-route ticket limit. No client widening implied. |
| `README.md` / security | Universal TLS, identifier-regex and error-envelope bullets flatten distinct bindings and exceptions. | Confirmed contradiction; Core §§3, 7–8 and DIR scheme rules. | Refer to binding-specific contracts, provider versus consumer credentials and production/development split. No improvised universal grammar remains. |
| `README.md` / maturity | Undated “Live”, “Ratified”, federation and relay assertions mix publication, deployment and qualification. | Missing current qualification; implementation index, pre-1 baseline and dated live evidence. | Replace status table with bounded evidence links. No stable or independent certification inferred. |
| `README.md` / SDKs and compatibility | “Conformant” and “fully compatible with the live network” exceed cited evidence. | Missing independent qualification; conformance runner and retained results. | Describe maintained reference implementations and scoped claims only. |
| `schemas/task.json` / scope | Schema itself states Phase 1, while README listed it as general `IicpTask`. | Explicit legacy scope; historical Phase 1 schema. | Relabel its index entry; do not widen or reinterpret its validation. Successor schema, if needed, requires separate review. |
| `spec/v1.9/README.md` / index | Path name and Phase 1 reading order can be read as the current full contract. | Confirmed navigation defect; `SPEC_STATUS.md` and role guide. | Explain compatibility lineage, role paths, Profile applicability and historical subset. Preserve path and anchors. |
| `CONTRIBUTING.md` / checks | Two checks alone obscure the required CI validation path and local prerequisites. | Confirmed guidance gap; current workflows and fixture script. | Document isolated dependencies, required `validate` job and manual diagnostic workflow. |
| `SPEC_RELEASE_PROCESS.md` / boundary | “Executable behavior takes precedence” could be read as permitting code to supersede released normative text. | Confirmed wording ambiguity; `SPEC_STATUS.md`. | Clarify that implementation evidence reveals discrepancies but cannot redefine an immutable contract. |
| `docs/agent-bootstrap.md` / dispatch | Fallback text lacked explicit single-route ticket and non-overridable eligibility limits. | Confirmed clarification; selection and trust contracts. | Clarify without changing SDK behavior. |
| `docs/architecture/decision-documentation-map.md` / Management | Optional Management/CUG authority and proposed remote administration lacked a concise navigation boundary. | Informative clarification; pre-1 crosswalk and Management owner. | Link owner; separate local policy enforcement from remote service and future SDI ideas. |
| `standards/PROTOCOL_COMPARISON_2026-08-15.md` / status | Dated rows do not cover later individual drafts, DAWN state or REQ-1–17. | Historical material, not wrong for its date. | Preserve file; create dated successor and mark old machine-readable ratings historical. |
| `standards/protocol-comparison-v1.json` / evidence | No current source-revision inventory or individual requirements mapping. | Confirmed data gap; IETF Datatracker and current IICP contracts. | Add compatible metadata and 17 rows; offline validator rejects omissions and unsupported dispositions. |
| `standards/EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-08-21.md` / principal | Cites principal-binding `-06`, now superseded by `-07`. | Historical material; current Datatracker revision. | Preserve snapshot; dated update records revision and unchanged IICP boundary. |

## Contract discrepancies retained for owning review

The Phase 1 `body.auth.node_token` schema does not represent every later
header-authorized consumer request; this is a scoped legacy contract, not a
reason to remove `auth` from it. Exact-match IICP identifiers do not implement
the Intent Routing draft's aggregated prefix-routing requirements. Optional
selection does not permit substitution under a single-route ticket. These
facts are documented here rather than repaired through an unreviewed schema or
wire change. Existing standards and registry issues (#40, #55, #56 and #58)
remain the appropriate review paths if a genuine interoperability requirement
is later established.

| Topic | Verified disposition |
|---|---|
| Standard/custom intents and `+modifier` | `iicp-semantics.md` §§1.2, 1.5 permits project and `x.<vendor>` forms, but deprecates `+modifier`; unknown modifiers are rejected before dispatch. `schemas/task.json` is too narrow to validate every current form, so it remains Phase 1-scoped. |
| Unknown required extensions | Use the applicable Profile's fail-closed rule; no README alias or universal ignore rule is added. |
| QoS, priority and consensus | Core §3.1 includes `realtime`, task priority and optional consensus that the historical schema omits. This confirms legacy scope rather than permission to widen its schema. |
| Timeout and task identity | Core §3.1 and `task-time-semantics.md` separate provider-attempt `timeout_ms` from caller wait; retries retain `task_id` but use a new attempt `call_id` under the lifecycle rules. No new idempotency semantics are created here. |
| Routing versus execution constraints | Eligibility and ticket route binding are applied before dispatch; provider admission and task constraints remain separate checks. |
| Errors and HTTP resource bounds | Core §§3.2 and 7–8 define binding-specific errors; working-main Core §3.2 supports bounded identity-encoded HTTP task requests/responses. These later working-main rules are not attributed to the older immutable tag. |
| Conditional capabilities | Effective-capability architecture describes the complete serving path. A legacy capability projection does not establish support for every conditional field; no schema widening is made. |

## Verification disposition

The pre-edit checks for generated projections, pre-1 baseline, comparison
dataset, release integrity and public-artifact closure passed. The first full
profile run stopped because the host Python lacked the local conformance
runner. After installing the repository requirements and runner in an isolated
environment, the next run found two new canonical-intent source paths in the
standalone PHP and Rust directory package-execution scripts. Their source
classification was added without changing the registry or the intent's
meaning. The final full profile fixture contract passed, including the
extended comparison and review-bundle tests. The Phase 1 task-schema example
and conceptual README JSON parsed successfully; generated projection,
release-integrity and all-public closure checks passed. Strict prose had one
advisory about README boldface density and no error.

The working-main integrity manifest now pins the reviewed documentation,
comparison, source-classification and validator changes. It is labelled a
working-main review candidate; the published v1.10.17 tag and release assets
were not changed. The pre-1 strict freeze remains **OPEN** with six component
reviews, and no issue closure, PR merge, preparation or same-project parity
result is counted as independent qualification.
