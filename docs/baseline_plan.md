# End-to-End Rule Baseline Plan

## Goal and constraints

Build a reproducible offline baseline for all 100 documents before model training.
Keep raw text immutable, preserve duplicates, invent no codes, and add no unapproved fields.
All models combined must remain at or below 9B, with the current budget at zero.

Ontology, recognition, span, candidate, and position policies are hidden evaluator variables.
Keep them configurable and infer them through controlled one-variable experiments.

## Architecture

```text
raw document
  -> offset-safe loader and mapped normalized view
  -> section parser and line roles
  -> rule extraction
  -> scoped assertions
  -> versioned ontology retrieval
  -> deterministic constraints
  -> configurable serializer and validator
  -> provisional evaluator
  -> output.zip
```

## Checkpoints

### 0. Freeze evidence

Record artifact hashes, tests, assumptions, and official examples.
Stop if canonical hashes or fixture spans change unexpectedly.

### 1. Offset-safe loader

Strictly decode UTF-8, preserve line endings, and map normalized boundaries to raw indices.
Accept only when every emitted span slices exact raw text.

### 2. Sections and line roles

Parse observed headers without dropping unknown content or modifying offsets.
Audit unknown headers across all 100 documents before expanding complexity.

### 3. Drug and laboratory extraction

Extract exact raw spans for drug regimens and laboratory names or results.
Support ranges, routes, frequencies, PRN, decimal commas, units, and multiple results.

### 4. Symptoms, diagnoses, and assertions

Use clause boundaries, section priors, negation terminators, temporal cues, and experiencer cues.
Keep type and assertion thresholds configurable.

### 5. Versioned ontology ingestion

Ingest legally usable ICD and RxNorm references with provenance and checksum.
For RxNorm, retain active and historical concepts plus replacement relationships.
Keep status, term type, branded or generic level, combination or component behavior, and candidate cardinality configurable.
Stop only for missing license or provenance, not for hidden organizer policy.

### 6. Serializer and validator

Validate fields, offsets, duplicate preservation, candidate provenance, filenames, and UTF-8.
Keep hidden schema and core versus modifier-inclusive span alternatives isolated.

### 7. Provisional evaluator

Implement WER, Jaccard, candidate weighting, and configurable mention matching.
Do not present one matching policy as official.

### 8. One-command baseline

Generate 100 JSON files, validation reports, semantic prediction diff, and `output.zip` from pinned inputs and configuration.

### 9. Error analysis

Bucket errors by span, type, assertion, section, parsing, ICD retrieval, and RxNorm retrieval.
Add models only for measured gaps and update the parameter ledger first.

## High-information experiments

Every experiment freezes all variables except the named primary change and records the commit, configuration, prediction diff, score delta, conclusion, confidence, and generalization class.

1. Top-one versus thresholded or top-two candidates.
2. Exact-only versus fuzzy lexical linking.
3. Active-only versus active-plus-historical RxNorm.
4. Ingredient versus clinical-drug versus branded-drug candidates.
5. Combination RXCUI versus component RXCUIs.
6. Core span versus modifier-inclusive span by entity type.
7. Negation, history, and family assertion ablations.
8. Type-specific precision threshold sweeps.
9. Exact raw LF offsets versus one alternative position strategy after all other predictions stabilize.

Never hard-code public-test data or bundle unrelated changes in a probing submission.
