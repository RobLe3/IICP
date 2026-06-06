# Portable Identity UX — Spam Prevention and Identity Friction

**Issue**: #307
**Date**: 2026-05-24

---

## The Spam Problem

Tier 1 (pseudonymous) identity is free. Without friction, users can create hundreds of
throwaway identities, defeating the reputation system's core assumption: identity = accountability.

---

## Defense Layer Analysis

### Layer 1: Identity-Age Gate (REP2, active)

Platinum routing tier requires `identity_age_hours ≥ 720` (30 days). This is the
primary economic deterrent: a new identity cannot access premium routing for 30 days
regardless of task volume. Most spam scenarios (rating farms, whitewash) require at
least temporary platinum access to be profitable.

**Effectiveness**: High for strategic spammers; zero for casual "I created a new key
because I lost my old one" cases (which is benign).

### Layer 2: Reputation Starting Credit (REP1, active)

New identities start at 0.50 (Silver/Gold boundary). A node with a fresh identity has
routing access immediately but not preferential routing. No warm-up advantage from fresh identity.

**Effectiveness**: Low — new identity vs old identity are treated identically for
Silver-tier work. Doesn't deter casual spam.

### Layer 3: Directory Rate Limiting (not yet implemented)

Proposal: rate-limit new node registrations per source IP per 24h window:
- Allow: 3 new node_token registrations per IP per 24h
- Warn: at 5+ registrations from same IP, flag for human review
- Block: at 10+ registrations from same IP within 1h, temporary ban

**Implementation**: Add IP-based rate limit to `RegisterController.php` using Laravel's
built-in rate limiter (already used on other endpoints). This is a lightweight directory-side
control, no cryptographic infrastructure needed.

**Effectiveness**: Medium — deters casual spam from a single machine; doesn't stop
distributed Sybil attacks using multiple IPs.

### Layer 4: Attestation Cost (ADR-030 Tier 2, future)

ADR-030 defines a second identity tier (attested/verifiable) that requires submitting
verifiable credentials (e.g., domain ownership proof, email confirmation). Attested
identities receive better routing trust and can access features that unattested identities cannot.

**Effectiveness**: High for attested identities. But Tier 1 (pseudonymous) must remain
free-to-create as a design principle (operators should be able to join without bureaucracy).
The cost model is: Tier 1 = free but limited trust ceiling; Tier 2 = attestation cost but
higher trust and routing priority.

---

## Recommended Friction Level for Tier 1

**Right friction**: The wizard's mandatory recovery phrase acknowledgment. Operators who
create throwaway identities will skip the recovery phrase step — or lose the identity
when they lose the key file. This natural consequence deters repeat creation:

> "I created 5 identities and lost them all because I didn't save the phrase. Now I understand
> I should keep one identity and back it up properly."

The wizard already enforces this by showing the phrase once and requiring acknowledgment.

**Wrong friction**: Email verification, CAPTCHA, or payment for Tier 1. These create
barriers for legitimate operators in privacy-sensitive or payment-inaccessible situations.

---

## Directory Rate Limit Recommendation

```php
// RegisterController.php — add to existing validation
RateLimiter::attempt(
    'register-identity:' . $request->ip(),
    $perMinute = 5,
    $perDay = 20,
    fn() => $this->processRegistration($validated)
) or abort(429, 'Too many node registrations from this IP');
```

**Threshold choice**: 20 registrations per IP per day is generous enough for legitimate
multi-node deployments and strict enough to deter casual Sybil farm automation.

---

## Recommendation Summary

| Defense | Status | Effectiveness vs spam |
|---------|--------|----------------------|
| Identity-age gate (REP2) | ✓ Active | HIGH for strategic spam |
| Recovery phrase ceremony | ✓ Active (wizard) | LOW but creates accountability mindset |
| Directory IP rate limit | ✗ Not implemented | MEDIUM — implement in Phase 5 |
| Attestation cost (ADR-030 T2) | ✗ Future | HIGH for attested tier |

**Immediate action**: Implement directory IP rate limit (20 registrations/IP/day).
All other defenses are either active or deferred to ADR-030 T2.
