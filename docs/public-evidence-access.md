# Public evidence access profile

**Status:** Project contract  
**Machine-readable manifest:**
[`evidence/public-evidence-access-v1.json`](../evidence/public-evidence-access-v1.json)  
**Related work:** IICP #62 and #97

IICP publishes a small set of artifacts for implementers, standards reviewers,
monitoring tools, and non-browser clients. These artifacts must remain usable
without JavaScript or an interactive browser challenge. This requirement does
not weaken authentication for private or state-changing routes.

## HTTP behavior

Required public artifacts support `GET` and `HEAD`. A successful response uses
the declared media type; an HTML challenge or login page returned with status
`200` is not a successful machine-readable response.

Servers may apply bounded abuse controls. A rate-limited request returns `429`
with `Retry-After`. A temporarily unavailable live artifact returns a non-`200`
status, preferably `503` with `Retry-After`. Errors must not be cached as if
they were the requested JSON document.

Immutable release artifacts may be cached permanently. Mutable version,
registry, deployment and status documents must expose a bounded cache policy
and enough version or observation metadata to detect stale data.

## Static and live evidence

Source and release authority has an independently retrievable repository copy.
The public website may mirror that copy, but the mirror does not become a new
authority. Raw repository hosts may serve JSON source as `text/plain`; clients
may parse that fallback only after a successful response from the pinned HTTPS
URL and normal JSON validation.

Live runtime evidence is different. A repository cannot reconstruct current
node counts, current health, or the deployed build after the endpoint becomes
unavailable. For those artifacts, a fallback may provide the most recent
signed or dated observation, but it must identify itself as stale evidence and
must never be presented as current state. When no such observation exists, a
client reports the live fact as unavailable rather than inferring it from
source or release metadata.

## Edge-protection boundary

Interactive protection may remain on human-facing pages. The paths in the
machine-readable manifest must have narrowly scoped non-interactive access,
content-type enforcement, normal rate limiting, and monitoring. This profile
does not authorize disabling the web application firewall, exposing private
topology, publishing operator identifiers, or making authenticated evidence
public.

The repository copy of the manifest is the static bootstrap. A website mirror
at `/.well-known/iicp-evidence.json` is the preferred discovery path after a
separately reviewed website release.
