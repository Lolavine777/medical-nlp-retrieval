import unittest

from medical_race.linking.icd10 import ICD10Term, build_term_index
from medical_race.linking.icd10 import exact_icd_candidates
from medical_race.linking.rxnorm import LinkResult, RxNormTerm, link_drug
from medical_race.linking.rxnorm import rank_drug_candidates
from medical_race.model_proposals import ModelProposal
from tools.audit_linking import audit_linking


RXNORM_TERMS = (
    RxNormTerm("1", "metoprolol", "IN", "RXNORM", True),
    RxNormTerm("3", "aspirin", "IN", "RXNORM", True),
    RxNormTerm("3", "ASPIRIN", "SU", "MTHSPL", False),
    RxNormTerm("5", "aspirin", "SY", "MTHSPL", False),
    RxNormTerm("6", "aspirin", "IN", "RXNORM", True),
)


class CandidateRankingDiagnosticsTest(unittest.TestCase):
    def test_exposes_rxnorm_ranking_without_changing_link_output(self):
        ranked = rank_drug_candidates("aspirin", RXNORM_TERMS)

        self.assertEqual(tuple(term.rxcui for term in ranked), ("3", "6", "5"))
        self.assertEqual(
            link_drug("aspirin", RXNORM_TERMS, candidate_output="top2"),
            LinkResult(("3", "6"), "aspirin"),
        )

    def test_exposes_ambiguous_exact_icd_titles_without_indexing_them(self):
        terms = (
            ICD10Term("A01", "Trùng tên", "category", True),
            ICD10Term("A02", "Trùng tên", "category", True),
        )

        self.assertEqual(
            tuple(term.code for term in exact_icd_candidates("trùng tên", terms)),
            ("A01", "A02"),
        )
        self.assertNotIn("trùng tên", build_term_index(terms))


class LinkingAuditTest(unittest.TestCase):
    def test_reports_linked_ambiguous_and_unlinked_queries(self):
        raw_text = (
            "Thuốc trước khi nhập viện\n"
            "- aspirin\n"
            "Chẩn đoán\n"
            "Viêm phổi\n"
            "Bệnh lạ\n"
            "Trùng tên\n"
            "Diễn biến\n"
            "- thuốc lạ\n"
        )
        icd_terms = (
            ICD10Term("J18", "Viêm phổi", "category", True),
            ICD10Term("A01", "Trùng tên", "category", True),
            ICD10Term("A02", "Trùng tên", "category", True),
        )
        proposals = {
            "input/1.txt": (
                ModelProposal(4, "Bệnh lạ", "CHẨN_ĐOÁN"),
                ModelProposal(5, "Trùng tên", "CHẨN_ĐOÁN"),
                ModelProposal(7, "thuốc lạ", "THUỐC"),
            )
        }

        report = audit_linking(
            {"input/1.txt": raw_text},
            (RxNormTerm("3", "aspirin", "IN", "RXNORM", True),),
            icd_terms,
            proposals,
        )

        self.assertEqual(
            report["summary"],
            {"queries": 5, "linked": 2, "ambiguous": 1, "unlinked": 2},
        )
        self.assertEqual(
            [(record["text"], record["source"], record["status"]) for record in report["records"]],
            [
                ("aspirin", "rule", "linked"),
                ("Viêm phổi", "rule", "linked"),
                ("Bệnh lạ", "qwen", "unlinked"),
                ("Trùng tên", "qwen", "ambiguous"),
                ("thuốc lạ", "qwen", "unlinked"),
            ],
        )
        ambiguous = next(record for record in report["records"] if record["status"] == "ambiguous")
        self.assertEqual([candidate["id"] for candidate in ambiguous["candidates"]], ["A01", "A02"])


if __name__ == "__main__":
    unittest.main()
