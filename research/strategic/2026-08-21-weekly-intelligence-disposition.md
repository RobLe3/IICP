# Weekly intelligence briefing disposition — 21 August 2026

**Reviewed:** 21 August 2026  
**Scope:** claims and recommendations in the 15–21 August intelligence briefing  
**Evidence rule:** repository and primary standards sources take precedence over the briefing. Individual Internet-Drafts are proposals, not IETF consensus or endorsement.

## Decision summary

The briefing's central architectural assessment is applicable: recent drafts reinforce a layered model in which discovery and eligibility precede endpoint authentication, sessions and execution, while identity, membership, delegated authority and evidence retain different verifiers and freshness rules. This supports IICP's current direction; it does not validate IICP as a standard.

Three follow-ups are justified:

1. refresh the standards crosswalk without adopting any draft (#190);
2. model current-state federation scale before changing the protocol (#191);
3. publish the `outcome-v2` incident as bounded implementation experience (#192).

The external-interoperability priority already belongs to #31. The next admissible evidence there is an outside implementation, not another project-controlled directory. No new implementation issue was created for SCITT, AIP, Web Bot Auth, DID Resolution or mocks because the briefing does not yet demonstrate an IICP implementation gap.

## Claim check

| Briefing claim | Disposition | Evidence and correction |
| --- | --- | --- |
| Published lines are protocol 1.10.16, PHP 1.10.93, Rust directory 0.1.14, SDKs 0.7.106 and browser node 0.2.5. | **Confirmed, with axis correction** | `ecosystem/current-versions.json` records these published versions. Published PHP 1.10.93 is not the deployed Genesis version. The live deployment projection still records Genesis 1.10.90. |
| `outcome-v2` corrects slow-success reputation penalties and retry-unsafe metric delivery. | **Confirmed in released source; live cutover incomplete** | IICP #182 and the 1.10.16 fixtures record the semantic correction. SDK retry evidence is merged. Genesis remains on PHP 1.10.90, so live outcome-v2 acceptance remains open. |
| The standalone external runner exists and the bottleneck is independent participation. | **Confirmed** | `iicp-conformance` 0.3.0 is published and #62 is closed. #31 excludes project-controlled implementations from satisfying the independent evidence class. “Participation problem” is a planning assessment, not a protocol fact. |
| Session Requirements `-02` treats sessions as orthogonal to discovery and intent routing. | **Confirmed** | [`draft-feng-agentproto-session-requirements-02`](https://datatracker.ietf.org/doc/draft-feng-agentproto-session-requirements/) says peers may be located through intent routing or directory discovery and places those functions outside its scope. |
| DRISAC `-01` proposes hierarchical capability classification and distributed management/access servers. | **Confirmed** | [`draft-wang-dmsc-drisac-01`](https://datatracker.ietf.org/doc/draft-wang-dmsc-drisac/) describes hierarchical capability representation, aggregation, synchronization and forwarding. Whether that architecture is suitable for IICP is unresolved. |
| Principal Binding `-06` separates authority, instance identity, resource identity, delegation, session continuity and action evidence. | **Confirmed** | [`draft-bu-agentproto-security-principal-binding-06`](https://datatracker.ietf.org/doc/draft-bu-agentproto-security-principal-binding/) defines separate claim rows and warns against treating one carrier as proof of another concern. |
| The SCITT action-receipt profile offers reusable evidence machinery. | **Eligible for crosswalk, not implementation** | Current [`draft-noa-scitt-ai-agent-receipt-01`](https://datatracker.ietf.org/doc/draft-noa-scitt-ai-agent-receipt/) is dated 15 August. It supports signed records and SCITT registration but explicitly limits what the record proves and notes that registration alone does not give an offline holder non-equivocation. |
| Web Bot Auth `-02` is a candidate HTTP authentication building block. | **Eligible for HTTP-binding assessment** | [`draft-meunier-webbotauth-httpsig-protocol-02`](https://datatracker.ietf.org/doc/draft-meunier-webbotauth-httpsig-protocol/) defines `Signature-Agent`, HTTP Message Signatures, key discovery and test vectors. The Datatracker revision timestamp is 19 August, not 18 August as stated in the briefing. |
| AIP `-01` overlaps IICP task authority and delegation. | **Eligible for crosswalk** | [`draft-prakash-aip-01`](https://datatracker.ietf.org/doc/draft-prakash-aip/) proposes invocation-bound capability tokens and attenuated delegation. That does not establish that IICP should replace purpose-specific membership, dispatch and receipt artifacts with one token. |
| `agentproto` is a BOF without a chartered working group. | **Confirmed** | The [Datatracker group page](https://datatracker.ietf.org/wg/agentproto/about/) labels the group BOF and states “Not chartered yet.” |
| DID Resolution is a Candidate Recommendation seeking implementation experience. | **Confirmed; action conditional** | [DID Resolution v1.0](https://www.w3.org/TR/did-resolution-1.0/) is a Candidate Recommendation Snapshot dated 6 August and asks for implementation experience. IICP should contribute only if it has a reproducible DID-resolution result or ambiguity. |
| The website still exposes protocol 1.10.13. | **Disproved as current state** | Website release `2026.08.21-v1.9.253` now publishes the three-axis ecosystem projection. Its artifact digest matches the live file, which reports published protocol 1.10.16 separately from deployed Genesis PHP 1.10.90 and observed SDK adoption. |
| No independent IICP result or third-party review appeared in the search window. | **Search-limited assessment** | No qualifying evidence is recorded by the project's external-evidence ledger. Absence across the public web cannot be proved exhaustively; do not label this claim “Confirmed.” |

## Recommendation disposition

| Briefing recommendation | Action | Owner |
| --- | --- | --- |
| Shift independent evidence from more internal tooling to outside participation. | **Update existing** | #31 retains the fixed clean-room boundary. Outreach must be an invitation, not manufactured independence. |
| Publish the reputation incident as implementation experience. | **New issue justified** | #192. It must preserve evidence limits and cannot close #182's live gate. |
| Add Session Requirements `-02` to the crosswalk. | **New consolidated issue justified** | #190. |
| Model Internet-scale state before changing federation. | **New issue justified** | #191. |
| Crosswalk DRISAC. | **Consolidated** | #191, rather than a duplicate DRISAC issue. |
| Evaluate SCITT receipts. | **Research first** | #190. No implementation issue until the mapping shows a gap and a stable benefit. |
| Crosswalk AIP and Principal Binding. | **Research first** | #190, coordinated with #53 and #58. |
| Evaluate Web Bot Auth. | **Research first** | #190, HTTP binding only. |
| Send no generic second IETF mail. | **No change** | #48 already requires attributable guidance or concrete requested evidence and separate authorization. |
| Update website version truth. | **Already delivered** | `iicp.network` #946, #950 and #952 are closed; website 1.9.253 is live. |
| Participate in DID Resolution testing. | **Conditional, no issue** | Open work only when a maintained IICP implementation can produce relevant test evidence or an ambiguity report. |
| Create an IICP mock package. | **Deferred intentionally** | Useful developer tooling, but it ranks below outside interoperability and current security/federation evidence. Reassess after external participation begins or an adopter reports a concrete testing barrier. |

## Goal impact

### Short term

- Complete live `outcome-v2` validation only after a separately authorized Genesis upgrade; do not use website deployment as a substitute.
- Finish restricted-domain lifecycle and black-box isolation already tracked by #53 and downstream issues.
- Make #31 easier for an external implementer to reserve and execute, without building another maintained implementation.
- Complete #190 as documentation/research; it must not delay current security work.

### Mid term

- Use #191 to decide whether federation needs summaries, sharding, hierarchy, a hybrid or no protocol change.
- Use #190 to determine whether SCITT, Web Bot Auth or AIP merit additive mappings. Keep endpoint authentication and authorization downstream of discovery/selection.
- Treat independently operated federation and clean-room interoperability as evidence gates, not feature checkboxes.

### Long term

- Keep IICP focused on policy-aware intent resolution, eligibility, selection and bounded route authority across heterogeneous execution protocols.
- Reuse mature standards where they provide an interoperable mechanism; do not expand IICP into a universal session, identity, HTTP-authentication or transparency protocol.
- Preserve multidimensional evidence. Reliability, latency, reachability, semantic quality, integrity and provenance must remain independently inspectable even when a local selector combines them.

## Issue harmonization

- **#31:** external clean-room interoperability; no replacement issue.
- **#40:** standards-readiness umbrella; #190 and #191 feed it but do not authorize outreach.
- **#48:** response intake and any later mailing-list follow-up; unchanged authorization boundary.
- **#53:** restricted-domain membership remains distinct from identity, dispatch authority and receipts; #190 is advisory, not blocking.
- **#58:** route tickets and receipts remain purpose-specific; SCITT/AIP mapping belongs in #190 first.
- **#102 in `iicp.network`:** operated federation evidence; #191 owns the scale-model decision and does not authorize deployment.
- **#182:** live outcome-v2 acceptance; #192 owns the reusable implementation note and does not delay or substitute for live evidence.

No issue was opened for a mock package, DID participation, a SCITT adapter, an AIP adapter or Web Bot Auth implementation. Those would be premature without the crosswalk or adopter evidence.
