import unittest

from medical_race.linking.rxnorm import RxNormTerm, link_drug


class RxNormPrecisionTest(unittest.TestCase):
    def test_dose_form_terms_do_not_link_as_drug_concepts(self):
        terms = (
            RxNormTerm("746839", "Pack", "DF", "RXNORM", False),
            RxNormTerm("999", "Tablet", "DF", "RXNORM", False),
        )
        self.assertIsNone(link_drug("z-pack", terms))
        self.assertIsNone(link_drug("tablet", terms))


if __name__ == "__main__":
    unittest.main()
