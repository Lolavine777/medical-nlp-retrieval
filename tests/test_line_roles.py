import unittest

from medical_race.line_roles import parse_line_roles


class LineRolesTest(unittest.TestCase):
    def test_preserves_inline_content_and_line_offsets(self):
        raw = (
            "Thuốc trước khi nhập viện: aspirin 325mg hằng ngày\r\n"
            "Kết quả xét nghiệm\r\n"
            "- kali là 2,4 mmol/L\r\n"
            "Đánh giá tại bệnh viện\r\n"
            "ổn định"
        )
        lines = parse_line_roles(raw)

        self.assertEqual(
            [(line.role, line.text) for line in lines],
            [
                ("medication", "aspirin 325mg hằng ngày"),
                ("header", "Kết quả xét nghiệm"),
                ("laboratory", "- kali là 2,4 mmol/L"),
                ("header", "Đánh giá tại bệnh viện"),
                ("content", "ổn định"),
            ],
        )
        for line in lines:
            self.assertEqual(raw[line.start : line.end], line.text)

    def test_keeps_blank_lines(self):
        lines = parse_line_roles("Ghi chú\n\nNội dung")
        self.assertEqual([line.role for line in lines], ["content", "blank", "content"])


if __name__ == "__main__":
    unittest.main()
