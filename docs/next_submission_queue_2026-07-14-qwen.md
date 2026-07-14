# Next Submission Queue - Grounded Qwen

## Upload candidate

Submission `local-s008` is ready for one portal evaluation.
The upload artifact is `outputs/submissions/08_qwen_grounded.zip`.
Its SHA-256 is `90921e43e204909cfe0c0c5c47c350d9b53634b427f5a3fff5f29ead9df4e142`.
The artifact was built from commit `6740c683bdf42240905dc33e2954128b40f42895` and `configs/submissions/08_qwen_grounded.json`.
Its parent is `local-s007` with portal score `15.86380`.

## Model evidence

The only active model is `Qwen/Qwen3-4B-Instruct-2507` at revision `1b4199c4f36b0cef378bfb12390c18780c18af4c`.
The active parameter budget is `4,000,000,000 / 9,000,000,000`.
The prompt SHA-256 is `c70bfb5e8c2b9e02ff8365ecc4685941473dba061337fd2d3f89b297715798cd`.
The transferred proposal ZIP SHA-256 is `44f1647f3680f251851dc36773cc2ceb51d7c7e2b6021d5e5771d27feaec409e`.
All 100 proposal records matched the canonical input hashes and strict manifest schema.
The run produced 593 valid proposals and 56 fail-closed parse errors.

## Deterministic gates

The builder accepted 17 short atomic symptom additions.
It rejected 139 proposals for invalid sections, 309 for invalid structure, 64 for stable overlap, and 62 for missing pinned links.
The semantic diff reports 17 additions, zero removals, and zero changes to text, type, position, candidates, or assertions from Submission 7.
The independent rebuild SHA-256 is also `90921e43e204909cfe0c0c5c47c350d9b53634b427f5a3fff5f29ead9df4e142`.
The complete addition audit is stored in `outputs/submissions/07_add_diagnoses_to_08_qwen_grounded.diff.json`.

## Hypothesis and decision rule

The hypothesis is that grounded Qwen proposals recover short symptom mentions missed by the stable structural extractor without degrading existing entities.
Promote this configuration only if the portal gain is interpretable against Submission 7 and is plausibly private-test generalizable.
Reject or revise it if the added symptoms reduce the overall score or produce a mixed component loss inconsistent with improved mention coverage.
