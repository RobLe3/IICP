# Standards submission governance decision packet

## Purpose

This packet turns IICP issue #47 into a bounded decision that the maintainer
and consenting editors can complete without implying outside authority. It
does not submit an Internet-Draft, contact a standards venue, request an IANA
registration or authorize any of those actions.

The current peer-transport draft names Rob Lee as the initial author and uses
`community@iicp.network` as its public contact. The project remains
founder-stewarded. A nominal backup must not be appointed merely to make the
governance record look distributed.

## Decisions required before submission

1. Record the consenting lead author/editor and a consenting backup editor or
   continuity contact.
2. Confirm which public addresses may appear in the draft and registry
   correspondence.
3. Name the change controller for the draft and any future registry entry.
4. State how errata, revisions and interoperability evidence enter the public
   change process.
5. Record the copyright, contribution and IPR treatment accepted by every
   named contributor.
6. Define what the backup may do if the lead steward is unavailable, including
   the threshold for temporary and permanent succession.
7. Keep implementation maintainers informative: PHP, Rust and SDK behavior may
   supply evidence but cannot silently redefine the specification.
8. Record a separate maintainer decision for the exact document, venue and
   submission commit after the technical gates pass.

## Evidence still required

Submission remains blocked by the applicable security, interoperability and
service-port gates in `STANDARDS_READINESS.md`. Completing governance names and
contacts does not waive those gates. The first document remains an individual
working draft unless and until a venue adopts it through its own process.

## Completion method

Copy `submission-governance-decision-v1.json`, complete only public and
consented information, and validate it with:

```bash
python3 tools/check_submission_governance_decision.py <completed-record.json>
```

The repository may retain the completed public record after consent. Private
addresses, identity documents, credentials, engagement terms and private
correspondence must remain outside it.

## Acceptance boundary

Issue #47 can close when the completed record identifies a real backup,
documents change control and succession, records consent to public contact
details, and preserves a separate explicit submission decision. Closure still
does not authorize an upload, mailing-list post or IANA application.
