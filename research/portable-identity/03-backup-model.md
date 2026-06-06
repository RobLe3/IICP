# Portable Identity UX — Backup and Recovery Model

**Issue**: #307
**Date**: 2026-05-24

---

## "Bitcoin Wallet Light" Design

The maintainer directive: identity should feel like a bitcoin wallet — something that needs
to be backed up and stored safely, enabling users to rebuild their client and node
associations easily and fast later.

**Design target**: The complete backup artifact is a single 43-character operator_id +
one of the recovery methods below. A user with the backup can reconstruct everything else.

---

## Recovery Method Comparison

| Method | Artifact size | Security | Usability | Recommendation |
|--------|--------------|---------|-----------|---------------|
| 12-word BIP39 mnemonic | 12 words | HIGH (128-bit entropy) | HIGH (memorizable, writable) | **Primary** |
| PEM key file copy | ~200 bytes | HIGH | MED (file management) | **Secondary (file backup)** |
| QR code | One image | HIGH | HIGH (mobile transfer) | **Mobile path** |
| Seed hex (64 chars) | 64 hex chars | HIGH | LOW (error-prone typing) | Advanced only |

---

## Primary: BIP39 12-word Mnemonic

**Derivation**: The Ed25519 seed (32 bytes / 256 bits) is mapped to a 12-word BIP39 mnemonic
using 128 bits of entropy (the first 16 bytes of the seed; the remaining 16 bytes are derived
deterministically). This yields 12 words from the standard 2048-word BIP39 wordlist.

```bash
iicp-node identity export --phrase
# Requires: key file exists at ~/.iicp/operator.key
# Output: 12-word mnemonic + operator_id for verification

iicp-node identity import --phrase
# Prompts for 12 words + optional passphrase
# Reconstructs operator.key + operator.pub
```

**Recovery guarantees**: Any machine with `iicp-node` installed can restore the full
identity from 12 words. No cloud service, no account, no internet required.

---

## Secondary: Key File Backup

The PEM key file (`~/.iicp/operator.key`) is the direct cryptographic artifact.

```bash
# Backup
cp ~/.iicp/operator.key /path/to/usb/iicp-operator.key

# Restore
iicp-node identity import --keyfile /path/to/iicp-operator.key
```

**Security**: Key file should be passphrase-encrypted (AES-256). The wizard asks for
a passphrase during creation (optional but strongly recommended).

**Portability limitation**: PEM file path must be copied correctly. Typos are common.
The 12-word phrase is more error-tolerant (BIP39 has checksum; typos are detected).

---

## Mobile Path: QR Code

```bash
iicp-node identity export --qr
# Opens a terminal QR code in the current window
# QR encodes: "iicp-identity:v1:<base64-encoded-encrypted-seed>"
# Encryption: AES-256-GCM with a user-provided PIN

# On mobile: scan with iicp mobile app → import identity
```

**Use case**: Operator wants to monitor their nodes from their phone. Same identity,
both devices.

**Security note**: QR code contains encrypted seed. PIN is required to decrypt. A
QR code without PIN knowledge is useless to an attacker. Recommend at least 6-digit PIN.

---

## Minimal Portable Artifact

The smallest possible backup is:
```
Operator ID:    iop_7xK9mN2vFqRsPbAeYtLwCdZuJ3hGnX8W   (43 chars)
Recovery phrase: canyon drift palace harbor motion river anchor bright tunnel voyage mirror stone
```

This fits in a password manager note (two lines). It's the "bitcoin wallet light" backup.
Any operator who saves these two things can reconstruct their full operator identity on
any machine at any time.

---

## Key File Location and Cross-Platform Paths

| Platform | Default path |
|----------|-------------|
| Linux/macOS | `~/.iicp/operator.key` |
| Windows | `%APPDATA%\iicp\operator.key` |
| Docker | `/run/secrets/iicp-operator-key` (bind-mount pattern) |

**Recommendation**: The wizard respects `IICP_KEY_PATH` env var for non-default locations.
This supports NixOS, Docker, and CI/CD environments where home-directory key storage is impractical.
