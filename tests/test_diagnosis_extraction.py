import unittest

from medical_race.extraction.diagnoses import extract_diagnoses
from medical_race.linking.icd10 import ICD10Term, build_term_index


def index(*values):
    return build_term_index(
        tuple(ICD10Term(code, name, "disease", True) for code, name in values)
    )


class DiagnosisExtractionTests(unittest.TestCase):
    def test_extracts_diagnosis_section_with_exact_raw_offset_and_stops_at_treatment(self):
        raw = (
            "Chẩn đoán\r\n"
            "Viêm tủy-xương mạn tính\r\n"
            "Điều trị:\r\n"
            "Viêm phổi\r\n"
        )
        terms = index(
            ("M86.6", "Viêm tủy xương mạn tính"),
            ("J18.9", "Viêm phổi"),
        )

        matches = extract_diagnoses(raw, terms)

        self.assertEqual([(match.text, match.code) for match in matches], [("Viêm tủy-xương mạn tính", "M86.6")])
        self.assertEqual(raw[matches[0].start : matches[0].end], matches[0].text)

    def test_extracts_inline_assessment_diagnosis_subblock_and_stops_at_next_heading(self):
        raw = (
            "Đánh giá tại bệnh viện\n"
            "Các phát hiện chẩn đoán khác: Bóc tách động mạch chủ\n"
            "Các thủ thuật đã thực hiện\n"
            "Viêm phổi\n"
        )
        terms = index(
            ("I71.0", "Bóc tách động mạch chủ"),
            ("J18.9", "Viêm phổi"),
        )

        matches = extract_diagnoses(raw, terms)

        self.assertEqual([(match.text, match.code) for match in matches], [("Bóc tách động mạch chủ", "I71.0")])

    def test_extracts_past_history_and_imaging_but_not_current_illness(self):
        raw = (
            "Tiền sử bệnh\n"
            "Tăng huyết áp\n"
            "Bệnh sử hiện tại\n"
            "Viêm phổi\n"
            "Chẩn đoán hình ảnh\n"
            "Không có thuyên tắc phổi\n"
        )
        terms = index(
            ("I10", "Tăng huyết áp"),
            ("J18.9", "Viêm phổi"),
            ("I26.9", "Thuyên tắc phổi"),
        )

        matches = extract_diagnoses(raw, terms)

        self.assertEqual(
            [(match.text, match.code) for match in matches],
            [("Tăng huyết áp", "I10"), ("thuyên tắc phổi", "I26.9")],
        )

    def test_preserves_distinct_duplicate_occurrences(self):
        raw = "Tiền sử bệnh\nViêm phổi, sau đó viêm phổi\n"
        terms = index(("J18.9", "Viêm phổi"))

        matches = extract_diagnoses(raw, terms)

        self.assertEqual([match.text for match in matches], ["Viêm phổi", "viêm phổi"])
        self.assertNotEqual(matches[0].start, matches[1].start)

    def test_prefers_longest_overlapping_specific_term(self):
        raw = "Tiền sử bệnh\nUng thư phổi tế bào nhỏ\n"
        terms = index(
            ("C34", "Ung thư phổi"),
            ("C34.9", "Ung thư phổi tế bào nhỏ"),
        )

        matches = extract_diagnoses(raw, terms)

        self.assertEqual([(match.text, match.code) for match in matches], [("Ung thư phổi tế bào nhỏ", "C34.9")])

    def test_rejects_single_token_generic_terms(self):
        raw = "Tiền sử bệnh\nSốt\n"
        terms = index(("R50", "Sốt"))

        self.assertEqual(extract_diagnoses(raw, terms), ())


if __name__ == "__main__":
    unittest.main()
