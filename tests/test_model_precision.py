import unittest
from collections import Counter

from medical_race.linking.rxnorm import RxNormTerm
from medical_race.model_proposals import ModelProposal
from medical_race.pipeline import SubmissionConfig, predict_document


def config():
    return SubmissionConfig(
        include_labs=False,
        span_policy="regimen",
        concept_level="all_retrievable",
        candidate_output="top1",
        include_model_proposals=True,
    )


class ModelPrecisionTests(unittest.TestCase):
    def test_rejects_structural_symptom_context_and_keeps_short_mention(self):
        raw = (
            "Đánh giá tại bệnh viện\n"
            "- đau ngực\n"
            "Các triệu chứng hiện tại triệu chứng\n"
            "Phủ nhận khó thở\n"
            "Bệnh nhân tỉnh, tiếp xúc được\n"
            "sốt lần cuối là vào ngày\n"
            "mệt mỏi\n"
        )
        proposals = (
            ModelProposal(1, "- đau ngực", "TRIỆU_CHỨNG"),
            ModelProposal(
                2,
                "Các triệu chứng hiện tại triệu chứng",
                "TRIỆU_CHỨNG",
            ),
            ModelProposal(3, "Phủ nhận khó thở", "TRIỆU_CHỨNG"),
            ModelProposal(
                4,
                "Bệnh nhân tỉnh, tiếp xúc được",
                "TRIỆU_CHỨNG",
            ),
            ModelProposal(5, "sốt lần cuối là vào ngày", "TRIỆU_CHỨNG"),
            ModelProposal(6, "mệt mỏi", "TRIỆU_CHỨNG"),
        )
        report = Counter()

        entities = predict_document(
            raw,
            (),
            config(),
            model_proposals=proposals,
            model_report=report,
        )

        self.assertEqual([entity["text"] for entity in entities], ["mệt mỏi"])
        self.assertEqual(report["invalid_structure"], 5)

    def test_rejects_broad_labs_and_treatment_context(self):
        raw = (
            "Đánh giá tại bệnh viện\n"
            "Thủ thuật đã thực hiện: nạo vét tổn thương\n"
            "bilirubin\n"
            "troponin là 0.03\n"
            "- phosphate là 5.6\n"
            "được cho vancomycin 1 gram\n"
            "0.03\n"
        )
        proposals = (
            ModelProposal(
                1,
                "Thủ thuật đã thực hiện: nạo vét tổn thương",
                "KẾT_QUẢ_XÉT_NGHIỆM",
            ),
            ModelProposal(2, "bilirubin", "KẾT_QUẢ_XÉT_NGHIỆM"),
            ModelProposal(3, "troponin là 0.03", "KẾT_QUẢ_XÉT_NGHIỆM"),
            ModelProposal(4, "- phosphate là 5.6", "KẾT_QUẢ_XÉT_NGHIỆM"),
            ModelProposal(5, "được cho vancomycin 1 gram", "THUỐC"),
            ModelProposal(6, "0.03", "KẾT_QUẢ_XÉT_NGHIỆM"),
        )
        report = Counter()

        entities = predict_document(
            raw,
            (RxNormTerm("1", "vancomycin", "IN", "RXNORM", True),),
            config(),
            model_proposals=proposals,
            model_report=report,
        )

        self.assertEqual(
            [(entity["text"], entity["type"]) for entity in entities],
            [("0.03", "KẾT_QUẢ_XÉT_NGHIỆM")],
        )
        self.assertEqual(report["invalid_structure"], 5)


if __name__ == "__main__":
    unittest.main()
