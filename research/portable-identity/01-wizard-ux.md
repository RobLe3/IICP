# Portable Identity UX — Onboarding Wizard Flow

**Issue**: #307 (Research: portable identity UX — onboarding wizard)
**Date**: 2026-05-24
**Author**: RESA loop, FORGE iter963

---

## Design Goal

First-time operator experience that:
1. Takes < 2 minutes from "no key" to "node registered"
2. Creates or imports an Ed25519 key pair (ADR-030)
3. Gives explicit, memorable backup instructions
4. Prevents spam by making the key feel consequential

---

## Wizard Flow: `iicp-node identity init`

```
$ iicp-node identity init

IICP Operator Identity Setup
─────────────────────────────────────────────────────

Welcome. Your operator identity is a cryptographic key pair.
It links your nodes, earns reputation, and cannot be recovered
if lost. Treat it like a password manager master key.

? What would you like to do?
  ❯ Create a new identity
    Import an existing identity

────────────────────────────────────────────────────
[NEW IDENTITY PATH]

Generating Ed25519 key pair...

✓ Identity created:
  Operator ID:  iop_7xK9mN2vFqRsPbAeYtLwCdZuJ3hGnX8W
  Key file:     ~/.iicp/operator.key    (keep secret)
  Public key:   ~/.iicp/operator.pub    (share freely)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BACKUP YOUR IDENTITY NOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your 12-word recovery phrase:
  canyon drift palace harbor motion river anchor bright
  tunnel voyage mirror stone

Write these words down. Store in a secure location.
If you lose your key file AND this phrase, your operator
identity and all associated reputation is permanently lost.

? I have written down my recovery phrase and stored it safely.
  ❯ Yes, I'm ready to continue

────────────────────────────────────────────────────
[IMPORT IDENTITY PATH]

? Choose import method:
  ❯ Recovery phrase (12 words)
    Key file (~/.iicp/operator.key or .pem)
    Operator ID + seed hex (advanced)

[Recovery phrase path]
? Enter your 12-word recovery phrase:
  > canyon drift palace harbor...

✓ Identity restored:
  Operator ID:  iop_7xK9mN2vFqRsPbAeYtLwCdZuJ3hGnX8W
  Key file:     ~/.iicp/operator.key

Found 3 nodes linked to this identity:
  • node-eu-1  (eu-central, last seen 2 hours ago)
  • node-us-1  (us-east, last seen 4 days ago)
  • node-sg-1  (ap-southeast, last seen offline)

? Re-register all linked nodes with new machine credentials? [Y/n]

────────────────────────────────────────────────────
✓ Identity setup complete.

Your operator ID: iop_7xK9mN2vFqRsPbAeYtLwCdZuJ3hGnX8W

Next steps:
  Register a node:     iicp-node register --endpoint https://yourhost:9484
  Check your nodes:    iicp-node status
  Export for mobile:   iicp-node identity export --qr
```

---

## Design Decisions

1. **Mandatory acknowledgment before continuing**: The backup step requires an explicit
   "Yes, I'm ready" before proceeding. This is not a skip-able checkbox — it is a
   single-question confirmation that creates a moment of deliberate action.

2. **Recovery phrase displayed inline**: Not in a separate file. Forces the operator
   to copy it before they can continue. The phrase is shown ONCE at creation — not
   stored by the tool after setup.

3. **Node re-association shown immediately**: On import, the wizard immediately shows
   which nodes are linked to the restored identity. This gives operators confidence
   the restore worked correctly.

4. **Two-minute target**: New identity path is 4 steps (choose, generate, write phrase,
   confirm). Import path is 3–4 steps depending on method. Both under 2 minutes.

5. **No UI bloat**: No progress bars, no animated logos, no lengthy explanatory text.
   Plain terminal UX that respects operator time.

---

## Implementation Notes for ADR-030 §Implementation Checklist

- `iicp-node identity init` — primary command (new this flow)
- `iicp-node identity export --qr` — QR code for mobile transfer
- `iicp-node identity export --phrase` — re-display recovery phrase (requires key file + passphrase)
- `iicp-node status` — list nodes linked to current identity via directory API
- Recovery phrase: BIP39 mnemonic derived from Ed25519 seed (128-bit entropy, 12 words)
- Key file format: PEM-encoded Ed25519 private key, passphrase-protected
- Operator ID format: `iop_` prefix + base58-encoded public key hash (33 chars total)
