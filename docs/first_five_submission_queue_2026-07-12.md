# First Five Submission Queue - 2026-07-12

## Upload boundary

These five artifacts were generated from commit `0df35e5104fe02ed35a9da2106ea7f4359daa598`.
They use canonical input SHA-256 `46fe4a578b2c4478faa7c570b218218f539c0bbf1ea409168ae67a14ad86ca35`.
They use RxNorm archive SHA-256 `e81e29a27575718dc1f0cf80b1371b283bcba53f446f27fc85f74c71def99829`.
The active model budget is `0 / 9B`.

Only the `.zip` files listed below are upload artifacts.
Do not upload JSON build reports, semantic diffs, or `outputs/NON_SUBMITTABLE-empty-output.zip`.

## Queue

### 1. Precision drug baseline

- Artifact: `outputs/submissions/01_drugs_top1.zip`.
- SHA-256: `b5be3ef215b1134426211dc2e880f8d1c4ec406260ef4d3358f7157a0087fdd8`.
- Config: `configs/submissions/01_drugs_top1.json`.
- Config SHA-256: `1732070e6ef6cdc9f9053d811b9d5416d469328293ff4ea622be8d4a827bd7cd`.
- Parent: None.
- Primary change: Establish the first non-empty ontology-backed baseline.
- Predictions: 61 drugs in 28 non-empty documents, 61 candidates, and 46 assertion labels.
- Hypothesis: Conservative regimen-inclusive drug predictions with top-one pinned RxNorm candidates produce a measurable non-zero score without speculative entity types or codes.

### 2. Add laboratory pairs

- Artifact: `outputs/submissions/02_add_labs.zip`.
- SHA-256: `45a62dd2f8b89bdb4a80c42a327b18a3864a51fc314816d03af4f45bbdc842e1`.
- Config: `configs/submissions/02_add_labs.json`.
- Config SHA-256: `dc365dca4d1bea319aa1d8464e2e071bcd569b15afeee96d5848a1661240cfa8`.
- Parent: Submission 1.
- Primary change: Enable laboratory output.
- Predictions: 61 drugs, 51 laboratory names, and 51 laboratory results in 41 non-empty documents.
- Semantic diff: 102 added entities, zero removed entities, and zero changed existing entities.
- Hypothesis: Existing exact-offset laboratory rules add text credit with acceptable precision under the provisional laboratory schema.

### 3. Core drug spans

- Artifact: `outputs/submissions/03_core_spans.zip`.
- SHA-256: `3cec6e5821f00dd81b628569287a943b02be561b8062197127e784a3fe48fa36`.
- Config: `configs/submissions/03_core_spans.json`.
- Config SHA-256: `1a357d2340a718252443066c7d1c39e025ced85888dea1fc005850c00a2d7c16`.
- Parent: Submission 2.
- Primary change: Change drug span policy from regimen-inclusive to core.
- Predictions: The same 163 entities and 61 candidates as Submission 2.
- Semantic diff: 30 drug text and position changes, zero additions, zero removals, and zero candidate changes.
- Hypothesis: The evaluator may prefer recoverable medication-name or name-strength spans over full regimen spans for noisy lines.

### 4. Ingredient-only candidates

- Artifact: `outputs/submissions/04_ingredient_only.zip`.
- SHA-256: `82e6d50bfaf4ce896957b07c6ae8ddd9553de5c91ec6067ae00dbae558c40bb8`.
- Config: `configs/submissions/04_ingredient_only.json`.
- Config SHA-256: `8f702f657a07f594b61e7657d33a9c017b2ce4490bbf35c96aa2a6b3cea7e631`.
- Parent: Submission 2.
- Primary change: Restrict drug concepts to `IN`, `PIN`, and `MIN` term types.
- Predictions: 36 drugs plus 102 laboratory entities in 34 non-empty documents.
- Semantic diff: 25 removed drugs and 10 changed candidate sets.
- Hypothesis: Ingredient targets may score better than clinical-strength or branded targets despite reduced brand coverage in the no-license subset.

### 5. Top-two candidates

- Artifact: `outputs/submissions/05_top2.zip`.
- SHA-256: `b68ff3de6d2f54ab57c9a6fa0f3f542f34a4030438253b8cac3ba64b4057792b`.
- Config: `configs/submissions/05_top2.json`.
- Config SHA-256: `4fb8ea4ffc8f093431deda7cc97d0f55b845e8013546a03c80c5e8b5c4370c3a`.
- Parent: Submission 2.
- Primary change: Increase candidate output from top one to top two.
- Predictions: The same 163 entities as Submission 2 with 100 candidates instead of 61.
- Semantic diff: 39 changed candidate sets, zero entity additions, and zero entity removals.
- Hypothesis: Candidate recall may outweigh the Jaccard penalty for one additional deterministic lexical alternative.

## Verified acceptance evidence

- Every artifact contains exactly `output/1.json` through `output/100.json`.
- Every JSON entry passed the strict type-dependent serializer and raw-offset validator.
- Every emitted candidate occurs in the pinned RxNorm archive.
- No artifact contains an exact duplicate `(type, text, position)` identity within a document.
- All five artifacts are non-empty and have distinct SHA-256 checksums.
- Independent rebuilds of all five artifacts were byte-identical.
- Semantic diffs confirm one primary configuration change from each documented parent.

## Manual portal loop

Check the portal's remaining daily quota before uploading artifact 1.
After each upload, capture the portal submission identifier, timestamp, total score, and any component scores.
Record the actual result in `docs/submissions.csv` before uploading the next artifact.
If an early score makes a later hypothesis redundant, stop and return the result so the remaining slot can test a higher-information one-variable change.

The public score is experimental evidence, not automatic proof of private-test generalization.
