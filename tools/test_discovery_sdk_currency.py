#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path


class DiscoverySdkCurrencyTest(unittest.TestCase):
    def test_language_specific_patch_keeps_common_baseline(self) -> None:
        from tools.check_discovery_sdk_currency import coordinated_baseline

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ecosystem").mkdir()
            (root / "ecosystem/releases.json").write_text(json.dumps({"releases": [
                {"id": "client-python", "version": "0.7.102"},
                {"id": "client-typescript", "version": "0.7.102"},
                {"id": "client-rust", "version": "0.7.103"},
            ]}))
            self.assertEqual(coordinated_baseline(root), "0.7.102")

    def test_current_catalog_and_fixture_agree(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["python3", str(root / "tools/check_discovery_sdk_currency.py")],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class SelectedDirectoryBindingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "parity").mkdir()
        (self.root / "compatibility").mkdir()
        (self.root / "VERSION").write_text("1.10.94\n")
        (self.root / "Cargo.toml").write_text('[package]\nversion = "0.1.17"\n')
        self.fixture = {"invariants": {"sdk_latest_known_version": "0.7.109"}}
        self.fixture_name = "discovery-evidence-v1.10.94.json"
        self.parity = {"contract_version": "v1.10.94", "authority": {"runtime_version": "v1.10.94"},
                       "discovery_evidence_fixture": self.fixture_name, "fixtures": {}}
        self.compatibility = {"implementation": {"flavor": "rust", "version": "0.1.17", "status": "operator_preview"}, "php_parity_baseline": {"version": "1.10.94"}, "contracts": {}}
        self.bind()

    def write_json(self, relative: str, data: dict) -> str:
        raw = (json.dumps(data, sort_keys=True) + "\n").encode()
        (self.root / relative).write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def bind(self) -> None:
        digest = self.write_json("parity/" + self.fixture_name, self.fixture)
        self.parity["fixtures"][self.fixture_name] = digest
        parity_digest = self.write_json("parity/contract-v1.10.94.json", self.parity)
        self.compatibility["contracts"] = {
            "discovery_evidence": {"path": "parity/" + self.fixture_name, "sha256": digest},
            "parity_manifest": {"path": "parity/contract-v1.10.94.json", "sha256": parity_digest},
        }
        self.write_json("compatibility/v0.1.17.json", self.compatibility)

    def version(self, flavor: str) -> str:
        from tools.check_discovery_sdk_currency import directory_fixture_version
        return directory_fixture_version(self.root, flavor)

    def test_both_current_bindings_ignore_historical_fixture(self) -> None:
        self.write_json("parity/discovery-evidence-v1.json", {"invariants": {"sdk_latest_known_version": "0.7.106"}})
        for flavor in ("php", "rust"):
            self.assertEqual(self.version(flavor), "0.7.109")

    def test_missing_current_manifest_does_not_fall_back(self) -> None:
        for flavor, path in (("php", "parity/contract-v1.10.94.json"), ("rust", "compatibility/v0.1.17.json")):
            with self.subTest(flavor=flavor):
                self.bind()
                (self.root / path).unlink()
                with self.assertRaises(FileNotFoundError):
                    self.version(flavor)

    def test_version_identity_mismatch_is_rejected(self) -> None:
        self.parity["contract_version"] = "v1.10.93"
        self.bind()
        with self.assertRaises(ValueError):
            self.version("php")
        self.compatibility["implementation"]["version"] = "0.1.16"
        self.write_json("compatibility/v0.1.17.json", self.compatibility)
        with self.assertRaises(ValueError):
            self.version("rust")

    def test_altered_selected_fixture_is_rejected_for_both(self) -> None:
        self.write_json("parity/" + self.fixture_name, {"invariants": {"sdk_latest_known_version": "0.7.106"}})
        for flavor in ("php", "rust"):
            with self.subTest(flavor=flavor), self.assertRaises(ValueError):
                self.version(flavor)

    def test_missing_or_malformed_role_is_rejected(self) -> None:
        for role in (None, [], "missing.json"):
            with self.subTest(role=role):
                self.parity["discovery_evidence_fixture"] = role
                self.bind()
                for flavor in ("php", "rust"):
                    with self.assertRaises((KeyError, ValueError)):
                        self.version(flavor)

    def test_duplicate_role_is_rejected(self) -> None:
        path = self.root / "parity/contract-v1.10.94.json"
        raw = path.read_text().replace('"discovery_evidence_fixture":', '"discovery_evidence_fixture": "foreign.json", "discovery_evidence_fixture":', 1)
        path.write_text(raw)
        with self.assertRaises(ValueError):
            self.version("php")

    def test_path_escape_is_rejected_for_both(self) -> None:
        for role in ("../escape.json", "/tmp/escape.json"):
            self.parity["discovery_evidence_fixture"] = role
            self.parity["fixtures"][role] = "a" * 64
            self.bind()
            for flavor in ("php", "rust"):
                with self.subTest(role=role, flavor=flavor), self.assertRaises(ValueError):
                    self.version(flavor)

    def test_symlink_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as external:
            target = Path(external) / "fixture.json"
            target.write_text(json.dumps(self.fixture))
            fixture = self.root / "parity" / self.fixture_name
            fixture.unlink()
            fixture.symlink_to(target)
            for flavor in ("php", "rust"):
                with self.subTest(flavor=flavor), self.assertRaises(ValueError):
                    self.version(flavor)

    def test_direct_and_nested_bindings_must_match(self) -> None:
        digest = self.write_json("parity/foreign.json", self.fixture)
        self.compatibility["contracts"]["discovery_evidence"] = {"path": "parity/foreign.json", "sha256": digest}
        self.write_json("compatibility/v0.1.17.json", self.compatibility)
        with self.assertRaises(ValueError):
            self.version("rust")

    def test_invalid_digest_is_rejected(self) -> None:
        for digest in (None, "bad", "A" * 64):
            self.parity["fixtures"][self.fixture_name] = digest
            self.write_json("parity/contract-v1.10.94.json", self.parity)
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                self.version("php")

    def test_unrelated_nested_corruption_is_not_ignored(self) -> None:
        nested = {"fixtures": {"leaf.json": self.write_json("parity/leaf.json", {"value": 1})}}
        self.parity["fixtures"]["nested.json"] = self.write_json("parity/nested.json", nested)
        self.bind()
        self.write_json("parity/leaf.json", {"value": 2})
        for flavor in ("php", "rust"):
            with self.subTest(flavor=flavor), self.assertRaises(ValueError):
                self.version(flavor)

    def test_rust_parity_baseline_identity_must_match(self) -> None:
        self.compatibility["php_parity_baseline"]["version"] = "1.10.93"
        self.write_json("compatibility/v0.1.17.json", self.compatibility)
        with self.assertRaises(ValueError):
            self.version("rust")

    def test_rust_parity_baseline_requires_strict_version_type(self) -> None:
        for version in (None, [], {}, True, "../1.10.94"):
            self.compatibility["php_parity_baseline"]["version"] = version
            self.write_json("compatibility/v0.1.17.json", self.compatibility)
            with self.subTest(version=version), self.assertRaises(ValueError):
                self.version("rust")

    def test_unsupported_source_version_is_rejected(self) -> None:
        (self.root / "VERSION").write_text("../1.10.94")
        with self.assertRaises(ValueError):
            self.version("php")
        (self.root / "Cargo.toml").write_text('[package]\nversion = "../0.1.17"\n')
        with self.assertRaises(ValueError):
            self.version("rust")


if __name__ == "__main__":
    unittest.main()
