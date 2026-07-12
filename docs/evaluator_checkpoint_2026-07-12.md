# Provisional evaluator checkpoint - 2026-07-12

## Result

- Added a standard-library evaluator at `src/medical_race/evaluate/__init__.py`.
- Added token-level Levenshtein word error rate and set Jaccard functions.
- Added deterministic one-to-one mention assignment in gold order.
- Added exact `(type, position)` and exact `(type, text, position)` policies.
- Added explicit unmatched-gold and unmatched-prediction records with zero component scores.
- Added configurable empty-set Jaccard behavior and component weights.
- Added clipped and unclipped `1 - WER` text-score policies with clipping enabled by default.
- Applied the documented default weights `0.3`, `0.3`, and `0.4`.
- Kept raw WER in each matched record.
- Added no dependency, ontology, model, CLI, or submission behavior.
- The active model parameter budget remains `0 / 9B`.

## Verification

The focused command was:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest tests.test_evaluate tests.test_evaluate_text_policy -v
```

All 8 evaluator tests passed.

The complete commands were:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q src tools tests
git diff --check
```

All 57 tests passed in 0.260 seconds.
Compilation exited successfully.
`git diff --check` produced no output.

## Mathematical implementation

Word error rate uses `str.split()` words, token-level Levenshtein distance, and reference-word normalization.
Set Jaccard uses intersection size divided by union size.
Component aggregation uses arithmetic means followed by the configured weighted sum.

These statements describe local mathematics only.
They do not establish organizer implementation details.

## Hidden-policy assumptions

Mention assignment order, exact matching keys, position use, WER aggregation, empty-reference behavior, empty-set scoring, missing-field behavior, unmatched penalties, and the WER-to-score conversion remain hidden evaluator variables.
The defaults are experiment controls, not official behavior.
Passing local tests provides no leaderboard evidence and makes no claim of official evaluator equivalence.

## Strategic impact

The project now has a stable local scoring surface for controlled prediction comparisons.
The next priority is legally usable versioned ICD and RxNorm ingestion with provenance, followed by lexical candidate retrieval.
Symptom and diagnosis extraction and the one-command non-empty baseline remain incomplete.
