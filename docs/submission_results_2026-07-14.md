# Submission Results - 2026-07-14

## Submission 6: Add structured symptoms

- Local identifier: `local-s006` because the portal submission identifier was not shown in the supplied result.
- Submitted: 2026-07-14 at 16:03 Asia/Bangkok.
- Artifact: `outputs/submissions/06_add_symptoms.zip`.
- Artifact SHA-256: `ea910695300e32bfa15082cc64c212c6566e063307342fc66dbdfb369bf888ed`.
- Config: `configs/submissions/06_add_symptoms.json`.
- Implementation commit: `7a7c576df978ecd74d3cf7b44bf29272f6aa2ccb`.
- Parent: `local-s002`.
- Final score: `9.86290`.
- Score delta: `+4.85350`.
- WER: `88.75`.
- Derived text score: `11.25`.
- Text score delta: `+7.25`.
- Assertion Jaccard: `13.0448`.
- Assertion Jaccard delta: `+8.9282`.
- Candidate Jaccard: `6.436`.
- Candidate Jaccard delta: `0`.
- `num_scored`: `100`.
- `num_records`: `100`.

The displayed score is consistent with the documented weighting after rounding:

```text
0.3 * 11.25 + 0.3 * 13.0448 + 0.4 * 6.436 = 9.86284
```

The score delta decomposes as follows before portal rounding:

```text
0.3 * 7.25 + 0.3 * 8.9282 + 0.4 * 0 = 4.85346
```

## Interpretation

Submission 6 adds 252 audited symptom entities without removing or changing any Submission 2 entity.
The unchanged candidate score cleanly confirms that drug linking was unaffected.
The text and assertion gains show that conservative structured symptom coverage addresses a large generalizable recall gap.
The gain is substantially larger than every earlier experiment and is directly attributable to the added entity class.

Submission 6 is promoted as the new stable baseline.
Future integrated submissions should derive from it unless a controlled result establishes a better generalizable parent.

## Competitive position and next milestone

The reported leading score is approximately `53`, leaving a public-score gap of `43.13710` from Submission 6.
The remaining gap is too large for minor span or candidate-cardinality probes.
The next primary milestone is high-precision diagnosis extraction backed by a pinned and documented ICD source.
That milestone can improve text, assertion, and candidate components together and should be developed as a complete product capability before its leaderboard validation.
