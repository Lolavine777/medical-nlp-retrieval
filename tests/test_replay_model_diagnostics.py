import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from medical_race.model_proposals import PROMPT_ALLOWED_TYPES, read_proposal_directory
from tools.generate_model_proposals import _manifest
from tools.replay_model_diagnostics import replay_proposals


def write_json(archive, name, value):
    archive.writestr(name, json.dumps(value, ensure_ascii=False, sort_keys=True))


class ReplayModelDiagnosticsTests(unittest.TestCase):
    def test_replay_keeps_valid_sibling_and_preserves_chunk_error_count(self):
        valid_type = sorted(PROMPT_ALLOWED_TYPES[2])[0]
        documents = {
            f"input/{index}.txt": "symptoms\ncough headache\n"
            for index in range(1, 101)
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_zip = root / "input.zip"
            proposal_zip = root / "proposals.zip"
            diagnostics_zip = root / "diagnostics.zip"
            output = root / "replayed"

            with zipfile.ZipFile(input_zip, "w") as archive:
                for name, raw_text in documents.items():
                    archive.writestr(name, raw_text)
            with zipfile.ZipFile(proposal_zip, "w") as archive:
                write_json(archive, "qwen3-4b-s010/manifest.json", _manifest(2))
                for name, raw_text in documents.items():
                    index = Path(name).stem
                    proposals = []
                    if index == "1":
                        proposals = [
                            {
                                "line_index": 1,
                                "text": "cough",
                                "type": valid_type,
                            }
                        ]
                    write_json(
                        archive,
                        f"qwen3-4b-s010/documents/{index}.json",
                        {
                            "name": name,
                            "raw_sha256": hashlib.sha256(
                                raw_text.encode("utf-8")
                            ).hexdigest(),
                            "chunk_count": 1,
                            "parse_error_count": 1 if index == "1" else 0,
                            "proposals": proposals,
                        },
                    )
            with zipfile.ZipFile(diagnostics_zip, "w") as archive:
                write_json(
                    archive,
                    "qwen3-4b-s010-diagnostics/1.json",
                    {
                        "name": "input/1.txt",
                        "prompt_version": 2,
                        "failures": [
                            {
                                "document": "input/1.txt",
                                "chunk_index": 0,
                                "prompt_version": 2,
                                "category": "grounding",
                                "raw_response": (
                                    '[{"line_index":1,"text":"cough","type":"'
                                    + valid_type
                                    + '"},{"line_index":1,"text":"headache",'
                                    '"type":"'
                                    + valid_type
                                    + '"},{"line_index":1,"text":"fever",'
                                    '"type":"'
                                    + valid_type
                                    + '"}]'
                                ),
                            }
                        ],
                    },
                )

            summary = replay_proposals(
                input_zip,
                proposal_zip,
                diagnostics_zip,
                output,
            )

            proposals = read_proposal_directory(output, documents)
            self.assertEqual(
                {proposal.text for proposal in proposals["input/1.txt"]},
                {"cough", "headache"},
            )
            record = json.loads(
                (output / "documents" / "1.json").read_text(encoding="utf-8")
            )
            self.assertEqual(record["parse_error_count"], 1)
            self.assertEqual(summary["recovered"], 1)
            self.assertEqual(summary["rejected"], 1)


if __name__ == "__main__":
    unittest.main()
