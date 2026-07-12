import unittest

from medical_race.evaluate import EvaluationPolicy, evaluate_entities


class TextScorePolicyTest(unittest.TestCase):
    def test_wer_to_score_conversion_is_configurable(self):
        gold = [{"text": "a", "type": "X", "position": [0, 1]}]
        predictions = [{"text": "x y", "type": "X", "position": [0, 1]}]
        clipped = evaluate_entities(gold, predictions)
        raw = evaluate_entities(
            gold,
            predictions,
            EvaluationPolicy(text_score_policy="one_minus_wer"),
        )
        self.assertEqual(clipped["records"][0]["wer"], 2.0)
        self.assertEqual(clipped["text_score"], 0.0)
        self.assertEqual(raw["text_score"], -1.0)
        with self.assertRaisesRegex(ValueError, "text score policy"):
            EvaluationPolicy(text_score_policy="unknown")


if __name__ == "__main__":
    unittest.main()
