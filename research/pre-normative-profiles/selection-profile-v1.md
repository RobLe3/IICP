# Proposal — Selection Profile v1

**Status:** pre-normative, additive draft · **Depends on:** profile fixture
`0.3.0-draft`, route-ticket/receipt profile and #616 evidence.

## Contract

`iicp.selection.v1` applies hard eligibility before any spreading: intent,
risk, encryption, reachability, region and requested manifest/trust policy.
It then permits bounded weighted selection only within the eligible top-k
candidates, with score-ordered safe retries after a failure.

The opt-in `weighted_v1` weight is
`max(score, 0.01) / (1 + clamp(load, 0, 1))`. `load` is directory-provided
advisory capacity metadata; it is clamped so a malformed value cannot dominate
selection. The canonical `fixtures/selection-v1.json` vectors are evaluated
after hard eligibility and before dispatch.

`deterministic` remains the diagnostic order. Existing `epsilon` remains the
default until the three native SDKs have matching deterministic vectors and
Docker evidence. A future weighted strategy must be explicit opt-in first; it
must not relax a hard policy gate merely to spread load.

## Receipt boundary

Selection receipts may contain the profile name, eligible candidate count,
redacted selected-node reference, exclusion categories and fallback outcome.
They must not contain prompt/response content, endpoint URLs or tokens.

Browser ticketed routing is labelled `directory_ticket_v1` until it has an
equivalent ticket-selection profile. It must not claim native local-selection
parity before that point.
