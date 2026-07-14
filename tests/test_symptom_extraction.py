import unittest

from medical_race.extraction.symptoms import extract_symptoms


RAW = (
    "Lý do nhập viện: đau ngực\n"
    "Thời điểm khởi phát triệu chứng: hôm qua\n"
    "Các triệu chứng hiện tại\n"
    "- Không chóng mặt\n"
    "- **khó thở khi gắng sức:**\n"
    "- Bệnh nhân có đau bụng vùng thượng vị\n"
    "- Được chụp x-quang ngực\n"
    "Đặc điểm triệu chứng\n"
    "- Vị trí: ngực\n"
    "Các sự kiện trước khi nhập viện\n"
    "- Nhập viện khoa Nội\n"
)


class SymptomExtractionTest(unittest.TestCase):
    def test_extracts_only_chief_complaint_and_active_short_bullets(self):
        spans = extract_symptoms(RAW)
        self.assertEqual(
            [span.text for span in spans],
            ["đau ngực", "chóng mặt", "khó thở khi gắng sức", "đau bụng vùng thượng vị"],
        )
        self.assertTrue(all(RAW[span.start : span.end] == span.text for span in spans))

    def test_rejects_actions_and_stops_at_characteristics(self):
        texts = [span.text for span in extract_symptoms(RAW)]
        self.assertNotIn("Được chụp x-quang ngực", texts)
        self.assertNotIn("Vị trí: ngực", texts)
        self.assertNotIn("Nhập viện khoa Nội", texts)

    def test_preserves_duplicate_mentions_at_distinct_offsets(self):
        raw = "Triệu chứng hiện tại\n- ho\n- ho\nCác sự kiện trước khi nhập viện\n- về nhà"
        spans = extract_symptoms(raw)
        self.assertEqual([span.text for span in spans], ["ho", "ho"])
        self.assertNotEqual(spans[0].start, spans[1].start)


if __name__ == "__main__":
    unittest.main()
