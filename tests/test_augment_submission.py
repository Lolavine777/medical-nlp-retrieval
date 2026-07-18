import hashlib
import json
import runpy
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from medical_race.submission import build_output_zip, validate_output_zip
import tools.augment_submission as augment_module
from tools.augment_submission import augment_submission
from tools.generate_model_proposals import generate_proposal_directory


RAW_WITH_PROPOSALS = "Triệu chứng hiện tại\n- đau cũ\n- đau mới\n"


def rrf_row():
    fields = [""] * 18
    fields[0] = "1"
    fields[1] = "ENG"
    fields[6] = "Y"
    fields[11] = "RXNORM"
    fields[12] = "IN"
    fields[14] = "aspirin"
    fields[16] = "N"
    return "|".join(fields) + "|\n"


class AugmentSubmissionTest(unittest.TestCase):
    def prepare(self, root, raw1=RAW_WITH_PROPOSALS, response_items=None):
        if response_items is None:
            response_items = [
                {
                    "line_index": 1,
                    "text": "đau cũ",
                    "type": "TRIỆU_CHỨNG",
                },
                {
                    "line_index": 2,
                    "text": "đau mới",
                    "type": "TRIỆU_CHỨNG",
                },
            ]
        documents = {
            f"input/{number}.txt": (
                raw1 if number == 1 else "Ghi chú\n"
            )
            for number in range(1, 101)
        }
        input_zip = root / "input.zip"
        with zipfile.ZipFile(input_zip, "w") as archive:
            for name, raw_text in documents.items():
                archive.writestr(name, raw_text)

        parent_predictions = {name: [] for name in documents}
        start = raw1.index("đau cũ")
        parent_predictions["input/1.txt"] = [
            {
                "text": "đau cũ",
                "type": "TRIỆU_CHỨNG",
                "assertions": [],
                "position": [start, start + len("đau cũ")],
            }
        ]
        parent_zip = root / "parent.zip"
        build_output_zip(documents, parent_predictions, parent_zip)

        proposals = root / "proposals"

        def generate(prompt):
            if "đau mới" not in prompt:
                return "[]"
            return json.dumps(
                response_items,
                ensure_ascii=False,
            )

        generate_proposal_directory(
            documents,
            proposals,
            generate,
            prompt_version=2,
        )

        rxnorm_zip = root / "rxnorm.zip"
        with zipfile.ZipFile(rxnorm_zip, "w") as archive:
            archive.writestr("rrf/RXNCONSO.RRF", rrf_row())
        rxnorm_md5 = hashlib.md5(rxnorm_zip.read_bytes()).hexdigest()

        config = root / "config.json"
        config.write_text(
            json.dumps(
                {
                    "include_labs": False,
                    "span_policy": "regimen",
                    "concept_level": "all_retrievable",
                    "candidate_output": "top1",
                    "include_symptoms": False,
                    "include_diagnoses": False,
                    "include_model_proposals": True,
                }
            ),
            encoding="utf-8",
        )
        return documents, input_zip, parent_zip, proposals, rxnorm_zip, rxnorm_md5, config

    def test_preserves_parent_entity_and_adds_non_overlapping_proposal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (
                documents,
                input_zip,
                parent_zip,
                proposals,
                rxnorm_zip,
                rxnorm_md5,
                config,
            ) = self.prepare(root)
            child_zip = root / "child.zip"

            report = augment_submission(
                input_zip,
                parent_zip,
                proposals,
                rxnorm_zip,
                config,
                child_zip,
                expected_md5=rxnorm_md5,
            )

            with zipfile.ZipFile(parent_zip) as parent, zipfile.ZipFile(child_zip) as child:
                parent_entities = json.loads(parent.read("output/1.json"))
                child_entities = json.loads(child.read("output/1.json"))

            self.assertEqual(child_entities[0], parent_entities[0])
            self.assertEqual(
                [entity["text"] for entity in child_entities],
                ["đau cũ", "đau mới"],
            )
            self.assertEqual(report["model_added_entity_count"], 1)
            self.assertEqual(report["model_rejections"]["stable_overlap"], 1)
            self.assertEqual(report["diff"]["added_entities"], 1)
            self.assertEqual(report["diff"]["removed_entities"], 0)
            self.assertEqual(report["diff"]["changed_entities"], 0)
            validate_output_zip(child_zip, documents)

    def test_report_contains_reproducibility_fields_and_cli_writes_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (
                _,
                input_zip,
                parent_zip,
                proposals,
                rxnorm_zip,
                rxnorm_md5,
                config,
            ) = self.prepare(root)
            child_zip = root / "child.zip"
            report_path = root / "child.report.json"
            argv = [
                "augment_submission.py",
                "--input",
                str(input_zip),
                "--parent",
                str(parent_zip),
                "--model-proposals",
                str(proposals),
                "--rxnorm",
                str(rxnorm_zip),
                "--config",
                str(config),
                "--output",
                str(child_zip),
                "--report",
                str(report_path),
                "--expected-md5",
                rxnorm_md5,
            ]

            with patch.object(sys, "argv", argv):
                runpy.run_path(augment_module.__file__, run_name="__main__")

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["diff"]["added_entities"], 1)
            self.assertTrue(report["promotion_eligible"])
            self.assertEqual(report["model_parameters"], 4_000_000_000)
            self.assertEqual(report["model_proposal_count"], 2)
            for field in (
                "parent_sha256",
                "input_sha256",
                "config_sha256",
                "ontology_sha256",
                "output_sha256",
                "model_id",
                "model_revision",
                "model_rejections",
                "entity_counts",
                "candidate_count",
                "assertion_count",
            ):
                self.assertIn(field, report)

    def test_rejects_invalid_parent_before_creating_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (
                documents,
                input_zip,
                parent_zip,
                proposals,
                rxnorm_zip,
                rxnorm_md5,
                config,
            ) = self.prepare(root)
            corrupt_parent = root / "corrupt-parent.zip"
            with zipfile.ZipFile(parent_zip) as source, zipfile.ZipFile(
                corrupt_parent, "w"
            ) as target:
                for name in source.namelist():
                    values = json.loads(source.read(name))
                    if name == "output/1.json":
                        values[0]["position"] = [0, 1]
                    target.writestr(name, json.dumps(values, ensure_ascii=False))
            destination = root / "child.zip"

            with self.assertRaisesRegex(ValueError, "offset"):
                augment_submission(
                    input_zip,
                    corrupt_parent,
                    proposals,
                    rxnorm_zip,
                    config,
                    destination,
                    expected_md5=rxnorm_md5,
                )
            self.assertFalse(destination.exists())

    def test_filters_treatment_action_but_keeps_atomic_symptom(self):
        raw = "Triệu chứng hiện tại\n- đau cũ\n- đau mới\n- điều trị chống đông\n"
        items = [
            {
                "line_index": 2,
                "text": "đau mới",
                "type": "TRIỆU_CHỨNG",
            },
            {
                "line_index": 3,
                "text": "điều trị chống đông",
                "type": "TRIỆU_CHỨNG",
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (
                _,
                input_zip,
                parent_zip,
                proposals,
                rxnorm_zip,
                rxnorm_md5,
                config,
            ) = self.prepare(root, raw1=raw, response_items=items)
            child_zip = root / "child.zip"

            report = augment_submission(
                input_zip,
                parent_zip,
                proposals,
                rxnorm_zip,
                config,
                child_zip,
                expected_md5=rxnorm_md5,
            )

            with zipfile.ZipFile(child_zip) as child:
                entities = json.loads(child.read("output/1.json"))
            self.assertEqual(
                [entity["text"] for entity in entities],
                ["đau cũ", "đau mới"],
            )
            self.assertEqual(report["model_rejections"]["precision_filter"], 1)

    def test_rejects_proposal_hash_mismatch_before_creating_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (
                _,
                input_zip,
                parent_zip,
                proposals,
                rxnorm_zip,
                rxnorm_md5,
                config,
            ) = self.prepare(root)
            record_path = proposals / "documents" / "1.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["raw_sha256"] = "0" * 64
            record_path.write_text(
                json.dumps(record, ensure_ascii=False),
                encoding="utf-8",
            )
            destination = root / "child.zip"

            with self.assertRaisesRegex(ValueError, "input SHA-256"):
                augment_submission(
                    input_zip,
                    parent_zip,
                    proposals,
                    rxnorm_zip,
                    config,
                    destination,
                    expected_md5=rxnorm_md5,
                )
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
