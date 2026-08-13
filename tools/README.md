# IICP Tools

Validation and analysis tools for the IICP specification.

| File | Purpose |
|------|---------|
| `protocol_integrity_analysis.py` | Analyses a spec file for internal consistency — checks cross-references, field usage, normative language coverage |
| `quick_validation.py` | Quick syntax + field validation against IICP v1.4.2 message schemas |
| `validation_results_v1.4.2.json` | Archived validation results for v1.4.2 |
| `audit_mcp_official_sdk.py` | Downloads one pinned official MCP TypeScript SDK tarball into a temporary directory and reports its declared wire revisions without changing IICP behavior |
| `test_mcp_legacy_official_endpoint.py` | Starts a temporary official MCP SDK loopback server and verifies the reviewed legacy initialization and safe tool-call path |
| `test_mcp_gateway_official_processes.py` | Runs the actual Python, TypeScript and Rust gateways against the pinned official legacy MCP endpoint; local project verification only |
| `check_context_event_ownership.py` | Validates unique bounded-context ownership, the closed federated event set, transition ownership, and the non-authoritative `service_id` boundary |
| `check_public_evidence_access.py` | Validates the public machine-evidence inventory, static fallbacks, live-state honesty, HTTP behavior and privacy exclusions |
| `check_relay_eligibility_record.py` | Validates the blank or externally completed relay-eligibility evidence record without exposing topology or payloads |
| `check_external_participation_campaign.py` | Validates the six-lane public participation index without inferring participant identity, consent, results or decisions |
| `test_provider_admission_capacity_fixture.py` | Validates bounded provider capacity, freshness, deadline, backpressure and redaction vectors |
| `test_managed_operator_fixture.py` | Validates convenience compatibility and fail-closed managed-operation vectors |

The separately installable preview under `conformance-runner/` exercises a
bounded public-directory profile and emits content-free machine-readable
results. It does not replace the complete conformance environment.

## Usage

```bash
python3 tools/protocol_integrity_analysis.py spec/v1.5/iicp-core.md
python3 tools/quick_validation.py <message.json>
python3 tools/audit_mcp_official_sdk.py
python3 tools/test_mcp_legacy_official_endpoint.py
python3 tools/test_mcp_gateway_official_processes.py
python3 tools/check_context_event_ownership.py
python3 tools/check_public_evidence_access.py
python3 tools/check_relay_eligibility_record.py
python3 tools/check_external_participation_campaign.py
python3 tools/test_provider_admission_capacity_fixture.py
python3 tools/test_managed_operator_fixture.py
```


The MCP SDK audit and local endpoint probes are deliberately project evidence,
not independent-interoperability claims. They record the reviewed behavior of
one pinned published SDK and the actual IICP gateway processes. Independent
interoperability and authorization certification require separately operated
testing.
