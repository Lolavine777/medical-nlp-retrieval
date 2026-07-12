import tempfile
import unittest
import zipfile
from pathlib import Path

from medical_race.submission import build_output_zip


def documents():
    return {f"input/{i}.txt": f"document {i}" for i in range(100, 0, -1)}


def predictions():
    return {f"input/{i}.txt": [] for i in range(1, 101)}


class SubmissionPackageTest(unittest.TestCase):
    def test_builds_identical_verified_archives_in_numeric_order(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.zip"
            second = Path(directory) / "second.zip"
            report = build_output_zip(documents(), predictions(), first)
            second_report = build_output_zip(documents(), predictions(), second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(report["sha256"], second_report["sha256"])
            self.assertEqual(report["entry_count"], 100)
            self.assertEqual(report["entity_count"], 0)
            self.assertEqual(report["empty_document_count"], 100)
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(
                    archive.namelist(),
                    [f"output/{i}.json" for i in range(1, 101)],
                )
                self.assertTrue(
                    all(archive.read(name) == b"[]\n" for name in archive.namelist())
                )

    def test_rejects_missing_extra_and_invalid_inputs_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "output.zip"
            missing_documents = documents()
            del missing_documents["input/100.txt"]
            with self.assertRaisesRegex(ValueError, "document keys"):
                build_output_zip(missing_documents, predictions(), target)
            missing = predictions()
            del missing["input/100.txt"]
            with self.assertRaisesRegex(ValueError, "prediction keys"):
                build_output_zip(documents(), missing, target)
            extra = predictions()
            extra["input/101.txt"] = []
            with self.assertRaisesRegex(ValueError, "prediction keys"):
                build_output_zip(documents(), extra, target)
            invalid = predictions()
            invalid["input/1.txt"] = [{"text": "document", "type": "THUỐC"}]
            with self.assertRaisesRegex(ValueError, "entity 0"):
                build_output_zip(documents(), invalid, target)
            self.assertFalse(target.exists())

    def test_refuses_existing_destination_and_missing_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            existing = Path(directory) / "existing.zip"
            existing.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                build_output_zip(documents(), predictions(), existing)
            with self.assertRaisesRegex(ValueError, "parent"):
                build_output_zip(
                    documents(),
                    predictions(),
                    Path(directory) / "missing" / "output.zip",
                )
            self.assertEqual(existing.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
