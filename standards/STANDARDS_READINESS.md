# IICP standards-readiness decision record

**Date:** 2026-07-30

This record separates work that can proceed now from actions that still need
evidence or maintainer authority.

## Port and registry decision

The project is not ready to submit a port request.

If the fixed-port evidence gate passes, the first candidate is service name
`iicp`, port 9484, TCP only, through RFC 6335 Expert Review. Port 9484 is
currently unassigned. It is not reserved for IICP.

Before applying, public IICP issue #42 must record evidence comparing the
dedicated port with:

- signed route metadata carrying a dynamic port;
- DNS SRV, SVCB or HTTPS discovery;
- an application protocol and ALPN over port 443;
- a service name without an assigned port.

UPnP, Quick Tunnel, port auto-increment and UDP-based NAT classification are
deployment behavior. They do not establish the need for a registered port.

UDP is out of scope for the first request. A later request for the same numeric
port requires a concrete QUIC mapping, applicable congestion and operational
analysis, and two interoperable implementations. The project will not request
a port block.

No CBOR tag is requested. Tag 65535 is invalid by registry definition.
Candidate media types require complete registration templates and independent
review before submission.

## Publication boundary

The first Internet-Draft candidate covers the peer transport only. Directory
selection, scoring, credits, federation, Cooperative Inference, MCP, mDNS and
deployment-specific NAT escalation remain outside its normative scope.

The draft is an individual working document. Building it locally does not
submit it or make it project-normative.

## Related standards work

Before external introduction, the project will maintain a dated comparison
with:

- IETF CATALIST and discussion on `agent2agent@ietf.org`;
- active intent-aware agent routing and gateway drafts;
- A2A and MCP;
- HTTP, QUIC, DNS-SD/SVCB, OAuth, DID/VC and OpenTelemetry.

The first contact should ask CATALIST participants about overlap and problem
scope. DISPATCH can advise on an application-area venue. TSVWG is the review
venue for transport and service-port questions. The QUIC working group should
be consulted only when a concrete QUIC application mapping exists.

These contacts are requests for review, not claims of support.

## Authorship and authority

The current draft lists Rob Lee as its initial author and
`community@iicp.network` as the public contact.

External submission is blocked until:

- a second consenting editor or backup contact is recorded;
- the change controller and succession procedure are documented;
- the maintainer explicitly authorizes the submission;
- the security, interoperability and fixed-port evidence gates pass.

Implementation repositories are informative evidence. PHP is a directory
implementation, not a native peer transport. The Rust directory is a
same-project alternate implementation and does not count as clean-room
independent evidence.

## Claim controls

Public standards material may describe a running beta network and maintained
implementations. It must not claim heavy production throughput without a
published measurement, call port 9484 assigned, describe the Rust directory as
independent, or imply IETF/IANA endorsement.

No item in this record authorizes deployment, an Internet-Draft upload, a
mailing-list post or an IANA application.
