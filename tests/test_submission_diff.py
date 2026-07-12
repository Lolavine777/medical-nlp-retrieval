import tempfile
import unittest
from pathlib import Path

from medical_race.submission import build_output_zip
from medical_race.submission_diff import diff_submission_archives


RAW = "aspirin 325mg metoprolol creatinine 1.4"


def documents():
    return {f"input/{index}.txt": RAW for index in range(1, 101)}


def empty_predictions():
    return {f"input/{index}.txt": [] for index in range(1, 101)}


def drug(text, candidate):
    start = RAW.index(text)
    return {
        "text": text,
        "type": "THUỐC",
        "candidates": [candidate],
        "assertions": [],
        "position": [start, start + len(text)],
    }


class SubmissionDiffTest(unittest.TestCase):
    def test_reports_added_entities_span_changes_and_candidate_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = empty_predictions()
            child = empty_predictions()
            parent["input/1.txt"] = [
                drug("aspirin 325mg", "1"),
                drug("metoprolol", "2"),
            ]
            child["input/1.txt"] = [
                drug("aspirin", "1"),
                drug("metoprolol", "3"),
                {
                    "text": "creatinine",
                    "type": "TÊN_XÉT_NGHIỆM",
                    "position": [RAW.index("creatinine"), RAW.index("creatinine") + 10],
                },
                {
                    "text": "1.4",
                    "type": "KẾT_QUẢ_XÉT_NGHIỆM",
                    "position": [RAW.index("1.4"), RAW.index("1.4") + 3],
                },
            ]
            parent_zip = root / "parent.zip"
            child_zip = root / "child.zip"
            build_output_zip(documents(), parent, parent_zip)
            build_output_zip(documents(), child, child_zip)
            report = diff_submission_archives(parent_zip, child_zip)
            self.assertEqual(report["added_entities"], 2)
            self.assertEqual(report["removed_entities"], 0)
            self.assertEqual(report["changed_entities"], 2)
            self.assertEqual(report["changed_candidates"], 1)
            self.assertEqual(report["changed_assertions"], 0)
            self.assertEqual(report["changed_text"], 1)
            self.assertEqual(report["changed_position"], 1)
            self.assertEqual(report["changed_type"], 0)


if __name__ == "__main__":
    unittest.main()
