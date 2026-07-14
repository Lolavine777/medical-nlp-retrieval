# Next Submission Queue - 2026-07-14

## Recommended upload

Upload only `outputs/submissions/06_add_symptoms.zip`.

- Artifact SHA-256: `ea910695300e32bfa15082cc64c212c6566e063307342fc66dbdfb369bf888ed`.
- Config: `configs/submissions/06_add_symptoms.json`.
- Config SHA-256: `80d245f32e2af5b7c3db8c36a34ce13511c0d1fa6eb87375f8deb99426c9a25c`.
- Implementation commit: `7a7c576df978ecd74d3cf7b44bf29272f6aa2ccb`.
- Parent submission: `local-s002`.
- Parent score: `5.00940`.
- Input SHA-256: `46fe4a578b2c4478faa7c570b218218f539c0bbf1ea409168ae67a14ad86ca35`.
- RxNorm SHA-256: `e81e29a27575718dc1f0cf80b1371b283bcba53f446f27fc85f74c71def99829`.
- Active model budget: `0 / 9B`.

## Controlled hypothesis

Conservative exact-offset symptom coverage from explicit chief-complaint and current-symptom structures improves the text and assertion components while all drug, laboratory, and candidate output remains fixed.

Submission 2 is the parent because it is the promoted stable baseline.
Submission 3 has a marginally higher public score, but its mixed span signal was not promoted.

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
Neither JSON report is an upload artifact.
The rebuild and audit ZIP files are verification artifacts and must not be uploaded.

## Verification evidence

Every entity passed the strict type-dependent serializer and exact raw-offset validator.
Every drug candidate occurs in the pinned RxNorm archive.
The final ZIP contains exactly `output/1.json` through `output/100.json`.
Three independent builds produced the same artifact SHA-256.
The corpus precision audit inspected every generated symptom and removed general event, procedure, follow-up, device, metadata, and normal-state false-positive patterns through tested structural rules.

## Portal feedback to return

After manual upload, return:

- Portal submission identifier if shown.
- Submission timestamp.
- Final score.
- WER.
- `J_assertion`.
- `J_candidates`.
- `num_scored`.
- `num_records`.

The result will be recorded as `local-s006` if the portal identifier is not shown.
