#!/usr/bin/env python3
"""Validate the IICP repository registry and render its human-readable index."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ecosystem" / "repositories.json"
OUTPUT = ROOT / "IMPLEMENTATIONS.md"
VISIBILITIES = {"public", "private"}
LIFECYCLES = {"active", "experimental", "publication-review", "restructuring", "archived"}


def load() -> dict:
    data = json.loads(MANIFEST.read_text())
    assert data["schema_version"] == 1
    repos = data["repositories"]
    assert repos and len({item["id"] for item in repos}) == len(repos)
    assert len({item["url"] for item in repos}) == len(repos)
    for item in repos:
        assert item["visibility"] in VISIBILITIES
        assert item["lifecycle"] in LIFECYCLES
        assert item["url"].startswith("https://github.com/")
        assert item["authority"].strip()
    assert sum(item["id"] == "specification" for item in repos) == 1
    return data


def render(data: dict) -> str:
    lines = [
        "# Official IICP repositories",
        "",
        "This index is generated from `ecosystem/repositories.json`. Repositories are",
        "independently versioned; they are logical members of the IICP ecosystem, not",
        "Git submodules. Visibility describes source access, not protocol maturity.",
        "",
        "| Component | Authority | Language | Visibility | Lifecycle | Release |",
        "|---|---|---|---|---|---|",
    ]
    for item in data["repositories"]:
        release = item["release"] or "—"
        component = (
            f"[{item['name']}]({item['url']})"
            if item["visibility"] == "public"
            else f"{item['name']} (source private)"
        )
        lines.append(
            f"| {component} | {item['authority']} | "
            f"{item['language']} | {item['visibility']} | {item['lifecycle']} | {release} |"
        )
    lines += [
        "",
        "## Governance boundary",
        "",
        "The specification repository defines protocol semantics. Implementations may",
        "propose changes but cannot silently redefine the protocol. Production access,",
        "credentials, backups and operator data are not part of this public repository map.",
        "",
        "The planned GitHub organization uses the free plan. No paid GitHub feature is a",
        "conformance, build, publication or governance dependency.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    data = load()
    rendered = render(data)
    if "--check" in __import__("sys").argv:
        assert OUTPUT.exists() and OUTPUT.read_text() == rendered, "IMPLEMENTATIONS.md is stale"
    else:
        OUTPUT.write_text(rendered)


if __name__ == "__main__":
    main()
