# IICP-selected A2A execution binding v0

**Status:** Informative, pre-normative interoperability profile  
**Issue:** IICP #60  
**Wire impact:** None

This profile lets an IICP consumer select an eligible provider and then execute
the task directly through A2A. IICP retains intent resolution, eligibility,
policy, provider selection, and route authorization. A2A owns messages, tasks,
streaming, cancellation, and execution errors. No task payload passes through
an IICP directory.

The profile was checked on 12 August 2026 against A2A v1.0 source commit
`0a431950ddd2c698394219eefc2ba32977fe0716` and Auto Agent Protocol v1.2.
AAP is used as a concrete typed-data fixture, not as a required IICP vertical.

## Provider advertisement

An IICP provider that offers A2A execution advertises a versioned binding beside
its existing intent and endpoint information:

- selected IICP node and operator references;
- the exact HTTPS Agent Card URL and SHA-256 digest of the canonical card JSON;
- the exact A2A interface URL, binding, protocol version, and optional tenant;
- an explicit IICP intent-to-A2A skill map;
- the card expiry time and supported optional operations.

The directory treats this as capability metadata. It does not fetch task data,
issue A2A credentials, or assert that the A2A agent is currently healthy. A
provider re-registers when the card digest, interface, skill map, or execution
identity changes.

## Consumer validation

After IICP selection and before sending a task, the consumer:

1. validates the IICP route ticket against its normal issuer, audience, node,
   intent, and expiry rules;
2. fetches the card from the selected HTTPS URL without cross-origin redirects;
3. applies the IICP endpoint-security profile to the card and interface URLs;
4. verifies the exact card digest and rejects expired binding metadata;
5. selects the advertised A2A interface only when its URL, protocol binding,
   protocol version, and tenant match the IICP binding;
6. verifies that the mapped skill and required extensions exist in the card;
7. checks optional A2A capabilities before requesting streaming, push, or
   extended-card behavior;
8. acquires A2A credentials through the security scheme declared by the card.

A signed Agent Card may add origin evidence, but it does not replace the digest
and endpoint binding supplied by the selected IICP record. Card-signature
verification follows A2A rules and the consumer's trust policy.

## Authorization boundary

An IICP route ticket authorizes route disclosure under its IICP audience. It is
not an A2A bearer credential and must not be forwarded in `Authorization`, A2A
message parts, task metadata, or extension parameters.

A2A credentials are obtained separately and scoped to the selected A2A
resource, tenant, and skill where the chosen security scheme permits. A token
whose resource or audience names another interface is rejected before task
submission. In-task credentials also follow A2A's out-of-band guidance; this
binding does not relay or transform them.

## Execution and lifecycle mapping

The consumer sends the selected skill's request using the chosen A2A binding.
The AAP interoperability fixture uses JSON-RPC `SendMessage`, an A2A v1.0
`Message`, and a typed `DataPart` for `dealer.information`.

| A2A result | IICP lifecycle projection |
| --- | --- |
| immediate `Message` | `completed` |
| `TASK_STATE_SUBMITTED` | `accepted` |
| `TASK_STATE_WORKING` | `running` |
| `TASK_STATE_INPUT_REQUIRED` or `TASK_STATE_AUTH_REQUIRED` | `waiting` |
| `TASK_STATE_COMPLETED` | `completed` |
| `TASK_STATE_FAILED` | `failed` |
| `TASK_STATE_CANCELED` | `cancelled` |
| `TASK_STATE_REJECTED` | `rejected` |
| absent or unknown state | fail closed as `invalid_response` |

Streaming is requested only when the card advertises it and the selected
interface supports it. A terminal-only agent remains terminal-only; the adapter
must not simulate incremental output or silently downgrade a request that
requires streaming.

Cancellation maps to A2A `CancelTask` after an A2A task identifier exists. A
local deadline may trigger a cancellation attempt, but a failed or ambiguous
cancellation is recorded as local `expired` with remote state unknown. It must
not be reported as remotely cancelled. Retries reuse the A2A `messageId` only
when the client deliberately requests A2A idempotency; IICP does not assume that
`SendMessage` is universally idempotent.

## Error mapping

Authentication failures remain authentication failures. A2A capability and
version errors map to unsupported-binding failures. `TaskNotFoundError` and
`TaskNotCancelableError` retain their distinct cancellation meanings. Invalid
A2A responses fail closed. Transport failure before a response may enter the
normal IICP candidate fallback policy; partial or acknowledged A2A execution
must not be automatically replayed on another provider.

## Receipt boundary

The client may add a content-free execution projection to its local routing
receipt:

- IICP ticket reference and selected node prefix;
- Agent Card digest and A2A protocol/binding;
- mapped skill identifier;
- hash of the A2A task identifier, when a task exists;
- terminal state, retry/fallback class, and timing metrics.

Receipts must not contain the Agent Card URL, interface URL, credential, message
part, task history, artifact content, prompt, or response. A2A task data remains
with the consumer and A2A server.

## Compatibility and non-goals

This profile is opt-in. Providers without it continue to use their existing
execution surface. A client that does not understand it does not advertise or
select it. Failure of card, interface, skill, audience, or capability validation
does not fall back to an unbound A2A endpoint.

The profile does not make IICP an A2A registry, duplicate the A2A task model,
standardize A2A credentials, move payloads through a directory, require AAP, or
change the IICP base wire protocol.

