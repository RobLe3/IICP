#!/usr/bin/env python3
"""Verify that public release and standards inputs have no private dependencies."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "spec/v1.9/release-integrity-manifest.json"
REVIEW_INPUTS = {
    "standards/REVIEWING.md",
    "standards/STANDARDS_READINESS.md",
    "standards/SUBMISSION_GOVERNANCE_DECISION.md",
    "standards/SECURITY_PRIVACY_OPERATIONAL_CONSIDERATIONS_2026-08-13.md",
    "standards/ietf/README.md",
    "standards/ietf/draft-roble-iicp-peer.md",
    "standards/ietf/evidence-matrix.md",
    "research/RESEARCH.md",
}
PATTERN_EXEMPTIONS = {
    "docs/governance/public-artifact-boundary.md",
    # Published negative vector: the generic /Users/operator path must remain
    # byte-stable because released directory parity contracts pin its digest.
    "fixtures/directory-implementation-metadata-v1.json",
    "tools/check_public_artifact_closure.py",
    "tools/test_public_artifact_closure.py",
}
TEXT_SUFFIXES = {".md", ".json", ".py", ".toml", ".yml", ".yaml", ".txt"}
PUBLIC_PROJECT_REPOSITORIES = {
    "IICP", "iicp-client-python", "iicp-client-rust", "iicp-client-typescript",
    "iicp-directory-php", "iicp-directory-rust", "iicp-management",
    "iicp-node-monitor", "iicp-web-node",
}
PROJECT_REPOSITORY = re.compile(
    r"(?:https://github\.com/RobLe3/|(?<![/A-Za-z0-9])RobLe3/)([A-Za-z0-9_.-]+)"
)
INTERNAL_PATH = re.compile(r"(?<![A-Za-z0-9_./:-])project/[A-Za-z0-9_.@/+-]+")
WORKSTATION_PATH = re.compile(r"(?:/Users/[^/\s]+/|/home/[^/\s]+/|[A-Za-z]:\\Users\\[^\\\s]+\\)")
PRIVATE_METHOD_MARKER = re.compile(
    r"(?:FORGE|WORK_QUEUE\.json|loop-prompt\.md|sub-loop|"
    r"(?:RESA|CORC|ADOPTION|ARCS|GRIT|WARDEN)\s+(?:loop|iter))"
)
MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]]*\])\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    message: str


def release_paths(root: Path) -> set[str]:
    manifest = json.loads((root / MANIFEST.relative_to(ROOT)).read_text(encoding="utf-8"))
    return set(manifest["files"]) | {"spec/v1.9/release-integrity-manifest.json"}


def tracked_public_paths(root: Path) -> set[str]:
    """Return tracked text artifacts for the optional whole-repository audit."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    paths: set[str] = set()
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = raw.decode("utf-8")
        if Path(relative).suffix.lower() in TEXT_SUFFIXES:
            paths.add(relative)
    return paths


def is_public_external(target: str) -> bool:
    parsed = urlsplit(target)
    return parsed.scheme in {"http", "https", "mailto", "urn"} or target.startswith("#")


def local_target_exists(source: Path, target: str, root: Path) -> bool:
    clean = target.split("#", 1)[0].split("?", 1)[0]
    if not clean or is_public_external(target):
        return True
    if clean.startswith("/"):
        return False
    return (source.parent / clean).resolve().is_relative_to(root.resolve()) and (source.parent / clean).resolve().exists()


def validate(root: Path = ROOT, paths: set[str] | None = None) -> list[Finding]:
    selected = paths if paths is not None else release_paths(root) | REVIEW_INPUTS
    findings: list[Finding] = []
    for relative in sorted(selected):
        source = root / relative
        if not source.is_file():
            findings.append(Finding(relative, 0, "required public artifact is missing"))
            continue
        if source.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), 1):
            if relative not in PATTERN_EXEMPTIONS:
                names = {name.removesuffix(".git") for name in PROJECT_REPOSITORY.findall(line)}
                unavailable = sorted(name for name in names if name not in PUBLIC_PROJECT_REPOSITORIES)
                if unavailable:
                    findings.append(Finding(relative, line_number, "depends on or names an unavailable repository"))
                if INTERNAL_PATH.search(line):
                    findings.append(Finding(relative, line_number, "depends on an unavailable internal project path"))
                if WORKSTATION_PATH.search(line):
                    findings.append(Finding(relative, line_number, "contains a workstation-local path"))
            if relative.startswith("research/") and PRIVATE_METHOD_MARKER.search(line):
                findings.append(Finding(relative, line_number, "exposes private development-method provenance"))
            if source.suffix.lower() == ".md":
                for match in MARKDOWN_LINK.finditer(line):
                    target = match.group(1).strip("<>")
                    if not local_target_exists(source, target, root):
                        findings.append(Finding(relative, line_number, f"unresolved local link: {target}"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", help="optional repository-relative paths")
    parser.add_argument(
        "--all-public",
        action="store_true",
        help="scan every tracked public text artifact, not only release/review inputs",
    )
    args = parser.parse_args()
    if args.paths and args.all_public:
        parser.error("paths and --all-public are mutually exclusive")
    selected = tracked_public_paths(ROOT) if args.all_public else (set(args.paths) if args.paths else None)
    findings = validate(ROOT, selected)
    if findings:
        for finding in findings:
            print(f"{finding.path}:{finding.line}: {finding.message}", file=sys.stderr)
        return 1
    count = len(selected if selected is not None else release_paths(ROOT) | REVIEW_INPUTS)
    print(f"public artifact closure passed: {count} self-contained artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
