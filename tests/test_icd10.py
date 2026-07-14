import hashlib
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from medical_race.linking.icd10 import (
    ICD10Term,
    build_term_index,
    link_diagnosis,
    normalize_icd_text,
    read_icd10_snapshot,
)


def snapshot(nodes):
    return (
        json.dumps(
            {
                "format_version": 1,
                "language": "vi",
                "source_api": "https://example.test/api/ICD10",
                "nodes": nodes,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def node(code, name, model="category", is_leaf=True, node_id=None, parent=None):
    return {
        "model": model,
        "id": node_id or code,
        "code": code,
        "name": name,
        "is_leaf": is_leaf,
        "parent": parent,
    }


class ICD10ReaderTests(unittest.TestCase):
    def write_snapshot(self, data):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name, "icd.json")
        path.write_bytes(data)
        return path, hashlib.sha256(data).hexdigest()

    def test_reads_verified_immutable_terms(self):
        data = snapshot([node("A00", "Bệnh tả")])
        path, checksum = self.write_snapshot(data)

        terms = read_icd10_snapshot(path, checksum)

        self.assertEqual(terms, (ICD10Term("A00", "Bệnh tả", "category", True),))
        with self.assertRaises(FrozenInstanceError):
            terms[0].code = "X"

    def test_rejects_checksum_mismatch(self):
        path, _ = self.write_snapshot(snapshot([node("A00", "Bệnh tả")]))

        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            read_icd10_snapshot(path, "0" * 64)

    def test_rejects_malformed_snapshot_and_duplicate_node_identity(self):
        invalid_payloads = (
            b"[]\n",
            snapshot([{"code": "A00"}]),
            snapshot(
                [
                    node("A00", "Bệnh tả", node_id="same"),
                    node("A01", "Bệnh khác", node_id="same"),
                ]
            ),
        )
        for data in invalid_payloads:
            with self.subTest(data=data):
                path, checksum = self.write_snapshot(data)
                with self.assertRaises(ValueError):
                    read_icd10_snapshot(path, checksum)

    def test_allows_official_alias_nodes_for_the_same_code(self):
        data = snapshot(
            [
                node("C97", "U ác nhiều vị trí", model="subsection", is_leaf=False),
                node("C97", "Ung thư nguyên phát đa ổ", model="type", node_id="C97-leaf"),
            ]
        )
        path, checksum = self.write_snapshot(data)

        terms = read_icd10_snapshot(path, checksum)
        index = build_term_index(terms)

        self.assertEqual(len(terms), 2)
        self.assertEqual(index["u ác nhiều vị trí"].code, "C97")
        self.assertEqual(index["ung thư nguyên phát đa ổ"].code, "C97")

    def test_normalization_is_unicode_case_and_separator_stable(self):
        self.assertEqual(
            normalize_icd_text("  VIÊM  tủy-xương, mạn tính "),
            "viêm tủy xương mạn tính",
        )

    def test_index_prefers_leaf_and_rejects_ambiguous_leaf_titles(self):
        terms = (
            ICD10Term("A00", "Bệnh tả", "type", False),
            ICD10Term("A00.0", "Bệnh tả", "category", True),
            ICD10Term("B00.0", "Trùng tên", "category", True),
            ICD10Term("B00.1", "Trùng tên", "category", True),
        )

        index = build_term_index(terms)

        self.assertEqual(index["bệnh tả"].code, "A00.0")
        self.assertNotIn("trùng tên", index)

    def test_exact_top_one_link_uses_snapshot_code(self):
        index = build_term_index(
            (ICD10Term("M86.6", "Viêm tủy xương mạn tính", "category", True),)
        )

        linked = link_diagnosis("Viêm tủy-xương mạn tính", index)

        self.assertIsNotNone(linked)
        self.assertEqual(linked.code, "M86.6")
        self.assertIsNone(link_diagnosis("viêm tủy xương", index))


if __name__ == "__main__":
    unittest.main()
