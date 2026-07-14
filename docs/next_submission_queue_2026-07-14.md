# Next Submission Queue - 2026-07-14

## Submission status

`outputs/submissions/06_add_symptoms.zip` was uploaded on 2026-07-14 at 16:03 Asia/Bangkok and scored `9.86290`.
It is now the promoted stable baseline.

- Artifact SHA-256: `ea910695300e32bfa15082cc64c212c6566e063307342fc66dbdfb369bf888ed`.
- Config: `configs/submissions/06_add_symptoms.json`.
- Config SHA-256: `80d245f32e2af5b7c3db8c36a34ce13511c0d1fa6eb87375f8deb99426c9a25c`.
- Implementation commit: `7a7c576df978ecd74d3cf7b44bf29272f6aa2ccb`.
- Parent submission: `local-s002`.
- Parent score: `5.00940`.
- Score delta: `+4.85350`.
- Input SHA-256: `46fe4a578b2c4478faa7c570b218218f539c0bbf1ea409168ae67a14ad86ca35`.
- RxNorm SHA-256: `e81e29a27575718dc1f0cf80b1371b283bcba53f446f27fc85f74c71def99829`.
- Active model budget: `0 / 9B`.

## Portal result

- Final score: `9.86290`.
- WER: `88.75`.
- Derived text score: `11.25`.
- Assertion Jaccard: `13.0448`.
- Candidate Jaccard: `6.436`.
- `num_scored`: `100`.
- `num_records`: `100`.

## Validated conclusion

Conservative exact-offset symptom coverage from explicit chief-complaint and current-symptom structures materially improves the text and assertion components while all drug, laboratory, and candidate output remains fixed.
The result is reproducible, interpretable, and plausibly private-test generalizable.

## Prediction summary

- Total entities: `415`.
- Drugs: `61`.
- Laboratory names: `51`.
- Laboratory results: `51`.
- Symptoms: `252`.
- Candidate identifiers: `61`.
- Assertion labels: `68`.
- Non-empty documents: `70`.
- Empty documents: `30`.
- Output records: `100`.

## Semantic diff from Submission 2

- Added symptom entities: `252`.
- Removed entities: `0`.
- Changed existing entities: `0`.
- Changed candidates: `0`.
- Changed assertions on existing entities: `0`.
- Changed text, type, or position on existing entities: `0`.

The diff report is `outputs/submissions/02_add_labs_to_06_add_symptoms.diff.json`.
The build report is `outputs/submissions/06_add_symptoms.report.json`.

## Next milestone

Do not spend the next guaranteed slot on another minor symptom, span, or candidate-cardinality ablation.
Build diagnosis extraction with pinned ICD linking on top of Submission 6, validate it offline, and submit the integrated improvement when it is ready.
