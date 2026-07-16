import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.build_controls import build_controls
from tools.generate_model_proposals import generate_proposal_directory


RAW = (
    "Thuốc trước khi nhập viện\n"
    "- aspirin\n"
    "Triệu chứng hiện tại\n"
    "Đau đầu\n"
)


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


class ControlBuilderTest(unittest.TestCase):
    def test_builds_preflighted_rule_and_qwen_controls_with_diff(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            documents = {f"input/{index}.txt": RAW for index in range(1, 101)}
            input_zip = root / "input.zip"
            with zipfile.ZipFile(input_zip, "w") as archive:
                for name, raw_text in documents.items():
                    archive.writestr(name, raw_text)
            rxnorm_zip = root / "rxnorm.zip"
            with zipfile.ZipFile(rxnorm_zip, "w") as archive:
                archive.writestr("rrf/RXNCONSO.RRF", rrf_row())
            expected_md5 = hashlib.md5(rxnorm_zip.read_bytes()).hexdigest()
            base_config = {
                "include_labs": False,
                "span_policy": "regimen",
                "concept_level": "all_retrievable",
                "candidate_output": "top1",
            }
            rule_config = root / "rule.json"
            rule_config.write_text(json.dumps(base_config), encoding="utf-8")
            qwen_config = root / "qwen.json"
            qwen_config.write_text(
                json.dumps({**base_config, "include_model_proposals": True}),
                encoding="utf-8",
            )
            proposals = root / "proposals"
            generate_proposal_directory(
                documents,
                proposals,
                lambda prompt: '[{"line_index":3,"text":"Đau đầu","type":"TRIỆU_CHỨNG"}]',
            )
            output = root / "controls"
            output.mkdir()

            summary = build_controls(
                input_zip,
                rxnorm_zip,
                root / "unused-icd.json",
                proposals,
                output,
                expected_md5,
                "0" * 64,
                rule_config,
                qwen_config,
            )

            expected_files = {
                "rule-control.zip",
                "rule-control.report.json",
                "qwen-control.zip",
                "qwen-control.report.json",
                "rule-to-qwen.diff.json",
                "controls.summary.json",
            }
            self.assertEqual({path.name for path in output.iterdir()}, expected_files)
            rule_report = json.loads((output / "rule-control.report.json").read_text(encoding="utf-8"))
            qwen_report = json.loads((output / "qwen-control.report.json").read_text(encoding="utf-8"))
            diff = json.loads((output / "rule-to-qwen.diff.json").read_text(encoding="utf-8"))
            self.assertEqual(rule_report["model_parameters"], 0)
            self.assertEqual(qwen_report["model_parameters"], 4_000_000_000)
            self.assertEqual(
                rule_report["output_sha256"],
                summary["rule"]["preflight"]["sha256"],
            )
            self.assertEqual(
                qwen_report["output_sha256"],
                summary["qwen"]["preflight"]["sha256"],
            )
            self.assertEqual(diff["added_entities"], 100)
            self.assertEqual(diff["removed_entities"], 0)
            self.assertEqual(diff["changed_entities"], 0)


if __name__ == "__main__":
    unittest.main()
