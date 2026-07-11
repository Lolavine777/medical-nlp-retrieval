import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.audit_sources import (
    audit_documents,
    audit_official_html,
    read_zip_documents,
    validate_document_names,
)


class AuditSourcesTest(unittest.TestCase):
    def test_reads_utf8_txt_entries_in_numeric_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("input/2.txt", "hai\n")
                archive.writestr("input/1.txt", "một\n")
            self.assertEqual(
                list(read_zip_documents(path)),
                ["input/1.txt", "input/2.txt"],
            )

    def test_rejects_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("input/1.txt", b"\xff")
            with self.assertRaises(UnicodeDecodeError):
                read_zip_documents(path)

    def test_counts_lines_headers_and_cues(self):
        report = audit_documents(
            {
                "input/1.txt": (
                    "1. Tiền sử bệnh\n"
                    "Không sốt\n"
                    "Xét nghiệm\n"
                    "Creatinin 120 umol/L\n"
                )
            }
        )
        self.assertEqual(report["line_count"]["sum"], 4)
        self.assertEqual(report["section_headers"]["Tiền sử bệnh"], 1)
        self.assertEqual(report["section_headers"]["Xét nghiệm"], 1)
        self.assertEqual(report["negation_cue_count"]["sum"], 1)
        self.assertEqual(report["lab_like_line_count"]["sum"], 2)

    def test_requires_exact_document_paths(self):
        with self.assertRaisesRegex(ValueError, "input/1.txt through input/100.txt"):
            validate_document_names([f"other/{value}.txt" for value in range(1, 101)])

    def test_parses_official_html_evidence(self):
        source = """
        <p>Word Error Rate (WER), Jaccard similarity, self-host, 9B params</p>
        <pre><code class="language-json">[
          {&quot;text&quot;:&quot;lo âu&quot;,&quot;type&quot;:&quot;TRIỆU_CHỨNG&quot;,&quot;assertions&quot;:[],&quot;position&quot;:[0,5]},
          {&quot;text&quot;:&quot;lo âu&quot;,&quot;type&quot;:&quot;TRIỆU_CHỨNG&quot;,&quot;assertions&quot;:[],&quot;position&quot;:[6,11]}
        ]</code></pre>
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "official.html"
            path.write_text(source, encoding="utf-8")
            report = audit_official_html(path)
        self.assertEqual(report["example_entity_count"], 2)
        self.assertEqual(report["duplicate_surface_counts"], {"lo âu": 2})
        self.assertTrue(report["mentions_wer"])
        self.assertTrue(report["mentions_jaccard"])
        self.assertTrue(report["mentions_self_host"])
        self.assertTrue(report["mentions_9b_limit"])


if __name__ == "__main__":
    unittest.main()
