import unittest

from medical_race.linking.icd10 import ICD10Term, build_term_index


class CodableICD10IndexTests(unittest.TestCase):
    def test_indexes_only_leaf_codes_while_retaining_same_code_parent_aliases(self):
        terms = (
            ICD10Term("A00-A09", "Bệnh nhiễm trùng đường ruột", "section", False),
            ICD10Term("C97", "U ác nhiều vị trí", "subsection", False),
            ICD10Term("C97", "Ung thư nguyên phát đa ổ", "type", True),
        )

        index = build_term_index(terms)

        self.assertNotIn("bệnh nhiễm trùng đường ruột", index)
        self.assertEqual(index["u ác nhiều vị trí"].code, "C97")
        self.assertEqual(index["ung thư nguyên phát đa ổ"].code, "C97")


if __name__ == "__main__":
    unittest.main()
