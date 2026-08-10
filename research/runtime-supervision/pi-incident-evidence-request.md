# Raspberry Pi Node Incident Evidence Request

Use this checklist after a node appears to die. It is designed to distinguish a process exit, runtime stall, connectivity failure, host failure, and out-of-memory termination without collecting credentials or task content.

## Before sharing

Remove tokens, environment values, public or private keys, node identifiers, IP addresses, hostnames, usernames, directory URLs, tunnel URLs, task payloads, model prompts, and private filesystem paths. Do not share `/proc/<pid>/environ`, service environment files, shell history, core dumps, or an unredacted external-watchdog script.

Record the incident time with timezone and whether the host itself remained reachable. Preserve the original files locally before redaction.

## Requested observations

1. Was the PID present? If so, was its CPU time or thread activity changing?
2. Did the local node listener answer `GET /iicp/health`? Record only status code and redacted, schema-preserving output.
3. Did `iicp-node doctor --json` complete? Remove identifiers, endpoints, and detailed error strings.
4. Did the directory heartbeat continue, fail, or stop being attempted?
5. Was the tunnel, provider/backend, or Internet connection unavailable?
6. Did the machine reboot, freeze, lose power, or experience storage errors?
7. Did the kernel or service manager report an out-of-memory kill?
8. Was the node launched manually or through a user/system service?
9. What exact condition did the external watchdog test, and what command did it invoke after failure?

## Sanitized command bundle

Run only commands appropriate to the actual service scope. Save output locally, then redact it before sharing.

```bash
date --iso-8601=seconds
uname -a
systemctl --user status iicp-node --no-pager
systemctl --user show iicp-node \
  -p Type -p Restart -p RestartUSec -p WatchdogUSec -p NotifyAccess \
  -p ActiveState -p SubState -p Result -p NRestarts -p ExecMainStatus
systemctl --user cat iicp-node
journalctl --user -u iicp-node --since '30 minutes ago' --no-pager
journalctl -k --since '30 minutes ago' --no-pager
```

For a system service, omit `--user`. Redact `ExecStart`, `Environment`, `EnvironmentFile`, working directories, URLs, and identifiers. In kernel logs, retain only resource, OOM, filesystem, watchdog, reboot, and process-exit evidence.

If the process remains alive, also record a short, content-free progression sample:

```text
sample time | PID present | local health status | doctor completed | CPU time advanced
```

Do not attach payloads or inference output.

## External watchdog summary

Provide a prose or pseudocode description containing only:

* test type: PID, port, local health, heartbeat age, tunnel, or another signal;
* interval and timeout;
* number of failures required;
* restart authority invoked;
* cooldown and false-positive protection;
* which condition triggered during the incident.

This evidence will classify the incident. It is not permission to reproduce private topology or deploy a new watchdog.
