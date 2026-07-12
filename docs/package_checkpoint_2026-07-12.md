# Package checkpoint - 2026-07-12

## Verified evidence

- Source: `input.zip`, SHA-256 `46fe4a578b2c4478faa7c570b218218f539c0bbf1ea409168ae67a14ad86ca35`, accessed 2026-07-12.
- Artifact: `outputs/NON_SUBMITTABLE-empty-output.zip`.
- Evidence: The builder read all 100 documents, validated one empty prediction list per document, built the ZIP in memory, reopened every entry, parsed every JSON value, and validated each value against its raw document before writing.
- Result: The archive contains exactly 100 entries, zero entities, and 100 empty documents.
- Result: The archive occupies 10,706 bytes and has SHA-256 `7fad042299b7c15f185ce4d083e4b1a55ecdc600d110f9ed85be382dd506bbd4`.
- Confidence: High for entry membership, JSON validity, byte size, checksum, and reproducibility because each property is covered by executable checks.
- Strategic impact: The repository can now exercise the complete output format boundary without inventing candidates or consuming a leaderboard submission.

## Deterministic package policy

- Input and prediction mappings must contain exactly `input/1.txt` through `input/100.txt`.
- Mapping insertion order is ignored and archive entries are written in numeric order.
- The archive contains only `output/1.json` through `output/100.json`.
- Every entry uses fixed timestamp metadata and `ZIP_STORED` compression.
- The destination parent must exist and an existing destination is never overwritten.
- The active model parameter budget remains `0 / 9B`.

## Non-submittable warning

This artifact is format-only and must never be uploaded to the competition.
It is intentionally excluded from `docs/submissions.csv` because it tests no leaderboard hypothesis.
Its all-empty predictions provide no information about extraction, linking, assertion accuracy, evaluator matching, or score.

## Next checkpoint

Implement the provisional local evaluator with mention matching, WER, assertion Jaccard, and candidate Jaccard policies isolated in configuration.
