import unittest

from medical_race.linking.rxnorm import RxNormTerm, _normalize, link_drug


class RxNormLinkerPerformanceTest(unittest.TestCase):
    def test_reuses_normalized_terms_across_mentions(self):
        terms = tuple(
            RxNormTerm(str(index), f"drug {index}", "IN", "RXNORM", True)
            for index in range(100)
        )
        _normalize.cache_clear()
        link_drug("drug 1", terms)
        first = _normalize.cache_info()
        link_drug("drug 2", terms)
        second = _normalize.cache_info()
        self.assertGreater(second.hits, first.hits)


if __name__ == "__main__":
    unittest.main()
