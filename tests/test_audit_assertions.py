import unittest

from tools.audit_assertions import audit_assertions


class AssertionAuditTest(unittest.TestCase):
    def test_counts_spans_and_labels_without_changing_offsets(self):
        documents = {
            "input/1.txt": "Thuốc trước khi nhập viện: aspirin 81mg po daily\n",
            "input/2.txt": "Kết quả xét nghiệm: kali là 2.4 mmol/L\n",
        }
        report = audit_assertions(documents)
        self.assertEqual(report["document_count"], 2)
        self.assertEqual(report["span_count"], 3)
        self.assertEqual(report["label_counts"], {"isHistorical": 1})
        self.assertEqual(report["offset_errors"], 0)


if __name__ == "__main__":
    unittest.main()
