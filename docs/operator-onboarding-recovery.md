# Verifiable operator onboarding and recovery

This guide is the maintained path for installing, checking, recovering and
removing an IICP provider node. It covers the Python, TypeScript and Rust node
packages. All three expose the same operator commands even though their
internal implementations differ.

The current package line is `0.7.102`. The preceding immutable rollback line is
`0.7.101`. Confirm both values in the [implementation registry](../IMPLEMENTATIONS.md)
and [release registry](../ecosystem/releases.json) before using this guide after
a later release.

## What this path proves

The checks below establish which package is installed, whether the local
runtime is live and ready, whether the operating-system service is active and
which deterministic recovery action the node recommends. They do not prove
independent conformance, adoption, privacy, uptime or credit eligibility.

The directory remains outside the task payload path. A remote provider can read
the task it executes. Relay and tunnel paths are experimental fallbacks, not a
prerequisite for this onboarding path or a production-availability guarantee.

## 1. Install one published package

Choose one SDK. Do not install multiple global `iicp-node` packages into the
same command path.

```bash
# Python
python3 -m pip install 'iicp-client==0.7.102'

# TypeScript
npm install -g '@iicp/client@0.7.102'

# Rust
cargo install iicp-client --version 0.7.102 --locked
```

Verify the command resolved to the intended line:

```bash
iicp-node --version
iicp-node update --check
```

`update --check` is read-only. It returns success when the installed release is
current and exit status 10 when a newer release exists.

## 2. Create the operator and node configuration

Run the interactive wizard:

```bash
iicp-node init
```

The wizard stores the operator identity and named node configuration below
`~/.iicp/`. Keep that directory private, exclude it from backups shared with
other people, and never paste its credentials into an issue or evidence bundle.
Use a short local name in the commands below in place of `NAME`.

Before installing a service, exercise the node in the foreground:

```bash
IICP_AUTO_UPDATE=0 iicp-node serve --node NAME
```

Stop the foreground run normally after registration, health and backend checks
have completed. Normal shutdown attempts to deregister the node. Deregistration
is best effort, so a directory may retain a stale record until its normal expiry
if the network is unavailable during shutdown.

## 3. Install the user service

The maintained CLI installs a user-level launchd service on macOS or a
user-level systemd service on supported Linux systems. It runs
`iicp-node serve --node NAME` in the foreground under the operating-system
supervisor; it does not create a second daemon process.

Keep automatic package replacement disabled during initial validation:

```bash
IICP_AUTO_UPDATE=0 iicp-node service install --node NAME
iicp-node service status --node NAME
```

Review the service-manager output. On systemd user services, boot operation
without a login also depends on the host's user-lingering policy. The installer
does not silently change system privileges or convert the service to system
scope.

## 4. Run content-free checks

These commands do not print prompts or responses. Their JSON may still contain
local operational details, so summarize the result rather than publishing raw
output.

```bash
iicp-node doctor --node NAME --json
iicp-node healthcheck --node NAME --json
iicp-node healthcheck --node NAME --ready
```

Record only:

- SDK family and exact version;
- operating-system family and service manager;
- whether installation, service activation and local liveness passed;
- whether readiness passed or was degraded;
- bounded reason codes, with credentials and node identifiers removed;
- whether restart and rollback were exercised;
- the UTC observation time.

Do not publish node tokens, keys, prompts, responses, backend URLs, private
addresses, logs or raw node identifiers. The machine-readable contract in
[`operator-onboarding-recovery-v1.json`](../research/pre-normative-profiles/fixtures/operator-onboarding-recovery-v1.json)
defines the allowed evidence shape and the claims it cannot support.

## 5. Recover without guessing

Use `doctor` before restarting. It distinguishes local health, directory
presence and backend conditions and returns a deterministic recommended action.
An unreachable directory or provider is not, by itself, proof that the local
runtime is dead.

```bash
iicp-node doctor --node NAME --json
iicp-node service status --node NAME
```

If the recommended action requires a supervised restart:

```bash
iicp-node service restart --node NAME
iicp-node healthcheck --node NAME --ready
```

If a package regression is suspected, disable automatic updating and install
the preceding immutable release using the matching package manager:

```bash
# Python
python3 -m pip install 'iicp-client==0.7.101'

# TypeScript
npm install -g '@iicp/client@0.7.101'

# Rust
cargo install iicp-client --version 0.7.101 --locked --force
```

Then reinstall or restart the service and repeat the health checks. Restore
automatic updates only after the current release and rollback path have both
been verified. The runtime default is automatic updating; the conservative
onboarding sequence overrides it deliberately.

## 6. Remove the node safely

First stop and remove the operating-system service:

```bash
iicp-node service uninstall --node NAME
```

The service shutdown attempts deregistration before removal. Confirm that the
service is no longer active and allow normal directory expiry if deregistration
could not reach the directory.

Remove only the package family that supplied the command:

```bash
# Python
python3 -m pip uninstall iicp-client

# TypeScript
npm uninstall -g @iicp/client

# Rust
cargo uninstall iicp-client
```

Package and service removal intentionally leave `~/.iicp/` intact. It may hold
operator identity shared by other nodes. Archive it securely or delete only the
retired node's state after confirming no other node depends on it.

## Evidence classes

A successful run is **operator-reported operational evidence**. It may support
an adoption count only when the project can correlate it with current public
directory evidence without publishing the operator's identity. It is not an
independent implementation, an independent conformance run, a privacy audit or
a promise of rewards. Those claims require their own evidence and review.

