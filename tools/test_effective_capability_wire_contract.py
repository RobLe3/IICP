from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any
import unittest

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
ADVERTISEMENT_SCHEMA = ROOT / "schemas/effective-capability-advertisement-v1.json"
REQUIREMENTS_SCHEMA = ROOT / "schemas/capability-requirements-v1.json"
REFUSAL_SCHEMA = ROOT / "schemas/capability-refusal-v1.json"
FIXTURE = ROOT / "research/pre-normative-profiles/fixtures/effective-capability-v1.json"

CLASS_FIELDS = {
    "input_modality": "input_modalities",
    "output_modality": "output_modalities",
    "feature": "features",
    "execution_capability": "execution_capabilities",
    "profile": "supported_profiles",
    "extension": "extensions",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def vocabulary_knows(
    vocabulary: dict[str, list[str]], requirement: dict[str, str]
) -> bool:
    requirement_class = requirement["class"]
    if requirement_class == "extension":
        return False
    return requirement["id"] in vocabulary.get(requirement_class, [])


def variant_has(variant: dict[str, Any], requirement: dict[str, str]) -> bool:
    field = CLASS_FIELDS[requirement["class"]]
    values = variant.get(field, {})
    return requirement["id"] in values


def limit_matches(candidate: dict[str, Any], requirement: dict[str, Any]) -> bool:
    advertised = candidate.get("limits", {}).get(requirement["id"])
    if advertised is None or advertised["unit"] != requirement["unit"]:
        return False
    candidate_value = advertised["value"]
    requested_value = requirement["value"]
    return {
        "gte": candidate_value >= requested_value,
        "lte": candidate_value <= requested_value,
        "eq": candidate_value == requested_value,
    }[requirement["operator"]]


def is_stale(variant: dict[str, Any], evaluation_time: datetime) -> bool:
    valid_until = variant.get("claim_provenance", {}).get("valid_until")
    return bool(valid_until and parse_time(valid_until) < evaluation_time)


def match(
    fixture: dict[str, Any], scenario: dict[str, Any]
) -> dict[str, Any]:
    request = scenario["request"]
    requirements = request.get("requires", [])
    preferences = request.get("prefers", [])
    vocabulary = fixture["vocabulary"]

    unknown_required = [
        item for item in requirements if not vocabulary_knows(vocabulary, item)
    ]
    if unknown_required:
        return {"eligible": False, "code": "required_capability_unknown"}

    denied = scenario.get("policy_denials", [])
    if any(item in denied for item in requirements):
        return {"eligible": False, "code": "capability_policy_denied"}

    candidates = [
        item
        for item in fixture["advertisement"]["capabilities"]
        if item["intent"] == request["intent"]
    ]
    candidates_with_required_capabilities = [
        item
        for item in candidates
        if all(variant_has(item, requirement) for requirement in requirements)
    ]
    if not candidates_with_required_capabilities:
        return {"eligible": False, "code": "required_capability_unsupported"}

    evaluation_time = parse_time(
        scenario.get("evaluation_time", fixture["evaluation_time"])
    )
    fresh_candidates = [
        item
        for item in candidates_with_required_capabilities
        if not is_stale(item, evaluation_time)
    ]
    if not fresh_candidates:
        return {"eligible": False, "code": "required_capability_stale"}

    matched = [
        item
        for item in fresh_candidates
        if all(limit_matches(item, limit) for limit in request.get("limits", []))
    ]
    if not matched:
        return {"eligible": False, "code": "capability_limit_unsatisfied"}

    result: dict[str, Any] = {
        "eligible": True,
        "variant_ids": [item.get("variant_id") for item in matched],
    }
    if any(not vocabulary_knows(vocabulary, item) for item in preferences):
        result["preference_unavailable"] = True
    requested_extension = scenario.get("expected", {}).get("preserved_extension")
    if requested_extension:
        if any(requested_extension in item.get("extensions", {}) for item in matched):
            result["preserved_extension"] = requested_extension
    return result


class EffectiveCapabilityWireContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.advertisement_schema = load_json(ADVERTISEMENT_SCHEMA)
        cls.requirements_schema = load_json(REQUIREMENTS_SCHEMA)
        cls.refusal_schema = load_json(REFUSAL_SCHEMA)
        cls.fixture = load_json(FIXTURE)
        checker = FormatChecker()
        cls.advertisement_validator = Draft202012Validator(
            cls.advertisement_schema, format_checker=checker
        )
        cls.requirements_validator = Draft202012Validator(
            cls.requirements_schema, format_checker=checker
        )
        cls.refusal_validator = Draft202012Validator(cls.refusal_schema)

    def test_schemas_are_valid_draft_2020_12(self) -> None:
        for schema in (
            self.advertisement_schema,
            self.requirements_schema,
            self.refusal_schema,
        ):
            Draft202012Validator.check_schema(schema)

    def test_fixture_advertisement_and_requests_validate(self) -> None:
        self.advertisement_validator.validate(self.fixture["advertisement"])
        for scenario in self.fixture["matching_scenarios"]:
            self.requirements_validator.validate(scenario["request"])
            refusal = scenario["expected"].get("refusal")
            if refusal:
                self.refusal_validator.validate(refusal)

    def test_invalid_advertisements_are_rejected(self) -> None:
        for case in self.fixture["invalid_advertisements"]:
            with self.subTest(case=case["name"]):
                self.assertFalse(
                    self.advertisement_validator.is_valid(case["value"]),
                    case["name"],
                )

    def test_variant_identity_and_exact_duplicate_rules(self) -> None:
        capabilities = self.fixture["advertisement"]["capabilities"]
        identities: set[tuple[str, str]] = set()
        canonical: set[str] = set()
        for capability in capabilities:
            variant_id = capability.get("variant_id")
            if variant_id is not None:
                identity = (capability["intent"], variant_id)
                self.assertNotIn(identity, identities)
                identities.add(identity)
            encoded = json.dumps(capability, sort_keys=True, separators=(",", ":"))
            self.assertNotIn(encoded, canonical)
            canonical.add(encoded)

    def test_all_shared_matching_scenarios(self) -> None:
        for scenario in self.fixture["matching_scenarios"]:
            with self.subTest(scenario=scenario["name"]):
                actual = match(self.fixture, scenario)
                expected = scenario["expected"]
                self.assertEqual(expected["eligible"], actual["eligible"])
                if expected["eligible"]:
                    self.assertEqual(expected["variant_ids"], actual["variant_ids"])
                    for key in ("preference_unavailable", "preserved_extension"):
                        if key in expected:
                            self.assertEqual(expected[key], actual.get(key))
                else:
                    self.assertEqual(expected["refusal"]["code"], actual["code"])


if __name__ == "__main__":
    unittest.main()
