import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import tools.build_submission as build_module
from tools.build_submission import build_submission
from tools.generate_model_proposals import generate_proposal_directory


RAW = "Ghi chú\nĐau đầu\n"


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


class ModelBuildTests(unittest.TestCase):
    def prepare(self, root, include_model_proposals):
        documents = {f"input/{number}.txt": RAW for number in range(1, 101)}
        input_zip = root / "input.zip"
        with zipfile.ZipFile(input_zip, "w") as archive:
            for name, raw_text in documents.items():
                archive.writestr(name, raw_text)
        rxnorm_zip = root / "rxnorm.zip"
        with zipfile.ZipFile(rxnorm_zip, "w") as archive:
            archive.writestr("rrf/RXNCONSO.RRF", rrf_row())
        config = root / "config.json"
        config.write_text(
            json.dumps(
                {
                    "include_labs": False,
                    "span_policy": "regimen",
                    "concept_level": "all_retrievable",
                    "candidate_output": "top1",
                    "include_model_proposals": include_model_proposals,
                }
            ),
            encoding="utf-8",
        )
        proposals = root / "proposals"
        generate_proposal_directory(
            documents,
            proposals,
            lambda prompt: '[{"line_index":1,"text":"Đau đầu","type":"TRIỆU_CHỨNG"}]',
        )
        return (
            input_zip,
            rxnorm_zip,
            hashlib.md5(rxnorm_zip.read_bytes()).hexdigest(),
            config,
            proposals,
        )

    def test_builds_identical_grounded_archives_and_model_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_zip, rxnorm_zip, rxnorm_md5, config, proposals = self.prepare(root, True)

            first = build_submission(
                input_zip,
                rxnorm_zip,
                config,
                root / "first.zip",
                rxnorm_md5,
                model_proposals_path=proposals,
            )
            second = build_submission(
                input_zip,
                rxnorm_zip,
                config,
                root / "second.zip",
                rxnorm_md5,
                model_proposals_path=proposals,
            )

            self.assertEqual(first["output_sha256"], second["output_sha256"])
            self.assertEqual(first["model_id"], "Qwen/Qwen3-4B-Instruct-2507")
            self.assertEqual(first["model_parameters"], 4_000_000_000)
            self.assertEqual(first["model_proposal_count"], 100)
            self.assertEqual(first["model_added_entity_count"], 100)
            self.assertEqual(first["model_parse_error_count"], 0)
            self.assertEqual(first["model_rejections"], {})
            self.assertEqual(first["entity_counts"], {"TRIỆU_CHỨNG": 100})

    def test_enabled_model_requires_valid_matching_proposal_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_zip, rxnorm_zip, rxnorm_md5, config, proposals = self.prepare(root, True)

            with self.assertRaisesRegex(ValueError, "proposal directory"):
                build_submission(
                    input_zip,
                    rxnorm_zip,
                    config,
                    root / "missing.zip",
                    rxnorm_md5,
                )

            record_path = proposals / "documents" / "1.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["raw_sha256"] = "0" * 64
            record_path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "input SHA-256"):
                build_submission(
                    input_zip,
                    rxnorm_zip,
                    config,
                    root / "wrong-hash.zip",
                    rxnorm_md5,
                    model_proposals_path=proposals,
                )

    def test_disabled_model_does_not_read_supplied_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_zip, rxnorm_zip, rxnorm_md5, config, _ = self.prepare(root, False)

            with patch.object(
                build_module,
                "read_proposal_directory",
                side_effect=AssertionError("model-off build read proposals"),
            ):
                report = build_submission(
                    input_zip,
                    rxnorm_zip,
                    config,
                    root / "legacy.zip",
                    rxnorm_md5,
                    model_proposals_path=root / "does-not-exist",
                )

            self.assertEqual(report["model_parameters"], 0)
            self.assertNotIn("model_id", report)


if __name__ == "__main__":
    unittest.main()
