import unittest

from medical_race.evaluate import (
    EvaluationPolicy,
    evaluate_entities,
    match_mentions,
    set_jaccard,
    word_error_rate,
)


def entity(text, entity_type, start, assertions=None, candidates=None):
    value = {
        "text": text,
        "type": entity_type,
        "position": [start, start + len(text)],
    }
    if assertions is not None:
        value["assertions"] = assertions
    if candidates is not None:
        value["candidates"] = candidates
    return value


class MetricTest(unittest.TestCase):
    def test_word_error_rate_covers_edits_and_empty_reference(self):
        self.assertAlmostEqual(word_error_rate("a b c", "a x c"), 1 / 3)
        self.assertAlmostEqual(word_error_rate("a b", "a x b"), 1 / 2)
        self.assertAlmostEqual(word_error_rate("a b c", "a c"), 1 / 3)
        self.assertEqual(word_error_rate("", ""), 0.0)
        self.assertEqual(word_error_rate("", "extra"), 1.0)

    def test_jaccard_has_explicit_empty_convention(self):
        self.assertEqual(set_jaccard(["a", "b"], ["b", "c"]), 1 / 3)
        self.assertEqual(set_jaccard([], []), 1.0)
        self.assertEqual(set_jaccard([], [], empty_score=0.0), 0.0)


class MatchingTest(unittest.TestCase):
    def test_duplicate_surface_mentions_are_assigned_by_position(self):
        gold = [
            entity("ho", "TRIỆU_CHỨNG", 0),
            entity("ho", "TRIỆU_CHỨNG", 10),
        ]
        predictions = [gold[1].copy(), gold[0].copy()]
        self.assertEqual(match_mentions(gold, predictions), [(0, 1), (1, 0)])

    def test_matching_policy_changes_assignment_only(self):
        gold = [entity("ho", "TRIỆU_CHỨNG", 0, assertions=[])]
        predictions = [entity("sốt", "TRIỆU_CHỨNG", 0, assertions=[])]
        predictions[0]["position"] = gold[0]["position"]
        loose = evaluate_entities(gold, predictions)
        strict = evaluate_entities(
            gold,
            predictions,
            EvaluationPolicy(matching_policy="type_text_position"),
        )
        self.assertEqual(len(loose["records"]), 1)
        self.assertEqual(loose["records"][0]["status"], "matched")
        self.assertEqual(len(strict["records"]), 2)
        self.assertTrue(
            all(record["status"] != "matched" for record in strict["records"])
        )

    def test_unmatched_wrong_type_has_two_explicit_zero_records(self):
        gold = [entity("ho", "TRIỆU_CHỨNG", 0, assertions=[])]
        predictions = [
            entity("ho", "CHẨN_ĐOÁN", 0, assertions=[], candidates=["X"])
        ]
        report = evaluate_entities(gold, predictions)
        self.assertEqual(len(report["records"]), 2)
        self.assertEqual(report["total_score"], 0.0)
        self.assertTrue(
            all(record["text_score"] == 0.0 for record in report["records"])
        )

    def test_components_weights_and_empty_inputs(self):
        gold = [entity("a", "THUỐC", 0, assertions=[], candidates=["1"])]
        predictions = [
            entity("b", "THUỐC", 0, assertions=[], candidates=["1"])
        ]
        report = evaluate_entities(
            gold,
            predictions,
            EvaluationPolicy(weights=(0.5, 0.25, 0.25)),
        )
        self.assertEqual(report["text_score"], 0.0)
        self.assertEqual(report["assertions_score"], 1.0)
        self.assertEqual(report["candidates_score"], 1.0)
        self.assertEqual(report["total_score"], 0.5)
        empty = evaluate_entities([], [])
        self.assertEqual(
            (
                empty["text_score"],
                empty["assertions_score"],
                empty["candidates_score"],
                empty["total_score"],
            ),
            (1.0, 1.0, 1.0, 1.0),
        )

    def test_invalid_policy_and_entity_values_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "matching policy"):
            EvaluationPolicy(matching_policy="unknown")
        with self.assertRaisesRegex(ValueError, "weights"):
            EvaluationPolicy(weights=(0.3, 0.3, 0.3))
        with self.assertRaisesRegex(ValueError, "position"):
            evaluate_entities(
                [{"text": "a", "type": "X", "position": [True, 1]}], []
            )
        with self.assertRaisesRegex(ValueError, "assertions"):
            evaluate_entities([entity("a", "X", 0, assertions=[1])], [])


if __name__ == "__main__":
    unittest.main()
