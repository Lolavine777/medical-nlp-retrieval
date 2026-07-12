import unittest

from medical_race.linking.rxnorm import RxNormTerm, _term_index, link_drug


class RxNormIndexTest(unittest.TestCase):
    def test_reuses_term_index_across_mentions(self):
        terms = tuple(
            RxNormTerm(str(index), f"drug {index}", "IN", "RXNORM", True)
            for index in range(1000)
        )
        _term_index.cache_clear()
        self.assertEqual(link_drug("drug 10 daily", terms).candidates, ("10",))
        first = _term_index.cache_info()
        self.assertEqual(link_drug("drug 20 daily", terms).candidates, ("20",))
        second = _term_index.cache_info()
        self.assertGreater(second.hits, first.hits)

    def test_keeps_reverse_containment_for_short_spans(self):
        terms = (
            RxNormTerm("1", "aspirin 325 MG Oral Tablet", "SCD", "RXNORM", True),
        )
        self.assertEqual(link_drug("aspirin 325 mg", terms).candidates, ("1",))


if __name__ == "__main__":
    unittest.main()
