import tempfile
import unittest
from pathlib import Path

from tools.run_kaggle_s009 import (
    _worker_environment,
    merge_shards,
    prepare_input_zip,
    wait_for_workers,
)
from tools.audit_sources import read_zip_documents
from tools.generate_model_proposals import generate_proposal_directory, select_document_shard


def write_documents(root: Path, prefix: str = "") -> Path:
    directory = root / prefix / "input"
    directory.mkdir(parents=True)
    for index in range(1, 101):
        (directory / f"{index}.txt").write_text(f"Document {index}\n", encoding="utf-8")
    return directory


class InputPreparationTests(unittest.TestCase):
    def test_builds_canonical_zip_from_one_hundred_text_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = write_documents(root)

            output = prepare_input_zip(root, root / "working.zip")

            self.assertEqual(output, root / "working.zip")
            self.assertEqual(len(read_zip_documents(output)), 100)
            self.assertEqual(
                read_zip_documents(output)["input/1.txt"],
                source.joinpath("1.txt").read_bytes().decode("utf-8"),
            )

    def test_rejects_ambiguous_different_document_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_documents(root, "one")
            other = write_documents(root, "two")
            (other / "1.txt").write_text("different\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "ambiguous"):
                prepare_input_zip(root, root / "working.zip")


class MergeTests(unittest.TestCase):
    def test_requires_exactly_two_shards(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            documents = {
                f"input/{index}.txt": f"Document {index}\n"
                for index in range(1, 101)
            }

            with self.assertRaisesRegex(ValueError, "exactly two"):
                merge_shards([root / "only-shard"], root / "final", documents, 2500)

    def test_merges_two_valid_shards_and_validates_all_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_documents(root)
            documents = {
                f"input/{index}.txt": f"Document {index}\n"
                for index in range(1, 101)
            }
            shards = []
            for shard_index in range(2):
                shard = root / f"shard-{shard_index}"
                (shard / "documents").mkdir(parents=True)
                (shard / "manifest.json").write_text(
                    '{"format_version":1}\n', encoding="utf-8"
                )
                for index in range(shard_index + 1, 101, 2):
                    (shard / "documents" / f"{index}.json").write_text(
                        "{}\n", encoding="utf-8"
                    )
                shards.append(shard)

            with self.assertRaises(ValueError):
                merge_shards(shards, root / "final", documents, 2500)


class ValidMergeTests(unittest.TestCase):
    def test_merges_valid_shards(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = write_documents(root)
            documents = {
                f"input/{index}.txt": (source / f"{index}.txt").read_text(encoding="utf-8")
                for index in range(1, 101)
            }
            shards = []
            for shard_index in range(2):
                shard = root / f"valid-shard-{shard_index}"
                generate_proposal_directory(
                    select_document_shard(documents, shard_index, 2),
                    shard,
                    lambda prompt: "[]",
                    2500,
                )
                shards.append(shard)

            summary = merge_shards(shards, root / "final", documents, 2500)

            self.assertEqual(summary["documents"], 100)
            self.assertEqual(summary["proposals"], 0)


class WorkerTests(unittest.TestCase):
    def test_builds_linux_pythonpath_for_kaggle_worker(self):
        environment = _worker_environment(1)

        self.assertEqual(environment["CUDA_VISIBLE_DEVICES"], "1")
        self.assertEqual(
            environment["PYTHONPATH"],
            f"{Path(__file__).resolve().parents[1] / 'src'}:{Path(__file__).resolve().parents[1]}",
        )
    def test_waits_for_every_worker_before_returning_exit_codes(self):
        waited = []

        class Worker:
            def __init__(self, index, code):
                self.index = index
                self.code = code

            def wait(self):
                waited.append(self.index)
                return self.code

        self.assertEqual(
            wait_for_workers([Worker(0, 1), Worker(1, 0)]),
            (1, 0),
        )
        self.assertEqual(waited, [0, 1])


if __name__ == "__main__":
    unittest.main()
