import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import tools.build_submission as build_module
from tools.build_submission import _console_json, build_submission


RAW = "Thuốc trước khi nhập viện\n- aspirin\n"


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


class SubmissionBuilderTest(unittest.TestCase):
    def test_builds_deterministic_ontology_backed_submission_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_zip = root / "input.zip"
            with zipfile.ZipFile(input_zip, "w") as archive:
                for index in range(1, 101):
                    archive.writestr(f"input/{index}.txt", RAW)
            rxnorm_zip = root / "rxnorm.zip"
            with zipfile.ZipFile(rxnorm_zip, "w") as archive:
                archive.writestr("rrf/RXNCONSO.RRF", rrf_row())
            expected_md5 = hashlib.md5(rxnorm_zip.read_bytes()).hexdigest()
            config = root / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "include_labs": False,
                        "span_policy": "regimen",
                        "concept_level": "all_retrievable",
                        "candidate_output": "top1",
                    }
                ),
                encoding="utf-8",
            )
            first = root / "first.zip"
            second = root / "second.zip"
            state = {"ontology_loaded": False}
            original_read = build_module.read_rxnorm_archive
            original_sha256 = build_module.sha256

            def tracked_read(*args):
                state["ontology_loaded"] = True
                return original_read(*args)

            def low_memory_sha256(path):
                if state["ontology_loaded"]:
                    raise MemoryError("hashing after ontology load exceeds memory budget")
                return original_sha256(path)

            with (
                patch.object(build_module, "read_rxnorm_archive", side_effect=tracked_read),
                patch.object(build_module, "sha256", side_effect=low_memory_sha256),
            ):
                report = build_submission(input_zip, rxnorm_zip, config, first, expected_md5)
            second_report = build_submission(input_zip, rxnorm_zip, config, second, expected_md5)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(report["output_sha256"], second_report["output_sha256"])
            self.assertEqual(report["entity_count"], 100)
            self.assertEqual(report["entity_counts"], {"THUỐC": 100})
            self.assertEqual(report["candidate_count"], 100)
            self.assertEqual(report["linked_drug_count"], 100)
            self.assertEqual(report["dropped_drug_count"], 0)
            self.assertEqual(report["model_parameters"], 0)
            self.assertEqual(len(report["input_sha256"]), 64)
            self.assertEqual(len(report["ontology_sha256"]), 64)
            self.assertEqual(len(report["config_sha256"]), 64)

    def test_console_json_survives_windows_legacy_encoding(self):
        value = {"type": "TRIỆU_CHỨNG"}
        encoded = _console_json(value).encode("cp1252")
        self.assertEqual(json.loads(encoded.decode("cp1252")), value)


if __name__ == "__main__":
    unittest.main()
