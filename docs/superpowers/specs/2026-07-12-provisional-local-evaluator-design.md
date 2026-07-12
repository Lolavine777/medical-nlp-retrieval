# Provisional Local Evaluator Design

## Scope

Implement a deterministic, standard-library-only evaluator for local experiments.
The evaluator will make hidden matching assumptions explicit and configurable.
It will not claim to reproduce the official evaluator, load files, provide a command-line interface, generate predictions, or alter submission artifacts.
The active model parameter budget remains `0 / 9B`.

## Interface and policy

The implementation will live in `src/medical_race/evaluate/__init__.py`.
It will expose pure functions for word error rate, set Jaccard, mention matching, and complete entity-list evaluation.
An immutable policy value will select the mention key, empty-set Jaccard score, component weights, and the provisional WER-to-score conversion.

The first matching policies are exact `(type, position)` and exact `(type, text, position)`.
The default text score is `max(0, 1 - WER)`, while raw WER remains present in the report.
The default Jaccard score for two empty sets is `1.0`.
The default component weights are `0.3` for text, `0.3` for assertions, and `0.4` for candidates.
These defaults are working hypotheses, not organizer-confirmed evaluator behavior.

## Mathematical components

Word error rate tokenizes both strings with `str.split()` and computes token-level Levenshtein distance using dynamic programming.
WER is edit distance divided by the number of reference words.
An empty reference and empty hypothesis has WER `0.0`.
An empty reference and non-empty hypothesis has WER `1.0`.

Set Jaccard is intersection size divided by union size.
When both sets are empty, the configured empty-set score is returned.
Assertions and candidates are compared as sets, so list order does not affect their score.

## Mention assignment

Gold mentions are processed in input order.
Each gold mention receives the first still-unmatched prediction satisfying the selected exact matching key.
This deterministic one-to-one assignment preserves separate occurrences and prevents one prediction from satisfying multiple gold mentions.

Any gold mention without a prediction and any prediction left after assignment becomes an explicit unmatched record.
Every unmatched record receives `0.0` for text, assertions, and candidates.
A wrong type therefore produces one unmatched gold record and one unmatched prediction record.

Changing the matching policy changes assignment only.
All metric functions, penalties, weights, and reporting remain identical.

## Aggregation and report

For matched records, the evaluator reports indices, raw WER, text score, assertion Jaccard, and candidate Jaccard.
For unmatched records, it reports the available gold or prediction index and zero component scores.
Missing assertion or candidate fields behave as empty sets so type-dependent schemas use the same scoring path.

Each component score is the arithmetic mean over matched and unmatched records.
The final score is `0.3 * text_score + 0.3 * assertions_score + 0.4 * candidates_score` under the default policy.
When both entity lists are empty, every component score and the final score are `1.0`.

## Validation and failure behavior

Unknown matching policies are rejected.
Positions must be two-integer lists, excluding booleans.
Entity types and text used by a selected matching key must be strings.
Assertions and candidates must be lists of strings when present.
The empty-set score and component weights must be finite values between `0.0` and `1.0`, and weights must sum to `1.0` within floating-point tolerance.
Invalid evaluator inputs raise `ValueError` instead of being repaired or silently ignored.

Raw-offset validation remains the serializer boundary's responsibility because this evaluator receives entity lists rather than raw documents.

## Verification

Tests will first fail before implementation under the repository's TDD workflow.
They will cover WER substitutions, insertions, deletions, and empty references.
They will cover ordinary Jaccard values and both empty-set conventions.
They will verify deterministic one-to-one assignment of duplicate surface mentions at different positions.
They will verify that exact `(type, position)` can match differing text while exact `(type, text, position)` leaves the same pair unmatched.
They will verify explicit unmatched penalties, wrong-type behavior, component aggregation, custom weights, empty inputs, and invalid policies.

The complete repository test suite and Python compilation will run before the checkpoint is considered complete.

## Hidden assumptions

The organizer has confirmed the metric families and weights but has not disclosed complete mention assignment, position use, WER aggregation, missing-field behavior, or empty-set behavior.
The checkpoint document will separate the implemented mathematics from these provisional choices.
Future leaderboard probes may change one policy value at a time without creating another evaluator implementation.
