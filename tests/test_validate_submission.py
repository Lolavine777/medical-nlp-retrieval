import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from medical_race.submission import build_output_zip
from medical_race.submission import validate_output_zip


def documents():
    return {f"input/{index}.txt": f"document {index}" for index in range(1, 101)}


def predictions():
    return {name: [] for name in documents()}


def write_records(path, replacements=None, extra=None):
    replacements = replacements or {}
    with zipfile.ZipFile(path, "w") as archive:
        for index in range(1, 101):
            name = f"output/{index}.json"
            archive.writestr(name, replacements.get(name, "[]\n"))
        if extra:
            archive.writestr(extra, "[]\n")


class SubmissionPreflightTest(unittest.TestCase):
    def test_valid_archive_reports_deterministic_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "submission.zip"
            build_output_zip(documents(), predictions(), path)

            report = validate_output_zip(path, documents())

            self.assertEqual(
                report,
                {
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "entry_count": 100,
                    "entity_count": 0,
                    "candidate_count": 0,
                    "assertion_count": 0,
                    "entity_counts": {},
                },
            )

    def test_rejects_intermediate_model_proposal_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "proposal.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("qwen3-4b-s009/manifest.json", "{}")
                archive.writestr("qwen3-4b-s009/documents/1.json", "{}")

            with self.assertRaisesRegex(ValueError, "intermediate model-proposal archive"):
                validate_output_zip(path, documents())

    def test_rejects_root_model_proposal_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "proposal.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("manifest.json", "{}")
                archive.writestr("documents/1.json", "{}")

            with self.assertRaisesRegex(ValueError, "intermediate model-proposal archive"):
                validate_output_zip(path, documents())
    def test_rejects_nested_submission_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("wrapper/output/1.json", "[]\n")

            with self.assertRaisesRegex(ValueError, "nested"):
                validate_output_zip(path, documents())

    def test_rejects_missing_extra_and_malformed_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "missing.zip"
            with zipfile.ZipFile(missing, "w") as archive:
                for index in range(1, 100):
                    archive.writestr(f"output/{index}.json", "[]\n")
            extra = root / "extra.zip"
            write_records(extra, extra="output/101.json")
            malformed = root / "malformed.zip"
            write_records(malformed, {"output/1.json": "{"})

            with self.assertRaisesRegex(ValueError, "exactly output/1.json"):
                validate_output_zip(missing, documents())
            with self.assertRaisesRegex(ValueError, "exactly output/1.json"):
                validate_output_zip(extra, documents())
            with self.assertRaisesRegex(ValueError, "invalid UTF-8 JSON in output/1.json"):
                validate_output_zip(malformed, documents())

    def test_rejects_invalid_schema_and_offset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            schema = root / "schema.zip"
            write_records(
                schema,
                {
                    "output/1.json": json.dumps(
                        [{"text": "document", "type": "THUỐC"}],
                        ensure_ascii=False,
                    )
                },
            )
            offset = root / "offset.zip"
            write_records(
                offset,
                {
                    "output/1.json": json.dumps(
                        [
                            {
                                "text": "document",
                                "type": "THUỐC",
                                "candidates": ["1"],
                                "assertions": [],
                                "position": [1, 9],
                            }
                        ],
                        ensure_ascii=False,
                    )
                },
            )

            with self.assertRaisesRegex(ValueError, "entity 0"):
                validate_output_zip(schema, documents())
            with self.assertRaisesRegex(ValueError, "entity 0"):
                validate_output_zip(offset, documents())

    def test_cli_rejects_proposal_archive_before_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_zip = root / "input.zip"
            with zipfile.ZipFile(input_zip, "w") as archive:
                for name, raw_text in documents().items():
                    archive.writestr(name, raw_text)
            proposal_zip = root / "proposal.zip"
            with zipfile.ZipFile(proposal_zip, "w") as archive:
                archive.writestr("qwen3-4b-s009/manifest.json", "{}")
                archive.writestr("qwen3-4b-s009/documents/1.json", "{}")

            environment = os.environ.copy()
            environment["PYTHONPATH"] = os.pathsep.join(("src", "."))
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/validate_submission.py",
                    "--input",
                    str(input_zip),
                    str(proposal_zip),
                ],
                cwd=Path(__file__).resolve().parents[1],
                env=environment,
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("intermediate model-proposal archive", result.stderr)


if __name__ == "__main__":
    unittest.main()
