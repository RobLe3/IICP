#!/usr/bin/env python3
"""Inventory intent-like URNs across the public IICP repositories.

The audit classifies observations; it never promotes an identifier into the
canonical registry. Missing sibling repositories are skipped so CI can still
verify that every occurrence in the specification repository is dispositioned.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
OUTPUT = ROOT / "registry/source-classification.json"
REPOSITORIES = (
    "IICP",
    "iicp-directory-php",
    "iicp-directory-rust",
    "iicp-client-python",
    "iicp-client-typescript",
    "iicp-client-rust",
    "iicp-web-node",
)
PATTERN = r"urn:iicp:intent:[A-Za-z0-9_:/.-]+:v[0-9]+"
PATTERN_BYTES = re.compile(PATTERN.encode("ascii"))
POLICY_PARTS = (
    "biometric",
    "credit:decision",
    "criminal-risk",
    "emotion:workplace",
    "employment:hiring",
    "fraud:detect",
    "medical:diagnosis",
    "mcp:bash",
    "mcp:read_file",
    "mcp:web_search",
    "mcp:write_file",
    "social-scoring",
    "tool:shell",
)
NEGATIVE_PARTS = ("bogus", "fancy", "missing", "nope", "unregistered")


def occurrences() -> dict[str, dict[str, set[str]]]:
    found: dict[str, dict[str, set[str]]] = {}
    for name in REPOSITORIES:
        repository = WORKSPACE / name
        if not repository.is_dir():
            continue
        result = subprocess.run(
            ["git", "-C", str(repository), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip() or f"git ls-files failed for {name}")
        for raw_relative in result.stdout.split(b"\0"):
            if not raw_relative:
                continue
            relative = raw_relative.decode("utf-8", errors="surrogateescape")
            if relative == "registry/source-classification.json":
                continue
            path = repository / relative
            if not path.is_file() or path.is_symlink():
                continue
            try:
                content = path.read_bytes()
            except OSError:
                continue
            for match in PATTERN_BYTES.finditer(content):
                urn = match.group().decode("ascii")
                found.setdefault(urn, {}).setdefault(name, set()).add(relative)
    return found


def classify(urn: str, canonical: set[str]) -> tuple[str, str]:
    if urn in canonical:
        return "canonical", "present in registry/intents.json"
    lowered = urn.lower()
    if any(part in lowered for part in POLICY_PARTS):
        return "policy-test", "risk/prohibition or authorization-policy example; not registry vocabulary"
    if ":x." in lowered or ":x:" in lowered or "acme" in lowered or "my-platform" in lowered:
        return "custom-example", "implementation-defined namespace example; not promoted"
    if any(part in lowered for part in NEGATIVE_PARTS) or not re.fullmatch(
        r"urn:iicp:intent:[a-z0-9_:/.-]+:v[1-9][0-9]*", urn
    ):
        return "negative-test", "invalid, unknown or rejection-path fixture"
    return "candidate-unregistered", "observed outside the canonical registry; requires separate review and evidence"


def render() -> dict:
    canonical_doc = json.loads((ROOT / "registry/intents.json").read_text())
    canonical = {entry["urn"] for entry in canonical_doc["intents"]}
    records = []
    for urn, repositories in sorted(occurrences().items()):
        classification, disposition = classify(urn, canonical)
        records.append({
            "urn": urn,
            "classification": classification,
            "disposition": disposition,
            "sources": [
                {"repository": repository, "paths": sorted(paths)}
                for repository, paths in sorted(repositories.items())
            ],
        })
    return {
        "version": "1.0.0",
        "generated_at": "2026-08-08",
        "repositories": list(REPOSITORIES),
        "description": "Reviewed source inventory. Observation does not grant registry status.",
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    document = render()
    rendered = json.dumps(document, indent=2) + "\n"
    if args.check:
        if not OUTPUT.exists():
            raise SystemExit("intent source classification is missing")
        expected = json.loads(OUTPUT.read_text())
        expected_records = {record["urn"]: record for record in expected.get("records", [])}
        for record in document["records"]:
            prior = expected_records.get(record["urn"])
            if prior is None:
                raise SystemExit(f"unclassified intent observation: {record['urn']}")
            if (prior["classification"], prior["disposition"]) != (
                record["classification"], record["disposition"]
            ):
                raise SystemExit(f"classification drift: {record['urn']}")
            prior_sources = {
                (source["repository"], path)
                for source in prior["sources"]
                for path in source["paths"]
            }
            for source in record["sources"]:
                for path in source["paths"]:
                    if (source["repository"], path) not in prior_sources:
                        raise SystemExit(
                            f"unclassified intent source: {record['urn']} at "
                            f"{source['repository']}/{path}"
                        )
        print("intent source classification is current")
    else:
        OUTPUT.write_text(rendered)
        print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
