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

## Interpretation

Submission 2 adds 51 laboratory names and 51 laboratory results without changing any drug prediction.
The unchanged candidate score confirms that the experiment did not disturb drug linking.
The text improvement shows that at least part of the laboratory schema and span output receives evaluator credit.
The assertion improvement is an evaluator-side effect of adding laboratory records with no assertion fields or of changed mention assignment; the public metrics do not distinguish those mechanisms.

The gain is reproducible, isolated, interpretable, and plausibly private-test generalizable.
Submission 2 is promoted as the stable rule baseline.

## Recommended next experiment

Upload Submission 3, which keeps all 163 entities and 61 candidate identifiers from Submission 2 but changes 30 drug text and position spans from noisy regimen-inclusive boundaries to recoverable core boundaries.
This directly probes span policy while candidate sets, assertions, laboratory entities, and entity count remain frozen.
