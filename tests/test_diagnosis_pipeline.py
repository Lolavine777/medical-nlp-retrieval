import json
import tempfile
import unittest
from pathlib import Path

from medical_race.linking.icd10 import ICD10Term, build_term_index
from medical_race.output import validate_entities
from medical_race.pipeline import SubmissionConfig, load_submission_config, predict_document


def config(**changes):
    values = {
        "include_labs": False,
        "span_policy": "regimen",
        "concept_level": "all_retrievable",
        "candidate_output": "top1",
    }
    values.update(changes)
    return SubmissionConfig(**values)


class DiagnosisPipelineTests(unittest.TestCase):
    def test_diagnosis_toggle_emits_strict_linked_entity_with_assertion(self):
        raw = "Tiền sử bệnh\nViêm phổi\n"
        index = build_term_index(
            (ICD10Term("J18.9", "Viêm phổi", "disease", True),)
        )

        entities = predict_document(
            raw,
            (),
            config(include_diagnoses=True),
            icd_index=index,
        )

        self.assertEqual(
            entities,
            [
                {
                    "text": "Viêm phổi",
                    "type": "CHẨN_ĐOÁN",
                    "candidates": ["J18.9"],
                    "assertions": ["isHistorical"],
                    "position": [raw.index("Viêm phổi"), raw.index("Viêm phổi") + len("Viêm phổi")],
                }
            ],
        )
        validate_entities(raw, entities)

    def test_enabled_diagnoses_require_verified_index(self):
        with self.assertRaisesRegex(ValueError, "ICD-10 term index"):
            predict_document("Tiền sử bệnh\nViêm phổi", (), config(include_diagnoses=True))

    def test_legacy_config_defaults_diagnoses_off_and_rejects_bad_value(self):
        values = {
            "include_labs": True,
            "span_policy": "regimen",
            "concept_level": "all_retrievable",
            "candidate_output": "top1",
            "include_symptoms": True,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "config.json")
            path.write_text(json.dumps(values), encoding="utf-8")
            self.assertFalse(load_submission_config(path).include_diagnoses)
            values["include_diagnoses"] = "yes"
            path.write_text(json.dumps(values), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "include_diagnoses"):
                load_submission_config(path)


if __name__ == "__main__":
    unittest.main()
