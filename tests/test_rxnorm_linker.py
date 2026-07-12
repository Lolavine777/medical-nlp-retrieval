import unittest

from medical_race.linking.rxnorm import LinkResult, RxNormTerm, link_drug


TERMS = (
    RxNormTerm("1", "metoprolol", "IN", "RXNORM", True),
    RxNormTerm("2", "Seroquel", "BN", "RXNORM", True),
    RxNormTerm("3", "aspirin", "IN", "RXNORM", True),
    RxNormTerm("3", "ASPIRIN", "SU", "MTHSPL", False),
    RxNormTerm("4", "aspirin 325 MG Oral Tablet", "SCD", "RXNORM", True),
    RxNormTerm("5", "aspirin", "SY", "MTHSPL", False),
    RxNormTerm("6", "aspirin", "IN", "RXNORM", True),
)


class RxNormLinkerTest(unittest.TestCase):
    def test_links_generic_brand_and_regimen_text(self):
        self.assertEqual(
            link_drug("metoprolol", TERMS),
            LinkResult(("1",), "metoprolol"),
        )
        self.assertEqual(
            link_drug("seroquel", TERMS),
            LinkResult(("2",), "Seroquel"),
        )
        self.assertEqual(
            link_drug("aspirin 325mg daily", TERMS),
            LinkResult(("3",), "aspirin"),
        )

    def test_collapses_duplicate_rxcui_and_ranks_deterministically(self):
        result = link_drug("aspirin", TERMS, candidate_output="top2")
        self.assertEqual(result, LinkResult(("3", "6"), "aspirin"))

    def test_filters_ingredient_concepts_and_rejects_noise(self):
        result = link_drug(
            "aspirin 325 MG Oral Tablet",
            TERMS,
            concept_level="ingredient",
            candidate_output="top2",
        )
        self.assertEqual(result, LinkResult(("3", "6"), "aspirin"))
        self.assertIsNone(link_drug("thuốc giảm đau", TERMS))

    def test_rejects_unknown_policies(self):
        with self.assertRaisesRegex(ValueError, "concept level"):
            link_drug("aspirin", TERMS, concept_level="unknown")
        with self.assertRaisesRegex(ValueError, "candidate output"):
            link_drug("aspirin", TERMS, candidate_output="unknown")


if __name__ == "__main__":
    unittest.main()
