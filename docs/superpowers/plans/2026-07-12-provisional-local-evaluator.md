# Provisional Local Evaluator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic provisional evaluator with configurable hidden-policy assumptions and checkpoint evidence.

**Architecture:** One standard-library module contains an immutable policy, pure metric functions, deterministic one-to-one mention matching, and report aggregation.
One focused unittest module drives the implementation, and one checkpoint document separates mathematical behavior from evaluator assumptions.

**Tech Stack:** Python 3.11 standard library, `unittest`, frozen dataclasses.

## Global Constraints

- Work inline on `master` as authorized.
- Keep model parameters at `0 / 9B`.
- Add no external dependency, model, ontology code, CLI, or file loader.
- Do not call any matching policy official.
- Preserve input ordering and duplicate mentions.
- Use `max(0, 1 - WER)` only as the configurable provisional default.
- Use exact `(type, position)` and exact `(type, text, position)` as the initial matching policies.
- Represent unmatched gold and prediction mentions explicitly with zero component scores.

---

### Task 1: Provisional evaluator and checkpoint evidence

**Files:**

- Create: `src/medical_race/evaluate/__init__.py`
- Create: `tests/test_evaluate.py`
- Create: `docs/evaluator_checkpoint_2026-07-12.md`

**Interfaces:**

- Consumes: validated-style entity lists containing `text`, `type`, `position`, and optional `assertions` or `candidates`.
- Produces: `EvaluationPolicy`, `word_error_rate`, `set_jaccard`, `match_mentions`, and `evaluate_entities`.
- Produces: an evaluation report containing `matching_policy`, `records`, `text_score`, `assertions_score`, `candidates_score`, and `total_score`.

- [ ] **Step 1: Write the failing evaluator tests**

Create `tests/test_evaluate.py` with focused tests for metric arithmetic, empty conventions, deterministic duplicate assignment, policy isolation, unmatched penalties, weights, and invalid inputs.

```python
import unittest

from medical_race.evaluate import (
    EvaluationPolicy,
    evaluate_entities,
    match_mentions,
    set_jaccard,
    word_error_rate,
)


def entity(text, entity_type, start, assertions=None, candidates=None):
    value = {"text": text, "type": entity_type, "position": [start, start + len(text)]}
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
        gold = [entity("ho", "TRIỆU_CHỨNG", 0), entity("ho", "TRIỆU_CHỨNG", 10)]
        predictions = [gold[1].copy(), gold[0].copy()]
        self.assertEqual(match_mentions(gold, predictions), [(0, 1), (1, 0)])

    def test_matching_policy_changes_assignment_only(self):
        gold = [entity("ho", "TRIỆU_CHỨNG", 0, assertions=[])]
        predictions = [entity("sốt", "TRIỆU_CHỨNG", 0, assertions=[])]
        loose = evaluate_entities(gold, predictions)
        strict = evaluate_entities(
            gold,
            predictions,
            EvaluationPolicy(matching_policy="type_text_position"),
        )
        self.assertEqual(len(loose["records"]), 1)
        self.assertEqual(loose["records"][0]["status"], "matched")
        self.assertEqual(len(strict["records"]), 2)
        self.assertTrue(all(record["status"] != "matched" for record in strict["records"]))

    def test_unmatched_wrong_type_has_two_explicit_zero_records(self):
        gold = [entity("ho", "TRIỆU_CHỨNG", 0, assertions=[])]
        predictions = [entity("ho", "CHẨN_ĐOÁN", 0, assertions=[], candidates=["X"])]
        report = evaluate_entities(gold, predictions)
        self.assertEqual(len(report["records"]), 2)
        self.assertEqual(report["total_score"], 0.0)
        self.assertTrue(all(record["text_score"] == 0.0 for record in report["records"]))

    def test_components_weights_and_empty_inputs(self):
        gold = [entity("a", "THUỐC", 0, assertions=[], candidates=["1"])]
        predictions = [entity("b", "THUỐC", 0, assertions=[], candidates=["1"])]
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
            (empty["text_score"], empty["assertions_score"], empty["candidates_score"], empty["total_score"]),
            (1.0, 1.0, 1.0, 1.0),
        )

    def test_invalid_policy_and_entity_values_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "matching policy"):
            EvaluationPolicy(matching_policy="unknown")
        with self.assertRaisesRegex(ValueError, "weights"):
            EvaluationPolicy(weights=(0.3, 0.3, 0.3))
        with self.assertRaisesRegex(ValueError, "position"):
            evaluate_entities([{"text": "a", "type": "X", "position": [True, 1]}], [])
        with self.assertRaisesRegex(ValueError, "assertions"):
            evaluate_entities([entity("a", "X", 0, assertions=[1])], [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest tests.test_evaluate -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'medical_race.evaluate'`.

- [ ] **Step 3: Implement the minimum evaluator**

Create `src/medical_race/evaluate/__init__.py`.
Use a frozen `EvaluationPolicy` with `matching_policy="type_position"`, `empty_set_score=1.0`, and `weights=(0.3, 0.3, 0.4)`.
Validate policy values in `__post_init__` with `math.isfinite` and `math.isclose`.
Implement token-level Levenshtein distance with one dynamic-programming row.
Implement Jaccard through Python sets.
Validate both entity lists before matching, including string `text` and `type`, a two-integer non-boolean `position`, and optional string lists.
Match gold mentions in order to the first unused prediction with the configured exact key, then append unused predictions.
Return dictionaries for records and the aggregate report so callers need no serialization layer or extra report classes.

The public signatures are:

```python
@dataclass(frozen=True)
class EvaluationPolicy:
    matching_policy: str = "type_position"
    empty_set_score: float = 1.0
    weights: tuple[float, float, float] = (0.3, 0.3, 0.4)


def word_error_rate(reference: str, hypothesis: str) -> float: ...


def set_jaccard(left: object, right: object, empty_score: float = 1.0) -> float: ...


def match_mentions(
    gold: object,
    predictions: object,
    matching_policy: str = "type_position",
) -> list[tuple[int | None, int | None]]: ...


def evaluate_entities(
    gold: object,
    predictions: object,
    policy: EvaluationPolicy = EvaluationPolicy(),
) -> dict[str, object]: ...
```

- [ ] **Step 4: Run the focused test and verify GREEN**

Run:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest tests.test_evaluate -v
```

Expected: seven tests pass.

- [ ] **Step 5: Write checkpoint evidence**

Create `docs/evaluator_checkpoint_2026-07-12.md`.
Record the exact focused and full verification commands, implemented functions, default weights, matching policies, explicit penalties, model budget `0 / 9B`, and the next roadmap checkpoint.
State that Levenshtein WER and set Jaccard are mathematical implementation choices, while assignment, empty-set scoring, WER aggregation, missing-field behavior, and WER-to-score conversion are hidden-policy assumptions.
State that no leaderboard claim or official evaluator equivalence follows from local passing tests.

- [ ] **Step 6: Run complete verification**

Run:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q src tools tests
git diff --check
```

Expected: 56 tests pass, compilation exits `0`, and `git diff --check` produces no output.

- [ ] **Step 7: Commit the evaluator checkpoint**

```powershell
git add src/medical_race/evaluate/__init__.py tests/test_evaluate.py docs/evaluator_checkpoint_2026-07-12.md
git commit -m "feat: add provisional local evaluator"
```
