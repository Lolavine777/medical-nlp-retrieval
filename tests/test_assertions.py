import unittest

from medical_race.assertions import AssertionState, classify_assertions
from medical_race.extraction import Span


def span_for(raw: str, text: str) -> Span:
    start = raw.index(text)
    return Span(text, start, start + len(text))


class AssertionStateTest(unittest.TestCase):
    def test_default_state_maps_to_no_organizer_labels(self):
        raw = "Bệnh nhân đau ngực"
        state = classify_assertions(raw, span_for(raw, "đau ngực"))
        self.assertEqual(state, AssertionState(False, "current", "patient"))
        self.assertEqual(state.labels(), ())

    def test_labels_have_stable_known_order(self):
        state = AssertionState(True, "historical", "family")
        self.assertEqual(state.labels(), ("isNegated", "isFamily", "isHistorical"))

    def test_rejects_empty_or_mismatched_span(self):
        with self.assertRaises(ValueError):
            classify_assertions("đau ngực", Span("", 0, 0))
        with self.assertRaisesRegex(ValueError, "offset mismatch"):
            classify_assertions("đau ngực", Span("đau", 1, 5))


class AssertionRuleTest(unittest.TestCase):
    def test_negation_stops_at_contrast_terminator(self):
        raw = "không đau ngực nhưng sốt"
        self.assertTrue(classify_assertions(raw, span_for(raw, "đau ngực")).negated)
        self.assertFalse(classify_assertions(raw, span_for(raw, "sốt")).negated)

    def test_post_mention_negative_result_is_negated(self):
        raw = "xét nghiệm viêm gan âm tính"
        self.assertTrue(classify_assertions(raw, span_for(raw, "viêm gan")).negated)

    def test_section_priors_distinguish_past_from_current_illness(self):
        past = "Tiền sử bệnh\n- tăng huyết áp"
        current = "Bệnh sử hiện tại\n- đau ngực"
        self.assertEqual(
            classify_assertions(past, span_for(past, "tăng huyết áp")).temporality,
            "historical",
        )
        self.assertEqual(
            classify_assertions(current, span_for(current, "đau ngực")).temporality,
            "current",
        )

    def test_local_temporality_overrides_section_default(self):
        historical = "Đánh giá tại bệnh viện\nBệnh nhân đã từng đột quỵ"
        hypothetical = "Tiền sử bệnh\nNếu xuất hiện sốt sẽ tái khám"
        self.assertEqual(
            classify_assertions(historical, span_for(historical, "đột quỵ")).temporality,
            "historical",
        )
        self.assertEqual(
            classify_assertions(hypothetical, span_for(hypothetical, "sốt")).temporality,
            "hypothetical",
        )

    def test_family_experiencer_differs_from_family_reporter(self):
        family = "Mẹ của bệnh nhân bị ung thư phổi"
        reporter = "Gia đình nhận thấy bệnh nhân đau ngực"
        self.assertEqual(
            classify_assertions(family, span_for(family, "ung thư phổi")).experiencer,
            "family",
        )
        self.assertEqual(
            classify_assertions(reporter, span_for(reporter, "đau ngực")).experiencer,
            "patient",
        )


if __name__ == "__main__":
    unittest.main()
