import unittest

from medical_race.extraction.drugs import extract_drugs
from medical_race.extraction.labs import extract_labs


class DrugRegressionTest(unittest.TestCase):
    def test_rejects_non_drug_volume_and_strips_administration_cues(self):
        raw = (
            "Diễn biến bệnh\n"
            "- giảm lượng nước tiểu từ 1800 ml xuống còn 300 ml trong 24 giờ\n"
            "- Bắt đầu dùng metoprolol 25mg po bid, không có cải thiện\n"
            "- Được chỉ định điều trị aspirin 325mg x 1"
        )
        self.assertEqual(
            [span.text for span in extract_drugs(raw)],
            ["metoprolol 25mg po bid", "aspirin 325mg x 1"],
        )


class LabRegressionTest(unittest.TestCase):
    def test_rejects_substring_and_treatment_dose_false_positives(self):
        raw = (
            "Rosuvastatin (Crestor): đã hết thuốc khoảng 3 tuần.\n"
            "Được bổ sung kali 80mEq trong 24 giờ.\n"
            "Truyền Natri clorid 0.9 %."
        )
        self.assertEqual(extract_labs(raw), ())

    def test_prefers_numeric_result_over_direction_word(self):
        raw = "Xét nghiệm cho thấy creatinine tăng từ 5.2 lên 6.3 mg/dl"
        result = extract_labs(raw)[0]
        self.assertEqual((result.name.text, result.value.text), ("creatinine", "5.2"))


if __name__ == "__main__":
    unittest.main()
