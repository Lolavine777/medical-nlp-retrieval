# Post-Upgrade Drift-Resilience Design

## Goal

Make the pipeline safe and measurable when the organizer changes the input dataset, output contract, ontology snapshot, or evaluator behavior on 2026-07-16.

The first post-upgrade action must be a reproducible control run, not model tuning.

## Current evidence

- Submission 9 reproduced Submission 8 at `16.13250` after the proposal archive was converted through the deterministic builder.
- The proposal-only archive scored `0.36220`, proving that artifact format is a separate failure mode from model quality.
- The current pipeline assumes 100 documents named `input/1.txt` through `input/100.txt`.
- The current strongest configuration uses deterministic extraction, pinned RxNorm and ICD-10 snapshots, and optional grounded Qwen proposals.
- The new organizer announcement explicitly states that the problem and dataset will be upgraded for greater difficulty and realism.

## Design

### 1. Immutable legacy control

Keep the current pipeline and Submission 9 artifact reproducible as a legacy control.

Do not retune the old 100-document distribution after the upgrade notice.

The legacy control records its input hash, ontology hashes, config hash, commit, and output checksum.

### 2. Upgrade intake and contract audit

Add one read-only intake command that accepts a new input root or ZIP and emits a machine-readable audit before prediction.

The audit must report:

- document count and deterministic document names;
- raw byte hashes, UTF-8 validity, line endings, and duplicate-document detection;
- whether the input is a ZIP or directory and its exact archive structure;
- observed text length, section headers, line-role vocabulary, and entity-density proxies;
- available ontology files, provenance metadata, and checksums;
- whether the existing output serializer accepts a minimal validated record;
- whether the existing configuration can run without silently dropping all entities.

The intake must fail closed on ambiguous sources, mutated raw text, duplicate names, invalid UTF-8, or unknown archive layout.

It must never normalize or rewrite raw documents.

### 3. Drift report

Compare the upgraded corpus against the legacy audit without treating the legacy corpus as ground truth.

The report must quantify:

- document and length distribution changes;
- new section and line-role vocabulary;
- frequency changes for drug, laboratory, symptom, and diagnosis cues;
- candidate-link coverage under the pinned ontologies;
- parse, grounding, schema, and linker rejection rates;
- counts of empty final documents and entities by type.

Every comparison must label results as distributional evidence, not evaluator truth.

### 4. Two-control execution

The first two post-upgrade runs are:

1. deterministic rule-only configuration;
2. the existing grounded-Qwen configuration, only if the intake audit confirms compatible model proposal and final-output contracts.

These controls establish whether the upgrade changed data distribution, output semantics, or both.

No new model is trained before both controls and the drift report exist.

### 5. Adaptation priority

After the controls, spend guaranteed submissions in this order:

1. repair contract or packaging incompatibilities;
2. recover high-confidence entities affected by new sections or vocabulary;
3. improve ontology candidate coverage and ranking;
4. improve assertion behavior on newly observed contexts;
5. only then test a model or model-assisted branch.

One primary variable changes per probing submission.

## Failure handling

- If the output schema changes, stop before leaderboard submission and update the serializer and validator from organizer evidence.
- If only the corpus changes, retain the output contract and compare rule-only versus Qwen controls.
- If ontology versions change, ingest and checksum the new snapshots before changing linking behavior.
- If the evaluator appears to change, record the observation as a hidden-policy hypothesis and do not hard-code a workaround from one public result.
- If any control produces zero entities or zero candidates unexpectedly, treat it as an intake or contract failure, not a model-quality result.

## Testing and acceptance

The implementation is accepted only when:

- legacy inputs still pass all existing tests unchanged;
- upgraded inputs can be audited without modifying raw bytes;
- ambiguous or malformed sources fail with actionable diagnostics;
- two runs on identical inputs produce identical audit and output checksums;
- the control reports distinguish proposal evidence from evaluator-ready output;
- every post-upgrade submission can be traced to commit, config, checksums, parent, hypothesis, and score.

## Explicit non-goals

- No immediate large-model training.
- No synthetic data generation before the upgraded distribution is measured.
- No replacement of the stable pipeline with a second divergent codebase.
- No inference about hidden evaluator policy from the announcement alone.
