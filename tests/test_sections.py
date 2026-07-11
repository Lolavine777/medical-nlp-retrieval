import unittest

from medical_race.sections import parse_sections


class SectionParserTest(unittest.TestCase):
    def test_preserves_raw_boundaries_for_numbered_and_inline_headers(self):
        raw = (
            "1. Tiền sử bệnh\r\n"
            "- tăng huyết áp\r\n"
            "2. Bệnh sử hiện tại\r\n"
            "Lý do nhập viện: đau ngực\r\n"
            "không sốt"
        )
        sections = parse_sections(raw)
        self.assertEqual(
            [section.kind for section in sections],
            ["past_history", "current_illness", "admission_reason"],
        )
        self.assertEqual(raw[sections[0].header_start : sections[0].header_end], "Tiền sử bệnh")
        self.assertEqual(raw[sections[0].content_start : sections[0].end], "- tăng huyết áp\r\n")
        self.assertEqual(raw[sections[2].content_start : sections[2].end], "đau ngực\r\nkhông sốt")

    def test_keeps_unrecognized_document_as_unsectioned(self):
        raw = "Dòng tự do\nkhông có tiêu đề"
        section = parse_sections(raw)[0]
        self.assertEqual(section.kind, "unsectioned")
        self.assertEqual((section.start, section.content_start, section.end), (0, 0, len(raw)))

    def test_keeps_preamble_before_first_known_header(self):
        raw = "Ghi chú mở đầu\n  1.  Đánh giá tại bệnh viện\nKhám ổn"
        sections = parse_sections(raw)
        self.assertEqual([section.kind for section in sections], ["unsectioned", "assessment"])
        self.assertEqual(raw[sections[0].start : sections[0].end], "Ghi chú mở đầu\n")
        self.assertEqual(raw[sections[1].content_start : sections[1].end], "Khám ổn")

    def test_does_not_treat_longer_unknown_phrase_as_known_header(self):
        raw = "Khám phá điều mới\nNội dung"
        self.assertEqual(parse_sections(raw)[0].kind, "unsectioned")


if __name__ == "__main__":
    unittest.main()
