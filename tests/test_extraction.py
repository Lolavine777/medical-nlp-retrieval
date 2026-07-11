import json
import unittest
from pathlib import Path

from medical_race.extraction.drugs import extract_drugs
from medical_race.extraction.labs import extract_labs


FIXTURE = Path("tests/fixtures/official_example.json")


class DrugExtractionTest(unittest.TestCase):
    def test_reproduces_all_official_drug_spans_without_ontology_codes(self):
        example = json.loads(FIXTURE.read_text(encoding="utf-8"))
        expected = [
            entity["text"]
            for entity in example["entities"]
            if entity["type"] == "THUỐC"
        ]

        spans = extract_drugs(example["raw_text"])

        self.assertEqual([span.text for span in spans], expected)
        for span in spans:
            self.assertEqual(example["raw_text"][span.start : span.end], span.text)

    def test_extracts_inline_medication_and_removes_status_cue(self):
        raw = "Thuốc trước khi nhập viện: đang dùng eliquis (cho rung nhĩ)"
        self.assertEqual([span.text for span in extract_drugs(raw)], ["eliquis"])


class LabExtractionTest(unittest.TestCase):
    def test_extracts_decimal_comma_unit_and_exact_offsets(self):
        raw = "Kết quả xét nghiệm\r\n- kali là 2,4 mmol/L\r\n"
        result = extract_labs(raw)[0]
        self.assertEqual((result.name.text, result.value.text), ("kali", "2,4 mmol/L"))
        self.assertEqual(raw[result.name.start : result.name.end], result.name.text)
        self.assertEqual(raw[result.value.start : result.value.end], result.value.text)

    def test_extracts_multiple_name_result_pairs_from_one_line(self):
        raw = "Kết quả xét nghiệm\n- alt là 176 và ast là 287"
        self.assertEqual(
            [(item.name.text, item.value.text) for item in extract_labs(raw)],
            [("alt", "176"), ("ast", "287")],
        )

    def test_extracts_range_and_qualitative_result(self):
        raw = (
            "Kết quả xét nghiệm\n"
            "- creatinine ổn định ở mức 1.4-1.6 mg/dL\n"
            "- bảng công thức máu bình thường"
        )
        self.assertEqual(
            [(item.name.text, item.value.text) for item in extract_labs(raw)],
            [("creatinine", "1.4-1.6 mg/dL"), ("bảng công thức máu", "bình thường")],
        )


if __name__ == "__main__":
    unittest.main()
