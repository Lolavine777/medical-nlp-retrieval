import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from medical_race.linking.icd10 import ICD10Term, build_term_index
from medical_race.linking.rxnorm import RxNormTerm
from medical_race.model_proposals import ModelProposal
from medical_race.output import validate_entities
from medical_race.pipeline import (
    SubmissionConfig,
    load_submission_config,
    predict_document,
)


TERMS = (RxNormTerm("1", "aspirin", "IN", "RXNORM", True),)
ICD_INDEX = build_term_index(
    (ICD10Term("J18.9", "Viêm phổi", "disease", True),)
)


def config(**changes):
    values = {
        "include_labs": False,
        "span_policy": "regimen",
        "concept_level": "all_retrievable",
        "candidate_output": "top1",
    }
    values.update(changes)
    return SubmissionConfig(**values)


class ModelPipelineTest(unittest.TestCase):
    def test_accepts_grounded_symptom_and_derives_assertion(self):
        raw = "Triệu chứng hiện tại\n- không đau ngực\n"
        proposals = (ModelProposal(1, "đau ngực", "TRIỆU_CHỨNG"),)

        entities = predict_document(
            raw,
            (),
            config(include_model_proposals=True),
            model_proposals=proposals,
        )

        self.assertEqual(
            entities,
            [
                {
                    "text": "đau ngực",
                    "type": "TRIỆU_CHỨNG",
                    "assertions": ["isNegated"],
                    "position": [raw.index("đau ngực"), raw.index("đau ngực") + 8],
                }
            ],
        )
        validate_entities(raw, entities)

    def test_links_model_diagnosis_and_drug_with_top_one_candidates(self):
        raw = "Tiền sử bệnh\nViêm phổi\nDiễn biến\nĐã dùng aspirin\n"
        proposals = (
            ModelProposal(1, "Viêm phổi", "CHẨN_ĐOÁN"),
            ModelProposal(3, "aspirin", "THUỐC"),
        )

        entities = predict_document(
            raw,
            TERMS,
            config(include_model_proposals=True),
            icd_index=ICD_INDEX,
            model_proposals=proposals,
        )

        self.assertEqual([entity["type"] for entity in entities], ["CHẨN_ĐOÁN", "THUỐC"])
        self.assertEqual([entity["candidates"] for entity in entities], [["J18.9"], ["1"]])
        validate_entities(raw, entities)

    def test_rejects_unlinked_diagnosis_and_drug(self):
        raw = "Chẩn đoán\nBệnh không có trong ontology\nDiễn biến\nĐã dùng thuốc lạ\n"
        proposals = (
            ModelProposal(1, "Bệnh không có trong ontology", "CHẨN_ĐOÁN"),
            ModelProposal(3, "thuốc lạ", "THUỐC"),
        )
        report = Counter()

        entities = predict_document(
            raw,
            (),
            config(include_model_proposals=True),
            icd_index={},
            model_proposals=proposals,
            model_report=report,
        )

        self.assertEqual(entities, [])
        self.assertEqual(report["unlinked_candidate"], 2)

    def test_stable_predictions_win_over_model_overlap(self):
        raw = "Triệu chứng hiện tại\n- đau ngực\n"
        proposals = (ModelProposal(1, "đau ngực", "TRIỆU_CHỨNG"),)
        report = Counter()

        stable = predict_document(raw, (), config(include_symptoms=True))
        merged = predict_document(
            raw,
            (),
            config(include_symptoms=True, include_model_proposals=True),
            model_proposals=proposals,
            model_report=report,
        )

        self.assertEqual(merged, stable)
        self.assertEqual(report["stable_overlap"], 1)

    def test_rejects_invalid_section_and_ambiguous_same_span_types(self):
        raw = "Thuốc trước khi nhập viện\n- đau ngực\nĐánh giá tại bệnh viện\nViêm phổi\n"
        proposals = (
            ModelProposal(1, "đau ngực", "TRIỆU_CHỨNG"),
            ModelProposal(3, "Viêm phổi", "TRIỆU_CHỨNG"),
            ModelProposal(3, "Viêm phổi", "CHẨN_ĐOÁN"),
        )
        report = Counter()

        entities = predict_document(
            raw,
            (),
            config(include_model_proposals=True),
            icd_index=ICD_INDEX,
            model_proposals=proposals,
            model_report=report,
        )

        self.assertEqual(entities, [])
        self.assertEqual(report["invalid_section"], 1)
        self.assertEqual(report["ambiguous_type"], 2)

    def test_prefers_longest_non_overlapping_model_span(self):
        raw = "Triệu chứng hiện tại\n- đau ngực dữ dội\n"
        proposals = (
            ModelProposal(1, "đau ngực", "TRIỆU_CHỨNG"),
            ModelProposal(1, "đau ngực dữ dội", "TRIỆU_CHỨNG"),
        )
        report = Counter()

        entities = predict_document(
            raw,
            (),
            config(include_model_proposals=True),
            model_proposals=proposals,
            model_report=report,
        )

        self.assertEqual([entity["text"] for entity in entities], ["đau ngực dữ dội"])
        self.assertEqual(report["model_overlap"], 1)
        self.assertEqual(report["accepted"], 1)

    def test_model_toggle_defaults_off_and_requires_boolean(self):
        values = {
            "include_labs": True,
            "span_policy": "regimen",
            "concept_level": "all_retrievable",
            "candidate_output": "top1",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(values), encoding="utf-8")
            self.assertFalse(load_submission_config(path).include_model_proposals)
            values["include_model_proposals"] = "yes"
            path.write_text(json.dumps(values), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "include_model_proposals"):
                load_submission_config(path)

    def test_disabled_model_ignores_supplied_proposals(self):
        raw = "Triệu chứng hiện tại\n- đau ngực\n"
        proposals = (ModelProposal(1, "đau ngực", "TRIỆU_CHỨNG"),)

        self.assertEqual(
            predict_document(raw, (), config(), model_proposals=proposals),
            predict_document(raw, (), config()),
        )


if __name__ == "__main__":
    unittest.main()
