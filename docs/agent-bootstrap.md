# Connect an AI agent to IICP

IICP helps one agent find a suitable provider. It does not define the agent's
reasoning loop, tool model or task language. The directory handles
registration, health and discovery; the selected agents exchange the task
directly.

For the boundary with IAIP, AIDIP, MCP, A2A and DNS-based discovery, read the
[protocol positioning](../standards/IICP_PROTOCOL_POSITIONING.md) and
[source-backed comparison](../standards/PROTOCOL_COMPARISON_2026-08-15.md).
The short version is that IICP selects an eligible provider; the selected
execution protocol defines how that provider performs the task.

## Choose a role

- A **consumer** discovers a provider for an intent and sends it a task.
- A **provider** advertises supported intents and accepts tasks.
- One process may perform both roles.

The maintained Python, TypeScript and Rust SDKs support both roles. See the
[implementation registry](../IMPLEMENTATIONS.md) for current releases and
source repositories. Operators running a persistent provider should use the
[verifiable onboarding and recovery path](operator-onboarding-recovery.md)
rather than treating this protocol overview as an installation runbook.

## Consumer bootstrap

1. Install one of the official SDKs.
2. Configure the directory URL. The public bootstrap directory is
   `https://iicp.network`.
3. Express the requested capability as an intent URN, for example
   `urn:iicp:intent:llm:chat:v1`.
4. Discover eligible providers and apply the SDK's health, policy and
   confidentiality checks.
5. Obtain dispatch authorization when the directory requires it.
6. Send the task to the selected provider endpoint, not to the directory.
7. Validate the response or receipt. If the provider fails, rediscover or try
   another eligible result within the task's retry policy.

Installation:

```text
Python:     pip install iicp-client
TypeScript: npm install @iicp/client
Rust:       cargo add iicp-client
```

Use the language repository's current quickstart for the exact API. SDK
interfaces evolve independently while the wire contract remains governed by
the specification.

## Provider bootstrap

1. Run the provider runtime shipped with an official SDK, or implement the
   provider contract directly.
2. Give the node a durable identity. Store its token and private keys outside
   source control.
3. Declare only the intents, models, limits and policy that the runtime can
   serve.
4. Register a routable endpoint, then send heartbeats at the required
   interval.
5. Keep health output consistent with registered capabilities. Remove a model
   from registration when the runtime no longer exposes it.
6. Authenticate incoming tasks, enforce local policy and return structured
   IICP errors.
7. Deregister cleanly when retiring the node.

For the maintained runtime, begin with:

```bash
iicp-node serve
```

The runtime can detect supported local backends and attempt the documented
reachability ladder. Tunnel and relay paths remain fallback mechanisms, not a
general production-availability guarantee.

## Agent-to-agent task flow

```text
provider agent ──register/heartbeat──> directory
consumer agent ─────discover─────────> directory
consumer agent <────route metadata──── directory
consumer agent ─────task─────────────> provider agent
consumer agent <────response────────── provider agent
```

The final two messages may use an IICP task envelope, an OpenAI-compatible
interface, MCP or an A2A task contract. IICP supplies discovery and routing; it
does not replace those application protocols.

## Security and failure handling

- Never put prompts, responses, node tokens, credentials or private endpoints
  in directory metadata.
- A remote provider can read the task it executes. Payload encryption protects
  the route and intermediaries, not the selected provider.
- In strict confidentiality mode, skip a provider that does not advertise a
  supported key. Do not silently send plaintext.
- Treat an empty discovery result as a normal unavailable-capability outcome.
- Bound timeouts and retries. Do not repeat a non-idempotent task unless its
  task identifier and provider contract make that safe.
- Re-check discovery after authentication failure, route expiry, capability
  mismatch or provider disappearance.

## Independent implementations

Implementers working without an official SDK should follow the normative
documents under [`spec/v1.9/`](../spec/v1.9/) and run the published
[conformance suite](../spec/v1.9/conformance-test-suite.md). Website examples
are introductory material; they do not override the specification.
