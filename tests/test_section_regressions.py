import unittest

from medical_race.extraction.drugs import extract_drugs
from medical_race.line_roles import parse_line_roles
from medical_race.sections import parse_sections


class SectionRegressionTest(unittest.TestCase):
    def test_observed_duplicate_word_header_ends_medication_section(self):
        raw = (
            "Thuốc trước khi nhập viện lần này\n"
            "- cipro\n"
            "2. Tiền sử bệnh bệnh hiện tại\n"
            "Lý do nhập viện: đau bụng"
        )
        self.assertEqual(
            [section.kind for section in parse_sections(raw)],
            ["medications", "current_illness", "admission_reason"],
        )
        self.assertEqual([span.text for span in extract_drugs(raw)], ["cipro"])

    def test_imaging_result_header_ends_laboratory_role(self):
        raw = (
            "Kết quả xét nghiệm: creatinine 1.2\n"
            "Kết quả chẩn đoán hình ảnh: chụp ct bình thường"
        )
        self.assertEqual(
            [(line.role, line.text) for line in parse_line_roles(raw)],
            [("laboratory", "creatinine 1.2"), ("content", "chụp ct bình thường")],
        )


if __name__ == "__main__":
    unittest.main()
