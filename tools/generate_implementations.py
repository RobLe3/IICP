#!/usr/bin/env python3
"""Validate the IICP repository registry and render its human-readable index."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ecosystem" / "repositories.json"
OUTPUT = ROOT / "IMPLEMENTATIONS.md"
CURRENT_JSON = ROOT / "ecosystem" / "current-versions.json"
CURRENT_MARKDOWN = ROOT / "ecosystem" / "CURRENT_VERSIONS.md"
PUBLIC_JSON = ROOT / "ecosystem" / "public-repositories.json"
VISIBILITIES = {"public"}
LIFECYCLES = {
    "active",
    "experimental",
    "operator-preview",
    "publication-review",
    "restructuring",
    "archived",
    "developer-preview",
}


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
        "Git submodules. Private operations, website and development-method sources are",
        "not public build, conformance or governance dependencies.",
        "",
        "| Component | Authority | Language | Visibility | Lifecycle | Release |",
        "|---|---|---|---|---|---|",
    ]
    for item in data["repositories"]:
        release = item["release"] or "—"
        component = f"[{item['name']}]({item['url']})"
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


def public_projection(data: dict) -> dict:
    """Return the stable machine-readable public repository handoff."""
    fields = (
        "id",
        "name",
        "url",
        "authority",
        "language",
        "protocol",
        "lifecycle",
        "release",
        "package",
    )
    return {
        "schema": "iicp.public-repositories.v1",
        "generated_at": data["generated_at"],
        "repositories": [
            {field: item[field] for field in fields if field in item}
            for item in data["repositories"]
        ],
    }


def current_projection(data: dict) -> dict:
    components = {
        item["id"]: {
            "name": item["name"],
            "release": item["release"],
            "lifecycle": item["lifecycle"],
            "visibility": item["visibility"],
        }
        for item in data["repositories"]
        if item["release"] is not None
    }
    specification = components["specification"]
    return {
        "schema": "iicp.ecosystem-current-versions.v1",
        "generated_at": data["generated_at"],
        "protocol_suite_release": specification["release"],
        "wire_compatibility_baseline": data["repositories"][0]["protocol"] + ".0",
        "components": components,
    }


def render_current_markdown(projection: dict) -> str:
    components = projection["components"]
    ordered = (
        "specification",
        "directory-php",
        "directory-rust",
        "client-python",
        "client-typescript",
        "client-rust",
        "web-node",
        "management",
    )
    lines = [
        "# Current IICP version axes",
        "",
        "This file is generated from `ecosystem/repositories.json`. The numbers",
        "version different contracts and do not need to match.",
        "",
        "| Axis or component | Current value | Lifecycle |",
        "|---|---:|---|",
        f"| Protocol-suite release | {projection['protocol_suite_release']} | project-normative beta |",
        f"| Wire compatibility baseline | {projection['wire_compatibility_baseline']} | stable v1.9 line |",
    ]
    for component_id in ordered[1:]:
        component = components[component_id]
        lines.append(f"| {component['name']} | {component['release']} | {component['lifecycle']} |")
    lines += [
        "",
        "Deployment identifiers and observed live adoption are time-bound evidence and",
        "are intentionally not represented as release versions in this projection.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    data = load()
    rendered = render(data)
    projection = current_projection(data)
    repositories_projection = public_projection(data)
    rendered_projection = json.dumps(projection, indent=2, sort_keys=True) + "\n"
    rendered_repositories = json.dumps(repositories_projection, indent=2, sort_keys=True) + "\n"
    rendered_current_markdown = render_current_markdown(projection)
    if "--check" in __import__("sys").argv:
        assert OUTPUT.exists() and OUTPUT.read_text() == rendered, "IMPLEMENTATIONS.md is stale"
        assert CURRENT_JSON.exists() and CURRENT_JSON.read_text() == rendered_projection, "current-versions.json is stale"
        assert CURRENT_MARKDOWN.exists() and CURRENT_MARKDOWN.read_text() == rendered_current_markdown, "CURRENT_VERSIONS.md is stale"
        assert PUBLIC_JSON.exists() and PUBLIC_JSON.read_text() == rendered_repositories, "public-repositories.json is stale"
    else:
        OUTPUT.write_text(rendered)
        CURRENT_JSON.write_text(rendered_projection)
        CURRENT_MARKDOWN.write_text(rendered_current_markdown)
        PUBLIC_JSON.write_text(rendered_repositories)


if __name__ == "__main__":
    main()
