# Submission Results - 2026-07-12

## Submission 1: Precision drug baseline

- Local identifier: `local-s001` because the portal submission identifier was not shown in the supplied result.
- Submitted: 2026-07-12 at 18:18 Asia/Bangkok.
- Artifact: `outputs/submissions/01_drugs_top1.zip`.
- Artifact SHA-256: `b5be3ef215b1134426211dc2e880f8d1c4ec406260ef4d3358f7157a0087fdd8`.
- Commit: `0df35e5104fe02ed35a9da2106ea7f4359daa598`.
- Final score: `3.47310`.
- WER: `98.403`.
- Derived text score: `100 - 98.403 = 1.597`.
- Assertion Jaccard: `1.3986`.
- Candidate Jaccard: `6.436`.
- `num_scored`: `100`.
- `num_records`: `100`.

The displayed score is consistent with the documented weighting after rounding:

```text
0.3 * 1.597 + 0.3 * 1.3986 + 0.4 * 6.436 = 3.47308
```

The portal displays `3.47310` after its own precision and rounding behavior.

## Interpretation

The baseline successfully earns non-zero credit from ontology-backed drug predictions.
Candidate linking is currently the strongest component and contributes approximately `2.5744` weighted points.
Text contributes approximately `0.4791` weighted points, showing that entity recall and span coverage are still extremely limited.
Assertions contribute approximately `0.41958` weighted points and are constrained by the small number of recognized mentions.

This result does not isolate RxNorm concept granularity because missing symptom, diagnosis, and laboratory entities dominate text recall.
The result is reproducible and interpretable but remains `unknown` for private-test generalization.

## Recommended next experiment

Upload Submission 2, which adds 51 laboratory-name and 51 laboratory-result entities while leaving all 61 drug predictions unchanged.
This is the cleanest available test of whether exact-offset laboratory coverage improves text score under the provisional laboratory schema.
Candidate and assertion behavior for existing drugs remains frozen.
