#!/usr/bin/env python3
"""Build and clean-install the standalone conformance runner without publishing it.

The preflight is intentionally local-only. It verifies that the candidate source,
wheel and source distribution can each run every bundled offline profile from a
clean working directory. It neither uploads artifacts nor labels any output as
independent evidence.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Final

OFFLINE_COMMANDS: Final[tuple[str, ...]] = (
    "verify-dispatch-ticket-fixture",
    "verify-dispatch-ticket-trust-v2-fixture",
    "verify-dispatch-ticket-trust-v2-semantics-fixture",
    "verify-policy-refusal-fixture",
    "verify-federation-chain-fixture",
)
ARTIFACT_KINDS: Final[tuple[str, ...]] = ("source", "wheel", "sdist")


def run(command: list[str], *, cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if completed.returncode:
        print(f"preflight command failed: {' '.join(command)}", file=sys.stderr)
        if completed.stdout:
            print(completed.stdout, file=sys.stderr, end="")
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end="")
        completed.check_returncode()


def venv_python(environment: Path) -> Path:
    return environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def install_and_verify(*, artifact: Path, kind: str, package_root: Path, workspace: Path) -> dict[str, object]:
    environment = workspace / f"venv-{kind}"
    venv.EnvBuilder(with_pip=True, clear=True).create(environment)
    python = venv_python(environment)
    install_target = str(package_root) if kind == "source" else str(artifact)
    run([str(python), "-m", "pip", "install", f"{install_target}[signing]"], cwd=workspace)

    outputs: dict[str, object] = {}
    for command in OFFLINE_COMMANDS:
        output = workspace / f"{kind}-{command}.json"
        run(
            [
                str(python),
                "-m",
                "iicp_conformance",
                command,
                "--evidence-class",
                "self-attested",
                "--output",
                str(output),
            ],
            cwd=workspace,
        )
        run([str(python), "-m", "iicp_conformance", "verify", str(output)], cwd=workspace)
        value = json.loads(output.read_text(encoding="utf-8"))
        if value.get("evidence_class") != "self-attested" or value.get("content_free") is not True:
            raise RuntimeError(f"{kind} {command} did not emit a self-attested content-free result")
        outputs[command] = {
            "profile": value.get("profile"),
            "fixture_digest": value.get("fixture_digest"),
            "summary": value.get("summary"),
            "result_ids": [entry.get("test_id", entry.get("id", entry.get("name"))) for entry in value.get("results", [])],
        }
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep-workdir",
        action="store_true",
        help="preserve temporary build and installation files for inspection",
    )
    args = parser.parse_args(argv)

    package_root = Path(__file__).resolve().parents[1]
    repository_root = package_root.parent
    with tempfile.TemporaryDirectory(prefix="iicp-conformance-preflight-") as temporary:
        workspace = Path(temporary)
        dist = workspace / "dist"
        run([sys.executable, "-m", "build", str(package_root), "--outdir", str(dist)], cwd=workspace)
        artifacts = sorted(dist.iterdir())
        wheels = [path for path in artifacts if path.suffix == ".whl"]
        sdists = [path for path in artifacts if path.name.endswith(".tar.gz")]
        if len(wheels) != 1 or len(sdists) != 1:
            raise RuntimeError("expected exactly one wheel and one source distribution")
        run([sys.executable, "-m", "twine", "check", *map(str, artifacts)], cwd=workspace)

        evidence = {
            "source": install_and_verify(
                artifact=package_root, kind="source", package_root=package_root, workspace=workspace
            ),
            "wheel": install_and_verify(
                artifact=wheels[0], kind="wheel", package_root=package_root, workspace=workspace
            ),
            "sdist": install_and_verify(
                artifact=sdists[0], kind="sdist", package_root=package_root, workspace=workspace
            ),
        }
        baseline = evidence["source"]
        if any(value != baseline for value in evidence.values()):
            raise RuntimeError("source, wheel and sdist offline-profile evidence differs")
        print(
            json.dumps(
                {
                    "status": "passed",
                    "artifacts": [path.name for path in artifacts],
                    "artifact_kinds": ARTIFACT_KINDS,
                    "offline_commands": OFFLINE_COMMANDS,
                    "evidence_class": "self-attested",
                    "content_free": True,
                    "published": False,
                    "profiles": baseline,
                },
                indent=2,
                sort_keys=True,
            )
        )
        if args.keep_workdir:
            retained = repository_root / ".preflight-retained"
            if retained.exists():
                shutil.rmtree(retained)
            shutil.copytree(workspace, retained)
            print(f"retained workdir: {retained}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
