# Privacy adversary and trust model

## Scope

This document records the public threat boundaries used by IICP Core and
IICP-CX. It describes protocol properties, not a deployment certification.

## Privacy adversaries

| ID | Adversary | Observable or controllable surface | Required posture |
|---|---|---|---|
| PA-1 | Network observer | addresses, timing, volume and any transport not protected by an authenticated secure channel | Use authenticated transport security and avoid payload logging. |
| PA-2 | Relay operator | connection metadata and ciphertext carried through the relay | Keep task-encryption keys outside relay control; a relay must forward CX envelopes without decrypting them. |
| PA-3 | Directory operator | registration, discovery, intent and route metadata | Task payloads must not pass through or be stored by the directory. |
| PA-4 | Selected execution provider | plaintext request, response and inference state required for ordinary execution | Disclose this boundary. IICP-CX does not hide plaintext from the selected executor; local or separately attested confidential execution is required for a stronger property. |

IICP transport confidentiality is not anonymity. Timing, volume, endpoint and
selection metadata can remain visible even when task content is encrypted.

## Cooperative-inference threats

Cooperative execution adds capability-boundary bypass, credit laundering,
timing inference, policy spoofing and receipt-identity substitution risks. The
public cooperative-inference specification defines the applicable controls:
provider policy enforcement, signed and replay-protected receipts, bounded
credit awards, caller binding and explicit local-only routing. A deployment
must not infer that one control removes the other threats.

## Federation and identity-slot threats

Federated directories and identity verifiers must account for:

- tampered discovery results from a compromised replica;
- replayed, reordered or truncated signed event streams;
- stale or replaced replica keys;
- circular or conflicting trust assertions;
- unavailable identity documents;
- identity-scheme and signature-algorithm confusion;
- downgrade to unsigned or unverified results.

Identity signatures bind the canonical message context. Verification dispatch
uses the asserted identity scheme, rejects mismatched key material and treats
network retrieval failure as unavailable evidence rather than successful
verification. Federation remains pre-normative until its separate evidence and
deployment gates pass.

## Evidence boundary

Specification requirements and conformance vectors show the intended behavior.
Implementation tests show that a particular release exercised that behavior.
Neither is a claim that a deployment, relay, operator or hardware environment
has been independently audited.
