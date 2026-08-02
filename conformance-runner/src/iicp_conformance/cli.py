from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runner import run, sign_result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="iicp-conformance")
    result.add_argument("--target", required=True, help="Directory base URL")
    result.add_argument("--output", type=Path, help="Write the content-free JSON result")
    result.add_argument(
        "--evidence-class",
        choices=("self-attested", "project-verified", "independent"),
        default="self-attested",
    )
    result.add_argument("--timeout", type=float, default=5.0)
    result.add_argument("--signing-key-file", type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.timeout <= 0:
        parser().error("--timeout must be greater than zero")
    result = run(
        args.target,
        evidence_class=args.evidence_class,
        timeout=args.timeout,
    )
    if args.signing_key_file:
        result = sign_result(result, args.signing_key_file.read_text(encoding="utf-8"))
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0 if result["summary"]["failed"] == 0 else 1
