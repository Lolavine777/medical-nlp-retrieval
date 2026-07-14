import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import tools.build_submission as build_module
from tools.build_submission import build_submission
from tools.fetch_icd10_vn import canonical_snapshot


RAW = "Tiền sử bệnh\nViêm phổi\n"


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


def icd_node():
    return {
        "model": "disease",
        "id": "J18.9",
        "code": "J18.9",
        "name": "Viêm phổi",
        "is_leaf": True,
        "parent": None,
    }


class DiagnosisBuildTests(unittest.TestCase):
    def prepare(self, root, include_diagnoses):
        input_zip = root / "input.zip"
        with zipfile.ZipFile(input_zip, "w") as archive:
            for number in range(1, 101):
                archive.writestr(f"input/{number}.txt", RAW)
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
                    "include_diagnoses": include_diagnoses,
                }
            ),
            encoding="utf-8",
        )
        icd = root / "icd.json"
        icd.write_bytes(canonical_snapshot([icd_node()], "https://example.test", "vi"))
        return (
            input_zip,
            rxnorm_zip,
            hashlib.md5(rxnorm_zip.read_bytes()).hexdigest(),
            config,
            icd,
            hashlib.sha256(icd.read_bytes()).hexdigest(),
        )

    def test_builds_diagnosis_submission_and_reports_verified_icd_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_zip, rxnorm_zip, rxnorm_md5, config, icd, icd_sha256 = self.prepare(root, True)

            report = build_submission(
                input_zip,
                rxnorm_zip,
                config,
                root / "output.zip",
                rxnorm_md5,
                icd_path=icd,
                expected_icd_sha256=icd_sha256,
            )

            self.assertEqual(report["entity_counts"], {"CHẨN_ĐOÁN": 100})
            self.assertEqual(report["diagnosis_count"], 100)
            self.assertEqual(report["candidate_count"], 100)
            self.assertEqual(report["candidate_counts_by_type"], {"CHẨN_ĐOÁN": 100})
            self.assertEqual(report["icd_ontology_sha256"], icd_sha256)
            self.assertEqual(report["model_parameters"], 0)

    def test_legacy_build_does_not_read_icd_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_zip, rxnorm_zip, rxnorm_md5, config, icd, icd_sha256 = self.prepare(root, False)

            with patch.object(
                build_module,
                "read_icd10_snapshot",
                side_effect=AssertionError("legacy build read ICD"),
            ):
                report = build_submission(
                    input_zip,
                    rxnorm_zip,
                    config,
                    root / "output.zip",
                    rxnorm_md5,
                    icd_path=icd,
                    expected_icd_sha256=icd_sha256,
                )

            self.assertEqual(report["entity_count"], 0)
            self.assertNotIn("icd_ontology_sha256", report)


if __name__ == "__main__":
    unittest.main()
