from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runner import (
    DEFAULT_PROFILE,
    PROFILE_FILES,
    run,
    run_dispatch_ticket_fixture,
    run_dispatch_ticket_trust_v2_fixture,
    run_dispatch_ticket_trust_v2_semantics_fixture,
    sign_result,
    verify_result,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="iicp-conformance")
    commands = result.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="Run a black-box conformance profile")
    run_parser.add_argument("--target", required=True, help="Directory base URL")
    run_parser.add_argument(
        "--profile",
        choices=tuple(PROFILE_FILES),
        default=DEFAULT_PROFILE,
        help="Bundled digest-addressed profile to execute",
    )
    run_parser.add_argument("--output", type=Path, help="Write the content-free JSON result")
    run_parser.add_argument(
        "--evidence-class",
        choices=("self-attested", "project-verified", "independent"),
        default="self-attested",
    )
    run_parser.add_argument("--timeout", type=float, default=5.0)
    run_parser.add_argument("--signing-key-file", type=Path)
    ticket_parser = commands.add_parser(
        "verify-dispatch-ticket-fixture",
        help="Run offline canonical dispatch-ticket signature vectors",
    )
    ticket_parser.add_argument("--output", type=Path, help="Write the content-free JSON result")
    ticket_parser.add_argument(
        "--evidence-class",
        choices=("self-attested", "project-verified", "independent"),
        default="self-attested",
    )
    ticket_parser.add_argument("--signing-key-file", type=Path)
    trust_ticket_parser = commands.add_parser(
        "verify-dispatch-ticket-trust-v2-fixture",
        help="Run offline pre-normative v2 dispatch-ticket trust vectors",
    )
    trust_ticket_parser.add_argument(
        "--output", type=Path, help="Write the content-free JSON result"
    )
    trust_ticket_parser.add_argument(
        "--evidence-class",
        choices=("self-attested", "project-verified", "independent"),
        default="self-attested",
    )
    trust_ticket_parser.add_argument("--signing-key-file", type=Path)
    trust_semantics_parser = commands.add_parser(
        "verify-dispatch-ticket-trust-v2-semantics-fixture",
        help="Run offline pre-normative v2 trust downgrade semantics",
    )
    trust_semantics_parser.add_argument(
        "--output", type=Path, help="Write the content-free JSON result"
    )
    trust_semantics_parser.add_argument(
        "--evidence-class",
        choices=("self-attested", "project-verified", "independent"),
        default="self-attested",
    )
    trust_semantics_parser.add_argument("--signing-key-file", type=Path)
    verify_parser = commands.add_parser("verify", help="Verify a result bundle offline")
    verify_parser.add_argument("result", type=Path)
    verify_parser.add_argument("--require-signature", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command in {
        "verify-dispatch-ticket-fixture",
        "verify-dispatch-ticket-trust-v2-fixture",
        "verify-dispatch-ticket-trust-v2-semantics-fixture",
    }:
        result = (
            run_dispatch_ticket_fixture(evidence_class=args.evidence_class)
            if args.command == "verify-dispatch-ticket-fixture"
            else run_dispatch_ticket_trust_v2_fixture(
                evidence_class=args.evidence_class
            )
            if args.command == "verify-dispatch-ticket-trust-v2-fixture"
            else run_dispatch_ticket_trust_v2_semantics_fixture(
                evidence_class=args.evidence_class
            )
        )
        if args.signing_key_file:
            result = sign_result(result, args.signing_key_file.read_text(encoding="utf-8"))
        encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8")
        else:
            sys.stdout.write(encoded)
        return 0 if result["summary"]["failed"] == 0 else 1
    if args.command == "verify":
        value = json.loads(args.result.read_text(encoding="utf-8"))
        verification = verify_result(value, require_signature=args.require_signature)
        sys.stdout.write(json.dumps(verification, indent=2, sort_keys=True) + "\n")
        return 0 if verification["valid"] else 1
    if args.timeout <= 0:
        parser().error("--timeout must be greater than zero")
    result = run(
        args.target,
        evidence_class=args.evidence_class,
        timeout=args.timeout,
        profile=args.profile,
    )
    if args.signing_key_file:
        result = sign_result(result, args.signing_key_file.read_text(encoding="utf-8"))
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0 if result["summary"]["failed"] == 0 else 1
