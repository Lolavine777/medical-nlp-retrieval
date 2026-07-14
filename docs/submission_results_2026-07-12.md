# Submission Results - 2026-07-12

## Submission 1: Precision drug baseline

- Local identifier: `local-s001` because the portal submission identifier was not shown in the supplied result.
- Submitted: 2026-07-12 at 18:18 Asia/Bangkok.
- Artifact: `outputs/submissions/01_drugs_top1.zip`.
- Artifact SHA-256: `b5be3ef215b1134426211dc2e880f8d1c4ec406260ef4d3358f7157a0087fdd8`.
- Commit: `0df35e5104fe02ed35a9da2106ea7f4359daa598`.
- Final score: `3.47310`.
- WER: `98.403`.
- Derived text score: `1.597`.
- Assertion Jaccard: `1.3986`.
- Candidate Jaccard: `6.436`.
- `num_scored`: `100`.
- `num_records`: `100`.

The displayed score is consistent with the documented weighting after rounding:

```text
0.3 * 1.597 + 0.3 * 1.3986 + 0.4 * 6.436 = 3.47308
```

The baseline earns non-zero credit, but missing entity coverage dominates text and assertion performance.

## Submission 2: Add laboratory pairs

- Local identifier: `local-s002` because the portal submission identifier was not shown in the supplied result.
- Submitted: 2026-07-12 at 18:29 Asia/Bangkok.
- Artifact: `outputs/submissions/02_add_labs.zip`.
- Artifact SHA-256: `45a62dd2f8b89bdb4a80c42a327b18a3864a51fc314816d03af4f45bbdc842e1`.
- Parent: `local-s001`.
- Final score: `5.00940`.
- Score delta: `+1.53630`.
- WER: `96`.
- Derived text score: `4`.
- Text score delta: `+2.403`.
- Assertion Jaccard: `4.1166`.
- Assertion Jaccard delta: `+2.718`.
- Candidate Jaccard: `6.436`.
- Candidate Jaccard delta: `0`.
- `num_scored`: `100`.
- `num_records`: `100`.

The displayed score is consistent with the documented weighting after rounding:

```text
0.3 * 4 + 0.3 * 4.1166 + 0.4 * 6.436 = 5.00938
```

The score delta decomposes cleanly:

```text
0.3 * 2.403 + 0.3 * 2.718 + 0.4 * 0 = 1.53630
```

Submission 2 adds 51 laboratory names and 51 laboratory results without changing any drug prediction.
The unchanged candidate score confirms that the experiment did not disturb drug linking.
The text improvement shows that at least part of the laboratory schema and span output receives evaluator credit.
The assertion improvement is an evaluator-side effect of adding laboratory records with no assertion fields or of changed mention assignment; the public metrics do not distinguish those mechanisms.

The gain is reproducible, isolated, interpretable, and plausibly private-test generalizable.
Submission 2 is promoted as the stable rule baseline.

## Submission 3: Core drug spans

- Local identifier: `local-s003` because the portal submission identifier was not shown in the supplied result.
- Submitted: 2026-07-12 at 18:43 Asia/Bangkok.
- Artifact: `outputs/submissions/03_core_spans.zip`.
- Artifact SHA-256: `3cec6e5821f00dd81b628569287a943b02be561b8062197127e784a3fe48fa36`.
- Parent: `local-s002`.
- Final score: `5.02730`.
- Score delta: `+0.01790`.
- WER: `96.1096`.
- Derived text score: `3.8904`.
- Text score delta: `-0.1096`.
- Assertion Jaccard: `4.1166`.
- Assertion Jaccard delta: `0`.
- Candidate Jaccard: `6.5631`.
- Candidate Jaccard delta: `+0.1271`.
- `num_scored`: `100`.
- `num_records`: `100`.

The displayed score is consistent with the documented weighting after rounding:

```text
0.3 * 3.8904 + 0.3 * 4.1166 + 0.4 * 6.5631 = 5.02734
```

The score delta decomposes as follows before portal rounding:

```text
0.3 * -0.1096 + 0.3 * 0 + 0.4 * 0.1271 = 0.01796
```

Core spans produced the best displayed score, but the gain is marginal and mixed.
The candidate gain indicates that changed boundaries affected mention matching, while the lower text score argues against a broad span-policy conclusion.
Because official examples support regimen-inclusive drug spans, this result is not promoted to the stable baseline.

## Submission 4: Ingredient-only candidates

- Local identifier: `local-s004` because the portal submission identifier was not shown in the supplied result.
- Submitted: 2026-07-12 at 18:59 Asia/Bangkok.
- Artifact: `outputs/submissions/04_ingredient_only.zip`.
- Artifact SHA-256: `82e6d50bfaf4ce896957b07c6ae8ddd9553de5c91ec6067ae00dbae558c40bb8`.
- Parent: `local-s002`.
- Final score: `3.71050`.
- Score delta: `-1.29890`.
- WER: `96.5857`.
- Derived text score: `3.4143`.
- Text score delta: `-0.5857`.
- Assertion Jaccard: `3.5828`.
- Assertion Jaccard delta: `-0.5338`.
- Candidate Jaccard: `4.0285`.
- Candidate Jaccard delta: `-2.4075`.
- `num_scored`: `100`.
- `num_records`: `100`.

The displayed score is consistent with the documented weighting after rounding:

```text
0.3 * 3.4143 + 0.3 * 3.5828 + 0.4 * 4.0285 = 3.71053
```

The score delta decomposes as follows before portal rounding:

```text
0.3 * -0.5857 + 0.3 * -0.5338 + 0.4 * -2.4075 = -1.29885
```

Strict ingredient-only filtering is rejected.
It removed 25 drug mentions as well as changing 10 candidate sets, so the result cannot isolate ingredient granularity from lost drug coverage.
The strong loss still shows that the pipeline must preserve branded and clinical-drug coverage.

## Submission 5: Top-two candidates

- Local identifier: `local-s005` because the portal submission identifier was not shown in the supplied result.
- Submitted: 2026-07-12 at 19:21 Asia/Bangkok.
- Artifact: `outputs/submissions/05_top2.zip`.
- Artifact SHA-256: `b68ff3de6d2f54ab57c9a6fa0f3f542f34a4030438253b8cac3ba64b4057792b`.
- Parent: `local-s002`.
- Final score: `4.30890`.
- Score delta: `-0.70050`.
- WER: `96`.
- Derived text score: `4`.
- Text score delta: `0`.
- Assertion Jaccard: `4.1166`.
- Assertion Jaccard delta: `0`.
- Candidate Jaccard: `4.6849`.
- Candidate Jaccard delta: `-1.7511`.
- `num_scored`: `100`.
- `num_records`: `100`.

The displayed score is consistent with the documented weighting after rounding:

```text
0.3 * 4 + 0.3 * 4.1166 + 0.4 * 4.6849 = 4.30896
```

The score delta is entirely explained by candidate output before portal rounding:

```text
0.3 * 0 + 0.3 * 0 + 0.4 * -1.7511 = -0.70044
```

Top-two candidates are rejected with high confidence.
The experiment changed only 39 candidate sets, so the loss cleanly establishes that one deterministic candidate per drug is the better policy.

## Batch conclusion and roadmap

The first five-submission batch is complete.
Submission 2 remains the stable rule baseline at `5.00940`, while Submission 3 is the best public score at `5.02730` but is not promoted because its small gain conflicts with its text component and official span evidence.

The batch resolves three major variables:

- Laboratory name and result coverage is valuable and stays enabled.
- Strict ingredient-only filtering is harmful because it sacrifices drug coverage.
- Top-two candidate output is harmful, so top-one remains mandatory.

The system is now in Phase C leaderboard calibration with a working Phase A baseline.
The next highest-information improvement is top-one candidate reranking that preserves every currently linked drug entity, followed by expanding conservative drug extraction coverage.
Model training remains deferred until those rule and ontology improvements are exhausted.
