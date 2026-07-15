# Submission Results - 2026-07-15

## Submission 9: Finalize grounded Qwen packaging

- Local identifier: `local-s009` because the portal submission identifier was not shown in the supplied result.
- Submitted: 2026-07-15 at 12:28 Asia/Bangkok.
- Artifact: `outputs/submissions/09_qwen_grounded.zip`.
- Artifact SHA-256: `90921e43e204909cfe0c0c5c47c350d9b53634b427f5a3fff5f29ead9df4e142`.
- Config: `configs/submissions/08_qwen_grounded.json`.
- Implementation commit: `604371d488744c3ba0d5e80ad6b2f583eb6e8412`.
- Parent: `local-s008`.
- Final score: `16.13250`.
- Score delta: `0.00000`.
- WER: `84.6803`.
- Assertion Jaccard: `16.933`.
- Candidate Jaccard: `16.1416`.
- `num_scored`: `100`.
- `num_records`: `100`.

The final archive contains exactly `output/1.json` through `output/100.json`.
The deterministic builder produced 521 entities, 150 linked candidates, and 139 assertions from 636 Qwen proposals.

This submission is packaging-only and has no semantic prediction change from Submission 8.
The earlier `0.36220` result came from submitting the intermediate proposal archive directly, which contained proposal records rather than evaluator-ready output records.
The corrected archive reproduces Submission 8's `16.13250` score and confirms the final packaging path.