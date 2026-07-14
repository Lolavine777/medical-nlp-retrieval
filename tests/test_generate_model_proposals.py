import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from medical_race.model_proposals import (
    MODEL_ID,
    MODEL_PARAMETERS,
    MODEL_REVISION,
    PROMPT_HEADER,
    read_proposal_directory,
)
from tools.generate_model_proposals import (
    generate_document,
    generate_proposal_directory,
)


RAW = "Triệu chứng hiện tại\n- đau ngực\nChẩn đoán\nViêm phổi\n"


def manifest():
    return {
        "format_version": 1,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_parameters": MODEL_PARAMETERS,
        "prompt_version": 1,
        "prompt_sha256": hashlib.sha256(PROMPT_HEADER.encode("utf-8")).hexdigest(),
        "generation": {"do_sample": False, "max_new_tokens": 2048},
    }


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class GenerateDocumentTests(unittest.TestCase):
    def test_parses_chunks_and_counts_fail_closed_errors(self):
        responses = iter(
            [
                '[{"line_index":1,"text":"đau ngực","type":"TRIỆU_CHỨNG"}]',
                "not json",
            ]
        )

        result = generate_document(RAW, lambda prompt: next(responses), max_chars=40)

        self.assertEqual(result["chunk_count"], 2)
        self.assertEqual(result["parse_error_count"], 1)
        self.assertEqual(
            result["proposals"],
            [{"line_index": 1, "text": "đau ngực", "type": "TRIỆU_CHỨNG"}],
        )

    def test_rejects_a_response_referring_outside_its_chunk(self):
        responses = iter(
            ['[{"line_index":3,"text":"Viêm phổi","type":"CHẨN_ĐOÁN"}]', "[]"]
        )
        result = generate_document(
            RAW,
            lambda prompt: next(responses),
            max_chars=40,
        )

        self.assertEqual(result["proposals"], [])
        self.assertEqual(result["parse_error_count"], 1)


class ProposalDirectoryTests(unittest.TestCase):
    def test_reads_strict_manifest_and_document_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "manifest.json", manifest())
            write_json(
                root / "documents" / "1.json",
                {
                    "name": "input/1.txt",
                    "raw_sha256": hashlib.sha256(RAW.encode("utf-8")).hexdigest(),
                    "chunk_count": 1,
                    "parse_error_count": 0,
                    "proposals": [
                        {"line_index": 1, "text": "đau ngực", "type": "TRIỆU_CHỨNG"}
                    ],
                },
            )

            proposals = read_proposal_directory(root, {"input/1.txt": RAW})

            self.assertEqual(proposals["input/1.txt"][0].text, "đau ngực")

    def test_rejects_wrong_input_hash_model_revision_and_extra_manifest_key(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = manifest()
            write_json(root / "manifest.json", value)
            write_json(
                root / "documents" / "1.json",
                {
                    "name": "input/1.txt",
                    "raw_sha256": hashlib.sha256(RAW.encode("utf-8")).hexdigest(),
                    "chunk_count": 0,
                    "parse_error_count": 0,
                    "proposals": [],
                },
            )
            with self.assertRaisesRegex(ValueError, "input SHA-256"):
                read_proposal_directory(root, {"input/1.txt": "changed"})

            value["model_revision"] = "wrong"
            write_json(root / "manifest.json", value)
            with self.assertRaisesRegex(ValueError, "model revision"):
                read_proposal_directory(root, {"input/1.txt": RAW})

            value = manifest()
            value["extra"] = True
            write_json(root / "manifest.json", value)
            with self.assertRaisesRegex(ValueError, "manifest fields"):
                read_proposal_directory(root, {"input/1.txt": RAW})

            value = manifest()
            value["prompt_version"] = True
            write_json(root / "manifest.json", value)
            with self.assertRaisesRegex(ValueError, "prompt version"):
                read_proposal_directory(root, {"input/1.txt": RAW})

            value = manifest()
            value["generation"]["do_sample"] = 0
            write_json(root / "manifest.json", value)
            with self.assertRaisesRegex(ValueError, "generation configuration"):
                read_proposal_directory(root, {"input/1.txt": RAW})

    def test_rejects_missing_extra_and_nondeterministic_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "manifest.json", manifest())
            write_json(
                root / "documents" / "1.json",
                {
                    "name": "input/1.txt",
                    "raw_sha256": hashlib.sha256(RAW.encode("utf-8")).hexdigest(),
                    "chunk_count": 1,
                    "parse_error_count": 0,
                    "proposals": [
                        {"line_index": 3, "text": "Viêm phổi", "type": "CHẨN_ĐOÁN"},
                        {"line_index": 1, "text": "đau ngực", "type": "TRIỆU_CHỨNG"},
                    ],
                },
            )
            with self.assertRaisesRegex(ValueError, "deterministic order"):
                read_proposal_directory(root, {"input/1.txt": RAW})

            write_json(root / "documents" / "2.json", {})
            with self.assertRaisesRegex(ValueError, "document files"):
                read_proposal_directory(root, {"input/1.txt": RAW})


class ResumableGenerationTests(unittest.TestCase):
    def test_skips_valid_files_and_regenerates_invalid_partial_files(self):
        calls = []

        def generate(prompt):
            calls.append(prompt)
            return "[]"

        documents = {"input/1.txt": RAW}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generate_proposal_directory(documents, root, generate, max_chars=6000)
            first_calls = len(calls)
            generate_proposal_directory(documents, root, generate, max_chars=6000)
            self.assertEqual(len(calls), first_calls)

            record_path = root / "documents" / "1.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["raw_sha256"] = "0" * 64
            write_json(record_path, record)
            generate_proposal_directory(documents, root, generate, max_chars=6000)

            self.assertGreater(len(calls), first_calls)
            self.assertFalse(list(root.rglob("*.tmp")))
            read_proposal_directory(root, documents)


if __name__ == "__main__":
    unittest.main()
