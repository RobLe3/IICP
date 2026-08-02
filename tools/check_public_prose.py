#!/usr/bin/env python3
"""Check public prose for objective defects and passages needing human review.

This is a writing-quality tool, not an authorship classifier.  Objective
findings can fail a gate; stylistic and substance heuristics remain advisory.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    path: str
    line: int | None = None
    excerpt: str | None = None


OBJECTIVE_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    (
        "leaked-citation-marker",
        "Remove internal retrieval/chatbot citation markup and verify the intended source.",
        re.compile(
            r"(?:contentReference|oaicite|oai_citation|turn\d+(?:search|news|file|image)\d+|"
            r"\[cite:\s*\d+\]|\[span_\d+\]|grok_(?:card|render)|ppl-ai-file-upload|attached_file)",
            re.I,
        ),
    ),
    (
        "chatbot-tracking-url",
        "Remove chatbot attribution/tracking parameters from the public URL.",
        re.compile(r"[?&]utm_source=(?:chatgpt\.com|openai|perplexity)(?:[&#\s\"')]|$)", re.I),
    ),
    (
        "broken-citation-placeholder",
        "Replace the citation placeholder with a real source or remove the claim.",
        re.compile(r"\[(?:citation needed|source needed|insert (?:source|link)|TODO: cite)\]", re.I),
    ),
)

ADVISORY_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    (
        "formulaic-contrast",
        "Review the formulaic contrast and state the relationship directly.",
        re.compile(r"\bnot\s+(?:just|only|merely)\b.{0,100}\bbut\s+(?:also\s+)?\b", re.I),
    ),
    (
        "generic-significance",
        "Replace generic significance language with the concrete result and its evidence.",
        re.compile(
            r"\b(?:pivotal moment|crucial role|key turning point|lasting legacy|indelible mark|"
            r"testament to|underscores? (?:its|the) (?:importance|significance)|"
            r"shap(?:es|ed|ing) the (?:evolving )?landscape)\b",
            re.I,
        ),
    ),
    (
        "promotional-tone",
        "Replace promotional wording with a specific mechanism or observable result.",
        re.compile(
            r"\b(?:revolutionary|game[- ]changing|groundbreaking|world[- ]class|"
            r"cutting[- ]edge|state[- ]of[- ]the[- ]art|unprecedented)\b",
            re.I,
        ),
    ),
    (
        "vague-attribution",
        "Name the source or remove the vague attribution.",
        re.compile(
            r"\b(?:critics|observers|experts|analysts|commentators|some reports|"
            r"many believe|it is widely (?:believed|recognized|regarded))\b",
            re.I,
        ),
    ),
    (
        "generic-outlook",
        "Check whether this outlook sentence adds a concrete, sourced action or limitation.",
        re.compile(
            r"\b(?:despite (?:these|its|the) challenges|future prospects|looking ahead|"
            r"continues? to evolve|remains? to be seen)\b",
            re.I,
        ),
    ),
)

STOCK_WORDS = re.compile(
    r"\b(?:aligns?|bolstered|crucial|delve|emphasiz(?:e|es|ed|ing)|enhanc(?:e|es|ed|ing)|"
    r"foster(?:s|ed|ing)?|highlight(?:s|ed|ing)?|interplay|intricat(?:e|ely)|"
    r"landscape|meticulous(?:ly)?|pivotal|robust|showcas(?:e|es|ed|ing)|"
    r"tapestry|testament|underscor(?:e|es|ed|ing)|valuable|vibrant)\b",
    re.I,
)

CONCRETE_ANCHOR = re.compile(
    r"(?:https?://|`[^`]+`|\b\d+(?:\.\d+)?%?\b|\b20\d{2}-\d{2}-\d{2}\b|"
    r"\b(?:IICP|PHP|Rust|Python|TypeScript|SDK|API|HTTP|JSON|MCP|A2A|GDPR|IETF|IANA)\b|"
    r"(?:^|\s)[#/][A-Za-z0-9_.-]+)",
    re.I,
)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def excerpt(value: str, limit: int = 150) -> str:
    compact = re.sub(r"\s+", " ", value).strip()
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def prose_only(text: str) -> str:
    """Blank fenced code, indented code, imports and direct quotations."""
    text = re.sub(r"```.*?```", lambda match: "\n" * match.group(0).count("\n"), text, flags=re.S)
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if line.startswith(("    ", "\t")) or stripped.startswith((">", "import ", "export ")):
            kept.append("")
        else:
            kept.append(line)
    return "\n".join(kept)


def paragraphs(text: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    offset = 0
    for match in re.finditer(r"(?:^|\n\s*\n)([^\n].*?)(?=\n\s*\n|\Z)", text, re.S):
        value = match.group(1).strip()
        if value and not value.startswith(("#", "|", "- ", "* ")):
            result.append((line_number(text, match.start(1)), value))
        offset = match.end()
    del offset
    return result


def lint_text(text: str, path: str) -> list[Finding]:
    prose = prose_only(text)
    findings: list[Finding] = []
    for code, message, pattern in OBJECTIVE_PATTERNS:
        for match in pattern.finditer(prose):
            findings.append(Finding(code, "error", message, path, line_number(prose, match.start()), excerpt(match.group(0))))
    for code, message, pattern in ADVISORY_PATTERNS:
        for match in pattern.finditer(prose):
            findings.append(Finding(code, "advisory", message, path, line_number(prose, match.start()), excerpt(match.group(0))))

    words = re.findall(r"\b[\w'-]+\b", prose)
    stock = list(STOCK_WORDS.finditer(prose))
    distinct = {match.group(0).lower() for match in stock}
    threshold = max(5, round(len(words) / 100))
    if len(stock) >= threshold and len(distinct) >= 4:
        findings.append(
            Finding(
                "stock-vocabulary-density",
                "advisory",
                f"Review {len(stock)} uses of stock abstract vocabulary ({len(distinct)} distinct terms).",
                path,
            )
        )

    for line, paragraph in paragraphs(prose):
        paragraph_words = re.findall(r"\b[\w'-]+\b", paragraph)
        if len(paragraph_words) >= 55 and len(STOCK_WORDS.findall(paragraph)) >= 3 and not CONCRETE_ANCHOR.search(paragraph):
            findings.append(
                Finding(
                    "concrete-anchor-missing",
                    "advisory",
                    "This long abstract passage has no date, quantity, component, mechanism, link, code term or explicit standard; verify that it gives the reader usable information.",
                    path,
                    line,
                    excerpt(paragraph),
                )
            )

    em_dashes = prose.count("—")
    if len(words) >= 100 and em_dashes >= max(4, round(len(words) / 125)):
        findings.append(Finding("em-dash-density", "advisory", f"Review {em_dashes} em dashes across {len(words)} words.", path))
    bold = len(re.findall(r"\*\*[^*\n]+\*\*", prose))
    if bold >= 6:
        findings.append(Finding("boldface-density", "advisory", f"Review whether all {bold} bold spans help navigation.", path))
    return findings


def normalized_paragraph(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def duplicate_findings(documents: list[tuple[str, str]]) -> list[Finding]:
    seen: dict[str, tuple[str, int]] = {}
    findings: list[Finding] = []
    for path, text in documents:
        for line, paragraph in paragraphs(prose_only(text)):
            normalized = normalized_paragraph(paragraph)
            if len(normalized.split()) < 35:
                continue
            if normalized in seen and seen[normalized][0] != path:
                first_path, first_line = seen[normalized]
                findings.append(
                    Finding(
                        "duplicate-public-prose",
                        "advisory",
                        f"Substantial prose duplicates {first_path}:{first_line}; keep one authority or verify both copies deliberately.",
                        path,
                        line,
                        excerpt(paragraph),
                    )
                )
            else:
                seen[normalized] = (path, line)
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", help="emit machine-readable findings")
    parser.add_argument("--strict", action="store_true", help="fail only when objective error findings exist")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    documents: list[tuple[str, str]] = []
    try:
        for path in args.paths:
            documents.append((str(path), path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError) as error:
        print(f"check_public_prose: {error}", file=sys.stderr)
        return 2

    findings = [finding for path, text in documents for finding in lint_text(text, path)]
    findings.extend(duplicate_findings(documents))
    findings.sort(key=lambda item: (item.path, item.line is None, item.line or 0, item.code))

    if args.json:
        print(json.dumps([asdict(item) for item in findings], indent=2, ensure_ascii=False))
    else:
        for finding in findings:
            location = f":{finding.line}" if finding.line else ""
            detail = f" [{finding.excerpt}]" if finding.excerpt else ""
            print(f"{finding.severity}: {finding.path}{location}: {finding.code}: {finding.message}{detail}")
        print(f"{len(findings)} finding(s): {sum(item.severity == 'error' for item in findings)} error, {sum(item.severity == 'advisory' for item in findings)} advisory")

    return 1 if args.strict and any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
