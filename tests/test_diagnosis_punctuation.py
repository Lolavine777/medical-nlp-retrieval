import unittest

from medical_race.extraction.diagnoses import extract_diagnoses
from medical_race.linking.icd10 import ICD10Term, build_term_index


class DiagnosisPunctuationTests(unittest.TestCase):
    def test_preserves_terminal_parenthesis_from_official_term(self):
        raw = "Tiền sử bệnh\nTăng huyết áp vô căn (nguyên phát)\n"
        index = build_term_index(
            (
                ICD10Term(
                    "I10",
                    "Tăng huyết áp vô căn (nguyên phát)",
                    "disease",
                    True,
                ),
            )
        )

        matches = extract_diagnoses(raw, index)

        self.assertEqual(matches[0].text, "Tăng huyết áp vô căn (nguyên phát)")
        self.assertEqual(raw[matches[0].start : matches[0].end], matches[0].text)


if __name__ == "__main__":
    unittest.main()
