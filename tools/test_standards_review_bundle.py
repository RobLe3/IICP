#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import posixpath
import re
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "standards/ietf/draft-roble-iicp-peer.md"


class StandardsReviewBundleTest(unittest.TestCase):
    def test_bundle_is_deterministic_and_self_describing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rendered = root / "rendered"
            rendered.mkdir()
            for suffix in ("xml", "txt", "html"):
                (rendered / f"{SOURCE.stem}.{suffix}").write_text(
                    f"test {suffix}\n", encoding="utf-8"
                )
            outputs = [root / "first", root / "second"]
            for output in outputs:
                subprocess.run(
                    [
                        "python3",
                        str(ROOT / "tools/build_standards_review_bundle.py"),
                        "--rendered-dir",
                        str(rendered),
                        "--output-dir",
                        str(output),
                    ],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            name = f"{SOURCE.stem}-review-bundle.zip"
            left = outputs[0] / name
            right = outputs[1] / name
            self.assertEqual(
                hashlib.sha256(left.read_bytes()).digest(),
                hashlib.sha256(right.read_bytes()).digest(),
            )

            prefix = f"{SOURCE.stem}-review-bundle/"
            with zipfile.ZipFile(left) as archive:
                names = set(archive.namelist())
                for required in (
                    "LICENSE",
                    "SECURITY.md",
                    "CONTINUATION.md",
                    "docs/governance/public-artifact-boundary.md",
                    "ecosystem/public-repositories.json",
                    "ecosystem/CURRENT_VERSIONS.md",
                    "pre1/README.md",
                    "pre1/feature-baseline-v1.json",
                    "spec/v1.9/release-integrity-manifest.json",
                    "tools/check_spec_release_integrity.py",
                    "tools/check_public_artifact_closure.py",
                    "docs/architecture/identifier-registry-v1.json",
                    "docs/architecture/effective-service-capability-v1.json",
                    "schemas/effective-capability-advertisement-v1.json",
                    "schemas/capability-requirements-v1.json",
                    "schemas/capability-refusal-v1.json",
                    "standards/REVIEWING.md",
                    "standards/IICP_PROTOCOL_POSITIONING.md",
                    "standards/PROTOCOL_COMPARISON_2026-08-15.md",
                    "standards/PROTOCOL_COMPARISON_2026-09-25.md",
                    "standards/EMERGING_SECURITY_SESSION_EVIDENCE_CROSSWALK_2026-09-25.md",
                    "standards/protocol-comparison-v1.json",
                    "standards/ietf/evidence-matrix.md",
                    f"standards/ietf/{SOURCE.name}",
                    f"rendered/{SOURCE.stem}.xml",
                    f"rendered/{SOURCE.stem}.txt",
                    f"rendered/{SOURCE.stem}.html",
                    "SHA256SUMS.json",
                ):
                    self.assertIn(prefix + required, names)
                manifest = json.loads(archive.read(prefix + "SHA256SUMS.json"))
                comparison = json.loads(archive.read(prefix + "standards/protocol-comparison-v1.json"))
                references = {
                    row[field]
                    for row in comparison["intent_routing_requirements"]
                    for field in ("iicp_reference", "fixture_reference")
                    if row.get(field)
                }
                self.assertTrue(references.issubset(manifest["files"]))
                for relative in manifest["files"]:
                    if not relative.endswith(".md"):
                        continue
                    markdown = archive.read(prefix + relative).decode("utf-8")
                    for target in re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", markdown):
                        target = target.split("#")[0].split(" ")[0]
                        if not target or target.startswith(("http:", "https:", "mailto:", "/")):
                            continue
                        linked = posixpath.normpath((Path(relative).parent / target).as_posix())
                        if (ROOT / linked).is_file():
                            self.assertIn(linked, manifest["files"], relative)
                for relative, expected in manifest["files"].items():
                    actual = hashlib.sha256(archive.read(prefix + relative)).hexdigest()
                    self.assertEqual(expected, actual, relative)


if __name__ == "__main__":
    unittest.main()
