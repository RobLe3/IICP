from __future__ import annotations

import base64
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def matches(value: object, schema: dict) -> bool:
    if "oneOf" in schema:
        return sum(matches(value, branch) for branch in schema["oneOf"]) == 1
    expected = schema.get("type")
    if isinstance(expected, list):
        return any(matches(value, {**schema, "type": item}) for item in expected)
    if expected == "object":
        if not isinstance(value, dict):
            return False
        if any(field not in value for field in schema.get("required", [])):
            return False
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and any(key not in properties for key in value):
            return False
        return all(key not in properties or matches(item, properties[key]) for key, item in value.items())
    if expected == "array":
        return (
            isinstance(value, list)
            and len(value) >= schema.get("minItems", 0)
            and all(matches(item, schema.get("items", {})) for item in value)
        )
    if expected == "string" and not isinstance(value, str):
        return False
    if expected == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
        return False
    if expected == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
        return False
    if expected == "boolean" and not isinstance(value, bool):
        return False
    if expected == "null" and value is not None:
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            return False
        if "maximum" in schema and value > schema["maximum"]:
            return False
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        return False
    if schema.get("contentEncoding") == "base64" and isinstance(value, str):
        try:
            base64.b64decode(value, validate=True)
        except ValueError:
            return False
    return True


class IntentPayloadFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads((ROOT / "registry/intents.json").read_text())
        cls.fixture = json.loads((ROOT / "registry/fixtures/intent-payloads-v1.json").read_text())
        cls.entries = {entry["urn"]: entry for entry in cls.registry["intents"]}

    def test_cases_match_pinned_input_schemas(self) -> None:
        for case in self.fixture["cases"]:
            entry = self.entries[case["intent"]]
            schema = json.loads((ROOT / entry["schemas"]["input"]["path"]).read_text())
            self.assertEqual(case["valid"], matches(case["payload"], schema), case["id"])

    def test_every_active_intent_has_positive_and_negative_cases(self) -> None:
        by_intent: dict[str, set[bool]] = {}
        for case in self.fixture["cases"]:
            by_intent.setdefault(case["intent"], set()).add(case["valid"])
        for entry in self.registry["intents"]:
            if entry["status"] == "active":
                self.assertEqual({False, True}, by_intent.get(entry["urn"]), entry["urn"])


if __name__ == "__main__":
    unittest.main()
