import json
import tempfile
import unittest
from pathlib import Path

from medical_race.linking.rxnorm import RxNormTerm
from medical_race.output import validate_entities
from medical_race.pipeline import (
    SubmissionConfig,
    load_submission_config,
    predict_document,
)


RAW = (
    "Thuốc trước khi nhập viện\n"
    "- aspirin 325mg daily\n"
    "- thuốc giảm đau\n"
    "Kết quả xét nghiệm\n"
    "- creatinine ổn định ở mức 1.4 mg/dL\n"
)
TERMS = (
    RxNormTerm("1", "aspirin", "IN", "RXNORM", True),
    RxNormTerm("2", "aspirin", "IN", "RXNORM", True),
    RxNormTerm("3", "aspirin 325 MG", "SCD", "RXNORM", True),
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


class PipelineTest(unittest.TestCase):
    def test_emits_only_linked_drugs_with_assertions_and_exact_offsets(self):
        entities = predict_document(RAW, TERMS, config())
        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0],
            {
                "text": "aspirin 325mg daily",
                "type": "THUỐC",
                "candidates": ["3"],
                "assertions": ["isHistorical"],
                "position": [RAW.index("aspirin"), RAW.index("aspirin") + 19],
            },
        )
        validate_entities(RAW, entities)

    def test_laboratory_toggle_adds_name_and_result_without_changing_drug(self):
        drugs = predict_document(RAW, TERMS, config())
        with_labs = predict_document(RAW, TERMS, config(include_labs=True))
        self.assertEqual(with_labs[0], drugs[0])
        self.assertEqual(
            [(entity["type"], entity["text"]) for entity in with_labs[1:]],
            [("TÊN_XÉT_NGHIỆM", "creatinine"), ("KẾT_QUẢ_XÉT_NGHIỆM", "1.4 mg/dL")],
        )
        validate_entities(RAW, with_labs)

    def test_core_span_and_candidate_policies_change_only_requested_fields(self):
        core = predict_document(RAW, TERMS, config(span_policy="core"))
        self.assertEqual(core[0]["text"], "aspirin 325mg")
        self.assertEqual(RAW[slice(*core[0]["position"])], core[0]["text"])
        ingredient = predict_document(RAW, TERMS, config(concept_level="ingredient"))
        self.assertEqual(ingredient[0]["candidates"], ["1"])
        top_two = predict_document(RAW, TERMS, config(candidate_output="top2"))
        self.assertEqual(top_two[0]["candidates"], ["3", "1"])

    def test_loads_strict_json_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "include_labs": True,
                        "span_policy": "core",
                        "concept_level": "ingredient",
                        "candidate_output": "top2",
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                load_submission_config(path),
                config(
                    include_labs=True,
                    span_policy="core",
                    concept_level="ingredient",
                    candidate_output="top2",
                ),
            )
            path.write_text('{"include_labs": true}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "fields"):
                load_submission_config(path)

    def test_symptom_toggle_adds_only_valid_symptom_entities(self):
        raw = "Lý do nhập viện: đau ngực\nCác triệu chứng hiện tại\n- Không chóng mặt"
        without = predict_document(raw, TERMS, config())
        enabled = predict_document(raw, TERMS, config(include_symptoms=True))
        self.assertEqual([e for e in enabled if e["type"] != "TRIỆU_CHỨNG"], without)
        self.assertEqual(
            [e for e in enabled if e["type"] == "TRIỆU_CHỨNG"],
            [
                {
                    "text": "đau ngực",
                    "type": "TRIỆU_CHỨNG",
                    "assertions": [],
                    "position": [raw.index("đau ngực"), raw.index("đau ngực") + len("đau ngực")],
                },
                {
                    "text": "chóng mặt",
                    "type": "TRIỆU_CHỨNG",
                    "assertions": ["isNegated"],
                    "position": [raw.index("chóng mặt"), raw.index("chóng mặt") + len("chóng mặt")],
                },
            ],
        )
        validate_entities(raw, enabled)

    def test_legacy_config_defaults_symptoms_off_and_rejects_bad_optional_field(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            values = {
                "include_labs": True,
                "span_policy": "regimen",
                "concept_level": "all_retrievable",
                "candidate_output": "top1",
            }
            path.write_text(json.dumps(values), encoding="utf-8")
            self.assertFalse(load_submission_config(path).include_symptoms)
            values["include_symptoms"] = "yes"
            path.write_text(json.dumps(values), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "include_symptoms"):
                load_submission_config(path)


if __name__ == "__main__":
    unittest.main()
