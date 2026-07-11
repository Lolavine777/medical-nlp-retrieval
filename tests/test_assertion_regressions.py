import unittest

from medical_race.assertions import classify_assertions
from medical_race.extraction import Span


class AssertionScopeRegressionTest(unittest.TestCase):
    def test_post_negation_does_not_cross_comma_delimited_results(self):
        raw = "12 bạch cầu, không vi khuẩn, 1 hồng cầu, âm tính nitrite"
        start = raw.index("bạch cầu")
        state = classify_assertions(
            raw,
            Span("bạch cầu", start, start + len("bạch cầu")),
        )
        self.assertFalse(state.negated)


if __name__ == "__main__":
    unittest.main()
