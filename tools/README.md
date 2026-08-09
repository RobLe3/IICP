# IICP Tools

Validation and analysis tools for the IICP specification.

| File | Purpose |
|------|---------|
| `protocol_integrity_analysis.py` | Analyses a spec file for internal consistency — checks cross-references, field usage, normative language coverage |
| `quick_validation.py` | Quick syntax + field validation against IICP v1.4.2 message schemas |
| `validation_results_v1.4.2.json` | Archived validation results for v1.4.2 |
| `audit_mcp_official_sdk.py` | Downloads one pinned official MCP TypeScript SDK tarball into a temporary directory and reports its declared wire revisions without changing IICP behavior |

The separately installable preview under `conformance-runner/` exercises a
bounded public-directory profile and emits content-free machine-readable
results. It does not replace the complete conformance environment.

## Usage

```bash
python3 tools/protocol_integrity_analysis.py spec/v1.5/iicp-core.md
python3 tools/quick_validation.py <message.json>
python3 tools/audit_mcp_official_sdk.py
```


The MCP SDK audit is deliberately an evidence check, not an interoperability
claim: it records the protocol revisions declared by the selected published
tarball. Endpoint interoperability and authorization behavior require separate
fixtures and independently operated testing.
