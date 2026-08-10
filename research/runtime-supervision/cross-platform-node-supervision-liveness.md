# Cross-Platform Node Supervision and Runtime Liveness Analysis

**Status:** research finding; no watchdog or wire change is authorized  
**Evidence date:** 2026-08-10

## Trigger and evidentiary limit

A Raspberry Pi operator reported that a hardened node “died” and that they added an external watchdog. The available report does not establish whether the process exited, the runtime stalled, the host failed, an out-of-memory killer intervened, or connectivity alone was lost. The incident therefore remains **unresolved**. The companion [evidence request](pi-incident-evidence-request.md) asks for the minimum sanitized material needed to classify it.

This analysis inspected these revisions:

| Repository | Revision |
|---|---|
| IICP specification | `7617e0bdaeaf` |
| Rust SDK/node | `2fde5630089a` |
| Python SDK/node | `2ab4ede01fe1` |
| TypeScript SDK/node | `220de9afbdda` |
| Website | `85cf7b864ba9` |

## Confirmed current architecture

All three official SDKs render user-service definitions through `iicp-node service install`. The generated systemd units use `Type=simple`, `Restart=on-failure`, and a 30-second restart delay. The launchd definitions use `RunAtLoad` and `KeepAlive`. The service helpers set `IICP_SUPERVISED=1` and `IICP_TUNNEL_DEAD_POLICY=auto`.

The helpers currently write a unit or plist and print follow-up commands. They do not themselves reload the service manager, enable boot startup, establish systemd user lingering, or activate the service. Existing tests verify rendering and dry-run behavior rather than install, upgrade, logout, reboot, and uninstall lifecycle behavior. The phrase “service install” therefore overstates the effective action unless the operator follows the printed commands.

The node has a separate internal recovery layer. It monitors tunnel and directory-related state, attempts recovery and re-registration, and can exit deliberately so an external supervisor restarts the process. A remote directory heartbeat normally runs at about a 30-second cadence. A successful remote heartbeat proves neither that every local runtime component is progressing nor that the node remains discoverable and routable.

The existing `GET /iicp/health` contract is a provider status and capacity surface that returns HTTP 200. It is already used by conformance and reachability checks. `doctor --json` diagnoses local configuration, directory presence, and recovery actions. Neither interface currently exposes a monotonic local runtime-progress signal or a clean liveness/readiness split. `/metrics` being unavailable with HTTP 503 is not evidence that node liveness failed.

Source inspection found no native `sd_notify`, `NOTIFY_SOCKET`, `WATCHDOG_USEC`, `READY=1`, `WATCHDOG=1`, `Type=notify`, or `WatchdogSec` support. Changing the unit to `Type=notify` now would be invalid.

## Supervision layers and responsibility

```text
Operating-system supervisor
  starts the process, observes exit, and performs final restart
                    |
                    v
                iicp-node
                    |
          Runtime Health Core
           /       |        \
   liveness    readiness   subsystem state
                    |
          IICP internal supervisor
       tunnel, directory and provider recovery
```

The operating-system supervisor should be the sole final restart authority. IICP's internal supervisor should repair recoverable subsystem failures. A future runtime-health core should determine whether meaningful local progress continues. Platform integrations should translate that one health calculation rather than redefine it.

## Failure taxonomy

| Class | Question | Primary owner | Restart implication |
|---|---|---|---|
| Process liveness | Does the OS process exist? | service manager | restart after exit |
| Runtime liveness | Is the local runtime making meaningful progress? | IICP runtime | restart only after a verified stall |
| Node readiness | Can the configured role accept useful work now? | IICP runtime | normally remove from selection, not restart |
| Subsystem health | Are tunnel, directory, provider, and routing components healthy? | internal supervisor | recover locally where possible |
| External connectivity | Are DNS, directory, Internet, and peers reachable? | environment plus subsystem | degrade and retry; do not restart-loop |
| Host health | Are kernel, memory, storage, power, and hardware healthy? | host/operator | outside an in-process watchdog |

This distinction is necessary because a live node may be unready, and a healthy runtime may be temporarily unable to reach its directory.

## Required generic health semantics

The smallest defensible shared abstraction is a local health snapshot with:

* a monotonic runtime-progress observation and its age;
* a supervisor-progress observation taken before potentially blocking remote I/O;
* readiness derived separately from provider, route, and capacity state;
* named subsystem states with bounded, content-free reason codes;
* external-connectivity state that cannot by itself make local liveness fail;
* a startup state so slow initialization is not mistaken for a stall.

The exact schema remains an issue-level decision. It should be additive. Reinterpreting the existing `/iicp/health` endpoint would break current provider and conformance assumptions. A local `healthcheck` command or new local-only surface can expose the shared snapshot first.

A watchdog pulse must depend on the same executor and progress state as the work being supervised. A detached timer thread that can continue after the main runtime stalls is not a valid signal.

## Platform mapping

| Environment | Suitable consumer of generic health | Immediate scope |
|---|---|---|
| systemd Linux | `sd_notify` readiness/status/watchdog adapter | reference implementation after core semantics |
| non-systemd Linux | local health command used by OpenRC, runit, s6, or an operator wrapper | compatibility requirement, not four implementations |
| macOS launchd | `KeepAlive` plus a health command/helper if application-stall recovery is required | architectural compatibility only |
| Windows SCM | service lifecycle and recovery; health may feed a service wrapper/monitor | architectural compatibility only |
| Docker/Kubernetes/Nomad | health command or local endpoint mapped separately to liveness/readiness | later consumer |

Kubernetes' separation of [liveness, readiness, and startup probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/) supports the same semantic boundary: readiness failure need not restart a process, while a genuine liveness failure may. Platform-specific mechanisms remain deployment concerns rather than IICP wire semantics.

## systemd adapter constraints

A later Linux adapter may use `READY=1`, `STATUS=…`, `WATCHDOG=1`, and `STOPPING=1`, with `Type=notify` and `NotifyAccess=main`. It must remain conditional on systemd availability and consume the generic snapshot. The watchdog period must be derived from measured progress under Raspberry Pi load, slow storage, long inference, startup, and memory pressure. No fixed value is justified by the present evidence.

The authoritative mechanism is documented by systemd's [`sd_notify`](https://www.freedesktop.org/software/systemd/man/latest/sd_notify.html) and [watchdog](https://www.freedesktop.org/software/systemd/man/latest/sd_watchdog_enabled.html) interfaces. Merely sending pulses on a timer would not meet the IICP health requirement.

## Controlled fault matrix

| Test | Expected classification | Expected owner/action |
|---|---|---|
| normal operation | live; readiness role-dependent | no action |
| deliberate process crash | process dead | service manager restarts |
| executor/runtime stall with PID present | runtime progress stale | platform watchdog restarts after threshold |
| tunnel failure | live; subsystem degraded | internal recovery; no whole-process restart unless recovery policy exhausts |
| directory outage | live; readiness/discovery degraded | retry without restart loop |
| DNS/Internet outage | live; external connectivity degraded | retry without restart loop |
| provider failure | live; normally unready | withdraw capacity/recover provider |
| watchdog timer alive while runtime stalls | runtime not live | pulse must be withheld |
| sustained legitimate inference load | live | no false restart |
| install, upgrade, logout, reboot, uninstall | service state matches declared policy | lifecycle test verifies effective manager state |

Tests must use fault injection rather than treating network failure as a runtime stall. ARM64 validation should cover Raspberry Pi OS or Debian ARM64 before enabling a default watchdog policy.

## Findings and recommendations

### Required

1. Obtain and classify the Pi incident evidence. Until then, do not claim a watchdog would have prevented it.
2. Define one OS-independent liveness/readiness model and parity fixtures for all official nodes.
3. Correct `service install` lifecycle behavior or rename it so its actual effect is unambiguous.

### Recommended

1. Implement the generic snapshot in the Rust node as a reference, including a local healthcheck interface and deterministic stall tests.
2. Port the semantics, not Rust code, to Python and TypeScript using shared fixtures.
3. Add a systemd adapter only after the generic health calculation passes false-positive and failure-injection tests.
4. Clarify documentation and installer output so process supervision, internal recovery, runtime watchdog, readiness, and unsupported capabilities are shown separately.

### Optional or future

* Map the same semantics to container probes and later platform adapters.
* Evaluate launchd and Windows-specific consumers only after the shared model is stable.

### Not recommended

* A second watchdog daemon on systemd hosts.
* `Type=notify` or `WatchdogSec` before native support exists.
* A watchdog pulse driven by a detached timer.
* Restarting because a remote directory, DNS, tunnel, or provider is unavailable.
* Changing the established `/iicp/health` meaning in place.

## Decision boundary

The evidence supports a supervision gap at the design level: process-exit supervision and subsystem recovery exist, but meaningful local runtime progress is not represented explicitly. It does **not** prove that this gap caused the Raspberry Pi incident. Implementation should proceed in dependency order: incident evidence and shared semantics, Rust reference health, parity ports, systemd integration, ARM validation, then documentation and broader platform consumers.

## Tracked follow-up

| Repository | Issue | Purpose |
|---|---:|---|
| IICP | [#121](https://github.com/RobLe3/IICP/issues/121) | shared semantics and fixtures |
| Rust SDK | [#64](https://github.com/RobLe3/iicp-client-rust/issues/64) | generic health reference |
| Python SDK | [#67](https://github.com/RobLe3/iicp-client-python/issues/67) | semantic parity |
| TypeScript SDK | [#61](https://github.com/RobLe3/iicp-client-typescript/issues/61) | semantic parity |
| Rust SDK | [#66](https://github.com/RobLe3/iicp-client-rust/issues/66) | gated systemd adapter and ARM validation |
| Rust SDK | [#65](https://github.com/RobLe3/iicp-client-rust/issues/65) | effective service lifecycle |
| Python SDK | [#68](https://github.com/RobLe3/iicp-client-python/issues/68) | effective service lifecycle |
| TypeScript SDK | [#62](https://github.com/RobLe3/iicp-client-typescript/issues/62) | effective service lifecycle |
| Website | `iicp-website#24` (private) | operator documentation after behavior stabilizes |
| Operations | `iicp-network-ops#24` (private) | sanitized Pi incident classification |

The platform adapter and documentation issues are dependency-gated. Their existence does not authorize implementation before the shared health model is accepted.
