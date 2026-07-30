---
title: "Intent-based Inter-agent Communication Protocol Peer Transport"
abbrev: "IICP Peer Transport"
docname: draft-roble-iicp-peer-latest
category: info
ipr: trust200902
submissiontype: IETF
area: Applications and Real-Time
workgroup: Individual Submission
keyword: [agents, intent, discovery, transport, CBOR]

author:
  -
    ins: R. Lee
    name: Rob Lee
    organization: IICP
    email: community@iicp.network

normative:
  RFC8949:
  RFC8446:

informative:
  RFC6335:

--- abstract

This document describes a minimal peer transport for intent-addressed agent
tasks.  A directory or another bootstrap mechanism can select a provider, but
task payloads do not pass through that directory.  The transport uses a
length-delimited frame over TLS-protected TCP and deterministic CBOR payloads.
This document does not specify directory ranking, credits, federation,
cooperative execution, or a QUIC mapping.

--- middle

# Introduction

IICP separates route selection from task execution.  A consumer obtains a
provider route, connects to that provider directly or through an explicitly
selected relay, negotiates a protocol version, submits an intent-addressed
task, and receives a structured result or error.

The directory is not on the task payload path.  A relay can be on that path and
therefore has separate metadata and confidentiality considerations.

# Conventions and Terminology

{::boilerplate bcp14-tagged}

Consumer:
: An endpoint that submits a task.

Provider:
: An endpoint that executes a task.

Directory:
: A control-plane service that returns candidate routes.  Directory behavior is
  outside this document.

Relay:
: A transport intermediary selected when a direct provider connection is not
  available.

# Protocol Scope

This document specifies:

* version negotiation;
* a fixed header and length-delimited frame;
* deterministic CBOR payloads;
* request identifiers and intent identifiers;
* task, result, error, ping, and close exchanges;
* resource, timeout, replay, and downgrade handling.

It does not specify provider selection, scoring, billing, reputation,
federation, MCP bindings, cooperative inference, local directory discovery, or
NAT traversal.

# Connection Establishment

A peer endpoint is obtained from authenticated configuration or route metadata.
The endpoint includes the host and actual port.  The current project convention
uses TCP port 9484, but IANA has not assigned or reserved that port for IICP.

Production connections MUST use TLS 1.3 or later as defined by {{RFC8446}} and MUST validate the peer
certificate or an explicitly configured peer identity.  Implementations MUST
NOT infer trust from a port number, local-network advertisement, tunnel, or
directory response alone.

# Frame Format

Every frame begins with a 12-octet header:

~~~ ascii-art
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-------------------------------+-------+-------+-------+-------+
|       Magic "IICP"            | Ver   | Type  | Flags | Rsvd  |
+-------------------------------+-------+-------+-------+-------+
|                         Length                                |
+---------------------------------------------------------------+
~~~

Magic:
: The four ASCII octets `IICP`.

Version:
: The negotiated framing version.  Version zero is invalid.

Type:
: The message type.

Flags:
: Versioned flags.  Unknown bits are ignored unless the negotiated profile
  states otherwise.

Reserved:
: Sent as zero and ignored on receipt.

Length:
: An unsigned 32-bit network-byte-order payload length.

A receiver MUST validate the header and configured size limit before allocating
memory proportional to Length.  The default maximum frame payload is 16 MiB.
Wrong magic causes an immediate connection close without a protocol response.

# Messages

The initial exchange is INIT followed by ACK or CLOSE.  INIT carries the
preferred and minimum supported versions.  ACK selects a version within that
range.  A peer MUST close on an out-of-range selection or a changed version
after negotiation.

CALL carries:

* a UUID task identifier;
* an intent URN;
* a bounded timeout;
* the application payload;
* optional constraints defined by a separately negotiated profile.

RESPONSE repeats the task identifier and carries either a result or a
structured error.  A provider MUST NOT return raw exceptions, stack traces,
filesystem paths, credentials, or unrelated task state.

PING and PONG provide connection liveness.  CLOSE terminates the protocol
session and carries a bounded machine-readable reason.

# CBOR Encoding

Payloads use deterministic CBOR as defined by {{RFC8949}}.  Map keys, numeric
representations, and string normalization MUST follow the versioned IICP
message schema.  Indefinite-length encoding MUST NOT be used for INIT, CALL,
RESPONSE, telemetry, or feedback messages.

No CBOR tag is assigned by this document.  Tag 65535 MUST NOT be emitted
because the IANA CBOR tag registry defines it as always invalid.

# Timeouts, Cancellation, and Replay

The consumer supplies a bounded task timeout.  Timeout expiry stops waiting for
the response but does not by itself prove that backend execution stopped.
Confirmed cancellation requires a negotiated lifecycle profile and is outside
this document.

A provider MUST bind task identifiers to the authenticated request context and
MUST reject conflicting reuse.  Implementations SHOULD retain bounded
idempotency state for the negotiated retry window.

# Error Handling

Malformed length, invalid version, invalid type, CBOR failure, oversized
payload, replay, and authentication failure are distinct errors.  Parsers MUST
fail before application dispatch and MUST bound diagnostic data.

# Security Considerations

A malicious directory can return attacker-controlled routes.  Consumers must
authenticate providers independently of route discovery.

The provider that executes a task can read its plaintext after transport
decryption.  Transport encryption does not provide executor blindness or
anonymity.

Relays can observe connection metadata.  A profile that carries encrypted
payloads through a relay must keep end-to-end keys outside relay control.

Implementations must limit concurrent connections, incomplete frames,
reassembly bytes, task sizes, diagnostic output, and retries.  They must reject
downgrades, conflicting task-ID reuse, invalid certificates, malformed CBOR,
and unnegotiated extensions.

Endpoint publication can expose providers to scanning and denial-of-service
traffic.  Operators should be able to disable automatic public exposure and
should not treat UPnP, tunnels, or multicast discovery as trust mechanisms.

# Privacy Considerations

Task payloads do not pass through a directory, but directory queries and route
records expose intent and routing metadata.  Providers see the tasks they
execute.  Relays and network observers can learn timing and volume.  Logs must
exclude task payloads, credentials, private keys, and bearer tokens.

# IANA Considerations

This document makes no IANA request.

The IICP project is evaluating the service name `iicp` and TCP port 9484 under
{{RFC6335}}.  Port 9484 is currently a provisional project convention and must
not be described as assigned.  A future request requires evidence that dynamic
ports, signed endpoint advertisement, DNS discovery, or operation over an
existing port are insufficient.

No UDP port, ALPN identifier, media type, or CBOR tag is requested here.

--- back

# Acknowledgements

The public IICP specifications, conformance fixtures, and maintained language
implementations informed this draft.  Those implementations are evidence and
are not normative authority.
