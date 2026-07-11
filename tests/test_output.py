import copy
import json
import unittest
from pathlib import Path

from medical_race.output import DEFAULT_SCHEMAS, serialize_entities, validate_entities


FIXTURE = Path("tests/fixtures/official_example.json")


class OutputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_official_entities_round_trip_with_unicode_and_duplicates(self):
        serialized = serialize_entities(self.example["raw_text"], self.example["entities"])
        entities = json.loads(serialized)
        self.assertEqual(entities, self.example["entities"])
        self.assertIn("đau nhức", serialized)
        self.assertEqual(serialized.count('"táo bón"'), 2)
        validate_entities(self.example["raw_text"], entities)

    def test_rejects_missing_candidate_empty_candidate_and_extra_field(self):
        entity = copy.deepcopy(self.example["entities"][0])
        del entity["candidates"]
        with self.assertRaisesRegex(ValueError, "entity 0.*missing"):
            validate_entities(self.example["raw_text"], [entity])
        entity = copy.deepcopy(self.example["entities"][0])
        entity["candidates"] = []
        with self.assertRaisesRegex(ValueError, "entity 0.*candidates"):
            validate_entities(self.example["raw_text"], [entity])
        entity = copy.deepcopy(self.example["entities"][0])
        entity["relations"] = []
        with self.assertRaisesRegex(ValueError, "entity 0.*extra"):
            validate_entities(self.example["raw_text"], [entity])

    def test_rejects_unknown_or_duplicate_list_values(self):
        entity = copy.deepcopy(self.example["entities"][0])
        entity["assertions"] = ["unknown"]
        with self.assertRaisesRegex(ValueError, "assertions"):
            validate_entities(self.example["raw_text"], [entity])
        entity = copy.deepcopy(self.example["entities"][0])
        entity["candidates"] = ["308135", "308135"]
        with self.assertRaisesRegex(ValueError, "candidates"):
            validate_entities(self.example["raw_text"], [entity])

    def test_rejects_boolean_and_inclusive_positions(self):
        entity = copy.deepcopy(self.example["entities"][0])
        entity["position"] = [True, 83]
        with self.assertRaisesRegex(ValueError, "position"):
            validate_entities(self.example["raw_text"], [entity])
        entity = copy.deepcopy(self.example["entities"][4])
        entity["position"] = [196, 197]
        with self.assertRaisesRegex(ValueError, "offset mismatch"):
            validate_entities(self.example["raw_text"], [entity])

    def test_rejects_unknown_type_and_non_list_top_level(self):
        entity = copy.deepcopy(self.example["entities"][0])
        entity["type"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "unknown type"):
            validate_entities(self.example["raw_text"], [entity])
        with self.assertRaisesRegex(ValueError, "entities must be a list"):
            validate_entities(self.example["raw_text"], tuple())

    def test_laboratory_schema_is_configurable_without_extra_code_path(self):
        raw = "kali"
        entity = {
            "text": "kali",
            "type": "TÊN_XÉT_NGHIỆM",
            "assertions": [],
            "position": [0, 4],
        }
        schemas = dict(DEFAULT_SCHEMAS)
        schemas["TÊN_XÉT_NGHIỆM"] = ("text", "type", "assertions", "position")
        validate_entities(raw, [entity], schemas)
        with self.assertRaisesRegex(ValueError, "extra"):
            validate_entities(raw, [entity])


if __name__ == "__main__":
    unittest.main()
