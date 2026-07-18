import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from medical_race.submission import build_output_zip, validate_output_zip
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
    def prepare(self, root):
        documents = {
            f"input/{number}.txt": (
                RAW_WITH_PROPOSALS if number == 1 else "Ghi chú\n"
            )
            for number in range(1, 101)
        }
        input_zip = root / "input.zip"
        with zipfile.ZipFile(input_zip, "w") as archive:
            for name, raw_text in documents.items():
                archive.writestr(name, raw_text)

        parent_predictions = {name: [] for name in documents}
        start = RAW_WITH_PROPOSALS.index("đau cũ")
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
                [
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
                ],
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


if __name__ == "__main__":
    unittest.main()
