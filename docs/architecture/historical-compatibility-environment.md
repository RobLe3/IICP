# Historical compatibility environments

**Status:** pre-normative release-evidence design  
**Related:** IICP #55, #160, #161 and #215

An IICP compatibility environment records which immutable semantic artifacts
belonged to one coordinated protocol release. It is an index over existing
release evidence, not another copy of the specification and not proof that
every implementation supports every optional Profile.

The v1 catalog binds the protocol release, registry generation, schemas,
Profiles, Bindings, identity and security profiles, compatibility fixtures,
lifecycle relationships and implementation-specific support projections.
Every referenced artifact is immutable within the release and carries a
SHA-256 digest. The catalog itself is covered by the existing release-integrity
manifest and release checksum.

The v1 `protocol_release.commit` value is the reviewed source-evidence cutoff
from which the catalog was assembled. It cannot be the commit that contains the
catalog itself without creating a self-reference. The
`protocol_release.immutable_reference`, release-integrity manifest and published
archive checksum bind the finished catalog to its released tree. Consumers must
not treat the evidence-cutoff commit alone as the complete release identity.

## Authority clarification

HTTP and HTTPS requirements in the connected-network specifications define the
current HTTP Binding and directory API. They do not define intent, capability,
identity, eligibility or task semantics. Native framing is another Binding.
A future Binding can carry the same logical semantics without redefining Core.

`capabilities[].models`, `capabilities[].max_tokens` and related model or token
metadata are conditional intent, capability or Profile projections. Historical
connected implementations may require those fields. A provider that does not
use models or tokens must not fabricate them merely to express an intelligence
capability.

## Extension criticality

Unknown data is not automatically safe to ignore. Receivers apply four semantic
classes through existing Profile requirements, negotiation, schemas and registry
metadata:

- `OPTIONAL_IGNORABLE` may be retained or ignored only when every required
  semantic, policy and security constraint remains satisfied.
- `OPTIONAL_NEGOTIABLE` applies only after peers select a common supported
  subset.
- `REQUIRED_UNDERSTOOD` rejects before execution when unknown or unsupported.
- `REQUIRED_SECURITY_CRITICAL` fails closed before dispatch when unknown,
  unsupported or prohibited and cannot be silently downgraded.

The sender must express required behavior through a registered required Profile
or another already defined requirement mechanism. Field novelty alone does not
determine criticality.

## Temporal compatibility boundary

Future implementations carry the burden of interpreting released historical
semantics. A historical implementation only follows the compatibility rules
published for its generation. Understanding a historical mechanism does not
require trusting or authorizing it under current policy.

This design improves reconstruction evidence. It does not prove that a future
implementation will interoperate across decades, authorize obsolete security,
or execute against every historical node.
