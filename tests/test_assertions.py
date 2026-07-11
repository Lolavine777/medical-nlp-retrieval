import unittest

from medical_race.assertions import AssertionState, classify_assertions
from medical_race.extraction import Span


class AssertionStateTest(unittest.TestCase):
    def test_default_state_maps_to_no_organizer_labels(self):
        raw = "Bệnh nhân đau ngực"
        start = raw.index("đau ngực")
        state = classify_assertions(raw, Span("đau ngực", start, start + len("đau ngực")))
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


if __name__ == "__main__":
    unittest.main()
