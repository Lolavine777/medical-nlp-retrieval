import json
import unittest
from collections import Counter
from pathlib import Path

from medical_race.offsets import validate_entity_offset


FIXTURE = Path("tests/fixtures/official_example.json")


class OffsetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_all_official_offsets_are_end_exclusive(self):
        for entity in self.example["entities"]:
            validate_entity_offset(self.example["raw_text"], entity)

    def test_repeated_mentions_are_preserved(self):
        counts = Counter(entity["text"] for entity in self.example["entities"])
        self.assertEqual(counts["táo bón"], 2)
        self.assertEqual(counts["lo âu"], 2)

    def test_observed_schema_is_type_dependent(self):
        drug = next(e for e in self.example["entities"] if e["type"] == "THUỐC")
        symptom = next(
            e for e in self.example["entities"] if e["type"] == "TRIỆU_CHỨNG"
        )
        self.assertIn("candidates", drug)
        self.assertNotIn("candidates", symptom)

    def test_rejects_inclusive_end_offset(self):
        with self.assertRaisesRegex(ValueError, "offset mismatch"):
            validate_entity_offset(
                self.example["raw_text"],
                {"text": "ho", "position": [196, 197]},
            )


if __name__ == "__main__":
    unittest.main()
