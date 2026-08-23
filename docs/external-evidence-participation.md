# External evidence participation lanes

IICP has reached the point where several important issues cannot be completed
by adding another project-owned fixture. They require a person, implementation
or environment outside the maintained repository family. This page gives each
participant a fixed starting point and states exactly what a result can prove.

Participation is voluntary. Do not include credentials, prompts, responses,
private topology, raw node identifiers, private addresses or personal data.
Signing a result proves who controlled its signing key; it does not make the
result independent.

The machine-readable campaign index is
[`external-participation-campaign-v1.json`](../evidence/external-participation-campaign-v1.json).
It fixes the participant class, artifact versions, record, validation command
and submission path for the five public protocol and implementation lanes. Every repository-owned state is
`awaiting-participant`; the project does not infer acceptance, consent, a
result or a decision. Validate the index with:

```bash
python3 tools/check_external_participation_campaign.py
```

## Choose one lane

| Lane | Tracker | Who is needed | Starting artifact | Completion evidence |
| --- | --- | --- | --- | --- |
| Clean-room directory | IICP #31 | An implementation team outside the IICP repository family | Protocol Suite `v1.10.13`, `iicp-conformance` `0.3.0`, the clean-room guide and the blank evidence record | External repository, ambiguity log, compatibility matrix, and signed content-free results |
| Newcomer usability | IICP #94 | At least one non-technical reader, one developer, and one prospective node operator | The script below and the published website/operator guide | Three consented, anonymized session records and a findings summary |
| Linux watchdog | Rust SDK #66 | A representative Linux/systemd operator, preferably including ARM | Rust SDK `0.7.108` and its opt-in native watchdog | Slow-start, pressure, reboot/logout, linger, restart, and rollback record |
| Relay eligibility | IICP #59 | An independent relay operator and topology measurement environment | Current pre-normative relay research | Stale, forged, replayed, overloaded and partial-evidence cases without topology leakage |
| Standards governance | IICP #47 | A consenting lead editor, backup editor, and change controller | The current draft candidate and governance decision contract | A non-sensitive governance decision with named stewardship roles |

Website and operator legal review is managed separately because its source
packet is not a protocol or implementation dependency. The standards-governance lane starts from
[`submission-governance-decision-v1.json`](../standards/submission-governance-decision-v1.json)
and requires a consenting backup editor before IICP #47 can close. That lane
does not authorize a deployment, publication or standards submission.

Two related paths are documented below but are not campaign intake lanes.
Public evidence access is a repeatable availability check for the evidence
endpoint and repository fallback; issue #97 already established the project
baseline. Confidential execution still needs a confidential-hardware operator
and external security reviewer, but its intake artifact must follow the
pre-normative profile work in #136 rather than implying that a hardware result
already exists.

The standards-gate issues #55, #56 and #58 consume suitable independent
evidence from these or later lanes. They are decision gates, not invitations to
declare a profile normative after one passing run.

## Lane 1: Clean-room directory

Follow the [clean-room implementation guide](../conformance-runner/CLEAN_ROOM_IMPLEMENTATION.md)
and [external runner guide](../conformance-runner/EXTERNAL_RUN.md). Reserve a
language or runtime on IICP #31 before starting. Questions that the pinned
public contracts cannot answer belong in the ambiguity log. Do not resolve
them by inspecting the PHP or Rust directory source.

The external team owns publication. An IICP maintainer may later verify the
bundle, but a project rerun remains `project-verified`, not `independent`.
The machine-readable intake record is
[`clean-room-interoperability-record-v1.json`](../evidence/clean-room-interoperability-record-v1.json).
Copy and complete it in the external repository, then run:

```bash
python3 tools/check_clean_room_interoperability_record.py <external-record.json>
```

## Lane 2: Newcomer usability

Use three participants who have not relied on maintainer guidance. One person
may cover only one role.

### Session script

1. Obtain informed consent for a content-minimized observation.
2. Record only the participant role, device class, input method and UTC date.
3. Ask: “In one sentence, what does IICP do, and where does the task payload
   go?” Do not correct the answer yet.
4. Ask the participant to find the quickest relevant path:
   - non-technical reader: current status, privacy boundary and beta caveat;
   - developer: install a client and locate discovery/call guidance;
   - node operator: locate the version-pinned install, health, recovery,
     rollback and removal path.
5. Test the same path using keyboard navigation. On a mobile-capable device,
   test one narrow viewport as well.
6. Give one realistic failure:
   - a discovery result is empty;
   - the node is live but not ready;
   - an update check reports a newer release;
   - a machine-readable evidence endpoint returns `429` or `503`.
7. Ask the participant to explain the next safe action without revealing
   credentials or task content.
8. Record whether each outcome passed, required a hint or failed. Record the
   first blocking phrase or control, not a full interaction transcript.
9. Remove personal data and let the participant review the retained summary.

Use the machine-readable template in
[`newcomer-validation-record-v1.json`](../evidence/newcomer-validation-record-v1.json).
The template is a blank record, not a project-generated result.

### Required summary

Publish aggregate counts by role, the most frequent misconception, the first
blocking step, prioritized corrections and links to resulting issues. Do not
publish names, contact details, raw recordings, prompts, responses, IP
addresses, credentials or full free-text transcripts.

## Complementary check: Public evidence access

Start at `https://iicp.network/.well-known/iicp-evidence.json`. For each
declared artifact, issue ordinary `GET` and `HEAD` requests and record:

- status;
- media type;
- cache and `Retry-After` behavior when present;
- whether an HTML challenge was returned;
- whether the repository fallback validated;
- whether a live-only fact was correctly reported unavailable instead of
  inferred from static source.

Use the validator in report-only live mode:

```bash
python3 tools/check_public_evidence_access.py --live
```

This probe changes no remote state. A pass is current retrieval evidence, not
permission to weaken edge protection. A `403`, HTML challenge, wrong media
type or misleading `200` becomes an exact diagnostic for IICP #97 and the
separately authorized private operations issue.

## Lane 3: Linux watchdog

Follow Rust SDK #66 and the runtime-supervision evidence request. Keep native
watchdog support opt-in. Exercise the real service manager rather than only a
rendered unit. Record slow startup, high CPU or long inference, memory
pressure, reboot/logout, user-service linger behavior, runtime stall recovery
and rollback. Keep directory or Internet loss separate from local runtime
death.

A representative run may justify either outcome: retain opt-in behavior, or
propose default enablement with a measured timeout and rollback. It must not be
used to guess the cause of the historical Raspberry Pi incident.

## Lane 4: Relay eligibility

Relay eligibility needs an environment the project does not currently control.
Prospective operators should comment on IICP #59 before collecting data. Do not
publish relay topology or stable hardware identifiers.

Relay operators can start from the blank machine-readable record in
[`relay-eligibility-record-v1.json`](../evidence/relay-eligibility-record-v1.json).
It fixes the required negative cases and privacy boundary without prescribing
the operator's topology. Validate a copy before publication:

```bash
python3 tools/check_relay_eligibility_record.py <external-record.json>
```

The blank template is preparation, not relay evidence. A completed result is
independent only when the outside operator controls the environment, publishes
the signed bundle and retains every fail-closed case.

## Complementary research: Confidential execution

Confidential execution also needs an environment the project does not control,
but it is not a campaign intake lane yet. Prospective hardware operators and
security reviewers should coordinate on IICP #136. Valid evidence must prove
private-key containment and the complete plaintext boundary; a software-only
quote or a TEE decryption proxy feeding a host backend is insufficient.

## Evidence classification

**Self-attested** means the participant ran the released tool and publishes
the result.

**Project-verified** means the IICP project reran or reviewed the result under
documented conditions.

**Independent** means an outside party controls the implementation or
environment and publishes its own result.

These classes describe provenance, not quality. Every result still needs its
artifact versions, scope, negative cases, limitations and privacy review.
