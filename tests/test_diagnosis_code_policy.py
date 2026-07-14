import unittest

from medical_race.extraction.diagnoses import extract_diagnoses
from medical_race.linking.icd10 import ICD10Term, build_term_index


class DiagnosisCodePolicyTests(unittest.TestCase):
    def test_rejects_symptom_chapter_and_resistance_supplement_codes(self):
        raw = "Tiền sử bệnh\nKhó thở\nKháng vancomycin\nViêm phổi\n"
        index = build_term_index(
            (
                ICD10Term("R06.0", "Khó thở", "disease", True),
                ICD10Term("U83.0", "Kháng vancomycin", "disease", True),
                ICD10Term("J18.9", "Viêm phổi", "disease", True),
            )
        )

        matches = extract_diagnoses(raw, index)

        self.assertEqual([(match.text, match.code) for match in matches], [("Viêm phổi", "J18.9")])


if __name__ == "__main__":
    unittest.main()
