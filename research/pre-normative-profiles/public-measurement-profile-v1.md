# Public multi-vantage measurement profile v1

**Status:** Implementation-neutral research profile  
**Issue:** IICP #98  
**Wire impact:** None

This profile defines the minimum content-free evidence needed to support public
latency and availability claims. It does not define probe infrastructure,
change provider reputation, or authorize production monitoring.

## Evidence boundary

Each observation describes one probe, one public target class, and one outcome.
It must not contain task payloads, credentials, full endpoint URLs, IP
addresses, node identifiers, or private topology. `vantage_id`, `operator_id`,
and `target_id` are opaque identifiers scoped to the evidence bundle.

An omitted or failed sample remains visible. Producers must record it as an
observation with an outcome such as `timeout`, `transport_error`, or
`invalid_response`; they must not delete it from the requested sample count.
Latency is reported only for successful observations.

## Evidence classes

| Class | Meaning |
| --- | --- |
| `self-observed` | The target operator also controls the only probe operator. |
| `project-observed` | The IICP project controls the probe, whether or not it controls the target. |
| `external-observed` | A separately operated probe reports evidence, but the independence requirements for the stated claim are not met. |
| `independent` | Every contributing operator is separate from the target operator, and the claim-specific operator, region, and network-diversity rules pass. |

The evidence class describes provenance, not correctness. A signed project run
is still project-observed. An external run does not become independent merely
because it ran outside project infrastructure.

## Claim scope

The bundle declares one claim scope and must satisfy its minimum diversity:

| Scope | Minimum evidence |
| --- | --- |
| `single-vantage` | One vantage. The claim is limited to that vantage. |
| `regional` | Three vantages, three operators, and three failure domains in the named region, spanning at least two network classes. |
| `multi-region` | Three vantages, three operators, three regions, and three failure domains, spanning at least two network classes. |
| `network-wide` | Four vantages, three operators, three regions, three failure domains, and three network classes. |

`independent` additionally requires every contributing operator to declare
`target_controlled: false`. An opaque, bundle-scoped failure-domain identifier
prevents three probes on the same underlying infrastructure from being counted
as independent. These thresholds are publication rules for this
research profile, not IICP protocol requirements or statistical proof that the
sample represents the whole Internet.

## Required accounting

The summary must equal the observations:

- `requested_samples` equals the number of observations;
- outcome counts cover every observation exactly once;
- availability is successful observations divided by requested observations;
- latency sample count covers successful observations only;
- latency percentiles are omitted when no request succeeded;
- the observation window contains every sample timestamp.

The producer records its aggregation algorithm. A verifier recomputes counts,
availability, and nearest-rank latency percentiles rather than trusting the
summary.

## Independence and negative cases

The validator rejects:

- a geographic or network-wide claim without the required diversity;
- an `independent` claim containing a target-controlled operator;
- hidden missing samples or inconsistent summary counts;
- latency attached to a failed observation;
- payload, prompt, response, credential, IP-address, URL, or raw node-identity
  fields;
- timestamps outside the declared observation window;
- unbounded free-form result or error material.

An implementation may retain more detailed private diagnostics under its own
policy. Those diagnostics are not part of the public evidence bundle.

## Relationship to operational work

The schema and fixtures are specification-neutral. The private integration
repository may simulate this profile and assess infrastructure cost and
ownership. Deploying probes, publishing live observations, or using results in
selection or reputation requires separate review and authorization.
