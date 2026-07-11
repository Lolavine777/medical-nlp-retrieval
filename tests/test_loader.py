import unittest
from dataclasses import FrozenInstanceError

from medical_race.loader import casefold_with_mapping, load_document


class LoaderTest(unittest.TestCase):
    def test_preserves_raw_text_and_line_endings(self):
        raw = "đau ngực\r\nkhông sốt\n"
        document = load_document("input/1.txt", raw.encode("utf-8"))
        self.assertEqual(document.name, "input/1.txt")
        self.assertEqual(document.raw_text, raw)

    def test_rejects_invalid_utf8(self):
        with self.assertRaises(UnicodeDecodeError):
            load_document("input/1.txt", b"\xff")

    def test_raw_document_is_immutable(self):
        document = load_document("input/1.txt", b"text")
        with self.assertRaises(FrozenInstanceError):
            document.raw_text = "changed"

    def test_casefold_view_maps_expansion_back_to_raw_span(self):
        view = casefold_with_mapping("ĐAU ß")
        self.assertEqual(view.text, "đau ss")
        self.assertEqual(view.raw_span(0, 3), (0, 3))
        self.assertEqual(view.raw_span(4, 6), (4, 5))

    def test_casefold_view_rejects_invalid_span(self):
        view = casefold_with_mapping("đau")
        with self.assertRaises(ValueError):
            view.raw_span(2, 4)


if __name__ == "__main__":
    unittest.main()
