# Diagnosis Submission Queue - 2026-07-14

## Recommended upload

Upload only `outputs/submissions/07_add_diagnoses.zip`.

- Artifact SHA-256: `f220956151b29cf60d9e7a94ab475b7bbe8b8a41276cb1b83872a733b5d06546`.
- Artifact size: `62121` bytes.
- Config: `configs/submissions/07_add_diagnoses.json`.
- Config SHA-256: `b52be96023032a69b0ddbda7471e5903dc9136ab13ac544171b3eb7b821a8374`.
- Implementation commit: `135ce8159ed87821ded64d34bc4d27fd3a66545c`.
- Parent submission: `local-s006`.
- Parent score: `9.86290`.
- Input SHA-256: `46fe4a578b2c4478faa7c570b218218f539c0bbf1ea409168ae67a14ad86ca35`.
- RxNorm SHA-256: `e81e29a27575718dc1f0cf80b1371b283bcba53f446f27fc85f74c71def99829`.
- ICD-10 SHA-256: `72b81f78e3fb971c2c44250d3a5ae67f7c41bef3b5bf1ded59954250e479212f`.
- Active model budget: `0 / 9B`.

## Product hypothesis

Adding exact ontology-backed diagnoses in diagnosis-bearing clinical contexts improves text, assertion, and candidate components while every Submission 6 entity remains fixed.
This is an integrated product capability, not a minor cardinality or span probe.
The leaderboard submission is the external validation step for the hidden ICD namespace and annotation policy.

## Prediction summary

- Total entities: `504`.
- Drugs: `61`.
- Laboratory names: `51`.
- Laboratory results: `51`.
- Symptoms: `252`.
- Diagnoses: `89` across `46` records and `49` distinct ICD codes.
- Candidate occurrences: `150`, consisting of `61` drug candidates and `89` diagnosis candidates.
- Assertion labels: `138`.
- Non-empty records: `79`.
- Empty records: `21`.

## Isolated semantic change from Submission 6

- Added entities: `89`.
- Removed entities: `0`.
- Changed existing entities: `0`.
- Changed existing candidates: `0`.
- Changed existing assertions: `0`.
- Changed text: `0`.
- Changed type: `0`.
- Changed position: `0`.

Every added entity has type `CHẨN_ĐOÁN`.
The diff report is `outputs/submissions/06_add_symptoms_to_07_add_diagnoses.diff.json`.

## Validation evidence

The official Vietnamese ICD-10 base catalog was pinned as 15,827 hierarchy nodes with 13,940 leaf nodes and 13,906 unambiguous leaf-backed titles.
The raw snapshot is untracked, not bundled, and restricted to internal competition use because no explicit redistribution license was located.

Every diagnosis was manually inspected with document, text, candidate, assertion, and position.
The full audit removed ICD chapter `R` symptom and sign codes plus `U82-U85` antimicrobial-resistance supplements from diagnosis output through tested ontology-level rules.
Every remaining diagnosis candidate occurs in the pinned leaf-code set.
Every entity satisfies `raw_text[start:end] == text`.

The final ZIP contains exactly `output/1.json` through `output/100.json`.
Two independent builds produced the same artifact SHA-256.
The complete suite passes `109` tests.

The rebuild ZIP, build reports, semantic diff, ontology snapshot, and provenance files are not upload artifacts.

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

The result will be recorded as `local-s007` if the portal identifier is not shown.
